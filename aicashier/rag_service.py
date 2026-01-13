import os
from dotenv import load_dotenv
import chromadb
import re
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_google_genai import GoogleGenerativeAI
from langchain_chroma import Chroma
from django.conf import settings
from django.apps import apps

load_dotenv()

# ===== Voice Command Management =====
class VoiceCommandManager:
    """จัดการคำสั่งเสียง (เพิ่ม/ลบ/เอาออก) จากฐานข้อมูล AISettings"""
    
    @staticmethod
    def get_voice_commands():
        """ดึงคำสั่งเสียงจาก AISettings"""
        try:
            AISettings = apps.get_model('aicashier', 'AISettings')
            settings_obj = AISettings.objects.first()
            if not settings_obj or not settings_obj.voice_commands:
                return VoiceCommandManager.get_default_commands()
            
            # Parse voice commands from text format
            # Format: "คำภาษาไทย|คำภาษาอังกฤษ" per line
            commands = {
                'add': [],
                'decrease': [],
                'delete': []
            }
            
            lines = settings_obj.voice_commands.strip().split('\n')
            for line in lines:
                line = line.strip()
                if not line or '|' not in line:
                    continue
                
                thai, eng = line.split('|', 1)
                thai = thai.strip().lower()
                eng = eng.strip().lower()
                
                # Classify based on keywords (จะต้องเพิ่ม logic ให้)
                if any(kw in thai or kw in eng for kw in ['เพิ่ม', 'add']):
                    commands['add'].extend([thai, eng])
                elif any(kw in thai or kw in eng for kw in ['ลด', 'decrease', 'ลดลง']):
                    commands['decrease'].extend([thai, eng])
                elif any(kw in thai or kw in eng for kw in ['ลบ', 'delete', 'remove', 'เอาออก']):
                    commands['delete'].extend([thai, eng])
            
            return commands
        except Exception as e:
            print(f"[VoiceCommand] Error loading commands: {e}")
            return VoiceCommandManager.get_default_commands()
    
    @staticmethod
    def get_default_commands():
        """คำสั่งเสียงค่าเริ่มต้น"""
        return {
            'add': ['เพิ่ม', 'add', 'ใส่', 'สั่ง', 'ซื้อ'],
            'decrease': ['ลด', 'decrease', 'ลดลง', 'ลดจำนวน', 'reduce'],
            'delete': ['ลบ', 'delete', 'remove', 'เอาออก', 'หยิบออก', 'ถอด']
        }

class RAGService:
    def __init__(self):
        self.api_key = os.getenv('GEMINI_API_KEY')
        try:
            model_path = os.path.join(
                settings.BASE_DIR, 
                'aicashier', 
                'models', 
                'paraphrase-multilingual-MiniLM-L12-v2'
            )
            if not os.path.exists(model_path):
                raise FileNotFoundError(f"ไม่เจอไฟล์โมเดลที่ {model_path}")
            
            self.embeddings = HuggingFaceEmbeddings(
                model_name=model_path,
                model_kwargs={'device': 'cpu'}
            )
            print("Using local HuggingFace embeddings")
        except Exception as e:
            print(f"Error: {e}")
            
        # Setup ChromaDB
        self.chroma_path = os.path.join(settings.BASE_DIR, 'data', 'chroma')
        os.makedirs(self.chroma_path, exist_ok=True)
        
        self.chroma_client = chromadb.PersistentClient(path=self.chroma_path)
        self.collection_name = "products_collection"
        
        self.vector_store = Chroma(
            client=self.chroma_client,
            collection_name=self.collection_name,
            embedding_function=self.embeddings,
        )
        print("Vector store initialized (collection: products_collection)")
        
        # Setup LLM (Google Gemini)
        try:
            self.llm = GoogleGenerativeAI(
                model="gemini-2.5-flash",
                google_api_key=self.api_key,
                temperature=0.5
            )
            print("Using Google Gemini LLM")
        except Exception as e:
            print(f"Google LLM not available")
            
        
        self.text_splitter = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=100)
        
        # Load products from database into RAG 
        self._load_products_from_db_optimized()
        
        # Load voice commands from settings
        self.voice_commands = VoiceCommandManager.get_voice_commands()
        
        print("RAG Service initialized successfully")
    
    def _load_products_from_db_optimized(self):
        
        try:
            # Check if collection already has products
            collection = self.chroma_client.get_collection(self.collection_name)
            existing_count = collection.count()
            
            if existing_count > 0:
                print(f"ChromaDB already has {existing_count} products loaded, skipping reload")
                return
            else:
                print(f"ChromaDB empty, loading products from database...")
                self._load_products_from_db()
        except Exception as e:
            print(f"Initializing collection, loading products from database...")
            try:
                self._load_products_from_db()
            except Exception as load_error:
                print(f"Error loading products: {load_error}")
    
    def _load_products_from_db(self):
        try:
            
            Product = apps.get_model('aicashier', 'Product')
            products = Product.objects.all()
            
            count = 0
            for product in products:
                self.add_product_to_rag(product)
                count += 1
            
            print(f"โหลดข้อมูลสินค้า {count} รายการเข้า RAG")
        except Exception as e:
            print(f"Error loading products: {e}")
    
    def reload_voice_commands(self):
        """Reload voice commands จาก database (เรียกใช้เมื่อ admin บันทึกการตั้งค่า)"""
        try:
            self.voice_commands = VoiceCommandManager.get_voice_commands()
            print(f"[VoiceCommand] Reloaded: add={len(self.voice_commands.get('add', []))}, "
                  f"decrease={len(self.voice_commands.get('decrease', []))}, "
                  f"delete={len(self.voice_commands.get('delete', []))}")
            return True
        except Exception as e:
            print(f"[VoiceCommand] Error reloading: {e}")
            return False
    
    def add_product_to_rag(self, product):
        try:
            product_id = str(product.id)
            try:
                existing = self.vector_store.get(
                    where={"product_id": product_id},
                    limit=1
                )
                if existing and existing.get("ids") and len(existing["ids"]) > 0:
                    print(f"Product {product_id} already exists, deleting old entries first...")
                    self.vector_store.delete(where={"product_id": product_id})
            except Exception as check_error:
                print(f"Note: Could not check for existing product: {check_error}")
            
            category_name = product.category.name if product.category else "ไม่มีหมวด"
            description = product.description if product.description else "-"
            
            text_content = f"""
สินค้า: {product.name}
หมวดหมู่: {category_name}
ราคา: {product.price} บาท
รายละเอียด: {description}
            """
            
            chunks = self.text_splitter.split_text(text_content)
            if not chunks:
                chunks = [text_content]
            
            metadatas = [{
                "product_id": product_id,
                "name": product.name,
                "price": str(product.price),
                "category": category_name
            } for _ in chunks]
            
            ids = [f"prod_{product_id}_{i}" for i in range(len(chunks))]
            
            self.vector_store.add_texts(texts=chunks, metadatas=metadatas, ids=ids)
            print(f"Product {product_id} ({product.name}) added to RAG with {len(chunks)} chunks")
        except Exception as e:
            print(f"Error adding product to RAG: {e}")
            import traceback
            traceback.print_exc()
    
    def update_product_in_rag(self, product):
        try:
            self.delete_product_from_rag(product.id)
            self.add_product_to_rag(product)
        except Exception as e:
            print(f"Error updating product in RAG: {e}")
    
    def delete_product_from_rag(self, product_id):
        try:
            self.vector_store.delete(where={"product_id": str(product_id)})
        except Exception:
            pass
    
    def search_products(self, query: str, k: int = 3):
        try:
            results = self.vector_store.similarity_search_with_score(query, k=k)
            return results
        except Exception as e:
            print(f"Error searching products: {e}")
            return []
    
    def extract_product_and_quantity(self, user_message: str):

        try:
            # แปลงคำตัวเลขไทยเป็นตัวเลข
            thai_numbers = {
                'ศูนย์': '0', 'หนึ่ง': '1', 'สอง': '2', 'สาม': '3', 'สี่': '4',
                'ห้า': '5', 'หก': '6', 'เจ็ด': '7', 'แปด': '8', 'เก้า': '9',
                'สิบ': '10', 'สิบเอ็ด': '11', 'สิบสอง': '12', 'ยี่สิบ': '20', 'สามสิบ': '30'
            }
            
            product_text = user_message
            quantity = 1
          
            for thai_word, digit in thai_numbers.items():
                if thai_word in product_text:
                    quantity = int(digit)
                    product_text = product_text.replace(thai_word, "").strip()
                    break
            
            # หารูปแบบตัวเลข Arabic
            numbers = re.findall(r'\d+', product_text)
            if numbers:
                quantity = int(numbers[0])
            
            # ลบตัวเลขจากข้อความ
            product_text = re.sub(r'\d+', '', product_text).strip()
            
            # ลบคำศัพท์ทั่วไป
            product_text = re.sub(r"(ให้|เพิ่ม|สั่ง|ซื้อ|แก้ว|ลูก|ชิ้น|ห่อ|ลง|ตะกร้า|ของ|ฉัน|เข้า)", "", product_text).strip()
            
            print(f"[RAG] Extracted: product='{product_text}', quantity={quantity}")
            return product_text, quantity
        except Exception as e:
            print(f"[RAG] Error extracting product: {e}")
            return None, 1
    
    def _detect_action_from_voice_commands(self, user_message: str):
        """
        ตรวจสอบ action (add/decrease/delete/clear) จากคำสั่งเสียงที่ admin กำหนด
        Return: 'add' | 'decrease' | 'delete' | 'clear' | None
        """
        try:
            msg = user_message.lower().strip()
            
            # ลำดับความสำคัญ: clear > delete > decrease > add
            
            # Priority 1: Clear Cart
            for cmd in self.voice_commands.get('delete', []):
                if re.search(rf'{re.escape(cmd)}.*?(ทั้งหมด|ทั้งตะกร้า)', msg):
                    return 'clear'
            if re.search(r'(ล้างตะกร้า|ลบ.*(ทั้งหมด|ทั้งตะกร้า)|ยกเลิก.*(ทั้งหมด|ออเดอร์))', msg):
                return 'clear'
            
            # Priority 2: Delete/Remove
            for cmd in self.voice_commands.get('delete', []):
                if cmd in msg:
                    # ตรวจสอบว่าไม่ใช่ "clear" (มีตัวเลขหลังคำ delete)
                    if not re.search(rf'{re.escape(cmd)}.*\d', msg):
                        return 'delete'
            
            # Priority 3: Decrease
            for cmd in self.voice_commands.get('decrease', []):
                if cmd in msg:
                    return 'decrease'
            
            # Priority 4: Add (Default)
            for cmd in self.voice_commands.get('add', []):
                if cmd in msg:
                    return 'add'
            
            # ถ้าไม่เจอคำสั่ง default เป็น 'add'
            return 'add'
        
        except Exception as e:
            print(f"[VoiceCommand] Error detecting action: {e}")
            return 'add'
    
    def parse_cart_command_with_cart_context(self, user_message: str, cart: list = None):
        try:
            print(f"[RAG-CART] Parsing V3: '{user_message}'")
            
            msg = user_message.lower().strip()

            
            # ตรวจสอบ action จาก voice commands ของ admin
            action = self._detect_action_from_voice_commands(user_message)
            
            print(f"[RAG-CART]  Action detected from voice commands: {action}")
            
            if action == 'clear':
                return {'action': 'clear', 'products': [], 'message': 'Clear cart'}
            
           
            cleaned = msg
            
            # ลบคำสั่งเสียงที่ admin กำหนดออกจากข้อความ
            for cmd_type in ['delete', 'decrease', 'add']:
                for cmd in self.voice_commands.get(cmd_type, []):
                    cleaned = re.sub(rf'\b{re.escape(cmd)}\b', ' ', cleaned, flags=re.IGNORECASE)
            
            # ลบคำศัพท์ทั่วไปออก
            cleaned = re.sub(r'(ล้างตะกร้า|ลบออก|เอาออก|ไม่เอา|ลดลง|น้อยลง|ถอด)', ' ', cleaned)
            # ลบคำกลุ่ม Add/General ("ลด" ที่เหลืออยู่คือ ลดราคา หรือชื่อสินค้าที่มีคำว่าลด)
            cleaned = re.sub(r'(เพิ่มเข้า|เพิ่ม|สั่ง|ซื้อ|ใส่|ให้|ทั้งตะกร้า|ทั้งหมด)', ' ', cleaned)

            cleaned = re.sub(r'\bเอา\s', ' ', cleaned) 

            cleaned = cleaned.strip()
            print(f"[RAG-CART] Cleaned for extraction: '{cleaned}'")
            
            products = []
            
            
            # 1. ลองหาจากสินค้าในตะกร้าก่อน (แม่นยำที่สุดสำหรับคำสั่งลด/แก้ไข)
            if cart:
                for item in cart:
                    p_name = item['product_name']
                    # เช็คว่าชื่อสินค้าอยู่ในข้อความที่ clean แล้วหรือไม่
                    if p_name in cleaned or (p_name.replace(' ', '') in cleaned.replace(' ', '')):
                        # หาจำนวน
                        qty = 1
                        # Pattern: "Product 5" or "5 Product"
                        pattern = f"{re.escape(p_name)}\\s*(\\d+)|\\d+\\s*{re.escape(p_name)}"
                        matches = re.finditer(pattern, cleaned)
                        found_num = False
                        
                        for match in matches:
                            found_num = True
                            qty_text = match.group()
                            nums = re.findall(r'\d+', qty_text)
                            if nums:
                                products.append((p_name, int(nums[0])))
                        
                        # ถ้าเจอชื่อแต่ไม่เจอตัวเลข
                        if not found_num and p_name in cleaned:
                             # ถ้า action เป็น add/decrease ให้ default=1
                             if not any(p[0] == p_name for p in products):
                                 products.append((p_name, 1))

            # 2. ถ้ายังไม่เจอ หรือเป็นการ "เพิ่ม" สินค้าใหม่ (ไม่อยู่ในตะกร้า)
            # ใช้ Regex จับคู่ "ชื่อสินค้า" กับ "ตัวเลข"
            if not products: 
                 # แยกส่วนด้วยตัวเลข
                segments = re.split(r'(\d+)', cleaned)
                i = 0
                while i < len(segments):
                    text_part = segments[i].strip()
                    
                    if text_part and not text_part.isdigit():
                        # Clean หน่วยนับออก
                        prod_name = re.sub(r'(ลูก|แก้ว|ชิ้น|ห่อ|อัน|ขวด|กล่อง|ถุง)$', '', text_part).strip()
                        
                        qty = 1
                        if i + 1 < len(segments) and segments[i+1].isdigit():
                            qty = int(segments[i+1])
                            i += 2
                        else:
                            i += 1
                            
                        if prod_name:
                            # กรองขยะที่อาจหลงเหลือ
                            if len(prod_name) > 1 and prod_name not in ['ครับ', 'ค่ะ', 'นะ', 'หน่อย']:
                                products.append((prod_name, qty))
                    else:
                        i += 1

            return {
                'action': action,
                'products': products,
                'message': f'Parsed {action} command'
            }
        
        except Exception as e:
            print(f"[RAG-CART]  Error: {e}")
            return {'action': 'add', 'products': [], 'message': str(e)}
    
    def parse_cart_command(self, user_message: str):
        """
        วิเคราะห์คำสั่งการจัดการตะกร้า (เพิ่ม/ลด/ลบ) รองรับหลายสินค้า
        Return: {
            'action': 'add'|'remove'|'delete'|'clear',
            'products': [('product_name', quantity), ...],
            'message': 'error/info message'
        }
        
        ตัวอย่าง:
        - "เพิ่มส้มโอ 3 ลูกนม 2 แก้วเค้ก 1 ชิ้น" 
          → [("ส้มโอ", 3), ("นม", 2), ("เค้ก", 1)]
        - "ลดส้มโอ 2 ลูกนม 1 แก้ว"
          → [("ส้มโอ", 2), ("นม", 1)]
        """
        msg = user_message.lower().strip()
        
        # แปลงคำตัวเลขไทยเป็นตัวเลข (เพิ่ม compound numbers เช่น สิบสอง, เจ็ดสิบห้า)
        thai_numbers = {
            'ศูนย์': '0', 'หนึ่ง': '1', 'สอง': '2', 'สาม': '3', 'สี่': '4',
            'ห้า': '5', 'หก': '6', 'เจ็ด': '7', 'แปด': '8', 'เก้า': '9',
            'สิบเอ็ด': '11', 'สิบสอง': '12', 'สิบสาม': '13', 'สิบสี่': '14', 'สิบห้า': '15',
            'สิบหก': '16', 'สิบเจ็ด': '17', 'สิบแปด': '18', 'สิบเก้า': '19',
            'ยี่สิบ': '20', 'สามสิบ': '30', 'สี่สิบ': '40', 'ห้าสิบ': '50',
            'หกสิบ': '60', 'เจ็ดสิบ': '70', 'แปดสิบ': '80', 'เก้าสิบ': '90',
            'หนึ่งร้อย': '100', 'สองร้อย': '200',
            'สิบ': '10' 
        }
        
        # แปลงตัวเลขไทย (เรียงลำดับเพื่อหลีกเลี่ยง partial match)
        normalized_msg = msg
        for thai_word in sorted(thai_numbers.keys(), key=len, reverse=True):
            normalized_msg = normalized_msg.replace(thai_word, f' {thai_numbers[thai_word]} ')
        
        print(f"[RAG] Normalized: {normalized_msg}")
        
        # ตรวจสอบ action
        action = None
        
        # ลบ/ลบออก (delete)
        if re.search(r'(ลบ(?!ลง)|เอา(?!ของ)|ถอด|ลบออก)', normalized_msg):
            # ตรวจสอบว่าลบทั้งหมดหรือเฉพาะรายการ
            if re.search(r'(ทั้งหมด|ทั้งตะกร้า|ตะกร้า\s*ทั้งหมด)', normalized_msg):
                action = 'clear'
            else:
                action = 'delete'
        
        # ลด (decrease)
        elif re.search(r'(^ลด|ลด(?!ลง)|หลุด|น้อยลง|ลดลง|รส|รถ|เอาออก)', normalized_msg):
            action = 'decrease'
        
        # เพิ่ม (add)
        elif re.search(r'(เพิ่ม|เพิ่มเข้า|ใส่|สั่ง|ซื้อ|เอา(?=\S+\s+\d)|add)', normalized_msg):
            action = 'add'
        
        # ถ้าไม่เจอ action ให้ถือว่าเป็น add
        else:
            action = 'add'
        
        print(f"[RAG] Action detected: {action}")
        
        products = []
        
        # clear action: ลบทั้งตะกร้า ไม่ต้องตัดแยก product
        if action == 'clear':
            return {
                'action': 'clear',
                'products': [],
                'message': 'Clear cart command'
            }
        
        # ลบคำศัพท์ทั่วไปและ action verbs ออก
        cleaned_msg = re.sub(
            r'(ให้|เพิ่ม|เพิ่มเข้า|ลด(?!ลง)|ลบ|เอา|ถอด|สั่ง|ซื้อ|เข้า|ทั้งหมด|ทั้งตะกร้า|\s+)',
            ' ', normalized_msg
        ).strip()
        
        print(f"[RAG] Cleaned: {cleaned_msg}")
        
        # ตัดแยก product และ quantity
        # Strategy: ค้นหา pattern "product_name quantity unit" หรือ "quantity product_name unit"
        
        # Pattern 1: ชื่อสินค้า ตัวเลข (อาจมี unit เช่น ลูก/แก้ว/ชิ้น)
        # เช่น: "ส้มโอ 3" หรือ "ส้มโอ 3 ลูก" หรือ "ส้มโอสาม"
        
        # First, split by numbers to identify product-quantity pairs
        # Split message by numbers to get segments
        segments = re.split(r'(\d+)', cleaned_msg)  # ['ส้มโอ', '3', 'นม', '2', ...]
        print(f"[RAG] Segments after split: {segments}")
        
        i = 0
        while i < len(segments):
            segment = segments[i].strip()
            
            # หา product name (text before number)
            if segment and not segment.isdigit():
                product_name = segment
                quantity = 1
                
                # ลบ unit words เช่น ลูก, แก้ว, ชิ้น, ห่อ
                # ระวัง: ห้าม substring ของชื่อสินค้า เช่น "ม" ในมะม่วง
                original_name = product_name
                product_name = re.sub(r'(ลูก|แก้ว|ชิ้น|ห่อ|อัน|หัว|ตัว)', '', product_name).strip()
                
                if original_name != product_name:
                    print(f"[RAG] Unit removed: '{original_name}' → '{product_name}'")
                
                # หาตัวเลขถัดไป
                if i + 1 < len(segments):
                    next_segment = segments[i + 1].strip()
                    if next_segment.isdigit():
                        quantity = int(next_segment)
                        i += 2  # skip both product and number
                    else:
                        i += 1
                else:
                    i += 1
                
                # เพิ่ม product ถ้าชื่อไม่ว่าง
                if product_name:
                    # ตรวจสอบว่ามี product นี้หรือไม่ (หลีกเลี่ยง duplicate)
                    if not any(p[0].lower() == product_name.lower() for p in products):
                        products.append((product_name, quantity))
                        print(f"[RAG] Parsed: product='{product_name}', qty={quantity}")
                    else:
                        print(f"[RAG] Duplicate: '{product_name}'")
                else:
                    print(f"[RAG] Empty product name after unit removal from '{segment}'")
            else:
                i += 1
        
        # ถ้ายังไม่เจอ product ให้พยายามใช้ regex เพิ่มเติม
        if not products:
            # Pattern: "product qty unit" เช่น "ส้มโอ 3 ลูก"
            pattern = r'([a-zA-Z\u0E00-\u0E7F]+?)\s*(\d+)\s*(?:ลูก|แก้ว|ชิ้น|ห่อ|อัน|หัว|ตัว)?'
            matches = re.findall(pattern, cleaned_msg)
            
            for product_name, qty_str in matches:
                product_name = product_name.strip()
                if product_name and not any(p[0].lower() == product_name.lower() for p in products):
                    products.append((product_name, int(qty_str)))
                    print(f"[RAG] Regex found: product='{product_name}', qty={qty_str}")
        
        # Fallback: ถ้ายังไม่เจอ ให้ใช้ข้อความทั้งหมด
        if not products and cleaned_msg.strip():
            products.append((cleaned_msg.strip(), 1))
            print(f"[RAG] Fallback: product='{cleaned_msg.strip()}', qty=1")
        
        return {
            'action': action,
            'products': products,
            'message': f"Parsed {action} command with {len(products)} products"
        }
    
    def voice_manage_cart(self, user_message: str, request=None):
        """
        ครอบคุมการจัดการตะกร้าจากคำพูด/แชท (เพิ่ม/ลด/ลบ)
        Return: {"success": True/False, "message": "...", "action": "...", "cart": [...]}
        """
        try:
            print(f"[RAG] voice_manage_cart START: '{user_message}'")
            
            if not request or not hasattr(request, 'session'):
                print("[RAG]  No request or session!")
                return {
                    'success': False,
                    'message': 'ไม่สามารถเข้าถึง session ได้',
                    'action': None,
                    'cart': []
                }
            
            # สำหรับ action อื่น (add, decrease, delete)
            if 'cart' not in request.session:
                request.session['cart'] = []
            
            cart = request.session['cart']
            
            # ใช้ parse_cart_command_with_cart_context เพื่อให้ดีขึ้น
            command = self.parse_cart_command_with_cart_context(user_message, cart)
            action = command['action']
            products = command['products']
            
            print(f"[RAG] Command: action={action}, products={products}")
            
            if action == 'clear':
                # ลบตะกร้าทั้งหมด
                print("[RAG]  Clearing entire cart")
                request.session['cart'] = []
                request.session.modified = True
                print(f"[RAG]  Cart cleared, session.modified={request.session.modified}")
                return {
                    'success': True,
                    'message': 'ลบทั้งตะกร้าแล้ว',
                    'action': 'clear',
                    'cart': []
                }
            
            # สำหรับ action อื่น (add, decrease, delete)
            if 'cart' not in request.session:
                request.session['cart'] = []
            
            cart = request.session['cart']
            print(f"[RAG] Current cart size: {len(cart)} items")
            print(f"[RAG] Current cart items: {[item['product_name'] for item in cart]}")
            
            result_messages = []
            modified = False
            
            from django.apps import apps
            Product = apps.get_model('aicashier', 'Product')
            
            for product_name, quantity in products:
                try:
                    print(f"[RAG] Finding product: '{product_name}' qty={quantity}")
                    
                    # ลองค้นหาจากตะกร้าก่อน (ด้วย similarity)
                    matching_cart_item = None
                    for item in cart:
                        cart_product_name = item['product_name'].lower().strip()
                        search_product_name = product_name.lower().strip()
                        
                        # Exact match
                        if cart_product_name == search_product_name:
                            matching_cart_item = item
                            print(f"[RAG] Found in cart (exact): {item['product_name']}")
                            break
                        
                        # Partial match (product_name in cart_product_name)
                        if search_product_name in cart_product_name or cart_product_name in search_product_name:
                            matching_cart_item = item
                            print(f"[RAG] Found in cart (partial): {item['product_name']}")
                            break
                    
                    # ถ้าในตะกร้า ให้ใช้ชื่อจากตะกร้า เพื่อค้นหา product จาก DB
                    if matching_cart_item:
                        actual_product_name = matching_cart_item['product_name']
                        product = self.find_product_by_name(actual_product_name)
                        cart_item = matching_cart_item
                    else:
                        # ถ้าไม่ในตะกร้า ค้นหาจาก DB ปกติ
                        product = self.find_product_by_name(product_name)
                        cart_item = None
                    
                    if not product:
                        print(f"[RAG] Product not found in DB: '{product_name}'")
                        result_messages.append(f" ไม่มี '{product_name}'")
                        continue
                    
                    print(f"[RAG]  Found product: ID={product.id}, name={product.name}, stock={product.quantity}")
                    
                    # ถ้ายังไม่เจอในตะกร้า ให้หาใหม่จาก product ID
                    if not cart_item:
                        for i, item in enumerate(cart):
                            if item['product_id'] == product.id:
                                cart_item = item
                                print(f"[RAG] Matched by ID!")
                                break
                    
                    if cart_item:
                        print(f"[RAG] Cart item found!")
                    
                    # จัดการตามเหตุการณ์ที่ต้องการ
                    if action == 'add':
                        print(f"[RAG] ADD action")
                        if not cart_item:
                            # เพิ่มใหม่
                            if product.quantity <= 0:
                                result_messages.append(f"'{product.name}' หมดสต็อก")
                                continue
                            if quantity > product.quantity:
                                result_messages.append(f"'{product.name}' เหลือเพียง {product.quantity} ชิ้น")
                                continue
                            
                            new_item = {
                                "product_id": product.id,
                                "product_name": product.name,
                                "price": float(product.price),
                                "quantity": quantity,
                                "category": product.category.name if product.category else "ไม่มีหมวด"
                            }
                            cart.append(new_item)
                            result_messages.append(f"เพิ่ม {product.name} {quantity}")
                            modified = True
                            print(f"[RAG] Added new: {product.name} {quantity}")
                        else:
                            # เพิ่มจำนวนที่มีอยู่
                            new_qty = cart_item['quantity'] + quantity
                            if new_qty > product.quantity:
                                result_messages.append(f"'{product.name}' เหลือเพียง {product.quantity} ชิ้น (มีในตะกร้า {cart_item['quantity']})")
                                continue
                            
                            cart_item['quantity'] = new_qty
                            result_messages.append(f"เพิ่ม {product.name} เป็น {new_qty}")
                            modified = True
                            print(f"[RAG] Updated: {product.name} to {new_qty}")
                    
                    elif action == 'decrease':
                        print(f"[RAG] DECREASE action")
                        if not cart_item:
                            result_messages.append(f"'{product.name}' ไม่มีในตะกร้า")
                            continue
                        
                        new_qty = cart_item['quantity'] - quantity
                        if new_qty <= 0:
                            # ถ้าลดจนเหลือ 0 ให้ลบออก
                            print(f"[RAG] Quantity <= 0, removing item")
                            cart.remove(cart_item)
                            result_messages.append(f" ลบ {product.name} ออกจากตะกร้า")
                            modified = True
                            print(f"[RAG] Deleted: {product.name}")
                        else:
                            cart_item['quantity'] = new_qty
                            result_messages.append(f" ลด {product.name} เป็น {new_qty}")
                            modified = True
                            print(f"[RAG] Decreased: {product.name} to {new_qty}")
                    
                    elif action == 'delete':
                        print(f"[RAG]  DELETE action")
                        if not cart_item:
                            result_messages.append(f"'{product.name}' ไม่มีในตะกร้า")
                            continue
                        
                        cart.remove(cart_item)
                        result_messages.append(f"ลบ {product.name} ออกจากตะกร้า")
                        modified = True
                        print(f"[RAG] Deleted: {product.name}")
                
                except Exception as item_error:
                    print(f"[RAG] Error processing '{product_name}': {item_error}")
                    import traceback
                    traceback.print_exc()
                    result_messages.append(f"เรียงข้อผิดพลาด: {product_name}")
            
            # บันทึก session
            if modified:
                request.session['cart'] = cart
                request.session.modified = True
                print(f"[RAG] Session SAVED, cart now has {len(cart)} items, modified={request.session.modified}")
            else:
                print(f"[RAG] ℹNo modifications made to cart")
            
            # สรุปผลการทำงาน
            summary = " | ".join(result_messages) if result_messages else "ไม่มีการเปลี่ยนแปลง"
            print(f"[RAG] Returning: success={modified or len(result_messages) > 0}, action={action}")
            
            return {
                'success': modified or len(result_messages) > 0,
                'message': summary,
                'action': action,
                'cart': [
                    {
                        'product_name': item['product_name'],
                        'quantity': item['quantity'],
                        'price': item['price'],
                        'total': item['quantity'] * item['price']
                    }
                    for item in cart
                ]
            }
        
        except Exception as e:
            print(f"[RAG] Error in voice_manage_cart: {e}")
            import traceback
            traceback.print_exc()
            return {
                'success': False,
                'message': f'เกิดข้อผิดพลาด: {str(e)[:50]}',
                'action': None,
                'cart': []
            }
    
    
    def find_product_by_name(self, product_name: str):
        """ค้นหา Product จากชื่อสินค้า"""
        try:
            from django.apps import apps
            Product = apps.get_model('aicashier', 'Product')
            
            # ค้นหาใน database ก่อน (exact match)
            products = Product.objects.filter(name__icontains=product_name)
            
            if products.exists():
                return products.first()
            
            # ถ้าไม่เจอ ใช้ similarity search จาก RAG
            search_results = self.search_products(product_name, k=1)
            if search_results:
                doc, score = search_results[0]
                metadata = doc.metadata
                if 'product_id' in metadata:
                    product_id = int(metadata['product_id'])
                    return Product.objects.get(id=product_id)
            
            return None
        except Exception as e:
            print(f"Error finding product: {e}")
            return None
    
    def add_to_cart_from_voice(self, user_message: str, request=None):
        """
        เพิ่มสินค้าลงตะกร้าจากข้อความเสียง/แชท (รองรับหลายสินค้า)
        คืนค่า: {"success": True/False, "message": "..."}
        """
        try:
            print(f"[RAG] add_to_cart_from_voice: user_message='{user_message}'")
            
            # ตัดแยก product list (รองรับหลายสินค้า) ใช้ parse_cart_command แทน
            parsed = self.parse_cart_command(user_message)
            products_list = parsed.get('products', [])
            
            if not products_list:
                return {
                    "success": False,
                    "message": "ขออภัยครับ ไม่พบชื่อสินค้า"
                }
            
            # เพิ่มลงตะกร้า
            added_items = []
            failed_items = []
            
            for product_name, quantity in products_list:
                try:
                    # ค้นหา product
                    product = self.find_product_by_name(product_name)
                    
                    if not product:
                        failed_items.append(f"ไม่มี '{product_name}'")
                        continue
                    
                    print(f"[RAG]  Found product: {product.name} (stock: {product.quantity})")
                    
                    # ตรวจสอบ stock
                    if product.quantity <= 0:
                        print(f"[RAG] Stock is 0: {product.name}")
                        failed_items.append(f"'{product.name}' ขายหมดแล้ว")
                        continue
                    
                    # ตรวจสอบว่าจำนวนสั่งไม่เกิน stock
                    if quantity > product.quantity:
                        print(f"[RAG] Quantity {quantity} > Stock {product.quantity}: {product.name}")
                        failed_items.append(f"'{product.name}' เหลือ {product.quantity} ชิ้น")
                        continue
                    
                    # เพิ่มลงตะกร้า (session)
                    if request and hasattr(request, 'session'):
                        if 'cart' not in request.session:
                            request.session['cart'] = []
                        
                        cart = request.session['cart']
                        
                        # ตรวจสอบว่ามีในตะกร้าแล้วหรือไม่
                        item_exists = False
                        for item in cart:
                            if item['product_id'] == product.id:
                                # ตรวจสอบว่าจำนวนใหม่ (เดิม + เพิ่ม) ไม่เกิน stock
                                new_quantity = item['quantity'] + quantity
                                print(f"[RAG]  Item exists: {product.name}, new_qty={new_quantity}, stock={product.quantity}")
                                
                                if new_quantity > product.quantity:
                                    failed_items.append(f"'{product.name}' จำนวนเกิน (เหลือ {product.quantity})")
                                    item_exists = True
                                    break
                                
                                item['quantity'] = new_quantity
                                item_exists = True
                                added_items.append(f"{product.name} x{new_quantity}")
                                print(f"[RAG] Updated: {product.name} x{new_quantity}")
                                break
                        
                        # ถ้าไม่มี ให้เพิ่มใหม่
                        if not item_exists:
                            cart.append({
                                "product_id": product.id,
                                "product_name": product.name,
                                "price": float(product.price),
                                "quantity": quantity,
                                "category": product.category.name if product.category else "ไม่มีหมวด"
                            })
                            added_items.append(f"{product.name} x{quantity}")
                            print(f"[RAG] Added new: {product.name} x{quantity}")
                        
                        request.session.modified = True
                
                except Exception as item_error:
                    print(f"[RAG]  Error adding item '{product_name}': {item_error}")
                    failed_items.append(f"เรียงข้อผิดพลาด: {product_name}")
            
            print(f"[RAG] Session saved")
            
            # สรุปผล
            if added_items and not failed_items:
                return {
                    "success": True,
                    "message": f"เพิ่ม {', '.join(added_items)} เข้าตะกร้าแล้ว"
                }
            elif added_items and failed_items:
                return {
                    "success": True,
                    "message": f"เพิ่ม {', '.join(added_items)} สำเร็จ แต่ {', '.join(failed_items)}"
                }
            else:
                return {
                    "success": False,
                    "message": f"ขออภัยครับ {', '.join(failed_items)}"
                }
        
        except Exception as e:
            print(f"[RAG] Error adding to cart: {e}")
            import traceback
            traceback.print_exc()
            return {
                "success": False,
                "message": f"เกิดข้อผิดพลาด: {str(e)[:50]}"
            }
    
    def _format_product_with_stock(self, product):
        """จัดรูป Product ข้อมูลพร้อมสถานะสต็อก"""
        try:
            status = " มีสินค้า" if product.quantity > 0 else " หมดสต็อก"
            category = product.category.name if product.category else "ไม่มีหมวด"
            description = product.description if product.description else "-"
            
            return f"""สินค้า: {product.name}
หมวดหมู่: {category}
ราคา: {product.price} บาท
คงเหลือ: {product.quantity} ชิ้น ({status})
รายละเอียด: {description}"""
        except Exception as e:
            return f"Error formatting product: {e}"
    
    def rag_query(self, query: str, conversation_history: list = None) -> str:
        """
        ค้นหาและตอบคำถามเกี่ยวกับสินค้า พร้อมแสดงสถานะสต็อก
        ไม่แนะนำสินค้าที่หมดสต็อก
        ใช้ AISettings เพื่อปรับปรุง greeting, promotion, featured items
        ใช้ conversation_history เพื่อให้ AI จำบทสนทนาก่อนหน้า
        
        Args:
            query: คำถามจากผู้ใช้
            conversation_history: รายการการสนทนาที่ผ่านมา [{"role": "user/assistant", "content": "..."}, ...]
        """
        try:
            print(f"\n RAG Query: {query}")
            
            if conversation_history is None:
                conversation_history = []
            
            print(f"Conversation history: {len(conversation_history)} messages")
            
            # ดึง AISettings
            from django.apps import apps
            AISettings = apps.get_model('aicashier', 'AISettings')
            ai_settings = AISettings.get_settings()
            print(f"Loaded AISettings: greeting='{ai_settings.greeting_message[:30]}...', featured_items={sum([1 for x in [ai_settings.featured_item_1, ai_settings.featured_item_2, ai_settings.featured_item_3, ai_settings.featured_item_4] if x])}")
            
            # ค้นหาเอกสารจาก ChromaDB (ค้นหาทั้งหมดไม่จำกัด)
            # ใช้ k=100 เพื่อให้ได้สินค้าทั้งหมดที่มี
            stats = self.get_collection_stats()
            max_k = max(10, stats.get('document_count', 10))  # ย่างน้อย 10 รายการ
            docs = self.search_products(query, k=max_k)
            
            if not docs:
                print("No documents found")
                return "ขออภัยครับ ไม่พบข้อมูลสินค้าที่เกี่ยวข้อง"
            
            # เพิ่มข้อมูลสินค้าที่มีสต็อก ส่วนสินค้าหมดให้บอกว่าหมด
            Product = apps.get_model('aicashier', 'Product')
            
            available_products_text = []
            out_of_stock_products = []
            
            for doc, score in docs:
                try:
                    product_id = doc.metadata.get('product_id')
                    if product_id:
                        product = Product.objects.get(id=product_id)
                        if product.quantity > 0:
                            available_products_text.append(self._format_product_with_stock(product))
                        else:
                            out_of_stock_products.append(product.name)
                except:
                    # Fallback to original doc content if product not found
                    available_products_text.append(doc.page_content)
            
            # สร้าง featured items section
            featured_products_text = ""
            featured_items = [ai_settings.featured_item_1, ai_settings.featured_item_2, 
                            ai_settings.featured_item_3, ai_settings.featured_item_4]
            featured_items = [item for item in featured_items if item]  # ลบ None
            
            if featured_items:
                featured_products_text = "\n\n **สินค้าแนะนำพิเศษ:**\n"
                for item in featured_items:
                    try:
                        if item.quantity > 0:
                            featured_products_text += f"• {item.name} - ฿{item.price} (เหลือ {item.quantity} ชิ้น)\n"
                        else:
                            featured_products_text += f"• {item.name} - ขายหมดแล้ว (⏳ กำลังเตรียม)\n"
                    except:
                        pass
                print(f"Added {len(featured_items)} featured items")
            
            # สร้าง context
            context_text = "\n\n".join(available_products_text)
            if not context_text:
                context_text = "ขณะนี้สินค้าทั้งหมดหมดสต็อก"
            
            # รวมข้อมูล out of stock
            out_of_stock_note = ""
            if out_of_stock_products:
                out_of_stock_note = f"\n\n หมดสต็อก: {', '.join(out_of_stock_products)}"
            
            print(f"Found {len(docs)} documents, {len(available_products_text)} available")
            
            # สร้าง conversation history text
            history_text = ""
            if conversation_history:
                history_text = "\n**ประวัติการสนทนาที่ผ่านมา:**\n"
                # แสดง last 5 messages เท่านั้น เพื่อไม่ให้ prompt ยาวเกินไป
                recent_history = conversation_history[-10:]  # last 10 messages
                for i, item in enumerate(recent_history):
                    role = "ลูกค้า" if item.get('role') == 'user' else " ร้าน"
                    content = item.get('content', '')
                    history_text += f"{role}: {content}\n"
                print(f"Added {len(recent_history)} messages to history text")
            else:
                print(f"No conversation history provided")
            
            # สร้าง Prompt พร้อม AISettings และ conversation history
            sales_steps = ai_settings.sales_steps if ai_settings.sales_steps else "1. ทักทาย\n2. เสนอสินค้า\n3. บอกราคา\n4. ขอบคุณ"
            
            prompt = f"""บทบาท: คุณเป็นพนักงานขายของร้าน AI CASHIER
ทักทาย: {ai_settings.greeting_message}
โปรโมชั่น: {ai_settings.promotion_text}

ขั้นตอนการขาย:
{sales_steps}

คำลงท้าย: {ai_settings.closing_message}

สินค้าของเรา:
{context_text}
{featured_products_text}
{out_of_stock_note}
{history_text}

คำถามจากลูกค้าตอนนี้: {query}

กรุณาตอบคำถามให้เป็นมิตรและเป็นประโยชน์ ใช้ภาษาไทยเท่านั้น
ในการตอบ ให้พิจารณาประวัติการสนทนาที่ผ่านมา เพื่อให้การตอบถูกต้องและสอดคล้องกัน
**สำคัญ: ห้ามแนะนำหรือสั่งสินค้าที่หมดสต็อก**"""
            
            print(f"Prompt prepared with {len(prompt)} characters")
            
            # เรียก LLM
            response = self.llm.invoke(prompt)
            return response
        
        except Exception as e:
            print(f"Error in RAG query: {e}")
            import traceback
            traceback.print_exc()
            return f"เกิดข้อผิดพลาด: {str(e)[:50]}"
    
    def get_collection_stats(self):
        """ดึงสถิติของ collection"""
        try:
            collection = self.chroma_client.get_collection(self.collection_name)
            return {"document_count": collection.count()}
        except Exception:
            return {"document_count": 0}

# สร้าง global instance
rag_service = None
try:
    rag_service = RAGService()
except Exception as e:
    print(f" Error initializing RAG Service: {e}")
    import traceback
    traceback.print_exc()

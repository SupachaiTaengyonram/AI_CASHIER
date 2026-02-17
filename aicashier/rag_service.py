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
            if not settings_obj:
                return VoiceCommandManager.get_default_commands()
            
            # Parse voice commands from new separate fields
            commands = {
                'add': [],
                'decrease': [],
                'delete': []
            }
            
            # Parse add commands
            if hasattr(settings_obj, 'voice_commands_add') and settings_obj.voice_commands_add:
                add_words = settings_obj.voice_commands_add.strip().split('|')
                commands['add'] = [word.strip().lower() for word in add_words if word.strip()]
            
            # Parse decrease commands
            if hasattr(settings_obj, 'voice_commands_decrease') and settings_obj.voice_commands_decrease:
                dec_words = settings_obj.voice_commands_decrease.strip().split('|')
                commands['decrease'] = [word.strip().lower() for word in dec_words if word.strip()]
            
            # Parse delete commands
            if hasattr(settings_obj, 'voice_commands_delete') and settings_obj.voice_commands_delete:
                del_words = settings_obj.voice_commands_delete.strip().split('|')
                commands['delete'] = [word.strip().lower() for word in del_words if word.strip()]
            
            # If any field is empty, use defaults for that category
            defaults = VoiceCommandManager.get_default_commands()
            if not commands['add']:
                commands['add'] = defaults['add']
            if not commands['decrease']:
                commands['decrease'] = defaults['decrease']
            if not commands['delete']:
                commands['delete'] = defaults['delete']
            
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
    
    
    
    def _detect_action_from_voice_commands(self, user_message: str):
        try:
            msg = user_message.lower().strip()
            
            print(f"[VoiceCommand] Detecting action for: '{msg}'")
            print(f"[VoiceCommand] Available commands: add={self.voice_commands.get('add', [])}, "
                  f"decrease={self.voice_commands.get('decrease', [])}, "
                  f"delete={self.voice_commands.get('delete', [])}")
            
            # Priority 1: Clear Cart (ลบทั้งหมด/ล้างตะกร้า)
            for cmd in self.voice_commands.get('delete', []):
                if re.search(rf'{re.escape(cmd)}.*?(ทั้งหมด|ทั้งตะกร้า|ออเดอร์)', msg):
                    print(f"[VoiceCommand] Detected CLEAR (delete cmd '{cmd}' + all/cart keyword)")
                    return 'clear'
            if re.search(r'(ล้างตะกร้า|ลบ.*(ทั้งหมด|ทั้งตะกร้า)|ยกเลิก.*(ทั้งหมด|ออเดอร์))', msg):
                print(f"[VoiceCommand]  Detected CLEAR (regex pattern)")
                return 'clear'
            
            # Priority 2: Delete/Remove (ลบสินค้า) - ห้ามไป check add/decrease ต่อ!
            for cmd in self.voice_commands.get('delete', []):
                if cmd in msg:
                    print(f"[VoiceCommand]  Detected DELETE (delete cmd '{cmd}')")
                    return 'delete'
            
            # Priority 3: Decrease (ลดจำนวน) - ห้ามไป check add ต่อ!
            for cmd in self.voice_commands.get('decrease', []):
                if cmd in msg:
                    print(f"[VoiceCommand]  Detected DECREASE (decrease cmd '{cmd}')")
                    return 'decrease'
            
            # Priority 4: Add (Default - เพิ่มสินค้า)
            for cmd in self.voice_commands.get('add', []):
                if cmd in msg:
                    print(f"[VoiceCommand]  Detected ADD (add cmd '{cmd}')")
                    return 'add'
            
            # Default to 'add' if no command matched
            print(f"[VoiceCommand]  No command matched, defaulting to ADD")
            return 'add'
        
        except Exception as e:
            print(f"[VoiceCommand]  Error detecting action: {e}")
            return 'add'
    
    def parse_cart_command_with_cart_context(self, user_message: str, cart: list = None):
        try:
            print(f"[RAG-CART] Parsing V3: '{user_message}'")
            
            msg = user_message.lower().strip()
            
            # ตรวจสอบ action
            action = self._detect_action_from_voice_commands(user_message)
            print(f"[RAG-CART] Action detected: {action}")
            
            if action == 'clear':
                return {'action': 'clear', 'products': [], 'message': 'Clear cart'}
            
            # Cleaning
            cleaned = msg
            for cmd in self.voice_commands.get(action, []):
                cleaned = re.sub(re.escape(cmd), ' ', cleaned, flags=re.IGNORECASE)
            
            cleaned = re.sub(r'(ล้างตะกร้า|ลบออก|เอาออก|ไม่เอา|ลดลง|น้อยลง|ถอด)', ' ', cleaned)
            cleaned = re.sub(r'(เพิ่มเข้า|เพิ่ม|สั่ง|ซื้อ|ใส่|ให้|ทั้งตะกร้า|ทั้งหมด)', ' ', cleaned)
            cleaned = re.sub(r'\bเอา\s', ' ', cleaned)
            cleaned = cleaned.strip()
            
            print(f"[RAG-CART] Cleaned: '{cleaned}'")
            
            products = []
            
            # Handle empty cleaned for delete/decrease
            if not cleaned and action in ['delete', 'decrease']:
                if cart:
                    first_item = cart[0]
                    products.append((first_item['product_name'], 1))
                    print(f"[RAG-CART] Using first cart item: {first_item['product_name']}")
                    return {'action': action, 'products': products, 
                            'message': f'Parsed {action} command (using first cart item)'}
                else:
                    action_text = 'ลด' if action == 'decrease' else 'ลบ'
                    return {'action': action, 'products': [], 
                            'message': f'ตะกร้าว่างเปล่า ไม่สามารถ{action_text}ได้'}
            
            from django.apps import apps
            Product = apps.get_model('aicashier', 'Product')
            
            # Pattern จับคู่ product-quantity
            # รองรับ: "สินค้า 3", "3 สินค้า", "น้ำมะนาว 4" (ชื่อหลายคำ)
            product_qty_pattern = r'([ก-๙a-z]+(?:\s+[ก-๙a-z]+)*)\s+(\d+)|(\d+)\s+([ก-๙a-z]+(?:\s+[ก-๙a-z]+)*)'
            matches = re.finditer(product_qty_pattern, cleaned, re.IGNORECASE)
            
            # เก็บคู่ที่พบ
            potential_pairs = []
            for match in matches:
                if match.group(1):  # "สินค้า จำนวน"
                    product_text = match.group(1).strip()
                    qty = int(match.group(2))
                else:  # "จำนวน สินค้า"
                    product_text = match.group(4).strip()
                    qty = int(match.group(3))
                
                potential_pairs.append((product_text, qty, match.start(), match.end()))
                print(f"[RAG-CART] Found potential pair: '{product_text}' qty={qty}")
            
            # Validate กับ database และ cart
            all_products = Product.objects.all()
            product_names_map = {p.name.lower(): p.name for p in all_products}
            
            # เพิ่ม cart items ถ้ามี
            if cart:
                for item in cart:
                    product_names_map[item['product_name'].lower()] = item['product_name']
            
            # Match potential pairs กับ product names
            used_positions = set()
            for product_text, qty, start, end in potential_pairs:
                # หา exact match หรือ partial match
                matched_name = None
                
                # Exact match
                if product_text in product_names_map:
                    matched_name = product_names_map[product_text]
                else:
                    # Partial match (สินค้าที่มีชื่อเป็น substring)
                    for db_name_lower, db_name_original in product_names_map.items():
                        if db_name_lower in product_text or product_text in db_name_lower:
                            matched_name = db_name_original
                            break
                        
                if matched_name and start not in used_positions:
                    products.append((matched_name, qty))
                    used_positions.add(start)
                    print(f"[RAG-CART] Matched: '{matched_name}' qty={qty}")
            
            # ถ้ายังไม่เจอเลย ลองหาแบบไม่มีตัวเลข (default qty=1)
            if not products and cleaned:
                for db_name_lower, db_name_original in product_names_map.items():
                    if db_name_lower in cleaned:
                        products.append((db_name_original, 1))
                        print(f"[RAG-CART] Found '{db_name_original}' without quantity, using qty=1")
                        break
                    
            return {
                'action': action,
                'products': products,
                'message': f'Parsed {action} command'
            }
        
        except Exception as e:
            print(f"[RAG-CART] Error: {e}")
            return {'action': 'add', 'products': [], 'message': str(e)}
        

    
    def _generate_cart_summary(self, cart):
        """สร้าง summary ของตะกร้า - แสดงรายการและราคารวม"""
        if not cart:
            return "ไม่มีสินค้าในตะกร้าค่ะ"
        
        # สร้างรายการสินค้า
        items_list = []
        total_price = 0
        
        for item in cart:
            product_name = item['product_name']
            quantity = item['quantity']
            price = item['price']
            item_total = quantity * price
            total_price += item_total
            
            items_list.append(f"• {product_name} {quantity} ชิ้น ฿{price:.2f} = ฿{item_total:.2f}")
        
        # สร้าง summary message
        items_text = "\n".join(items_list)
        summary = f"\n ตะกร้าของคุณ:\n{items_text}\n\n รวมเป็นเงินทั้งสิ้น: ฿{total_price:.2f} ค่ะ"
        
        return summary
    
    def voice_manage_cart(self, user_message: str, request=None):
       
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
            products_list = command['products']
            
            print(f"[RAG] Command: action={action}, products={products_list}")
            
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
            products = apps.get_model('aicashier', 'Product')
            
            for product_name, quantity in products_list:
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
            action_summary = " | ".join(result_messages) if result_messages else "ไม่มีการเปลี่ยนแปลง"
            
            # สร้าง cart summary - แสดงรายการและราคารวม
            cart_summary = self._generate_cart_summary(cart)
            
            # รวม action message + cart summary
            full_message = f"{action_summary}\n{cart_summary}"
            
            print(f"[RAG] Returning: success={modified or len(result_messages) > 0}, action={action}")
            
            return {
                'success': modified or len(result_messages) > 0,
                'message': full_message,
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
                SIMILARITY_THRESHOLD = 0.5
                if score < SIMILARITY_THRESHOLD:
                    print(f"[RAG] Score too low ({score:.2f}) for '{product_name}'")
                    return None
                metadata = doc.metadata
                if 'product_id' in metadata:
                    product_id = int(metadata['product_id'])
                    return Product.objects.get(id=product_id)
            
            return None
        except Exception as e:
            print(f"Error finding product: {e}")
            return None
    
    
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
                            featured_products_text += f"• {item.name} - ขายหมดแล้ว ( กำลังเตรียม)\n"
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

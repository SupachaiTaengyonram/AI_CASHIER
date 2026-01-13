import os
from dotenv import load_dotenv
import google.generativeai as genai
from google.generativeai.types import HarmCategory, HarmBlockThreshold # สำหรับการตั้งค่าความปลอดภัย
from django.apps import apps

# โหลดตัวแปรจากไฟล์ .env
load_dotenv()

def get_ai_settings():
    """ดึงการตั้งค่า AI จาก Django models"""
    try:
        AISettings = apps.get_model('aicashier', 'AISettings')
        return AISettings.get_settings()
    except Exception as e:
        print(f"Warning: Could not load AISettings: {e}")
        return None

def get_rag_service():
    """ดึง RAG Service instance"""
    try:
        from .rag_service import rag_service
        return rag_service
    except Exception as e:
        print(f"Warning: Could not load RAG service: {e}")
        return None

class GeminiChatService:
    """บริการแชทโดยใช้ Google Gemini API"""
    
    def __init__(self):
        # 1. การจัดการ API Key (ปรับปรุง)
        # ใช้ os.getenv โดยตรง (load_dotenv() จัดการแล้ว)
        self.api_key = os.getenv('GEMINI_API_KEY')
        if not self.api_key:
            raise ValueError("GEMINI_API_KEY environment variable is not set or .env file is not loaded properly.")
        
        # 2. การกำหนดค่า (Configuration) (ปรับปรุง)
        # ตั้งค่า API Key สำหรับ genai
        genai.configure(api_key=self.api_key)
        
        # 3. การสร้าง Model และ Chat Session (ปรับปรุง)
        # ใช้ genai.GenerativeModel สำหรับการสนทนาที่มีประวัติ
        self.model_name = 'gemini-2.5-flash' # ใช้ gemini-2.5-flash (มี support Chat history)
        self.model = genai.GenerativeModel(self.model_name)
        self.chat_session = None
        
        # 4. ดึงการตั้งค่าจาก Django AISettings model
        self.ai_settings = get_ai_settings()
        
        # สร้าง System Context สำหรับแชท (จะใส่ในข้อความแรก)
        self.system_context = self._build_system_context()
        
        # 5. การจัดการประวัติการสนทนา
        self.chat_history = []
        self._start_new_chat_session()
    
    def _build_system_context(self):
        """สร้าง system context จากการตั้งค่า AISettings"""
        if self.ai_settings and self.ai_settings.is_active:
            sales_steps_text = self.ai_settings.sales_steps.replace('\n', '\n• ')
            context = f"""บทบาท: คุณคือพนักงานขายของร้านค้า AI CASHIER 
ทักทาย: {self.ai_settings.greeting_message}
โปรโมชั่น: {self.ai_settings.promotion_text}
ขั้นตอนการขาย:
• {sales_steps_text}
คำลงท้าย: {self.ai_settings.closing_message}

คำแนะนำ: เป็นมิตร สุภาพ ช่วยลูกค้าเลือกสินค้า ใช้ภาษาไทย"""
        else:
            context = """บทบาท: คุณคือพนักงานขายของร้านค้า AI CASHIER
คำแนะนำ: เป็นมิตร สุภาพ ช่วยลูกค้าเลือกสินค้า ใช้ภาษาไทย"""
        return context

    def _start_new_chat_session(self):
        """สร้างและเริ่มต้น Chat Session ใหม่"""
        # สร้าง chat session ด้วย GenerativeModel.start_chat()
        self.chat_session = self.model.start_chat(history=self.chat_history)
        return self.chat_session
    
    def get_response(self, user_message: str, shop_context: str = None) -> str:
        """
        ส่งข้อความไป Gemini และรับคำตอบกลับ พร้อมจัดการบริบทของร้านค้า
        
        Args:
            user_message: ข้อความจากผู้ใช้
            shop_context: บริบทของร้านค้า (ชื่อร้าน, สินค้าที่มี ฯลฯ)
        
        Returns:
            คำตอบจาก Gemini
        """
        try:
            # ตรวจสอบว่า AI ปิดใช้งานหรือไม่
            if self.ai_settings and not self.ai_settings.is_active:
                return "ขออภัยครับ ระบบ AI กำลังปิดใช้งาน"
            
            # 6. การจัดการบริบทของร้านค้า (ปรับปรุง)
            # รวม system context + shop context + user message
            full_message = self.system_context + "\n\n"
            
            if shop_context:
                full_message += f"บริบทร้านค้า: {shop_context}\n\n"
            
            full_message += user_message
            
            # 7. การเรียก Gemini API (ใช้ chat session)
            response = self.chat_session.send_message(full_message)
            
            if response.text:
                return response.text.strip()
            else:
                return "ขออภัยครับ ไม่สามารถประมวลผลคำขอของคุณได้ในขณะนี้"
        
        except Exception as e:
            # การจัดการข้อผิดพลาดที่ดีขึ้น
            error_message = f"Error in Gemini API: {str(e)}"
            print(error_message)
            return f"ขออภัยครับ เกิดข้อผิดพลาด: {error_message}"
    


    def get_product_recommendation(self, customer_needs: str, available_products: list) -> str:
        """
        ให้คำแนะนำสินค้าตามความต้องการของลูกค้า (ใช้ generate_content โดยไม่มีประวัติ)
        # ... Docstring คงเดิม ...
        """
        try:
            # ตรวจสอบว่า AI ปิดใช้งานหรือไม่
            if self.ai_settings and not self.ai_settings.is_active:
                return "ขออภัยครับ ระบบ AI กำลังปิดใช้งาน"
            
            products_info = "\n".join([
                f"- {p['name']}: ฿{p['price']} ({p['category']})"
                for p in available_products
            ])
            
            # ใช้ prompt ที่ชัดเจน พร้อมข้อมูลจาก AISettings
            greeting = self.ai_settings.greeting_message if self.ai_settings else "สวัสดีครับ"
            promotion = self.ai_settings.promotion_text if self.ai_settings else ""
            
            prompt = f"""{greeting}

คุณเป็นพนักงานขายของร้าน AI CASHIER กรุณาแนะนำสินค้าจากรายการด้านล่างนี้
ลูกค้าต้องการ: {customer_needs}

สินค้าที่มีในร้าน:
{products_info}

{promotion if promotion else ''}

กรุณาแนะนำสินค้าที่เหมาะสมที่สุด เพียง 1-2 รายการ โดยอธิบายเหตุผลสั้น ๆ"""
            
            # 8. การเรียก API สำหรับงานที่ไม่ต้องการประวัติ (ใช้ generate_content)
            response = self.model.generate_content(prompt)
            
            return response.text.strip() if response.text else "ขออภัยครับ ไม่มีสินค้าที่เหมาะสม"
        
        except Exception as e:
            error_message = f"Error in product recommendation: {str(e)}"
            print(error_message)
            return "ขออภัยครับ ไม่สามารถให้คำแนะนำได้ในขณะนี้"


    
    def clear_history(self):
        """ล้างประวัติการสนทนาโดยการเริ่ม Chat Session ใหม่"""
        # 9. การล้างประวัติ (ปรับปรุง)
        self.chat_history = []
        self._start_new_chat_session()
        print("Conversation history cleared and new chat session started.")

    def get_history(self):
        """แสดงประวัติการสนทนาปัจจุบัน"""
        # 10. การเข้าถึงประวัติ (เพิ่มฟังก์ชัน)
        if not self.chat_session:
            return []
        
        history = self.chat_session.history
        formatted_history = []
        for message in history:
            text_content = ""
            if hasattr(message, 'parts') and message.parts:
                # Extract text from parts
                for part in message.parts:
                    if hasattr(part, 'text'):
                        text_content += part.text
            
            formatted_history.append({
                'role': message.role, 
                'text': text_content
            })
        return formatted_history
    
    def get_featured_products(self):
        """ดึงสินค้าแนะนำจาก AISettings"""
        if not self.ai_settings:
            return []
        
        featured = []
        for item in [self.ai_settings.featured_item_1, self.ai_settings.featured_item_2, 
                     self.ai_settings.featured_item_3, self.ai_settings.featured_item_4]:
            if item:
                featured.append({
                    'id': item.id,
                    'name': item.name,
                    'price': float(item.price),
                    'category': item.category.name if item.category else 'ไม่ระบุ',
                    'description': item.ai_information or item.description or ''
                })
        return featured
    
    def get_settings_info(self):
        """ดึงข้อมูลการตั้งค่า AI ทั้งหมด"""
        if not self.ai_settings:
            return None
        
        return {
            'is_active': self.ai_settings.is_active,
            'greeting_message': self.ai_settings.greeting_message,
            'promotion_text': self.ai_settings.promotion_text,
            'sales_steps': self.ai_settings.sales_steps,
            'closing_message': self.ai_settings.closing_message,
            'featured_products': self.get_featured_products()
        }
    
    def get_response_with_rag(self, user_message: str) -> str:
        """
        ตอบคำถามโดยใช้ RAG (Retrieval Augmented Generation)
        ค้นหาข้อมูลสินค้าจาก ChromaDB แล้วตอบคำถาม
        """
        try:
            # ตรวจสอบว่า RAG service พร้อมใช้งานหรือไม่
            rag_service = get_rag_service()
            if not rag_service:
                # ถ้า RAG ไม่พร้อม ให้ใช้ normal response
                return self.get_response(user_message)
            
            # ใช้ RAG เพื่อค้นหาและตอบคำถาม
            response = rag_service.rag_query(user_message)
            return response
        
        except Exception as e:
            print(f"Error in RAG response: {e}")
            # Fallback ไปใช้ normal response
            return self.get_response(user_message)


# ทดสอบการเชื่อมต่อ Gemini API และโหลดการตั้งค่า AISettings
try:
    gemini_service = GeminiChatService()
    print("Gemini Service initialized successfully.")
    print("AI Settings loaded from database")
    
    # ดึงข้อมูลการตั้งค่า
    if gemini_service.ai_settings:
        settings_info = gemini_service.get_settings_info()
        print(f"\n--- AI Settings Information ---")
        print(f"Status: {'Active' if settings_info['is_active'] else 'Inactive'}")
        print(f"Greeting: {settings_info['greeting_message'][:50]}...")
        print(f"Promotion: {settings_info['promotion_text'][:50]}...")
        print(f"Featured Products: {len(settings_info['featured_products'])} items")
    

except Exception as e:
    print(f"*** Warning: Could not initialize Gemini Service: {e} ***")
    gemini_service = None

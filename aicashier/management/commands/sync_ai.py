# aicashier/management/commands/sync_ai.py

from django.core.management.base import BaseCommand
from aicashier.models import Product
import sys
import time  # <--- 1. เพิ่มบรรทัดนี้

class Command(BaseCommand):
    help = 'Sync product data to RAG Vector Database'

    def handle(self, *args, **kwargs):
        self.stdout.write("⏳ กำลังเตรียมการเชื่อมต่อ AI Service...")

        try:
            from aicashier.rag_service import rag_service
            if rag_service is None:
                self.stdout.write(self.style.ERROR("❌ Error: rag_service เป็น None"))
                return
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"❌ Error Service: {e}"))
            return

        products = Product.objects.all()
        total = products.count()
        self.stdout.write(f"📦 พบสินค้าทั้งหมด: {total} รายการ")

        if total == 0:
            return

        self.stdout.write("🔄 กำลังเริ่ม Sync ข้อมูล (จะหน่วงเวลา 5 วินาทีต่อรายการ เพื่อกันโดนบล็อก)...")
        
        success = 0
        for i, p in enumerate(products):
            try:
                # 2. เพิ่มการหน่วงเวลาตรงนี้ (สำคัญมาก!)
                if i > 0: 
                    self.stdout.write("   ...พัก 5 วินาที...")
                    time.sleep(0) 

                rag_service.update_product_in_rag(p)
                success += 1
                self.stdout.write(self.style.SUCCESS(f"   ✓ Sync สำเร็จ ({i+1}/{total}): {p.name}"))
            
            except Exception as e:
                # ถ้ายัง Error 429 ให้พักยาวหน่อยแล้วลองใหม่
                if "429" in str(e):
                    self.stdout.write(self.style.WARNING(f"   ⚠️ โดนจำกัดความเร็ว! พัก 30 วินาที..."))
                    time.sleep(0)
                    try:
                        rag_service.update_product_in_rag(p) # ลองอีกครั้ง
                        success += 1
                        self.stdout.write(self.style.SUCCESS(f"   ✓ Sync สำเร็จ (Retry): {p.name}"))
                    except:
                         self.stdout.write(self.style.ERROR(f"   × Sync ล้มเหลว: {p.name}"))
                else:
                    self.stdout.write(self.style.ERROR(f"   × Sync ล้มเหลว: {p.name} ({e})"))

        self.stdout.write(self.style.SUCCESS(f"\n✅ เสร็จสิ้น! Sync ข้อมูลไปแล้ว {success}/{total} รายการ"))
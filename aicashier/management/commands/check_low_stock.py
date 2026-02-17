"""
Management command to check low stock inventory and send email notifications
Usage: python manage.py check_low_stock
"""

from django.core.management.base import BaseCommand
from aicashier.services import InventoryService


class Command(BaseCommand):
    help = 'ตรวจสอบสินค้าที่ใกล้หมด และส่อง email แจ้งเตือน'

    def handle(self, *args, **options):
        self.stdout.write('🔍 กำลังตรวจสอบสินค้าคงเหลือ...')
        
        result = InventoryService.check_and_notify_low_stock()
        
        if result['success']:
            if result['products_count'] > 0:
                self.stdout.write(
                    self.style.WARNING(
                        f'⚠️  พบสินค้าที่ใกล้หมด: {result["products_count"]} รายการ'
                    )
                )
                for product in result['products']:
                    self.stdout.write(
                        f"  • {product['name']} - เหลือ {product['quantity']} ชิ้น"
                    )
                self.stdout.write(
                    self.style.SUCCESS('✓ ส่งอีเมลแจ้งเตือนเรียบร้อย')
                )
            else:
                self.stdout.write(
                    self.style.SUCCESS('✓ สินค้าทั้งหมดมีจำนวนเพียงพอ')
                )
        else:
            self.stdout.write(
                self.style.ERROR(f'✗ เกิดข้อผิดพลาด: {result.get("error", "Unknown error")}')
            )

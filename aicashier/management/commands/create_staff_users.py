from django.core.management.base import BaseCommand
from aicashier.models import Customer

class Command(BaseCommand):
    help = 'สร้างบัญชีผู้ใช้สำหรับ 3 หน้า: หน้าร้าน (cashier), คิว (queue), หน้าออเดอร์ (order_manager)'

    def handle(self, *args, **options):
        staff_accounts = [
            {
                'username': 'cashier',
                'email': 'cashier@aicashier.local',
                'contact_number': '0800000001',
                'password': 'cashier1234',
                'staff_role': 'cashier',
                'page_name': 'หน้าร้าน (Cashier / POS)',
            },
            {
                'username': 'queue',
                'email': 'queue@aicashier.local',
                'contact_number': '0800000002',
                'password': 'queue1234',
                'staff_role': 'order_complete',
                'page_name': 'คิว (Queue Display)',
            },
            {
                'username': 'order_complete',
                'email': 'ordercomplete@aicashier.local',
                'contact_number': '0800000003',
                'password': 'queue1234',
                'staff_role': 'order_complete',
                'page_name': 'คิว (Queue Display - Alias)',
            },
            {
                'username': 'order',
                'email': 'order@aicashier.local',
                'contact_number': '0800000004',
                'password': 'order1234',
                'staff_role': 'order_manager',
                'page_name': 'หน้าออเดอร์ (Order Management / Kitchen)',
            },
            {
                'username': 'order_manager',
                'email': 'ordermanager@aicashier.local',
                'contact_number': '0800000005',
                'password': 'order1234',
                'staff_role': 'order_manager',
                'page_name': 'หน้าออเดอร์ (Order Management - Alias)',
            },
        ]

        self.stdout.write(self.style.SUCCESS("=" * 60))
        self.stdout.write(self.style.SUCCESS("🚀 กำลังสร้าง/อัปเดตบัญชีพนักงานสำหรับ 3 หน้างาน..."))
        self.stdout.write(self.style.SUCCESS("=" * 60))

        for acc in staff_accounts:
            user, created = Customer.objects.get_or_create(
                username=acc['username'],
                defaults={
                    'email': acc['email'],
                    'contact_number': acc['contact_number'],
                    'is_staff': True,
                    'is_active': True,
                    'staff_role': acc['staff_role'],
                }
            )

            user.set_password(acc['password'])
            user.is_staff = True
            user.is_active = True
            user.staff_role = acc['staff_role']
            if not user.email:
                user.email = acc['email']
            if not user.contact_number:
                user.contact_number = acc['contact_number']
            user.save()

            action = "สร้างใหม่" if created else "อัปเดตรหัสผ่านและสิทธิ์"
            self.stdout.write(
                f"✅ [{acc['page_name']}] {action}: "
                f"Username: {acc['username']} | Password: {acc['password']} | Role: {acc['staff_role']}"
            )

        self.stdout.write(self.style.SUCCESS("=" * 60))
        self.stdout.write(self.style.SUCCESS("🎉 เรียบร้อย! สามารถนำ Username และ Password ไปเข้าสู่ระบบได้ทันที"))
        self.stdout.write(self.style.SUCCESS("=" * 60))

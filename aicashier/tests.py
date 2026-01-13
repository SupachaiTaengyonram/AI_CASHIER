from django.test import TestCase
from django.urls import reverse
from .models import Customer, Product

# การตั้งค่าพื้นฐานสำหรับ Tests ทั้งหมด
class BaseTestCase(TestCase):
    
    def setUp(self):
        # 1. สร้าง User ทั่วไป (สำหรับทดสอบ Login และการเข้าถึง)
        self.user_password = 'UserPass123!'
        self.user = Customer.objects.create_user(
            username='testuser',
            email='user@example.com',
            contact_number='0810001111',
            password=self.user_password
        )

        # 2. สร้าง Superuser (Admin) (สำหรับทดสอบส่วน Admin)
        self.admin_password = 'AdminPass123!'
        self.admin_user = Customer.objects.create_superuser(
            username='adminuser',
            email='admin@example.com',
            contact_number='0890009999',
            password=self.admin_password
        )

        # 3. URL ที่ใช้บ่อย
        self.login_url = reverse('login')
        self.home_url = reverse('home')
        self.product_manage_url = reverse('product_manage')
        self.product_create_url = reverse('product_create')


class CustomerModelTests(BaseTestCase):
    
    def test_create_customer(self):
        """
        Test 1: เขียน Test สำหรับการสร้าง Customer (User)
        ทดสอบว่า create_user สร้างผู้ใช้ทั่วไปได้ถูกต้อง
        """
        self.assertEqual(self.user.username, 'testuser')
        self.assertEqual(self.user.email, 'user@example.com')
        # ตรวจสอบว่ารหัสผ่านถูก Hashed (ไม่ใช่ Plain text)
        self.assertTrue(self.user.check_password(self.user_password))
        # ตรวจสอบว่าไม่ใช่ Admin
        self.assertFalse(self.user.is_staff)
        self.assertFalse(self.user.is_superuser)

    def test_create_superuser(self):
        """
        Test 1: เขียน Test สำหรับการสร้าง Customer (Superuser)
        ทดสอบว่า create_superuser สร้างแอดมินได้ถูกต้อง
        """
        self.assertEqual(self.admin_user.username, 'adminuser')
        self.assertTrue(self.admin_user.check_password(self.admin_password))
        # ตรวจสอบว่าเป็น Admin
        self.assertTrue(self.admin_user.is_staff)
        self.assertTrue(self.admin_user.is_superuser)


class AuthAndAccessTests(BaseTestCase):

    def test_customer_login_success(self):
        """
        Test 2: เขียน Test สำหรับการ Login (สำเร็จ)
        """
        response = self.client.post(self.login_url, {
            'username': 'testuser',
            'password': self.user_password
        })
        # หลัง Login สำเร็จ (User ทั่วไป) ควรเด้งไปหน้า 'home'
        self.assertRedirects(response, self.home_url)
        # ตรวจสอบว่ามี Session login จริง
        self.assertTrue('_auth_user_id' in self.client.session)

    def test_customer_login_fail(self):
        """
        Test 2: เขียน Test สำหรับการ Login (ล้มเหลว - รหัสผิด)
        """
        response = self.client.post(self.login_url, {
            'username': 'testuser',
            'password': 'WrongPassword!'
        })
        # ถ้า Login ผิด, ควรกลับมาที่หน้า Login (Status 200)
        self.assertEqual(response.status_code, 200)
        # ตรวจสอบว่า *ไม่มี* Session login
        self.assertFalse('_auth_user_id' in self.client.session)

    def test_normal_user_cannot_access_admin_page(self):
        """
        Test 3: เขียน Test ว่า User ทั่วไป ไม่สามารถ เข้าถึงหน้า Admin ได้
        (ทดสอบหน้า 'product_manage')
        """
        # 1. ล็อกอินด้วย User ทั่วไป
        self.client.login(username='testuser', password=self.user_password)
        
        # 2. พยายามเข้าหน้า Admin ('product_manage')
        response = self.client.get(self.product_manage_url)

        # 3. ตรวจสอบว่าถูก Redirect ไปหน้า Login
        #    (ตัว decorator @user_passes_test จะ redirect ไปหน้า login ที่กำหนดไว้)
        expected_redirect_url = f"{self.login_url}?next={self.product_manage_url}"
        
        self.assertEqual(response.status_code, 302) # 302 คือรหัสของการ Redirect
        self.assertRedirects(response, expected_redirect_url)


class ProductTests(BaseTestCase):

    def test_admin_can_create_product(self):
        """
        Test 4: เขียน Test สำหรับการสร้าง Product (โดย Admin)
        """
        # 1. ล็อกอินด้วย Admin
        self.client.login(username='adminuser', password=self.admin_password)

        # 2. ข้อมูล Product ที่จะสร้าง
        product_data = {
            'name': 'New Test Product',
            'description': 'A product for testing.',
            'price': 199.99,
            'quantity': 50
        }

        # 3. ส่ง POST request ไปยัง URL 'product_create'
        response = self.client.post(self.product_create_url, product_data)

        # 4. ตรวจสอบว่าถูก Redirect ไปหน้า 'product_manage' (ตาม success_url)
        self.assertRedirects(response, self.product_manage_url)

        # 5. ตรวจสอบว่า Product ถูกสร้างขึ้นในฐานข้อมูลจริง
        self.assertTrue(Product.objects.filter(name='New Test Product').exists())
        self.assertEqual(Product.objects.count(), 1)
        
        created_product = Product.objects.get(name='New Test Product')
        self.assertEqual(created_product.price, 199.99)

    def test_user_cannot_create_product(self):
        """
        Test (เพิ่มเติม): ตรวจสอบว่า User ทั่วไป *สร้าง* Product ไม่ได้
        """
        # 1. ล็อกอินด้วย User ทั่วไป
        self.client.login(username='testuser', password=self.user_password)

        # 2. ข้อมูล Product
        product_data = {
            'name': 'Unauthorized Product',
            'price': 10.00,
            'quantity': 1
        }
        
        # 3. พยายามส่ง POST request
        response = self.client.post(self.product_create_url, product_data)
        
        # 4. ตรวจสอบว่าถูก Redirect ไปหน้า Login (เหมือน Test 3)
        expected_redirect_url = f"{self.login_url}?next={self.product_create_url}"
        self.assertRedirects(response, expected_redirect_url)
        
        # 5. ตรวจสอบว่า Product *ไม่* ถูกสร้างขึ้นในฐานข้อมูล
        self.assertFalse(Product.objects.filter(name='Unauthorized Product').exists())
        self.assertEqual(Product.objects.count(), 0)

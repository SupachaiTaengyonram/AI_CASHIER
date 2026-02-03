from django.db import models
from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin, BaseUserManager

class CustomerManager(BaseUserManager):
    def create_user(self, username, email, contact_number, password=None, **extra_fields):
        if not email:
            raise ValueError('The Email must be set')
        email = self.normalize_email(email)
        user = self.model(username=username, email=email, contact_number=contact_number, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, username, email, contact_number, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        return self.create_user(username, email, contact_number, password, **extra_fields)

class Customer(AbstractBaseUser, PermissionsMixin):
    STAFF_ROLE_CHOICES = [
        ('cashier', 'พนักงานแคชเชียร์ (หน้าร้าน)'),
        ('order_manager', 'พนักงานจัดการออเดอร์ (คิวออเดอร์)'),
        ('order_complete', 'พนักงานยืนยันเสร็จ (ยืนยันคิว)'),
    ]
    
    username = models.CharField(max_length=150, unique=True)
    email = models.EmailField(unique=True)
    contact_number = models.CharField(max_length=20)
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    staff_role = models.CharField(max_length=20, choices=STAFF_ROLE_CHOICES, blank=True, null=True, help_text="สิทธิ์การใช้งานของพนักงาน")
    date_joined = models.DateTimeField(auto_now_add=True)

    objects = CustomerManager()

    USERNAME_FIELD = 'username'
    REQUIRED_FIELDS = ['email', 'contact_number']

    def __str__(self):
        return self.username

class Category(models.Model):
    """หมวดหมู่สินค้า"""
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name_plural = "Categories"
        ordering = ['name']
    
    def __str__(self):
        return self.name

class Product(models.Model):
    product_code = models.CharField(max_length=10, unique=True, blank=True, null=True, help_text="รหัสสินค้า เช่น P0001, F1234")
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True, null=True)
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True, blank=True, related_name='products')
    price = models.DecimalField(max_digits=10, decimal_places=2)
    quantity = models.PositiveIntegerField(default=0)
    image_url = models.URLField(max_length=500, blank=True, null=True)
    image = models.ImageField(upload_to='products/', blank=True, null=True, help_text="อัพโหลดรูปภาพสินค้า")
    ai_information = models.TextField(blank=True, null=True, help_text="ข้อมูลส่วนนี้จะถูกใช้โดย AI เพื่อให้ข้อมูลกับลูกค้า")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name


class Order(models.Model):
    ORDER_STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
    ]
    
    ORDER_TYPE_CHOICES = [
        ('online', '🌐 ออนไลน์'),
        ('counter', '🏪 หน้าร้าน'),
    ]
    
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE, related_name='orders')
    total_price = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.CharField(max_length=20, choices=ORDER_STATUS_CHOICES, default='pending')
    order_type = models.CharField(max_length=20, choices=ORDER_TYPE_CHOICES, default='online', help_text='ประเภทออเดอร์')
    order_number = models.PositiveIntegerField(null=True, blank=True, help_text='หมายเลขออเดอร์ (รีเซ็ททุกวัน)')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Order #{self.order_number or self.id} - {self.product.name} x{self.quantity}"

    class Meta:
        ordering = ['-created_at']
    
    @staticmethod
    def get_next_order_number():
        """สร้างหมายเลขออเดอร์ที่รีเซ็ททุกวัน เริ่มจาก 1000"""
        from django.utils import timezone
        from datetime import datetime
        
        today = timezone.now().date()
        today_orders = Order.objects.filter(
            created_at__date=today,
            order_number__isnull=False
        ).order_by('-order_number')
        
        if today_orders.exists():
            last_number = today_orders.first().order_number
            return last_number + 1
        return 1000


class OrderItem(models.Model):
    """รายการสินค้าในแต่ละออเดอร์"""
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1)
    price = models.DecimalField(max_digits=10, decimal_places=2, help_text="ราคาต่อหน่วยตอนที่สั่ง")
    subtotal = models.DecimalField(max_digits=10, decimal_places=2)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['id']
    
    def __str__(self):
        return f"{self.order.order_number} - {self.product.name} x{self.quantity}"
    
    def save(self, *args, **kwargs):
        """คำนวณ subtotal ก่อนบันทึก"""
        self.subtotal = self.price * self.quantity
        super().save(*args, **kwargs)


class AISettings(models.Model):
    """AI Sales Assistant Configuration"""
    
    # Status
    is_active = models.BooleanField(default=True, help_text="Enable/Disable AI Sales Assistant")
    
    # AI Greeting and Messages
    greeting_message = models.TextField(
        default="สวัสดีครับ! ยินดีต้อนรับสู่ร้าน AI CASHIER",
        help_text="ข้อความทักทายเริ่มแรก"
    )
    
    # Promotions
    promotion_text = models.TextField(
        default="เรามีโปรโมชั่นพิเศษ: ซื้อ 2 แก้ว ลด 10%",
        help_text="ข้อความแนะนำโปรโมชั่น"
    )
    
    # Sales Flow/Steps
    sales_steps = models.TextField(
        default="""1. ทักทาย
2. ถามความต้องการ
3. แนะนำสินค้า
4. ให้ดูรายละเอียด
5. เสนอราคา
6. ยืนยันการสั่งซื้อ
7. ขอบคุณและลาจาก""",
        help_text="ลำดับขั้นตอนการขายให้ลูกค้า (แต่ละขั้นตอนคั่นด้วย newline)"
    )
    
    # Closing Message
    closing_message = models.TextField(
        default="ขอบคุณที่ใช้บริการ! หวังว่าจะพบคุณอีกครั้ง",
        help_text="คำลงท้ายหลังจากขายสินค้า"
    )
    
    # Featured Menu Items (Top 4)
    featured_item_1 = models.ForeignKey(
        Product,
        null=True,
        blank=True,
        related_name='featured_as_first',
        on_delete=models.SET_NULL,
        help_text="เมนูแรก (ด้านบน)"
    )
    featured_item_2 = models.ForeignKey(
        Product,
        null=True,
        blank=True,
        related_name='featured_as_second',
        on_delete=models.SET_NULL,
        help_text="เมนูที่สอง (ด้านบน)"
    )
    featured_item_3 = models.ForeignKey(
        Product,
        null=True,
        blank=True,
        related_name='featured_as_third',
        on_delete=models.SET_NULL,
        help_text="เมนูที่สาม (ด้านบน)"
    )
    featured_item_4 = models.ForeignKey(
        Product,
        null=True,
        blank=True,
        related_name='featured_as_fourth',
        on_delete=models.SET_NULL,
        help_text="เมนูที่สี่ (ด้านบน)"
    )
    
    # Voice Commands for Adding/Removing Items
    voice_commands_add = models.TextField(
        default="เพิ่ม|add|ใส่|put|สั่ง|order|ซื้อ|buy",
        help_text="คำสั่งเสียงสำหรับ เพิ่มสินค้า (แต่ละคำคั่นด้วย |)"
    )
    
    voice_commands_decrease = models.TextField(
        default="ลด|decrease|ลดจำนวน|reduce|ลดลง|down",
        help_text="คำสั่งเสียงสำหรับ ลดจำนวนสินค้า (แต่ละคำคั่นด้วย |)"
    )
    
    voice_commands_delete = models.TextField(
        default="ลบ|delete|เอาออก|remove|หยิบออก|pick|ถอด|extract",
        help_text="คำสั่งเสียงสำหรับ ลบสินค้า (แต่ละคำคั่นด้วย |)"
    )
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "AI Settings"
        verbose_name_plural = "AI Settings"
    
    def __str__(self):
        return "AI Settings Configuration"
    
    @classmethod
    def get_settings(cls):
        """Get or create default settings"""
        settings, created = cls.objects.get_or_create(pk=1)
        return settings


class Promotion(models.Model):
    """โปรโมชั่นและแบนเนอร์"""
    title = models.CharField(max_length=200, help_text="ชื่อโปรโมชั่น")
    description = models.TextField(blank=True, null=True, help_text="รายละเอียดโปรโมชั่น")
    image_url = models.URLField(max_length=500, blank=True, null=True)
    image = models.ImageField(upload_to='promotions/', blank=True, null=True, help_text="อัพโหลดรูปภาพโปรโมชั่น")
    is_active = models.BooleanField(default=True, help_text="เปิด/ปิดการแสดง")
    display_order = models.PositiveIntegerField(default=0, help_text="ลำดับการแสดง (เรียงจากน้อยไปมาก)")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['display_order', '-created_at']
        verbose_name = "Promotion"
        verbose_name_plural = "Promotions"
    
    def __str__(self):
        return self.title


class Payment(models.Model):
    """บันทึกการชำระเงิน"""
    PAYMENT_STATUS_CHOICES = [
        ('pending', 'รอการชำระเงิน'),
        ('confirmed', 'ชำระเงินแล้ว'),
        ('failed', 'ชำระเงินล้มเหลว'),
        ('expired', 'หมดเวลา'),
    ]
    
    PAYMENT_METHOD_CHOICES = [
        ('promptpay', 'PromptPay QR'),
        ('cash', 'เงินสด'),
        ('card', 'บัตรเครดิต'),
        ('stripe', 'Stripe Payment'),
    ]
    
    # Order info
    customer = models.ForeignKey(Customer, on_delete=models.SET_NULL, null=True, blank=True, related_name='payments')
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    
    # Payment details
    payment_method = models.CharField(max_length=20, choices=PAYMENT_METHOD_CHOICES, default='promptpay')
    payment_status = models.CharField(max_length=20, choices=PAYMENT_STATUS_CHOICES, default='pending')
    
    # PromptPay QR Code
    qr_code_data = models.TextField(blank=True, null=True, help_text="QR Code payload for PromptPay")
    reference_number = models.CharField(max_length=50, unique=True, help_text="Unique payment reference")
    
    # Stripe Payment Link fields
    stripe_checkout_session_id = models.CharField(max_length=100, blank=True, null=True, help_text="Stripe Checkout Session ID")
    stripe_payment_link_id = models.CharField(max_length=100, blank=True, null=True, help_text="Stripe Payment Link ID")
    stripe_payment_url = models.TextField(blank=True, null=True, help_text="Stripe Payment Link or Checkout URL")
    stripe_qr_code_url = models.URLField(max_length=1000, blank=True, null=True, help_text="Stripe QR Code URL")
    stripe_response = models.JSONField(blank=True, null=True, help_text="Full Stripe API response")
    
    # Timeline
    created_at = models.DateTimeField(auto_now_add=True)
    confirmed_at = models.DateTimeField(blank=True, null=True)
    updated_at = models.DateTimeField(auto_now=True)
    expires_at = models.DateTimeField(blank=True, null=True, help_text="QR expires after 15 minutes")
    
    # Notes
    transaction_id = models.CharField(max_length=100, blank=True, null=True, help_text="Bank transaction ID")
    notes = models.TextField(blank=True, null=True)
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = "Payment"
        verbose_name_plural = "Payments"
    
    def __str__(self):
        return f"Payment #{self.id} - {self.amount} THB - {self.get_payment_status_display()}"
    
    @property
    def is_expired(self):
        """ตรวจสอบว่า QR Code หมดอายุหรือไม่"""
        from django.utils import timezone
        if self.expires_at and timezone.now() > self.expires_at:
            return True
        return False






from .models import Product, AISettings, Category, Promotion
from django import forms
from .models import Customer
import re

class ProductForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs.update({
                'style': 'background-color:#393a5a;color:#fff;border-radius:6px;padding:8px 12px;border:1.5px solid #b16cff;',
            })
        # กำหนด help text
        self.fields['product_code'].help_text = "รหัสสินค้า (2 ตัวอักษร + 4 ตัวเลข เช่น P0001, F1234) - ถ้าไม่ระบุจะสร้างอัตโนมัติ"
    
    def clean_product_code(self):
        product_code = self.cleaned_data.get('product_code')
        if product_code:
            # ตรวจสอบรูปแบบ: 2 ตัวอักษร + 4 ตัวเลข
            if not re.match(r'^[A-Za-z]{2}\d{4}$', product_code):
                raise forms.ValidationError('รหัสสินค้าต้องเป็น 2 ตัวอักษรและ 4 ตัวเลข (เช่น P0001, F1234)')
            
            # ตรวจสอบว่าซ้ำหรือไม่
            existing = Product.objects.filter(product_code=product_code)
            if self.instance.pk:
                existing = existing.exclude(pk=self.instance.pk)
            if existing.exists():
                raise forms.ValidationError('รหัสสินค้านี้มีอยู่แล้ว')
        
        return product_code
    
    class Meta:
        model = Product
        fields = ['product_code', 'name', 'description', 'category', 'price', 'quantity', 'image', 'image_url', 'ai_information']

class CustomerForm(forms.ModelForm):
    password = forms.CharField(widget=forms.PasswordInput, label="Password")
    confirm_password = forms.CharField(widget=forms.PasswordInput, label="Confirm password")

    class Meta:
        model = Customer
        fields = ['username', 'email', 'contact_number', 'password']

    def clean(self):
        cleaned = super().clean()
        p1 = cleaned.get('password')
        p2 = cleaned.get('confirm_password')
        if p1 and p2 and p1 != p2:
            self.add_error('confirm_password', 'Passwords do not match')
        return cleaned

    def save(self, commit=True):
        user = super().save(commit=False)
        # แปลงรหัสผ่านเป็น hash ด้วย set_password
        user.set_password(self.cleaned_data['password'])
        if commit:
            user.save()
        return user

class CustomerUpdateForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs.update({
                'style': 'background-color:#393a5a;color:#fff;border-radius:6px;padding:8px 12px;border:1.5px solid #b16cff;',
            })
    
    class Meta:
        model = Customer
        fields = ['username', 'email', 'contact_number']


class AISettingsForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            if isinstance(field.widget, forms.Textarea):
                field.widget.attrs.update({
                    'style': 'background-color:#393a5a;color:#fff;border-radius:6px;padding:8px 12px;border:1.5px solid #b16cff;min-height:100px;',
                    'rows': 4,
                })
            elif isinstance(field.widget, forms.CheckboxInput):
                field.widget.attrs.update({
                    'style': 'width:18px;height:18px;cursor:pointer;',
                })
            elif isinstance(field.widget, forms.Select):
                field.widget.attrs.update({
                    'style': 'background-color:#393a5a;color:#fff;border-radius:6px;padding:8px 12px;border:1.5px solid #b16cff;',
                })
            else:
                field.widget.attrs.update({
                    'style': 'background-color:#393a5a;color:#fff;border-radius:6px;padding:8px 12px;border:1.5px solid #b16cff;',
                })
    
    class Meta:
        model = AISettings
        fields = ['is_active', 'greeting_message', 'promotion_text', 'sales_steps', 'closing_message', 'voice_commands', 'featured_item_1', 'featured_item_2', 'featured_item_3', 'featured_item_4']
        labels = {
            'is_active': 'เปิดใช้งาน AI',
            'greeting_message': 'ข้อความทักทายเริ่มแรก',
            'promotion_text': 'ข้อความโปรโมชั่น',
            'sales_steps': 'ลำดับขั้นตอนการขาย',
            'closing_message': 'คำลงท้าย',
            'voice_commands': 'คำสั่งเสียงจัดการสินค้า',
            'featured_item_1': 'เมนูแนะนำที่ 1',
            'featured_item_2': 'เมนูแนะนำที่ 2',
            'featured_item_3': 'เมนูแนะนำที่ 3',
            'featured_item_4': 'เมนูแนะนำที่ 4',
        }

class PromotionForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            if isinstance(field.widget, forms.Textarea):
                field.widget.attrs.update({
                    'style': 'background-color:#393a5a;color:#fff;border-radius:6px;padding:8px 12px;border:1.5px solid #b16cff;min-height:80px;',
                    'rows': 3,
                })
            elif isinstance(field.widget, forms.CheckboxInput):
                field.widget.attrs.update({
                    'style': 'width:18px;height:18px;cursor:pointer;',
                })
            elif isinstance(field.widget, forms.NumberInput):
                field.widget.attrs.update({
                    'style': 'background-color:#393a5a;color:#fff;border-radius:6px;padding:8px 12px;border:1.5px solid #b16cff;width:80px;',
                })
            else:
                field.widget.attrs.update({
                    'style': 'background-color:#393a5a;color:#fff;border-radius:6px;padding:8px 12px;border:1.5px solid #b16cff;',
                })
    
    class Meta:
        model = Promotion
        fields = ['title', 'description', 'image', 'image_url', 'is_active', 'display_order']
        labels = {
            'title': 'ชื่อโปรโมชั่น',
            'description': 'รายละเอียด',
            'image': 'อัพโหลดรูปภาพ',
            'image_url': 'URL รูปภาพ',
            'is_active': 'เปิดใช้งาน',
            'display_order': 'ลำดับการแสดง',
        }
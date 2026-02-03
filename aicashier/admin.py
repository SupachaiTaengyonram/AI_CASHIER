from django.contrib import admin
from django import forms
from django.contrib.auth.forms import ReadOnlyPasswordHashField
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import Product, Customer, AISettings, Payment, Promotion

class CustomerCreationAdminForm(forms.ModelForm):
    password1 = forms.CharField(label="Password", widget=forms.PasswordInput)
    password2 = forms.CharField(label="Password confirmation", widget=forms.PasswordInput)

    class Meta:
        model = Customer
        fields = ("username", "email", "contact_number")

    def clean_password2(self):
        p1 = self.cleaned_data.get("password1")
        p2 = self.cleaned_data.get("password2")
        if p1 and p2 and p1 != p2:
            raise forms.ValidationError("Passwords don't match")
        return p2

    def save(self, commit=True):
        user = super().save(commit=False)
        user.set_password(self.cleaned_data["password1"])
        if commit:
            user.save()
        return user

class CustomerChangeAdminForm(forms.ModelForm):
    password = ReadOnlyPasswordHashField()

    class Meta:
        model = Customer
        fields = ("username", "email", "contact_number", "password", "is_active", "is_staff", "is_superuser", "groups", "user_permissions")

@admin.register(Customer)
class CustomerAdmin(BaseUserAdmin):
    form = CustomerChangeAdminForm
    add_form = CustomerCreationAdminForm

    list_display = ("username", "email", "contact_number", "is_staff", "is_superuser", "is_active", "date_joined")
    list_filter = ("is_staff", "is_superuser", "is_active")
    search_fields = ("username", "email", "contact_number")
    ordering = ("id",)

    fieldsets = (
        (None, {"fields": ("username", "password")}),
        ("Personal info", {"fields": ("email", "contact_number")}),
        ("Permissions", {"fields": ("is_active", "is_staff", "is_superuser", "groups", "user_permissions")}),
        ("Important dates", {"fields": ("last_login", "date_joined")}),
    )
    add_fieldsets = (
        (None, {
            "classes": ("wide",),
            "fields": ("username", "email", "contact_number", "password1", "password2", "is_staff", "is_superuser", "is_active"),
        }),
    )

@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ("name", "price", "image_url", "updated_at")
    search_fields = ("name",)
    list_filter = ("created_at",)


@admin.register(Promotion)
class PromotionAdmin(admin.ModelAdmin):
    list_display = ("title", "is_active", "display_order", "updated_at")
    list_filter = ("is_active", "created_at")
    search_fields = ("title", "description")
    list_editable = ("display_order", "is_active")
    fieldsets = (
        ("Basic Info", {
            "fields": ("title", "description")
        }),
        ("Media", {
            "fields": ("image", "image_url")
        }),
        ("Display Settings", {
            "fields": ("is_active", "display_order")
        }),
    )


@admin.register(AISettings)
class AISettingsAdmin(admin.ModelAdmin):
    fieldsets = (
        ("Status", {"fields": ("is_active",)}),
        ("Messages", {"fields": ("greeting_message", "promotion_text", "closing_message")}),
        ("Sales Steps", {"fields": ("sales_steps",)}),
        ("Featured Menu Items (Top 3)", {
            "fields": ("featured_item_1", "featured_item_2", "featured_item_3"),
            "description": "เลือกเมนู 3 รายการที่จะแสดงบนหน้าหลัก"
        }),
        ("Voice Commands for Cart Management", {
            "fields": ("voice_commands_add", "voice_commands_decrease", "voice_commands_delete"),
            "description": "คำสั่งเสียงสำหรับจัดการตะกร้า (แต่ละคำคั่นด้วย |)<br>เมื่อบันทึก voice commands จะ auto-reload ในระบบ"
        }),
    )
    
    def has_add_permission(self, request):
        # ให้มีได้แค่ 1 settings เท่านั้น
        return not AISettings.objects.exists()
    
    def has_delete_permission(self, request, obj=None):
        # ห้ามลบ settings
        return False


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ("reference_number", "amount", "payment_status", "payment_method", "created_at")
    list_filter = ("payment_status", "payment_method", "created_at")
    search_fields = ("reference_number", "transaction_id")
    readonly_fields = ("reference_number", "qr_code_data", "created_at", "confirmed_at", "expires_at")
    
    fieldsets = (
        ("Payment Info", {
            "fields": ("reference_number", "amount", "payment_method", "payment_status")
        }),
        ("Customer", {
            "fields": ("customer",)
        }),
        ("PromptPay QR", {
            "fields": ("qr_code_data",)
        }),
        ("Timeline", {
            "fields": ("created_at", "confirmed_at", "expires_at", "updated_at")
        }),
        ("Transaction", {
            "fields": ("transaction_id", "notes")
        }),
    )
    
    def has_add_permission(self, request):
        return False


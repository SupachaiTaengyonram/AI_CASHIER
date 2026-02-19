from chromadb import logger
from django.conf import settings
from django.contrib.auth.views import LoginView
import os
import logging
from django.contrib.auth.decorators import user_passes_test
from django.utils.decorators import method_decorator
from django.db import models
from .forms import ProductForm, AISettingsForm, CustomerUpdateForm, PromotionForm
from django.shortcuts import render,redirect, get_object_or_404
from django.urls import reverse, reverse_lazy
from django.views.generic import ListView, CreateView, UpdateView, DeleteView, DetailView, TemplateView, View
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.messages.views import SuccessMessageMixin
from django.contrib import messages
from django.http import JsonResponse, StreamingHttpResponse
from django.utils import timezone
import json
import uuid
from .models import Customer, Product, AISettings, Category, Payment, Order, Promotion
from aicashier.models import OrderItem
from .forms import CustomerForm
from django.contrib.auth import authenticate, logout
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
from .rag_service import rag_service
from django.db.models import Sum, Count, Avg, F
from datetime import timedelta
from django.contrib.auth.mixins import UserPassesTestMixin
from django.http import HttpResponseForbidden
from .services import (
    StaffCallService,
    OrderCancellationService,
    InventoryService,
    OrderAnalyticsService
)


# Setup logger
logger = logging.getLogger(__name__)

# Initialize Stripe Service
stripe_service = None
try:
    from .stripe_service import stripe_service
except Exception as e:
    print(f"Warning: Could not initialize Stripe service: {e}")
    stripe_service = None


# Initialize RAG Service - โหลดข้อมูลสินค้าจากฐานข้อมูล
rag_service = None
try:
    from .rag_service import rag_service
    if rag_service:
        print("✓ RAG Service initialized and products loaded")
except Exception as e:
    print(f"Warning: Could not initialize RAG service: {e}")
    rag_service = None

# --- Admin check helper (must be above all uses) ---
def admin_required(user):
    return user.is_authenticated and user.is_staff

class CustomLoginView(LoginView):
    def form_valid(self, form):
        response = super().form_valid(form)
        return response

@method_decorator(user_passes_test(admin_required, login_url='login'), name='dispatch')
class CustomerListView(LoginRequiredMixin, ListView):
    model = Customer
    template_name = 'aicashier/customer_list.html'
    context_object_name = 'customers'
    login_url = 'login'

@method_decorator(user_passes_test(admin_required, login_url='login'), name='dispatch')
class CustomerDetailView(LoginRequiredMixin, DetailView):
    model = Customer
    template_name = 'aicashier/customer_detail.html'
    context_object_name = 'customer'
    login_url = 'login'

class CustomerCreateView(SuccessMessageMixin, CreateView):
    model = Customer
    form_class = CustomerForm
    template_name = 'aicashier/sing_up.html'   # ใช้ชื่อไฟล์ตามที่คุณตั้งไว้ (sing_)
    success_url = reverse_lazy('login')        # สมัครเสร็จ → เด้งไป sign in
    success_message = "สมัครสมาชิกเรียบร้อย! กรุณาเข้าสู่ระบบ"

@method_decorator(user_passes_test(admin_required, login_url='login'), name='dispatch')
class CustomerUpdateView(LoginRequiredMixin, UpdateView):
    model = Customer
    form_class = CustomerForm
    template_name = 'aicashier/customer_form.html'
    success_url = reverse_lazy('customer_list')
    login_url = 'login'

@method_decorator(user_passes_test(admin_required, login_url='login'), name='dispatch')
class CustomerDeleteView(LoginRequiredMixin, DeleteView):
    model = Customer
    template_name = 'aicashier/customer_confirm_delete.html'
    success_url = reverse_lazy('customer_list')
    login_url = 'login'


class HomeView(LoginRequiredMixin, ListView):
    template_name = 'aicashier/home.html'
    context_object_name = 'products'
    login_url = 'login'  # ถ้าไม่ล็อกอินให้เด้งไปหน้า sign in

    def get(self, request, *args, **kwargs):
        # ตรวจสอบสิทธิ์: staff ที่เป็น order_manager ห้ามเข้าหน้าร้าน
        if request.user.is_staff and request.user.staff_role == 'order_manager':
            return redirect('order_management')
        
        # ตรวจสอบสิทธิ์: staff ที่เป็น order_complete ให้เข้าหน้าแสดงคิว
        if request.user.is_staff and request.user.staff_role == 'order_complete':
            return redirect('order_queue_display')
        
        # ตรวจสอบว่า AI ถูกปิดหรือไม่
        ai_settings = AISettings.get_settings()
        if not ai_settings.is_active and not request.user.is_staff:
            return redirect('ai_disabled')
        
        response = super().get(request, *args, **kwargs)
        
        # เพิ่ม cache control ให้ home page ปลอดภัย
        response['Cache-Control'] = 'no-cache, no-store, must-revalidate, max-age=0'
        response['Pragma'] = 'no-cache'
        response['Expires'] = '0'
        
        return response

    def get_queryset(self):
        qs = Product.objects.order_by('-updated_at')
        q = self.request.GET.get('q')
        if q:
            qs = qs.filter(name__icontains=q)
        return qs

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        # เผื่อไว้ให้ cart/ยอดรวมในอนาคต
        ctx['cart_total'] = 0
        
        # ส่ง user role ไป template
        ctx['is_staff'] = self.request.user.is_staff
        
        # ดึง AI Settings และ Featured Items
        ai_settings = AISettings.get_settings()
        featured_items = []
        
        if ai_settings.featured_item_1:
            featured_items.append(ai_settings.featured_item_1)
        if ai_settings.featured_item_2:
            featured_items.append(ai_settings.featured_item_2)
        if ai_settings.featured_item_3:
            featured_items.append(ai_settings.featured_item_3)
        if ai_settings.featured_item_4:
            featured_items.append(ai_settings.featured_item_4)
        
        ctx['featured_items'] = featured_items
        ctx['categories'] = Category.objects.all()
        ctx['promotions'] = Promotion.objects.filter(is_active=True)
        
        return ctx


@method_decorator(user_passes_test(admin_required, login_url='login'), name='dispatch')
class ProductListView(ListView):
    model = Product
    template_name = 'aicashier/product/manage_product.html'
    context_object_name = 'products'

@method_decorator(user_passes_test(admin_required, login_url='login'), name='dispatch')
class ProductCreateView(CreateView):
    model = Product
    form_class = ProductForm
    template_name = 'aicashier/product/product_form.html'
    success_url = reverse_lazy('product_manage')
    
    def form_valid(self, form):
        # สร้างรหัสอัตโนมัติถ้าไม่ระบุ
        if not form.cleaned_data.get('product_code'):
            product_code = self._generate_product_code()
            form.instance.product_code = product_code
        
        response = super().form_valid(form)
        
        # เพิ่มสินค้าเข้า RAG system
        try:
            if rag_service:
                product = self.object
                rag_service.add_product_to_rag(
                    product_id=product.id,
                    product_name=product.name,
                    description=product.description or "",
                    price=float(product.price),
                    category=product.category.name if product.category else "ไม่มีหมวด"
                )
        except Exception as e:
            print(f"Warning: Could not add product to RAG: {e}")
        
        return response
    
    def _generate_product_code(self):
        """สร้างรหัสสินค้าอัตโนมัติ: P + 4 ตัวเลข"""
        # หารหัสสินค้าสูงสุด
        last_product = Product.objects.filter(
            product_code__startswith='P'
        ).order_by('-product_code').first()
        
        if last_product and last_product.product_code:
            try:
                # แยกเลขออกมา
                last_code = last_product.product_code
                last_number = int(last_code[1:])  # ลบ 'P' ตัวแรก
                next_number = last_number + 1
            except (ValueError, IndexError):
                next_number = 1
        else:
            next_number = 1
        
        # สร้างรหัสใหม่ 2 ตัวอักษร (P) + 4 ตัวเลข
        return f"P{str(next_number).zfill(4)}"

@method_decorator(user_passes_test(admin_required, login_url='login'), name='dispatch')
class ProductUpdateView(UpdateView):
    model = Product
    form_class = ProductForm
    template_name = 'aicashier/product/product_form.html'
    success_url = reverse_lazy('product_manage')
    
    def form_valid(self, form):
        response = super().form_valid(form)
        
        # อัพเดตสินค้าใน RAG system (ลบเก่า + เพิ่มใหม่)
        try:
            from .rag_service import rag_service
            if rag_service:
                product = self.object
                # ลบของเก่า
                rag_service.delete_product_from_rag(product.id)
                # เพิ่มของใหม่
                rag_service.add_product_to_rag(
                    product_id=product.id,
                    product_name=product.name,
                    description=product.description or "",
                    price=float(product.price),
                    category=product.category.name if product.category else "ไม่มีหมวด"
                )
        except Exception as e:
            print(f"Warning: Could not update product in RAG: {e}")
        
        return response

@method_decorator(user_passes_test(admin_required, login_url='login'), name='dispatch')
class ProductDeleteView(DeleteView):
    model = Product
    template_name = 'aicashier/product/product_confirm_delete.html'
    success_url = reverse_lazy('product_manage')
    
    def delete(self, request, *args, **kwargs):
        product = self.get_object()
        
        # ลบสินค้าออกจาก RAG system
        try:
            from .rag_service import rag_service
            if rag_service:
                rag_service.delete_product_from_rag(product.id)
        except Exception as e:
            print(f"Warning: Could not delete product from RAG: {e}")
        
        return super().delete(request, *args, **kwargs)

@method_decorator(user_passes_test(admin_required, login_url='login'), name='dispatch')
class OverviewsView(LoginRequiredMixin, ListView):
    model = Product
    template_name = 'aicashier/overviews/overviews.html'
    context_object_name = 'products'
    login_url = 'login'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        
        # Get all products
        all_products = Product.objects.all().order_by('-updated_at')
        
        # Calculate statistics from products
        total_products = all_products.count()
        total_stock = all_products.aggregate(Sum('quantity'))['quantity__sum'] or 0
        avg_price = all_products.aggregate(Avg('price'))['price__avg'] or 0
        
        
        # Get today's date
        today = timezone.now().date()
        
        # Calculate revenue from orders (TODAY)
        today_orders = Order.objects.filter(
            created_at__date=today,
            status='completed'
        )
        today_revenue = today_orders.aggregate(Sum('total_price'))['total_price__sum'] or 0.0
        today_order_count = today_orders.count()
        
        # Get total customers
        total_customers = Customer.objects.count()
        total_customers_today = Customer.objects.filter(
            date_joined__date=today
        ).count()
        
        # Calculate total completed orders
        total_completed_orders = Order.objects.filter(status='completed').count()
        
        # Prepare statistics cards data
        stats = {
            'total_revenue': f"฿{float(today_revenue):,.2f}",
            'total_orders': total_completed_orders,
            'new_customers': total_customers_today,
            'products_in_stock': total_stock,
            'today_orders': today_order_count,
        }
        
        # Prepare product data for charts - TOP SELLERS BY ORDERS
        # Use OrderItem to access products since Order now has many-to-many relationship through OrderItem

        
        products_orders = OrderItem.objects.filter(order__status='completed').values('product__name').annotate(
            quantity=Sum('quantity')
        ).order_by('-quantity')[:4]
        
        top_products = [{'name': p['product__name'], 'quantity': p['quantity']} for p in products_orders]
        
        pie_labels = json.dumps([p['name'][:20] for p in top_products] if top_products else [])
        pie_data = json.dumps([p['quantity'] for p in top_products] if top_products else [])
        
        # Prepare bar chart data (LAST 7 DAYS) - ต้องแสดงวันจริงไทย
        from datetime import datetime, date
        
        # Get last 7 days with Thai day names
        # weekday() returns: 0=Mon, 1=Tue, 2=Wed, 3=Thu, 4=Fri, 5=Sat, 6=Sun
        thai_days = {
            0: 'จ',      # จันทร์
            1: 'อ',      # อังคาร  
            2: 'พ',      # พุธ
            3: 'พฤ',     # พฤหัสบดี
            4: 'ศ',      # ศุกร์
            5: 'ส',      # เสาร์
            6: 'อา'      # อาทิตย์
        }
        
        # Get last 7 days of orders with actual dates
        weekly_data_list = []
        days_display = []  # วันและวันที่ เช่น "จ.11"
        
        for i in range(6, -1, -1):
            target_date = today - timedelta(days=i)
            day_of_week = target_date.weekday()  # 0=Mon, 6=Sun
            day_order_count = Order.objects.filter(
                created_at__date=target_date,
                status='completed'
            ).count()
            weekly_data_list.append(max(0, day_order_count))
            # สร้างป้ายกำกับเป็น "จ.11" (วันจันทร์ที่ 11) - ตรงกับวันจริง
            days_display.append(f"{thai_days[day_of_week]}.{target_date.day}")
        
        weekly_data_json = json.dumps(weekly_data_list)
        days_json = json.dumps(days_display)
        
        # Prepare line chart data (THIS MONTH) - รองรับจำนวนวันที่เปลี่ยนแปลง
        from calendar import monthrange
        
        # Get number of days in current month
        days_in_month = monthrange(today.year, today.month)[1]
        
        # Get first day of current month
        first_day_of_month = date(today.year, today.month, 1)
        
        monthly_data_list = []
        monthly_labels = []
        
        for day in range(1, days_in_month + 1):
            target_date = date(today.year, today.month, day)
            day_order_count = Order.objects.filter(
                created_at__date=target_date,
                status='completed'
            ).count()
            monthly_data_list.append(max(0, day_order_count))
            
            # สร้างป้ายกำกับ: แสดงแต่วันที่และวันของสัปดาห์
            # เช่น "11 จ" (11 จันทร์) หรือแค่ "11" ถ้าต้องการเรียบง่าย
            day_of_week = target_date.weekday()
            monthly_labels.append(str(day))  # แสดงเลขวันที่เท่านั้น
        
        monthly_data_json = json.dumps(monthly_data_list)
        monthly_labels_json = json.dumps(monthly_labels)
        
        # === NEW ANALYTICS DATA ===
        from .services import OrderAnalyticsService
        
        # ดึงข้อมูลวิเคราะห์เฉพาะ staff เท่านั้น
        aov_data = {}
        cancellation_data = {}
        
        if self.request.user.is_staff:
            # Average Order Value (30 days)
            aov_data = OrderAnalyticsService.get_average_order_value(days=30)
            
            # Cancellation Rate (30 days)
            cancellation_data = OrderAnalyticsService.get_cancellation_rate(days=30)
        
        context.update({
            'stats': stats,
            'top_products': top_products,
            'pie_labels': pie_labels,
            'pie_data': pie_data,
            'days': days_json,
            'weekly_data': weekly_data_json,
            'monthly_data': monthly_data_json,
            'monthly_labels': monthly_labels_json,
            'total_customers': total_customers,
            'avg_price': f"฿{avg_price:.2f}" if avg_price else "฿0.00",
            # New analytics
            'aov_data': aov_data,
            'cancellation_data': cancellation_data,
        })
        
        return context


@method_decorator(user_passes_test(admin_required, login_url='login'), name='dispatch')
class AISettingsView(LoginRequiredMixin, UpdateView):
    """Admin view to manage AI Settings"""
    model = AISettings
    form_class = AISettingsForm
    template_name = 'aicashier/ai_settings.html'
    success_url = reverse_lazy('ai_settings')
    login_url = 'login'
    
    def get_object(self, queryset=None):
        """Get or create the single AISettings object"""
        obj, created = AISettings.objects.get_or_create(pk=1)
        return obj
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'AI Settings - ตั้งค่า AI'
        return context
    
    def form_valid(self, form):
        """บันทึก AI Settings และ reload voice commands"""
        response = super().form_valid(form)
        
        # Reload voice commands ใน RAG service
        if rag_service:
            try:
                rag_service.reload_voice_commands()
                messages.success(self.request, '✓ บันทึกตั้งค่าเรียบร้อย (อัปเดตคำสั่งเสียงแล้ว)')
            except Exception as e:
                print(f"Error reloading voice commands: {e}")
                messages.warning(self.request, '✓ บันทึกตั้งค่าเรียบร้อย (แต่ประสบปัญหาในการอัปเดตคำสั่งเสียง)')
        else:
            messages.success(self.request, '✓ บันทึกตั้งค่าเรียบร้อย')
        
        return response


@method_decorator(user_passes_test(admin_required, login_url='login'), name='dispatch')
class AIStatusToggleView(LoginRequiredMixin, UpdateView):
    """Toggle AI active status (requires admin password)"""
    model = AISettings
    fields = ['is_active']
    success_url = reverse_lazy('ai_settings')
    login_url = 'login'
    
    def get_object(self, queryset=None):
        obj, created = AISettings.objects.get_or_create(pk=1)
        return obj
    
    def post(self, request, *args, **kwargs):
        # Check admin credentials
        username = request.POST.get('admin_username')
        password = request.POST.get('admin_password')
        
        # Authenticate admin
        from django.contrib.auth import authenticate
        admin_user = authenticate(username=username, password=password)
        
        if admin_user is None or not admin_user.is_staff:
            from django.contrib import messages
            messages.error(request, 'ชื่อผู้ใช้หรือรหัสผ่าน Admin ไม่ถูกต้อง')
            return redirect('ai_settings')
        
        # Toggle AI status
        ai_settings = self.get_object()
        ai_settings.is_active = not ai_settings.is_active
        ai_settings.save()
        
        from django.contrib import messages
        status_text = "เปิด" if ai_settings.is_active else "ปิด"
        messages.success(request, f'AI Assistant ถูก{status_text}แล้ว')
        
        return redirect('ai_settings')


# Close AI view - requires authentication
def close_ai_view(request):
    """Admin closes AI and takes over manually"""
    from django.contrib.auth import authenticate
    from django.contrib import messages
    
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        
        # Authenticate the user
        user = authenticate(request, username=username, password=password)
        
        if user is not None and user.is_staff:
            # Turn off AI
            from aicashier.models import AISettings
            try:
                ai_settings = AISettings.objects.first()
                if ai_settings:
                    ai_settings.is_active = False
                    ai_settings.save()
                    messages.success(request, f'AI ถูกปิดแล้ว! {user.username} เข้ามาจัดการแทน')
            except:
                pass
            logout(request)
            return redirect('login')
        
        else:
            messages.error(request, 'ชื่อผู้ใช้หรือรหัสผ่านไม่ถูกต้อง หรือไม่มีสิทธิ์')
            return redirect('home')
    
    return redirect('home')


# Profile Views
class ProfileView(LoginRequiredMixin, DetailView):
    model = Customer
    template_name = 'aicashier/profile.html'
    context_object_name = 'customer'
    login_url = 'login'
    
    def get_object(self):
        return self.request.user

class ProfileUpdateView(LoginRequiredMixin, UpdateView):
    model = Customer
    form_class = CustomerUpdateForm
    template_name = 'aicashier/profile_edit.html'
    login_url = 'login'
    
    def get_object(self):
        return self.request.user
    
    def form_valid(self, form):
        from django.contrib import messages
        messages.success(self.request, 'ข้อมูลของคุณได้รับการอัปเดตเรียบร้อย!')
        return super().form_valid(form)
    
    def get_success_url(self):
        return reverse_lazy('profile')


class FeaturedMenuView(LoginRequiredMixin, TemplateView):
    """จัดการเมนูแนะนำ (Featured Menu) ใน Product Manage Page"""
    template_name = 'aicashier/product/featured_menu.html'
    login_url = 'login'
    
    def dispatch(self, request, *args, **kwargs):
        # อนุญาตเฉพาะ staff/admin
        if not request.user.is_staff:
            return HttpResponseForbidden()
        return super().dispatch(request, *args, **kwargs)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        ai_settings = AISettings.get_settings()
        context['ai_settings'] = ai_settings
        context['products'] = Product.objects.all()
        context['featured_item_1'] = ai_settings.featured_item_1
        context['featured_item_2'] = ai_settings.featured_item_2
        context['featured_item_3'] = ai_settings.featured_item_3
        context['featured_item_4'] = ai_settings.featured_item_4
        return context
    
    def post(self, request, *args, **kwargs):
        ai_settings = AISettings.get_settings()
        
        # รับค่าจาก form
        featured_item_1_id = request.POST.get('featured_item_1')
        featured_item_2_id = request.POST.get('featured_item_2')
        featured_item_3_id = request.POST.get('featured_item_3')
        featured_item_4_id = request.POST.get('featured_item_4')
        
        # อัพเดท
        if featured_item_1_id and featured_item_1_id != 'none':
            ai_settings.featured_item_1 = Product.objects.get(id=featured_item_1_id)
        else:
            ai_settings.featured_item_1 = None
            
        if featured_item_2_id and featured_item_2_id != 'none':
            ai_settings.featured_item_2 = Product.objects.get(id=featured_item_2_id)
        else:
            ai_settings.featured_item_2 = None
            
        if featured_item_3_id and featured_item_3_id != 'none':
            ai_settings.featured_item_3 = Product.objects.get(id=featured_item_3_id)
        else:
            ai_settings.featured_item_3 = None
            
        if featured_item_4_id and featured_item_4_id != 'none':
            ai_settings.featured_item_4 = Product.objects.get(id=featured_item_4_id)
        else:
            ai_settings.featured_item_4 = None
        
        ai_settings.save()
        
        from django.contrib import messages
        messages.success(request, 'บันทึกเมนูแนะนำเรียบร้อย!')
        return redirect('featured_menu')


# ===== Promotion Views =====
@method_decorator(user_passes_test(admin_required, login_url='login'), name='dispatch')
class PromotionListView(LoginRequiredMixin, ListView):
    model = Promotion
    template_name = 'aicashier/product/manage_promotion.html'
    context_object_name = 'promotions'
    login_url = 'login'
    
    def get_queryset(self):
        return Promotion.objects.all().order_by('display_order')


@method_decorator(user_passes_test(admin_required, login_url='login'), name='dispatch')
class PromotionCreateView(LoginRequiredMixin, CreateView):
    model = Promotion
    form_class = PromotionForm
    template_name = 'aicashier/product/promotion_form.html'
    success_url = reverse_lazy('manage_promotion')
    login_url = 'login'
    
    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['title'] = 'เพิ่มโปรโมชั่น'
        ctx['button_text'] = 'เพิ่มโปรโมชั่น'
        return ctx
    
    def form_valid(self, form):
        messages.success(self.request, 'เพิ่มโปรโมชั่นเรียบร้อย!')
        return super().form_valid(form)


@method_decorator(user_passes_test(admin_required, login_url='login'), name='dispatch')
class PromotionUpdateView(LoginRequiredMixin, UpdateView):
    model = Promotion
    form_class = PromotionForm
    template_name = 'aicashier/product/promotion_form.html'
    success_url = reverse_lazy('manage_promotion')
    login_url = 'login'
    
    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['title'] = f'แก้ไขโปรโมชั่น: {self.object.title}'
        ctx['button_text'] = 'บันทึกการเปลี่ยนแปลง'
        return ctx
    
    def form_valid(self, form):
        messages.success(self.request, 'อัพเดทโปรโมชั่นเรียบร้อย!')
        return super().form_valid(form)


@method_decorator(user_passes_test(admin_required, login_url='login'), name='dispatch')
class PromotionDeleteView(LoginRequiredMixin, DeleteView):
    model = Promotion
    template_name = 'aicashier/product/promotion_confirm_delete.html'
    success_url = reverse_lazy('manage_promotion')
    login_url = 'login'
    
    def delete(self, request, *args, **kwargs):
        messages.success(request, 'ลบโปรโมชั่นเรียบร้อย!')
        return super().delete(request, *args, **kwargs)


@method_decorator(user_passes_test(admin_required, login_url='login'), name='dispatch')
class CategoryListView(ListView):
    """แสดงรายการหมวดหมู่ และจัดการแก้ไขหมวดของสินค้า"""
    model = Category
    template_name = 'aicashier/product/manage_category.html'
    context_object_name = 'categories'
    
    def get_context_data(self, **kwargs):
        import json
        context = super().get_context_data(**kwargs)
        # นับจำนวนสินค้าในแต่ละหมวด
        categories = Category.objects.annotate(product_count=models.Count('products'))
        context['categories'] = categories
        
        products = Product.objects.all()
        context['products'] = products
        
        # เตรียมข้อมูล JSON สำหรับ JavaScript
        products_data = []
        for product in products:
            products_data.append({
                'id': product.id,
                'name': product.name,
                'price': float(product.price),
                'category_id': product.category.id if product.category else None,
            })
        context['products_json'] = json.dumps(products_data)
        
        return context
    
    def post(self, request, *args, **kwargs):
        from django.contrib import messages
        product_id = request.POST.get('product_id')
        category_id = request.POST.get('category_id')
        
        try:
            product = Product.objects.get(id=product_id)
            if category_id:
                category = Category.objects.get(id=category_id)
                product.category = category
            else:
                product.category = None
            product.save()
            messages.success(request, f'อัปเดตหมวดของ "{product.name}" สำเร็จ!')
        except (Product.DoesNotExist, Category.DoesNotExist):
            messages.error(request, 'ไม่พบข้อมูล')
        
        return redirect('manage_category')

@method_decorator(user_passes_test(admin_required, login_url='login'), name='dispatch')
class CategoryCreateView(CreateView):
    """สร้างหมวดหมู่ใหม่"""
    model = Category
    fields = ['name', 'description']
    template_name = 'aicashier/product/category_form.html'
    success_url = reverse_lazy('manage_category')
    
    def form_valid(self, form):
        from django.contrib import messages
        messages.success(self.request, f'สร้างหมวด "{form.cleaned_data["name"]}" สำเร็จ!')
        return super().form_valid(form)


@method_decorator(user_passes_test(admin_required, login_url='login'), name='dispatch')
class CategoryUpdateView(UpdateView):
    """แก้ไขหมวดหมู่"""
    model = Category
    fields = ['name', 'description']
    template_name = 'aicashier/product/category_form.html'
    success_url = reverse_lazy('manage_category')
    
    def post(self, request, *args, **kwargs):
        # ประมวลผล POST data
        self.object = self.get_object()
        
        # อัปเดตข้อมูลพื้นฐาน
        self.object.name = request.POST.get('name', self.object.name)
        self.object.description = request.POST.get('description', self.object.description)
        self.object.save()
        
        # จัดการการเปลี่ยนแปลงสินค้า
        product_ids_str = request.POST.get('product_ids', '')
        if product_ids_str:
            try:
                new_product_ids = [int(id) for id in product_ids_str.split(',') if id.strip()]
                
                # ลบสินค้าที่ไม่อยู่ในรายการใหม่
                old_products = self.object.products.all()
                for product in old_products:
                    if product.id not in new_product_ids:
                        product.category = None
                        product.save()
                
                # เพิ่มสินค้าใหม่
                for product_id in new_product_ids:
                    try:
                        product = Product.objects.get(id=product_id)
                        product.category = self.object
                        product.save()
                    except Product.DoesNotExist:
                        pass
            except (ValueError, AttributeError):
                pass
        
        from django.contrib import messages
        messages.success(request, f'อัปเดตหมวด "{self.object.name}" สำเร็จ!')
        
        return redirect(self.get_success_url())


@method_decorator(user_passes_test(admin_required, login_url='login'), name='dispatch')
class CategoryDeleteView(DeleteView):
    """ลบหมวดหมู่"""
    model = Category
    template_name = 'aicashier/product/category_confirm_delete.html'
    success_url = reverse_lazy('manage_category')
    
    def delete(self, request, *args, **kwargs):
        from django.contrib import messages
        category = self.get_object()
        messages.success(request, f'ลบหมวด "{category.name}" สำเร็จ!')
        return super().delete(request, *args, **kwargs)


class DisableAIView(LoginRequiredMixin, TemplateView):
    """หน้าแสดงว่า AI ถูกปิดใช้งาน แล้วต้องใส่ password เพื่อเปิดใช้งาน"""
    template_name = 'aicashier/ai_disabled.html'
    login_url = 'login'
    
    def get(self, request, *args, **kwargs):
        # ตรวจสอบว่า AI ถูกปิดใช้งานหรือไม่
        ai_settings = AISettings.objects.first()
        if ai_settings and ai_settings.is_active:
            # ถ้า AI ยังเปิดอยู่ เด้งกลับไป home
            return redirect('home')
        
        # ตั้ง session เพื่อให้รู้ว่าผู้ใช้อยู่ในหน้า disabled
        request.session['ai_disabled_page'] = True
        request.session['ai_disabled_time'] = str(__import__('time').time())
        
        response = super().get(request, *args, **kwargs)
        
        # ตั้ง HTTP headers ป้องกัน caching และ back button
        response['Cache-Control'] = 'no-cache, no-store, must-revalidate, max-age=0, post-check=0, pre-check=0'
        response['Pragma'] = 'no-cache'
        response['Expires'] = '0'
        
        return response
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        return context
    
    def post(self, request, *args, **kwargs):
        from django.contrib import messages
        username = request.POST.get('username', '').strip()
        password = request.POST.get('password', '').strip()
        
        # ตรวจสอบ Admin Credentials
        user = authenticate(username=username, password=password)
        if user and user.is_staff:
            # เปิดใช้งาน AI
            ai_settings = AISettings.objects.first()
            if ai_settings:
                ai_settings.is_active = True
                ai_settings.save()
                
                # ล้าง session marker
                if 'ai_disabled_page' in request.session:
                    del request.session['ai_disabled_page']
                if 'ai_disabled_time' in request.session:
                    del request.session['ai_disabled_time']

                messages.success(request, 'เปิดใช้งาน AI แล้ว!')
                return redirect('home')
        
        messages.error(request, 'ชื่อผู้ใช้หรือรหัสผ่านไม่ถูกต้อง')
        return redirect('ai_disabled')


class ConfirmDisableAIView(LoginRequiredMixin, TemplateView):
    """หน้ายืนยันการปิด AI ต้องใส่ username/password ก่อน"""
    template_name = 'aicashier/confirm_disable_ai.html'
    login_url = 'login'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        return context
    
    def post(self, request, *args, **kwargs):
        from django.contrib import messages
        username = request.POST.get('username', '').strip()
        password = request.POST.get('password', '').strip()
        
        # ตรวจสอบ Admin Credentials
        user = authenticate(username=username, password=password)
        if user and user.is_staff:
            # ปิด AI
            ai_settings = AISettings.objects.first()
            if ai_settings:
                ai_settings.is_active = False
                ai_settings.save()
            
            messages.success(request, 'ปิดใช้งาน AI แล้ว!')
            return redirect('ai_disabled')
        
        messages.error(request, 'ชื่อผู้ใช้หรือรหัสผ่านไม่ถูกต้อง')
        return redirect('confirm_disable_ai')


class DisableAIActionView(LoginRequiredMixin, TemplateView):
    """Action view ที่เมื่อเข้าก็เด้งไปหน้า confirm"""
    login_url = 'login'
    
    def get(self, request, *args, **kwargs):
        # เด้งไปหน้า confirm_disable_ai แทนที่ปิด AI ทันที
        response = redirect('confirm_disable_ai')
        response['Cache-Control'] = 'no-cache, no-store, must-revalidate, max-age=0'
        response['Pragma'] = 'no-cache'
        response['Expires'] = '0'
        
        return response



# ======================== PAYMENT VIEWS ========================



class PaymentView(LoginRequiredMixin, View):
    """Redirect to Stripe Payment Link directly"""
    
    def get(self, request, *args, **kwargs):
        try:
            customer = request.user.customer
        except AttributeError:
            customer = None

        total_amount = request.session.get('payment_amount', 0)
        
        if total_amount <= 0:
            return redirect('home')

        reference = str(uuid.uuid4())[:12].upper()
        
        # 1. สร้าง Payment Record
        payment = Payment.objects.create(
            customer=customer,
            amount=total_amount,
            payment_method='stripe',
            reference_number=reference,
            created_at=timezone.now(),
            expires_at=timezone.now() + timezone.timedelta(hours=1)
        )
        
        # 2. สร้าง Payment Link ผ่าน Stripe
        if stripe_service:
            # สร้าง success URL - ต้องเป็น absolute URL
            success_url = request.build_absolute_uri(reverse('payment_success', args=[payment.id]))
            cancel_url = request.build_absolute_uri(reverse('home'))
            
            logger.info(f"Creating payment - Success URL: {success_url}")
            logger.info(f"Creating payment - Cancel URL: {cancel_url}")
            
            # สร้าง Checkout Session + Payment Link (เพื่อได้ QR code)
            payment_result = stripe_service.create_payment_link(
                amount=total_amount,
                description=f"Order Ref: {reference}",
                metadata={
                    "payment_id": payment.id,
                    "customer": request.user.username if request.user else "guest"
                },
                success_url=success_url,
                cancel_url=cancel_url
            )
            
            if payment_result['success']:
                payment_url = payment_result.get('payment_url')
                qr_code_url = payment_result.get('qr_code_url')
                payment.stripe_checkout_session_id = payment_result.get('checkout_session_id')
                payment.stripe_payment_link_id = payment_result.get('payment_link_id')
                payment.stripe_payment_url = payment_url
                payment.stripe_qr_code_url = qr_code_url
                payment.save()
                
                if payment_result.get('checkout_session_id'):
                    logger.info(f"✓ Stripe Checkout Session created: {payment_result['checkout_session_id']}")
                if payment_result.get('payment_link_id'):
                    logger.info(f"✓ Stripe Payment Link created: {payment_result.get('payment_link_id')}")
                
                # Redirect ไป Stripe Payment Page โดยตรง
                return redirect(payment_url)
            else:
                error_msg = payment_result.get('error')
                logger.error(f"Payment Link creation failed: {error_msg}")
                messages.error(request, f"ไม่สามารถสร้าง Payment Link: {error_msg}")
                return redirect('home')
        else:
            messages.error(request, "Stripe service ไม่พร้อม")
            return redirect('home')

    def post(self, request, *args, **kwargs):
        return redirect('payment')

# ฟังก์ชันเช็คสถานะ
def check_payment_status(request, payment_id):
    try:
        payment = Payment.objects.get(id=payment_id)
        if payment.payment_status == 'confirmed':
             return JsonResponse({'status': 'confirmed'})

        # Payment Link จะ redirect โดยตรง ไม่ต้องตรวจสอบ status
        if payment.stripe_payment_link_id:
            return JsonResponse({'status': 'pending'})
                
        return JsonResponse({'status': 'pending'})
    except Payment.DoesNotExist:
        return JsonResponse({'status': 'error'}, status=404)


class PaymentSuccessView(DetailView):
    """หน้าแสดงความสำเร็จของการชำระเงิน พร้อมแสดงสินค้าที่สั่ง"""
    model = Payment
    template_name = 'aicashier/payment_success.html'
    context_object_name = 'payment'
    login_url = 'login'
    pk_url_kwarg = 'payment_id'
    
    def get_object(self, queryset=None):
        """ดึง Payment object และ auto-confirm ถ้า redirect มาจาก Stripe"""
        payment = super().get_object(queryset)
        
        # Fallback: ถ้า payment ยังเป็น pending แต่ user redirect มาจาก Stripe
        # แสดงว่า payment สำเร็จแล้ว (webhook อาจไม่ได้ trigger ในเวลา)
        if payment.payment_status == 'pending':
            # ตรวจสอบว่ามี Stripe payment link ID หรือไม่
            if payment.stripe_payment_link_id or payment.stripe_checkout_session_id:
                # Stripe ได้ redirect มา = payment สำเร็จ
                payment.payment_status = 'confirmed'
                payment.confirmed_at = timezone.now()
                payment.save()
                logger.info(f"✓ Payment {payment.id} auto-confirmed (fallback from Stripe redirect)")
        
        return payment
    
    def get_context_data(self, **kwargs):
        """เพิ่มข้อมูลสินค้าที่สั่ง"""
        context = super().get_context_data(**kwargs)
        payment = self.get_object()
        
        # ดึงรายการสินค้าจากตะกร้า (session)
        cart_items = self.request.session.get('cart', [])
        
        # ใช้ payment_id ที่เก็บไว้ในตะกร้าเพื่อหา orders ที่เกี่ยวข้อง
        payment_order_key = f'payment_{payment.id}_orders'
        order_ids = self.request.session.get(payment_order_key, [])
        
        # ถ้ายังไม่มี orders สำหรับการชำระเงินนี้ ให้สร้าง
        if cart_items and not order_ids:
            try:
                from aicashier.models import OrderItem
                
                # กำหนด order_type: counter หรือ online
                order_type = 'counter' if self.request.user.is_staff else 'online'
                
                # คำนวณ total amount
                total_amount = sum(item['price'] * item['quantity'] for item in cart_items)
                
                # สร้างออเดอร์หลัก 1 ออเดอร์สำหรับชุดสินค้า
                order = Order.objects.create(
                    customer=self.request.user,
                    total_price=total_amount,
                    status='pending',
                    order_type=order_type,
                    order_number=Order.get_next_order_number()
                )
                
                # สร้าง OrderItem สำหรับแต่ละสินค้า
                for item in cart_items:
                    product = Product.objects.get(id=item['product_id'])
                    OrderItem.objects.create(
                        order=order,
                        product=product,
                        quantity=item['quantity'],
                        price=item['price'],
                        subtotal=item['price'] * item['quantity']
                    )
                    
                    # ลดสต็อกสินค้า
                    product.quantity -= item['quantity']
                    if product.quantity < 0:
                        product.quantity = 0
                    product.save()
                    logger.info(f"Updated {product.name} stock: -{item['quantity']} → {product.quantity} remaining")
                
                order_ids = [order.id]
                
                # เก็บ order IDs ในตะกร้า
                self.request.session[payment_order_key] = order_ids
                
                # ล้างตะกร้า
                self.request.session['cart'] = []
                self.request.session.modified = True
            except Exception as e:
                logger.error(f"Error creating orders: {e}")
        
        # ดึง Orders ที่เกี่ยวข้องกับการชำระเงินนี้
        if order_ids:
            orders = Order.objects.filter(id__in=order_ids).order_by('-created_at')
            
            # ทั้ง counter และ online orders ต้องขึ้นคิว pending
            # ให้ staff2 (order_manager) ยืนยันเมื่อเสร็จ
            if payment.payment_status == 'confirmed':
                for order in orders:
                    order_type = getattr(order, 'order_type', 'online')
                    logger.info(f"Order {order.id} ({order_type}) created - waiting for staff2 to confirm")
                    
                    # ส่งอีเมลใบเสร็จสำหรับออเดอร์ออนไลน์
                    if order_type == 'online':
                        try:
                            self.send_receipt_email(order, payment)
                        except Exception as e:
                            logger.error(f"Failed to send receipt email: {e}")
        else:
            orders = []
        
        context['orders'] = orders
        context['total_items'] = sum(item.quantity for order in orders for item in order.items.all())
        context['cart_items'] = None  # ไม่ใช้ session cart_items อีกต่อไป เนื่องเก็บในฐานข้อมูลแล้ว
        
        return context
    
    def send_receipt_email(self, order, payment):
        """ส่งอีเมลใบเสร็จไปให้ลูกค้าสำหรับออเดอร์ออนไลน์"""
        from django.core.mail import send_mail
        from django.template.loader import render_to_string
        
        customer = order.customer
        if not customer.email:
            logger.warning(f"Customer {customer.username} has no email address")
            return
        
        # สร้างเนื้อหาอีเมล
        order_items = order.items.all()
        items_html = ""
        for item in order_items:
            items_html += f"""
            <tr>
                <td style="padding: 10px; border-bottom: 1px solid #ddd;">{item.product.name}</td>
                <td style="padding: 10px; border-bottom: 1px solid #ddd; text-align: center;">{item.quantity}</td>
                <td style="padding: 10px; border-bottom: 1px solid #ddd; text-align: right;">฿{item.price}</td>
                <td style="padding: 10px; border-bottom: 1px solid #ddd; text-align: right;">฿{item.subtotal}</td>
            </tr>
            """
        
        html_content = f"""
        <html>
        <head>
            <meta charset="utf-8">
            <style>
                body {{ font-family: Arial, sans-serif; direction: rtl; text-align: right; }}
                .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                .header {{ background-color: #23243a; color: #b16cff; padding: 20px; text-align: center; border-radius: 5px; }}
                .content {{ background-color: #f5f5f5; padding: 20px; margin: 20px 0; border-radius: 5px; }}
                table {{ width: 100%; border-collapse: collapse; margin: 20px 0; }}
                .total {{ font-weight: bold; font-size: 18px; text-align: right; margin-top: 20px; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>ขอบคุณที่ทำการสั่งซื้อ!</h1>
                </div>
                
                <div class="content">
                    <h2>ใบเสร็จสำหรับออเดอร์ #{order.order_number or order.id}</h2>
                    <p>สวัสดีค่ะ {customer.username}</p>
                    <p>เราได้รับออเดอร์ของคุณแล้ว ทีมของเรากำลังเตรียมสินค้าให้คุณ</p>
                    
                    <h3>รายละเอียดสินค้า</h3>
                    <table border="1" cellpadding="10">
                        <thead style="background-color: #23243a; color: white;">
                            <tr>
                                <th>สินค้า</th>
                                <th>จำนวน</th>
                                <th>ราคา/ชิ้น</th>
                                <th>รวม</th>
                            </tr>
                        </thead>
                        <tbody>
                            {items_html}
                        </tbody>
                    </table>
                    
                    <div class="total">
                        ยอดรวมทั้งสิ้น: ฿{payment.amount}
                    </div>
                    
                    <h3>หมายเลขอ้างอิง</h3>
                    <p style="font-family: monospace; background-color: white; padding: 10px; border-radius: 5px;">
                        {payment.reference_number}
                    </p>
                    
                    <h3>ขั้นตอนต่อไป</h3>
                    <ol>
                
                        <li>เมื่อสินค้าพร้อม จะมีหมายเลขคิวแสดงในจอ</li>
                        <li>โปรดเก็บใบเสร็จนี้ไว้เพื่อใช้อ้างอิง</li>
                    </ol>
                    
                    <p style="margin-top: 20px; border-top: 1px solid #ddd; padding-top: 20px;">
                        หากมีคำถาม กรุณาติดต่อ: <strong>supachai.ta.66@ubu.ac.th</strong>
                    </p>
                </div>
            </div>
        </body>
        </html>
        """
        
        subject = f'ใบเสร็จ: ออเดอร์ #{order.order_number or order.id} | AI CASHIER'
        
        try:
            send_mail(
                subject=subject,
                message=f'ใบเสร็จสำหรับออเดอร์ #{order.order_number or order.id}',
                from_email='noreply@aicashier.local',
                recipient_list=[customer.email],
                html_message=html_content,
                fail_silently=False
            )
            logger.info(f"Receipt email sent to {customer.email} for Order {order.id}")
        except Exception as e:
            logger.error(f"Failed to send receipt email to {customer.email}: {e}")



class CheckPaymentStatusView(LoginRequiredMixin, View):
    """API endpoint สำหรับตรวจสอบสถานะการชำระเงิน (polling)"""
    login_url = 'login'
    
    def get(self, request, payment_id):
        """ตรวจสอบสถานะการชำระเงิน"""
        try:
            payment = Payment.objects.get(id=payment_id)
            
            # ตรวจสอบว่า QR หมดอายุหรือไม่
            if payment.is_expired and payment.payment_status == 'pending':
                payment.payment_status = 'expired'
                payment.save()
            
            return JsonResponse({
                'success': True,
                'status': payment.payment_status,
                'amount': str(payment.amount),
                'reference': payment.reference_number,
                'confirmed_at': payment.confirmed_at.isoformat() if payment.confirmed_at else None,
            })
        except Payment.DoesNotExist:
            return JsonResponse({'success': False, 'error': 'Payment not found'}, status=404)


@method_decorator(csrf_exempt, name='dispatch')
@csrf_exempt
def set_payment_amount_view(request):
    """API endpoint สำหรับตั้งจำนวนเงินก่อนไปหน้า payment - ไม่ต้อง login"""
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            amount = float(data.get('amount', 0))
            
            if amount <= 0:
                return JsonResponse({'success': False, 'error': 'Invalid amount'})
            
            request.session['payment_amount'] = amount
            request.session.modified = True
            
            print(f"[PAYMENT] Session updated: payment_amount={amount}")
            return JsonResponse({'success': True, 'amount': amount})
        except (json.JSONDecodeError, ValueError) as e:
            print(f"[PAYMENT] Error parsing request: {e}")
            return JsonResponse({'success': False, 'error': 'Invalid request'}, status=400)
    return JsonResponse({'success': False, 'error': 'Method not allowed'}, status=405)


class SetPaymentAmountView(LoginRequiredMixin, View):
    """API endpoint สำหรับตั้งจำนวนเงินก่อนไปหน้า payment"""
    login_url = 'login'
    
    @method_decorator(csrf_exempt)
    def dispatch(self, *args, **kwargs):
        return super().dispatch(*args, **kwargs)
    
    def post(self, request):
        try:
            data = json.loads(request.body)
            amount = float(data.get('amount', 0))
            
            if amount <= 0:
                return JsonResponse({'success': False, 'error': 'Invalid amount'})
            
            request.session['payment_amount'] = amount
            request.session.modified = True
            
            return JsonResponse({'success': True, 'amount': amount})
        except (json.JSONDecodeError, ValueError):
            return JsonResponse({'success': False, 'error': 'Invalid request'}, status=400)


# ===== Chat API Endpoint =====
@csrf_exempt
@require_http_methods(["POST"])
def chat_with_ai(request):
   
    try:

        if not rag_service:
            return JsonResponse({
                'success': False,
                'error': 'RAG service is not available'
            }, status=503)
        
        data = json.loads(request.body)
        user_message = data.get('message', '').strip()
        conversation_history = data.get('conversation_history', [])
        
        if not user_message:
            return JsonResponse({
                'success': False,
                'error': 'Message cannot be empty'
            }, status=400)
        
        # Debug: log conversation history
        print(f"[CHAT]  Received message: {user_message[:50]}...")
        print(f"[CHAT]  Conversation history: {len(conversation_history)} messages")
        if conversation_history:
            for i, item in enumerate(conversation_history[-50:]):  # Show last 3 messages
                print(f"  [{i}] {item.get('role')}: {item.get('content', '')[:50]}...")
        
        # ใช้ RAG query เพื่อตอบคำถามจากข้อมูลสินค้าจริง พร้อมประวัติการสนทนา
        response_text = rag_service.rag_query(user_message, conversation_history)
        
        return JsonResponse({
            'success': True,
            'message': response_text
        })
    
    except json.JSONDecodeError:
        return JsonResponse({
            'success': False,
            'error': 'Invalid JSON format'
        }, status=400)
    except Exception as e:
        import logging
        logging.error(f"Chat API error: {str(e)}")
        return JsonResponse({
            'success': False,
            'error': f'Error: {str(e)}'
        }, status=500)

@csrf_exempt
@require_http_methods(["POST"])
def get_product_recommendation(request):
   
    try:
        
        if not rag_service:
            return JsonResponse({
                'success': False,
                'error': 'RAG service is not available'
            }, status=503)
        
        data = json.loads(request.body)
        customer_needs = data.get('needs', '').strip()
        
        if not customer_needs:
            return JsonResponse({
                'success': False,
                'error': 'Needs cannot be empty'
            }, status=400)
        
        # ใช้ RAG query เพื่อค้นหาและแนะนำสินค้า
        # จะค้นหาเฉพาะสินค้าที่มีอยู่จริงในระบบ
        recommendation = rag_service.rag_query(
            f"โปรดแนะนำสินค้าสำหรับ: {customer_needs}",
            conversation_history=[]
        )
        
        return JsonResponse({
            'success': True,
            'recommendation': recommendation
        })
    
    except json.JSONDecodeError:
        return JsonResponse({
            'success': False,
            'error': 'Invalid JSON format'
        }, status=400)
    except Exception as e:
        import logging
        logging.error(f"Recommendation API error: {str(e)}")
        return JsonResponse({
            'success': False,
            'error': f'Error: {str(e)}'
        }, status=500)



@csrf_exempt
@require_http_methods(["POST"])
def voice_order_api(request):
    ai_response = "ขอโทษค่ะ ฉันไม่สามารถประมวลผลคำสั่งของคุณได้ในขณะนี้"
   
    try:
        if not rag_service:
            return JsonResponse({
                'success': False,
                'error': 'AI service is not available'
            }, status=503)
        
        data = json.loads(request.body)
        user_message = data.get('user_message', '').strip()
        conversation_history = data.get('conversation_history', [])
        
        if not user_message:
            return JsonResponse({
                'success': False,
                'error': 'Message cannot be empty'
            }, status=400)
        
        print(f"[VOICE]  Received: {user_message[:50]}...")
        print(f"[VOICE]  Conversation history: {len(conversation_history)} messages")
        
        # ตรวจสอบว่ากำลังสั่งซื้อหรือแค่ถามคำถาม (ดึงจาก AISettings database)
        # รวมคำสั่งจาก voice_commands_add, voice_commands_decrease, voice_commands_delete
        try:
            ai_settings = AISettings.get_settings()
            order_keywords = []
            
            # รวมทุกประเภทคำสั่ง
            if ai_settings.voice_commands_add:
                order_keywords.extend(ai_settings.voice_commands_add.split('|'))
            if ai_settings.voice_commands_decrease:
                order_keywords.extend(ai_settings.voice_commands_decrease.split('|'))
            if ai_settings.voice_commands_delete:
                order_keywords.extend(ai_settings.voice_commands_delete.split('|'))
            
            # Normalize: lowercase, strip whitespace
            order_keywords = [kw.strip().lower() for kw in order_keywords if kw.strip()]
            print(f"[VOICE] Order keywords from DB: {order_keywords}")
        except Exception as e:
            print(f"[VOICE] Error loading keywords from DB: {e}, using defaults")
            # Fallback หากดึงจาก DB ล้มเหลว
            order_keywords = ["เพิ่ม", "สั่ง", "ซื้อ", "ให้", "ลง", "ใส่", "ลด", "ลบ", "เอาออก", "ถอด", "ลดลง", "ดาว"]
        
        # ตรวจสอบว่ามีคำสั่งใน message (compare lowercase)
        is_order = any(keyword in user_message.lower() for keyword in order_keywords)
        
        cart_response = None
        
        # ถ้าดูเหมือนเป็นการจัดการตะกร้า ลองใช้ voice_manage_cart
        if is_order:
            try:
                
                if rag_service:
                    cart_response = rag_service.voice_manage_cart(user_message, request)
                    print(f"Cart response: {cart_response}")
            except Exception as cart_error:
                print(f"Cart Error: {cart_error}")
                import traceback
                traceback.print_exc()
        
        # ลองใช้ RAG system ก่อน
        try:
            
            if rag_service:
                # ตรวจสอบว่ามีข้อมูลในฐานข้อมูล RAG หรือไม่
                stats = rag_service.get_collection_stats()
                if stats and stats['document_count'] > 0:
                    # มีข้อมูล ใช้ RAG พร้อมส่ง conversation history
                    ai_response = rag_service.rag_query(user_message, conversation_history=conversation_history)
                else:
                    # ไม่มีข้อมูล ใช้ normal response
                    ai_response = "ขอโทษค่ะ ฉันไม่พบข้อมูลที่เกี่ยวข้องในระบบ แต่ฉันจะพยายามช่วยคุณเท่าที่ทำได้"
                    print("[RAG] No documents in RAG collection")
            else:
                ai_response = "ขอโทษค่ะ ฉันไม่สามารถเชื่อมต่อกับระบบ RAG ได้ในขณะนี้ แต่ฉันจะพยายามช่วยคุณเท่าที่ทำได้"
                print("[RAG] RAG service not available")
        except Exception as rag_error:
            print(f"RAG Error (fallback to normal): {rag_error}")
            ai_response = "ขอโทษค่ะ ฉันมีปัญหาในการประมวลผลข้อมูลในขณะนี้ แต่ฉันจะพยายามช่วยคุณเท่าที่ทำได้"
        
        # ถ้าสั่งซื้อสำเร็จ ให้ใช้ response จากการเพิ่มตะกร้า
        if cart_response and cart_response.get('success'):
            ai_response = cart_response.get('message', ai_response)
        
        # บันทึกการแชทไปยัง ChatLog
        # try:
        #     from .models import ChatLog
        #     ChatLog.objects.create(
        #         customer=request.user if request.user.is_authenticated else None,
        #         user_query=user_message,
        #         ai_response=ai_response
        #     )
        # except Exception as log_error:
        #     print(f"Warning: Could not save chat log: {log_error}")
        
        # ส่ง actual session cart กลับไป
        session_cart = request.session.get('cart', [])
        
        return JsonResponse({
            'success': True,
            'message': ai_response,
            'cart': session_cart,  # ส่ง actual session cart
            'cart_response': cart_response,  # เก็บ cart_response แยกไว้
            'timestamp': timezone.now().isoformat()
        })
    
    except json.JSONDecodeError:
        return JsonResponse({
            'success': False,
            'error': 'Invalid JSON format'
        }, status=400)
    except Exception as e:
        import logging
        logging.error(f"Voice Order API error: {str(e)}")
        return JsonResponse({
            'success': False,
            'error': f'Error: {str(e)}'
        }, status=500)


@csrf_exempt
@require_http_methods(["POST"])
def cart_api(request):

    try:
        print(f"[CART API] Received request: {request.method}")
        print(f"[CART API] Content-Type: {request.content_type}")
        
        data = json.loads(request.body)
        action = data.get('action', 'get')
        print(f"[CART API] Action: {action}")
        
        # ตั้งค่า session cart
        if 'cart' not in request.session:
            request.session['cart'] = []
            print("[CART API] Initialized new cart in session")
        
        cart = request.session['cart']
        print(f"[CART API] Current cart size: {len(cart)}")
        
        if action == 'add':
            product_id = data.get('product_id')
            quantity = data.get('quantity', 1)
            
            print(f"[CART API] ADD action: product_id={product_id}, quantity={quantity}")
            
            if not product_id:
                print("[CART API]  Missing product_id")
                return JsonResponse({'success': False, 'error': 'product_id required'}, status=400)
            
            try:
                from .models import Product
                product = Product.objects.get(id=product_id)
                print(f"[CART API] Found product: {product.name}, stock={product.quantity}")
                
                #  ตรวจสอบ stock
                if product.quantity <= 0:
                    return JsonResponse({
                        'success': False, 
                        'error': f'ขออภัยครับ สินค้า {product.name} ขายหมดแล้ว'
                    }, status=400)
                
                # ตรวจสอบว่าจำนวนสั่งไม่เกิน stock
                if quantity > product.quantity:
                    return JsonResponse({
                        'success': False, 
                        'error': f'ขออภัยครับ เหลือแค่ {product.quantity} ชิ้นเท่านั้น'
                    }, status=400)
                
                # ตรวจสอบว่ามีในตะกร้าแล้วหรือไม่
                item_exists = False
                for item in cart:
                    if item['product_id'] == product_id:
                        # ตรวจสอบว่าจำนวนใหม่ (เดิม + เพิ่ม) ไม่เกิน stock
                        new_quantity = item['quantity'] + quantity
                        if new_quantity > product.quantity:
                            return JsonResponse({
                                'success': False, 
                                'error': f'ขออภัยครับ เหลือแค่ {product.quantity} ชิ้น แต่คุณเลือก {new_quantity} ชิ้น'
                            }, status=400)
                        item['quantity'] = new_quantity
                        item_exists = True
                        break
                
                # ถ้าไม่มี ให้เพิ่มใหม่
                if not item_exists:
                    cart.append({
                        'product_id': product_id,
                        'product_name': product.name,
                        'price': float(product.price),
                        'quantity': quantity,
                        'category': product.category.name if product.category else 'ไม่มีหมวด'
                    })
                
                request.session.modified = True
                print(f"Added product {product_id} to cart. Cart now: {cart}")
                
                return JsonResponse({
                    'success': True,
                    'message': f'เพิ่ม {product.name} เข้าตะกร้าแล้ว',
                    'cart': cart
                })
            
            except Product.DoesNotExist:
                return JsonResponse({'success': False, 'error': 'Product not found'}, status=404)
        
        elif action == 'remove':
            product_id = data.get('product_id')
            
            if not product_id:
                return JsonResponse({'success': False, 'error': 'product_id required'}, status=400)
            
            # ลบจากตะกร้า
            request.session['cart'] = [item for item in cart if item['product_id'] != product_id]
            request.session.modified = True
            print(f"Removed product {product_id} from cart. Cart now: {request.session['cart']}")
            
            return JsonResponse({
                'success': True,
                'message': 'ลบสินค้าออกจากตะกร้าแล้ว',
                'cart': request.session['cart']
            })
        
        elif action == 'get':
            # ดึงรายการตะกร้า
            total = sum(item['price'] * item['quantity'] for item in cart)
            print(f"Getting cart. Items: {len(cart)}, Total: {total}")
            
            return JsonResponse({
                'success': True,
                'cart': cart,
                'total': total,
                'count': len(cart)
            })
        
        elif action == 'update':
            # อัพเดทจำนวนสินค้า
            product_id = data.get('product_id')
            quantity = data.get('quantity', 1)
            
            if not product_id:
                return JsonResponse({'success': False, 'error': 'product_id required'}, status=400)
            
            try:
                from .models import Product
                product = Product.objects.get(id=product_id)
                
                #  ตรวจสอบ stock
                if quantity <= 0:
                    return JsonResponse({
                        'success': False, 
                        'error': 'จำนวนต้องมากกว่า 0'
                    }, status=400)
                
                if quantity > product.quantity:
                    return JsonResponse({
                        'success': False, 
                        'error': f'ขออภัยครับ เหลือแค่ {product.quantity} ชิ้นเท่านั้น'
                    }, status=400)
                
                # ค้นหาและอัพเดทสินค้าในตะกร้า
                found = False
                for item in cart:
                    if item['product_id'] == product_id:
                        item['quantity'] = quantity
                        found = True
                        break
                
                if not found:
                    return JsonResponse({
                        'success': False, 
                        'error': 'Product not found in cart'
                    }, status=404)
                
                request.session.modified = True
                print(f"Updated product {product_id} quantity to {quantity}. Cart now: {cart}")
                
                # คำนวณราคารวม
                total = sum(item['price'] * item['quantity'] for item in cart)
                
                return JsonResponse({
                    'success': True,
                    'message': f'อัพเดทจำนวน {product.name} เป็น {quantity} ชิ้นแล้ว',
                    'cart': cart,
                    'total': total
                })
            
            except Product.DoesNotExist:
                return JsonResponse({'success': False, 'error': 'Product not found'}, status=404)
        
        elif action == 'clear':
            # ล้างตะกร้า
            request.session['cart'] = []
            request.session.modified = True
            print("Cart cleared")
            
            return JsonResponse({
                'success': True,
                'message': 'ล้างตะกร้าแล้ว'
            })
        
        else:
            return JsonResponse({'success': False, 'error': 'Invalid action'}, status=400)
    
    
    except json.JSONDecodeError:
        return JsonResponse({'success': False, 'error': 'Invalid JSON'}, status=400)
    except Exception as e:
        import logging
        logging.error(f"Cart API error: {str(e)}")
        return JsonResponse({'success': False, 'error': str(e)}, status=500)



class StripePaymentStatusView(LoginRequiredMixin, View):
    """
    API View สำหรับตรวจสอบสถานะ Stripe Payment Intent
    """
    login_url = 'login'

    def get(self, request, payment_id):
        try:
            payment = Payment.objects.get(id=payment_id)
            
            # ถ้ายังไม่มี Payment Link ID ให้ส่ง Error
            if not payment.stripe_payment_link_id:
                return JsonResponse({
                    'success': False,
                    'error': 'No payment intent found'
                }, status=400)
            
            # ถ้าจ่ายแล้วใน DB ให้ตอบกลับเลย
            if payment.payment_status == 'confirmed':
                return JsonResponse({
                    'success': True,
                    'status': 'succeeded',
                    'paid': True
                })
            
            # Payment Link ไม่ต้องตรวจสอบ status - Stripe redirect จะจัดการ
            if payment.stripe_payment_link_id:
                return JsonResponse({
                    'success': True,
                    'status': 'pending',
                    'paid': False
                })
            
            return JsonResponse({
                'success': False,
                'error': 'Stripe service not available'
            }, status=503)
            
        except Payment.DoesNotExist:
            return JsonResponse({
                'success': False,
                'error': 'Payment not found'
            }, status=404)
        except Exception as e:
            logger.error(f"Error checking payment status: {str(e)}")
            return JsonResponse({
                'success': False,
                'error': str(e)
            }, status=500)




@csrf_exempt
@require_http_methods(["POST"])
def set_payment_amount_view(request):
    """API สำหรับบันทึกยอดเงินลง Session"""
    try:
        data = json.loads(request.body) if request.body else {}
        amount = data.get('amount') or request.POST.get('amount')

        if amount:
            request.session['payment_amount'] = float(amount)
            request.session.save()
            return JsonResponse({'success': True, 'amount': float(amount)})
        
        return JsonResponse({'success': False, 'error': 'No amount provided'}, status=400)
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)


@csrf_exempt
@require_http_methods(["POST"])
def stripe_webhook(request):
    """
    Webhook สำหรับรับแจ้งเตือนจาก Stripe
    จัดการ checkout.session.completed event
    """
    import stripe   
    try:
        payload = request.body
        sig_header = request.META.get('HTTP_STRIPE_SIGNATURE')
        endpoint_secret = os.getenv('STRIPE_WEBHOOK_SECRET', '')
        
        if not endpoint_secret:
            logger.warning("Stripe webhook secret not configured")
            return JsonResponse({'success': False, 'error': 'Webhook secret not configured'}, status=400)
        
        # ตรวจสอบลายเซ็นของ Webhook
        try:
            event = stripe.Webhook.construct_event(payload, sig_header, endpoint_secret)
        except ValueError as e:
            logger.error(f"Invalid payload: {e}")
            return JsonResponse({'success': False, 'error': 'Invalid payload'}, status=400)
        except stripe.error.SignatureVerificationError as e:
            logger.error(f"Invalid signature: {e}")
            return JsonResponse({'success': False, 'error': 'Invalid signature'}, status=400)
        
        # จัดการ checkout.session.completed
        if event['type'] == 'checkout.session.completed':
            session = event['data']['object']
            checkout_session_id = session['id']
            metadata = session.get('metadata', {})
            
            logger.info(f"✓ Checkout session completed: {checkout_session_id}")
            
            # ค้นหา Payment record โดยใช้ checkout_session_id
            try:
                payment = Payment.objects.get(stripe_checkout_session_id=checkout_session_id)
                payment.payment_status = 'confirmed'
                payment.confirmed_at = timezone.now()
                payment.save()
                logger.info(f"✓ Payment {payment.id} marked as confirmed via webhook")
            except Payment.DoesNotExist:
                logger.warning(f"Payment with checkout_session_id {checkout_session_id} not found")
        
        return JsonResponse({'success': True, 'message': 'Webhook processed'})
        
    except json.JSONDecodeError:
        logger.error("Invalid JSON in webhook")
        return JsonResponse({'success': False, 'error': 'Invalid JSON'}, status=400)
    except Exception as e:
        logger.error(f"Webhook error: {str(e)}")
        return JsonResponse({'success': False, 'error': str(e)}, status=500)


# Order Management Views for Store Owner
class OrderManagementView(LoginRequiredMixin, ListView):
    """หน้าจัดการออเดอร์สำหรับพนักงานจัดการออเดอร์ - จัดกลุ่มตาม customer"""
    model = Order
    template_name = 'aicashier/order_management.html'
    context_object_name = 'customer_orders'
    paginate_by = 8
    login_url = 'login'
    
    def dispatch(self, request, *args, **kwargs):
        # ตรวจสอบสิทธิ์: ต้องเป็น staff ที่มี role = 'order_manager'
        if not request.user.is_authenticated:
            return redirect('login')
        if not request.user.is_staff or request.user.staff_role != 'order_manager':
            return redirect('home')
        return super().dispatch(request, *args, **kwargs)
    
    def get_queryset(self):
        # ดึงออเดอร์ที่ pending
        return Order.objects.filter(status='pending').order_by('-created_at')
    
    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        
        # ดึง pending orders ทั้งหมด
        pending_orders = self.get_queryset()
        
        # แยก counter orders กับ online orders
        counter_orders = []
        online_orders = []
        
        for order in pending_orders:
            order_type = getattr(order, 'order_type', 'online')
            
            # สร้าง order group object สำหรับแต่ละออเดอร์
            order_group = {
                'customer': order.customer,
                'orders': [order],  # เก็บ Order object เพื่อการ complete
                'order_number': getattr(order, 'order_number', None) or order.id,
                'order_type': order_type,
                'total_price': order.total_price,
                'total_items': sum(item.quantity for item in order.items.all()),
                'created_at': order.created_at,
                'items_detail': [{
                    'product_name': item.product.name,
                    'quantity': item.quantity,
                    'price': item.price,
                    'subtotal': item.subtotal
                } for item in order.items.all()]
            }
            
            if order_type == 'counter':
                counter_orders.append(order_group)
            else:
                online_orders.append(order_group)
        
        # เรียงตามเวลาสร้าง (ใหม่สุดขึ้นก่อน)
        counter_orders = sorted(counter_orders, key=lambda x: x['created_at'], reverse=True)
        online_orders = sorted(online_orders, key=lambda x: x['created_at'], reverse=True)
        
        # ไม่ต้อง group by customer เพราะเก็บแต่ละออเดอร์แยก
        ctx['counter_orders'] = counter_orders
        ctx['online_orders'] = online_orders
        ctx['customer_orders'] = counter_orders + online_orders  # รวมสำหรับ pagination
        ctx['orders'] = pending_orders  # สำหรับ pagination
        ctx['is_staff'] = self.request.user.is_staff
        return ctx
@csrf_exempt
@require_http_methods(["POST"])
def complete_order(request):
    """API สำหรับทำเสร็จออเดอร์ - เฉพาะ order_manager role"""
    if not request.user.is_authenticated or not request.user.is_staff or request.user.staff_role != 'order_manager':
        return JsonResponse({'success': False, 'error': 'Unauthorized - Only order_manager staff can complete orders'}, status=403)
    
    try:
        data = json.loads(request.body)
        order_id = data.get('order_id')
        
        order = get_object_or_404(Order, id=order_id)
        order.status = 'completed'
        order.save()
        
        logger.info(f" Order {order.id} (#{order.order_number or order.id}) marked as completed by {request.user.username} (order_manager)")
        
        return JsonResponse({
            'success': True,
            'message': f'Order #{order.order_number or order.id} completed',
            'order_id': order.id,
            'order_number': order.order_number or order.id,
            'order_type': getattr(order, 'order_type', 'online')
        })
    except Exception as e:
        logger.error(f"Error completing order: {e}")
        return JsonResponse({'success': False, 'error': str(e)}, status=400)


def order_queue_display(request):
    """หน้าแสดงคิวออเดอร์สำหรับลูกค้าที่อยู่หน้าร้าน - แสดง counter และ online orders""" 
    today = timezone.now().date()
    
    # ดึงออเดอร์ที่ completed ของวันนี้ (ทั้ง counter และ online) เรียงจากใหม่สุด
    completed_orders = Order.objects.filter(
        status='completed',
        order_type__in=['counter', 'online'],
        created_at__date=today
    ).order_by('-created_at')
    
    # ดึง pending orders สำหรับแสดง "กำลังเตรียม"
    pending_orders = Order.objects.filter(
        status='pending',
        order_type__in=['counter', 'online'],
        created_at__date=today
    ).order_by('created_at')
    
    logger.info(f"Queue display: completed={completed_orders.count()}, pending={pending_orders.count()}")
    
    context = {
        'completed_orders': completed_orders,
        'pending_orders': pending_orders,
    }
    
    return render(request, 'aicashier/queue_display.html', context)



@require_http_methods(["GET"])
def get_pending_orders(request):
    """API สำหรับดึงออเดอร์ pending ที่ยังไม่สำเร็จ"""
    if not request.user.is_authenticated or not request.user.is_staff or request.user.staff_role != 'order_manager':
        return JsonResponse({'success': False, 'error': 'Unauthorized'}, status=403)
    
    orders = Order.objects.filter(status='pending').order_by('-created_at')[:8]
    
    orders_data = []
    for order in orders:
        orders_data.append({
            'id': order.id,
            'product_name': order.product.name,
            'customer_name': order.customer.username,
            'quantity': order.quantity,
            'total_price': str(order.total_price),
            'order_number': getattr(order, 'order_number', None) or order.id,
            'order_type': getattr(order, 'order_type', 'online'),
            'created_at': order.created_at.strftime('%H:%M:%S'),
            'created_date': order.created_at.strftime('%d/%m/%Y')
        })
    
    return JsonResponse({
        'success': True,
        'total': len(orders_data),
        'orders': orders_data
    })


@require_http_methods(["GET"])
def order_stream(request):
    """Server-Sent Events สำหรับ real-time order updates"""
    if not request.user.is_authenticated or not request.user.is_staff or request.user.staff_role != 'order_manager':
        return JsonResponse({'success': False, 'error': 'Unauthorized'}, status=403)
    
    def event_stream():
        last_check = timezone.now()
        while True:
            import time
            time.sleep(1)  # ตรวจสอบทุก 1 วินาที
            
            # ดึงออเดอร์ใหม่ที่เพิ่งสร้าง
            new_orders = Order.objects.filter(
                status='pending',
                created_at__gte=last_check
            ).order_by('-created_at')
            
            if new_orders.exists():
                for order in new_orders:
                    # ดึงสินค้าจาก OrderItem (ไม่ใช่จาก order.product ที่ลบออกแล้ว)
                    items = order.items.all()
                    product_names = ', '.join([f"{item.product.name} x{item.quantity}" for item in items]) if items else "ไม่มีสินค้า"
                    total_quantity = sum(item.quantity for item in items)
                    
                    data = {
                        'id': order.id,
                        'product_name': product_names,
                        'customer_name': order.customer.username,
                        'quantity': total_quantity,
                        'total_price': str(order.total_price),
                        'order_number': getattr(order, 'order_number', None) or order.id,
                        'order_type': getattr(order, 'order_type', 'online'),
                        'created_at': order.created_at.strftime('%H:%M:%S'),
                        'type': 'new_order'
                    }
                    yield f"data: {json.dumps(data)}\n\n"
            
            last_check = timezone.now()
    
    response = StreamingHttpResponse(event_stream(), content_type='text/event-stream')
    response['Cache-Control'] = 'no-cache'
    response['X-Accel-Buffering'] = 'no'
    return response


@method_decorator(user_passes_test(admin_required, login_url='login'), name='dispatch')
@require_http_methods(["POST"])
def call_staff_api(request):
    """เรียกพนักงาน - สำหรับลูกค้าหน้าร้าน"""
    try:
        data = json.loads(request.body)
        reason = data.get('reason', 'ทำให้ฉันได้รับความช่วยเหลือ')
        
        result = StaffCallService.call_staff(request.user, reason)
        return JsonResponse(result)
    except json.JSONDecodeError:
        return JsonResponse({'success': False, 'message': 'Invalid JSON'}, status=400)
    except Exception as e:
        logger.error(f"Error in call_staff_api: {str(e)}")
        return JsonResponse({'success': False, 'message': str(e)}, status=500)


@method_decorator(user_passes_test(admin_required, login_url='login'), name='dispatch')
@require_http_methods(["GET"])
def get_staff_calls_api(request):
    """ดึงรายการการเรียกพนักงานที่รอการอ้าง - สำหรับ Order Management"""
    try:
        result = StaffCallService.get_pending_calls()
        return JsonResponse(result)
    except Exception as e:
        logger.error(f"Error in get_staff_calls_api: {str(e)}")
        return JsonResponse({'success': False, 'error': str(e)}, status=500)


@method_decorator(user_passes_test(admin_required, login_url='login'), name='dispatch')
@require_http_methods(["POST"])
def acknowledge_staff_call_api(request):
    """พนักงาน acknowledge การเรียก"""
    try:
        if not request.user.is_staff:
            return JsonResponse({'success': False, 'error': 'เฉพาะพนักงานเท่านั้น'}, status=403)
        
        data = json.loads(request.body)
        call_id = data.get('call_id')
        
        if not call_id:
            return JsonResponse({'success': False, 'error': 'Missing call_id'}, status=400)
        
        result = StaffCallService.acknowledge_call(call_id)
        return JsonResponse(result)
    except json.JSONDecodeError:
        return JsonResponse({'success': False, 'error': 'Invalid JSON'}, status=400)
    except Exception as e:
        logger.error(f"Error in acknowledge_staff_call_api: {str(e)}")
        return JsonResponse({'success': False, 'error': str(e)}, status=500)


@method_decorator(user_passes_test(admin_required, login_url='login'), name='dispatch')
@require_http_methods(["POST"])
def complete_staff_call_api(request):
    """พนักงาน complete การเรียก"""
    try:
        if not request.user.is_staff:
            return JsonResponse({'success': False, 'error': 'เฉพาะพนักงานเท่านั้น'}, status=403)
        
        data = json.loads(request.body)
        call_id = data.get('call_id')
        
        if not call_id:
            return JsonResponse({'success': False, 'error': 'Missing call_id'}, status=400)
        
        result = StaffCallService.complete_call(call_id)
        return JsonResponse(result)
    except json.JSONDecodeError:
        return JsonResponse({'success': False, 'error': 'Invalid JSON'}, status=400)
    except Exception as e:
        logger.error(f"Error in complete_staff_call_api: {str(e)}")
        return JsonResponse({'success': False, 'error': str(e)}, status=500)


# ============================================
# ORDER CANCELLATION API
# ============================================
@method_decorator(user_passes_test(admin_required, login_url='login'), name='dispatch')
@require_http_methods(["POST"])
def cancel_order_api(request):
    """ยกเลิกออเดอร์ - สำหรับลูกค้าออนไลน์"""
    try:
        data = json.loads(request.body)
        order_id = data.get('order_id')
        reason = data.get('reason', 'ลูกค้าขอยกเลิก')
        
        if not order_id:
            return JsonResponse({'success': False, 'message': 'order_id required'}, status=400)
        
        # ตรวจสอบว่าผู้ใช้เป็นเจ้าของออเดอร์หรือเป็น staff
        order = Order.objects.get(id=order_id)
        is_order_owner = order.customer == request.user
        is_staff = request.user.is_staff
        
        if not (is_order_owner or is_staff):
            return JsonResponse({
                'success': False,
                'message': 'ไม่มีสิทธิ์ยกเลิกออเดอร์นี้'
            }, status=403)
        
        result = OrderCancellationService.cancel_order(order_id, reason)
        status_code = 200 if result['success'] else 400
        return JsonResponse(result, status=status_code)
    
    except Order.DoesNotExist:
        return JsonResponse({'success': False, 'message': 'ไม่พบออเดอร์'}, status=404)
    except json.JSONDecodeError:
        return JsonResponse({'success': False, 'message': 'Invalid JSON'}, status=400)
    except Exception as e:
        logger.error(f"Error in cancel_order_api: {str(e)}")
        return JsonResponse({'success': False, 'message': str(e)}, status=500)


# ============================================
# INVENTORY CHECK API
# ============================================
@method_decorator(user_passes_test(admin_required, login_url='login'), name='dispatch')
@require_http_methods(["GET"])
def check_low_stock_api(request):
    """ตรวจสอบและส่อง email สินค้าใกล้หมด - Admin only"""
    if not request.user.is_staff:
        return JsonResponse({
            'success': False,
            'message': 'เฉพาะแอดมินเท่านั้น'
        }, status=403)
    
    try:
        result = InventoryService.check_and_notify_low_stock()
        return JsonResponse(result)
    except Exception as e:
        logger.error(f"Error in check_low_stock_api: {str(e)}")
        return JsonResponse({'success': False, 'error': str(e)}, status=500)


# ============================================
# ANALYTICS APIS
# ============================================
@method_decorator(user_passes_test(admin_required, login_url='login'), name='dispatch')
@require_http_methods(["GET"])
def get_aov_api(request):
    """ดึงข้อมูล Average Order Value - Admin only"""
    if not request.user.is_staff:
        return JsonResponse({
            'success': False,
            'message': 'เฉพาะแอดมินเท่านั้น'
        }, status=403)
    
    try:
        days = int(request.GET.get('days', 30))
        result = OrderAnalyticsService.get_average_order_value(days)
        return JsonResponse(result)
    except Exception as e:
        logger.error(f"Error in get_aov_api: {str(e)}")
        return JsonResponse({'error': str(e)}, status=500)


@method_decorator(user_passes_test(admin_required, login_url='login'), name='dispatch')
@require_http_methods(["GET"])
def get_cancellation_rate_api(request):
    """ดึงข้อมูล Cancellation Rate - Admin only"""
    if not request.user.is_staff:
        return JsonResponse({
            'success': False,
            'message': 'เฉพาะแอดมินเท่านั้น'
        }, status=403)
    
    try:
        days = int(request.GET.get('days', 30))
        result = OrderAnalyticsService.get_cancellation_rate(days)
        return JsonResponse(result)
    except Exception as e:
        logger.error(f"Error in get_cancellation_rate_api: {str(e)}")
        return JsonResponse({'error': str(e)}, status=500)
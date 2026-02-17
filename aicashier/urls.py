# aicashier/urls.py
from django.urls import path
from django.shortcuts import redirect, render
from django.contrib.auth.views import (
    LogoutView,
    PasswordResetView,
    PasswordResetDoneView,
    PasswordResetConfirmView,
    PasswordResetCompleteView,
)
from .views import (
    CustomLoginView, close_ai_view, chat_with_ai, get_product_recommendation, 
    voice_order_api, cart_api, stripe_webhook, 
    StripePaymentStatusView, set_payment_amount_view,
    CustomerListView, CustomerCreateView, CustomerUpdateView,
    CustomerDeleteView, CustomerDetailView, HomeView,
    ProductListView, ProductCreateView, ProductUpdateView, ProductDeleteView,
    OverviewsView, AISettingsView, AIStatusToggleView,
    ProfileView, ProfileUpdateView, FeaturedMenuView,
    CategoryListView, CategoryCreateView, CategoryUpdateView, CategoryDeleteView,
    DisableAIView, DisableAIActionView, ConfirmDisableAIView,
    PaymentView, PaymentSuccessView, CheckPaymentStatusView, SetPaymentAmountView,
    check_payment_status, OrderManagementView, complete_order, get_pending_orders, order_stream,
    order_queue_display,
    PromotionListView, PromotionCreateView, PromotionUpdateView, PromotionDeleteView
)
from .api_views import (
    call_staff_api, cancel_order_api, check_low_stock_api,
    get_aov_api, get_cancellation_rate_api, get_top_queries_api,
    get_staff_calls_api, acknowledge_staff_call_api, complete_staff_call_api
)

urlpatterns = [
    # หน้าแรกเด้งไปหน้า sign in (กัน 404 ที่ '/')
    path('', lambda r: redirect('home'), name='root'),
    path('home/', HomeView.as_view(), name='home'),

    # Auth
    path('sign_in/', CustomLoginView.as_view(template_name='aicashier/sing_in.html'), name='login'),
    path('staff/login/', CustomLoginView.as_view(template_name='aicashier/sing_in.html'), name='staff_login'),
    path('logout/', LogoutView.as_view(next_page='login'), name='logout'),

    # Sign up (สมัครสมาชิก) → ใช้ CustomerCreateView ที่บันทึก DB แล้วเด้งไป sign in
    path('sign_up/', CustomerCreateView.as_view(), name='sign_up'),

        # Password reset (รีเซ็ตรหัสผ่าน)
        path('password_reset/',
            PasswordResetView.as_view(template_name='aicashier/password_reset_form.html'),
            name='password_reset'),
        path('password_reset/done/',
            PasswordResetDoneView.as_view(template_name='aicashier/password_reset_done.html'),
            name='password_reset_done'),
        path('reset/<uidb64>/<token>/',
            PasswordResetConfirmView.as_view(template_name='aicashier/password_reset_confirm.html'),
            name='password_reset_confirm'),
        path('reset/done/',
            PasswordResetCompleteView.as_view(template_name='aicashier/password_reset_complete.html'),
            name='password_reset_complete'),

    # Profile
    path('profile/', ProfileView.as_view(), name='profile'),
    path('profile/edit/', ProfileUpdateView.as_view(), name='profile_edit'),

    # CRUD (ตัวอย่างบนตาราง Customer)
    path('customers/', CustomerListView.as_view(), name='customer_list'),
    path('customers/<int:pk>/', CustomerDetailView.as_view(), name='customer_detail'),
    path('customers/<int:pk>/edit/', CustomerUpdateView.as_view(), name='customer_edit'),
    path('customers/<int:pk>/delete/', CustomerDeleteView.as_view(), name='customer_delete'),

    # Product CRUD (admin only)
    path('products/manage/', ProductListView.as_view(), name='product_manage'),
    path('products/create/', ProductCreateView.as_view(), name='product_create'),
    path('products/<int:pk>/edit/', ProductUpdateView.as_view(), name='product_edit'),
    path('products/<int:pk>/delete/', ProductDeleteView.as_view(), name='product_delete'),
    path('products/featured-menu/', FeaturedMenuView.as_view(), name='featured_menu'),
    
    # Category Management (admin only)
    path('categories/manage/', CategoryListView.as_view(), name='manage_category'),
    path('categories/create/', CategoryCreateView.as_view(), name='create_category'),
    path('categories/<int:pk>/edit/', CategoryUpdateView.as_view(), name='category_edit'),
    path('categories/<int:pk>/delete/', CategoryDeleteView.as_view(), name='delete_category'),
    
    # Promotion Management (admin only)
    path('promotions/manage/', PromotionListView.as_view(), name='manage_promotion'),
    path('promotions/create/', PromotionCreateView.as_view(), name='create_promotion'),
    path('promotions/<int:pk>/edit/', PromotionUpdateView.as_view(), name='promotion_edit'),
    path('promotions/<int:pk>/delete/', PromotionDeleteView.as_view(), name='delete_promotion'),

    # Overviews
    path('overviews/', OverviewsView.as_view(), name='overviews'),
    
    # AI Settings (Admin Only)
    path('ai/settings/', AISettingsView.as_view(), name='ai_settings'),
    path('ai/toggle/', AIStatusToggleView.as_view(), name='ai_toggle'),
    path('ai/close/', close_ai_view, name='close_ai'),
    
    # AI Disable/Enable
    path('ai/disabled/', DisableAIView.as_view(), name='ai_disabled'),
    path('ai/disable-action/', DisableAIActionView.as_view(), name='ai_disable_action'),
    path('ai/confirm-disable/', ConfirmDisableAIView.as_view(), name='confirm_disable_ai'),

    
    # Payment
    path('payment/', PaymentView.as_view(), name='payment'),
    path('payment/success/<int:payment_id>/', PaymentSuccessView.as_view(), name='payment_success'),
    path('api/payment/status/<int:payment_id>/', CheckPaymentStatusView.as_view(), name='check_payment_status'),
    path('set-payment-amount/', set_payment_amount_view, name='set_payment_amount'),
    path('webhook/stripe/', stripe_webhook, name='stripe_webhook'),
    
    # Order Management (for store owner)
    path('orders/manage/', OrderManagementView.as_view(), name='order_management'),
    path('orders/queue-display/', order_queue_display, name='order_queue_display'),  # สำหรับแสดงคิวลูกค้า
    path('api/orders/pending/', get_pending_orders, name='api_pending_orders'),
    path('api/orders/complete/', complete_order, name='api_complete_order'),
    path('api/orders/stream/', order_stream, name='api_order_stream'),
    
    # Stripe Payment Pages
    #path('stripe/payment/<int:payment_id>/', StripePaymentView.as_view(), name='stripe_payment'),
    path('api/stripe/status/<int:payment_id>/', StripePaymentStatusView.as_view(), name='stripe_payment_status'),
    path(
        'payment/check-status/<int:order_id>/',
        check_payment_status,
        name='payment_check_status'),
    
    # Chat API
    path('api/chat/', chat_with_ai, name='api_chat'),
    path('api/recommendation/', get_product_recommendation, name='api_recommendation'),
    path('api/voice-order/', voice_order_api, name='api_voice_order'),
    path('api/cart/', cart_api, name='api_cart'),
    
    
    # New Feature APIs
    path('api/staff/call/', call_staff_api, name='api_call_staff'),
    path('api/staff/calls/', get_staff_calls_api, name='api_get_staff_calls'),
    path('api/staff/call/acknowledge/', acknowledge_staff_call_api, name='api_acknowledge_staff_call'),
    path('api/staff/call/complete/', complete_staff_call_api, name='api_complete_staff_call'),
    path('api/orders/cancel/', cancel_order_api, name='api_cancel_order'),
    path('api/inventory/check-low-stock/', check_low_stock_api, name='api_check_low_stock'),
    path('api/analytics/aov/', get_aov_api, name='api_get_aov'),
    path('api/analytics/cancellation-rate/', get_cancellation_rate_api, name='api_get_cancellation_rate'),
    path('api/analytics/top-queries/', get_top_queries_api, name='api_get_top_queries'),
]

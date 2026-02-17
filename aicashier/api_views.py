"""
API Views for new features (Call Staff, Cancel Order, Analytics)
"""

import logging
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.views.generic import View
from django.utils import timezone
import json

from .services import (
    StaffCallService,
    OrderCancellationService,
    InventoryService,
    OrderAnalyticsService
)
from .models import Order

logger = logging.getLogger(__name__)


# ============================================
# STAFF CALL API
# ============================================
@login_required
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


@login_required
@require_http_methods(["GET"])
def get_staff_calls_api(request):
    """ดึงรายการการเรียกพนักงานที่รอการอ้าง - สำหรับ Order Management"""
    try:
        result = StaffCallService.get_pending_calls()
        return JsonResponse(result)
    except Exception as e:
        logger.error(f"Error in get_staff_calls_api: {str(e)}")
        return JsonResponse({'success': False, 'error': str(e)}, status=500)


@login_required
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


@login_required
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
@login_required
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
@login_required
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
@login_required
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


@login_required
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


@login_required
@require_http_methods(["GET"])
def get_top_queries_api(request):
    """ดึงข้อมูล Top User Queries - Admin only"""
    if not request.user.is_staff:
        return JsonResponse({
            'success': False,
            'message': 'เฉพาะแอดมินเท่านั้น'
        }, status=403)
    
    try:
        limit = int(request.GET.get('limit', 5))
        result = OrderAnalyticsService.get_top_user_queries(limit)
        return JsonResponse(result)
    except Exception as e:
        logger.error(f"Error in get_top_queries_api: {str(e)}")
        return JsonResponse({'error': str(e)}, status=500)

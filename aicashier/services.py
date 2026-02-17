"""
Services for AI Cashier System
Handles business logic without modifying database structure
"""

import logging
import uuid
from django.core.mail import send_mail
from django.conf import settings
from django.db.models import Sum, Count, Avg, Q, F
from django.utils import timezone
from datetime import timedelta
from .models import Order, OrderItem, Product, Customer
import json

logger = logging.getLogger(__name__)


class StaffCallService:
    """จัดการการเรียกพนักงาน - ใช้ Cache สำหรับแจ้งเตือน Real-time"""
    
    @staticmethod
    def call_staff(user, reason="ไม่มีเหตุผลระบุ"):
        """บันทึกการเรียกพนักงานและส่งแจ้งเตือน"""
        try:
            from django.core.cache import cache
            import uuid
            
            # 1️⃣ สร้าง unique call ID
            call_id = str(uuid.uuid4())
            
            # 2️⃣ เก็บข้อมูลการเรียก
            staff_call_data = {
                'call_id': call_id,
                'user_id': user.id if user else None,
                'username': user.username if user else 'Unknown',
                'timestamp': timezone.now().isoformat(),
                'reason': reason,
                'status': 'pending'  # pending, acknowledged, completed
            }
            
            # 3️⃣ เพิ่มลงรายการ pending calls (เก็บ 10 นาที)
            pending_calls = cache.get('pending_staff_calls', [])
            pending_calls.append(staff_call_data)
            cache.set('pending_staff_calls', pending_calls, timeout=600)
            
            logger.info(f"Staff called by {user.username}: {reason} (ID: {call_id})")
            
            return {
                'success': True,
                'message': 'ส่งสัญญาณเรียกพนักงานแล้ว',
                'call_id': call_id,
                'timestamp': staff_call_data['timestamp']
            }
        except Exception as e:
            logger.error(f"Error in call_staff: {str(e)}")
            return {'success': False, 'message': f'เกิดข้อผิดพลาด: {str(e)}'}
    
    @staticmethod
    def get_pending_calls():
        """ดึงรายการการเรียกพนักงานที่รอการอ้าง"""
        try:
            from django.core.cache import cache
            
            pending_calls = cache.get('pending_staff_calls', [])
            return {
                'success': True,
                'calls': pending_calls,
                'count': len(pending_calls)
            }
        except Exception as e:
            logger.error(f"Error in get_pending_calls: {str(e)}")
            return {'success': False, 'calls': [], 'error': str(e)}
    
    @staticmethod
    def acknowledge_call(call_id):
        """พนักงานยอมรับการเรียก"""
        try:
            from django.core.cache import cache
            
            pending_calls = cache.get('pending_staff_calls', [])
            
            for call in pending_calls:
                if call.get('call_id') == call_id:
                    call['status'] = 'acknowledged'
                    call['acknowledged_at'] = timezone.now().isoformat()
                    break
            
            cache.set('pending_staff_calls', pending_calls, timeout=600)
            logger.info(f"Staff call {call_id} acknowledged")
            
            return {'success': True, 'message': 'ยอมรับการเรียกแล้ว'}
        except Exception as e:
            logger.error(f"Error in acknowledge_call: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    @staticmethod
    def complete_call(call_id):
        """พนักงานเสร็จสิ้นการเรียก"""
        try:
            from django.core.cache import cache
            
            pending_calls = cache.get('pending_staff_calls', [])
            
            # ลบการเรียกออกจาก pending list
            pending_calls = [c for c in pending_calls if c.get('call_id') != call_id]
            
            cache.set('pending_staff_calls', pending_calls, timeout=600)
            logger.info(f"Staff call {call_id} completed")
            
            return {'success': True, 'message': 'เสร็จสิ้นการเรียกแล้ว'}
        except Exception as e:
            logger.error(f"Error in complete_call: {str(e)}")
            return {'success': False, 'error': str(e)}


class OrderCancellationService:
    """จัดการการยกเลิกออเดอร์สำหรับลูกค้าออนไลน์"""
    
    @staticmethod
    def cancel_order(order_id, reason="ลูกค้าขอยกเลิก"):
        """ยกเลิกออเดอร์และบันทึกเหตุผล"""
        try:
            order = Order.objects.get(id=order_id)
            
            # ตรวจสอบว่าเป็นออเดอร์ออนไลน์เท่านั้น
            if order.order_type != 'online':
                return {
                    'success': False,
                    'message': 'สามารถยกเลิกได้เฉพาะออเดอร์ออนไลน์เท่านั้น'
                }
            
            # ตรวจสอบว่า order ยังไม่เสร็จสิ้น
            if order.status == 'completed':
                return {
                    'success': False,
                    'message': 'ไม่สามารถยกเลิกออเดอร์ที่เสร็จสิ้นแล้ว'
                }
            
            # อัปเดตสถานะ
            order.status = 'cancelled'
            order.save()
            
            # บันทึก log
            logger.info(f"Order #{order.order_number} cancelled. Reason: {reason}")
            
            return {
                'success': True,
                'message': 'ยกเลิกออเดอร์เรียบร้อย',
                'order_id': order_id
            }
        except Order.DoesNotExist:
            return {'success': False, 'message': 'ไม่พบออเดอร์'}
        except Exception as e:
            logger.error(f"Error in cancel_order: {str(e)}")
            return {'success': False, 'message': f'เกิดข้อผิดพลาด: {str(e)}'}


class InventoryService:
    """จัดการการตรวจสอบสินค้าคงเหลือและส่งการแจ้งเตือน"""
    
    LOW_STOCK_THRESHOLD = 10  # ขีด จำกัด สินค้าใกล้หมด
    LOW_STOCK_EMAIL_RECIPIENTS = []  # เจ้าของ emails
    
    @classmethod
    def check_and_notify_low_stock(cls):
        """ตรวจสอบสินค้าที่ใกล้หมด และส่อง email"""
        try:
            low_stock_products = Product.objects.filter(
                quantity__lte=cls.LOW_STOCK_THRESHOLD,
                quantity__gt=0
            )
            
            if low_stock_products.exists():
                cls._send_low_stock_email(low_stock_products)
                logger.info(f"Low stock notification sent for {low_stock_products.count()} products")
                return {
                    'success': True,
                    'products_count': low_stock_products.count(),
                    'products': list(low_stock_products.values('id', 'name', 'quantity'))
                }
            
            return {'success': True, 'products_count': 0, 'products': []}
        
        except Exception as e:
            logger.error(f"Error in check_and_notify_low_stock: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    @classmethod
    def _send_low_stock_email(cls, products):
        """ส่อง email แจ้งเตือนสินค้าใกล้หมด"""
        try:
            subject = "⚠️ แจ้งเตือน: สินค้าใกล้หมด"
            
            # สร้างรายชื่อสินค้า
            product_list = "\n".join([
                f"• {p.name} - เหลือ {p.quantity} ชิ้น"
                for p in products
            ])
            
            message = f"""
สวัสดีครับ,

มีสินค้าที่ตัวเข้มต่อไปนี้ใกล้หมดแล้ว (น้อยกว่า {cls.LOW_STOCK_THRESHOLD} ชิ้น):

{product_list}

โปรดเติมสต็อกโดยเร็วที่สุด

AI Cashier System
            """
            
            # ส่งไปยัง superuser/owner
            admin_emails = Customer.objects.filter(
                is_superuser=True
            ).values_list('email', flat=True)
            
            if admin_emails:
                send_mail(
                    subject,
                    message,
                    settings.DEFAULT_FROM_EMAIL,
                    list(admin_emails),
                    fail_silently=True
                )
                logger.info(f"Low stock email sent to {len(admin_emails)} recipients")
        except Exception as e:
            logger.error(f"Error sending low stock email: {str(e)}")


class OrderAnalyticsService:
    """จัดการการวิเคราะห์ข้อมูลออเดอร์"""
    
    @staticmethod
    def get_average_order_value(days=30):
        """คำนวณค่าเฉลี่ยต่อบิล (AOV)"""
        try:
            start_date = timezone.now() - timedelta(days=days)
            
            completed_orders = Order.objects.filter(
                status='completed',
                created_at__gte=start_date
            )
            
            if not completed_orders.exists():
                return {'aov': 0, 'order_count': 0, 'total_revenue': 0}
            
            total_revenue = completed_orders.aggregate(Sum('total_price'))['total_price__sum'] or 0
            order_count = completed_orders.count()
            aov = total_revenue / order_count if order_count > 0 else 0
            
            return {
                'aov': float(aov),
                'order_count': order_count,
                'total_revenue': float(total_revenue),
                'period_days': days
            }
        except Exception as e:
            logger.error(f"Error in get_average_order_value: {str(e)}")
            return {'aov': 0, 'order_count': 0, 'total_revenue': 0, 'error': str(e)}
    
    @staticmethod
    def get_cancellation_rate(days=30):
        """คำนวณอัตราการยกเลิก (Cancellation Rate)"""
        try:
            start_date = timezone.now() - timedelta(days=days)
            
            total_orders = Order.objects.filter(
                created_at__gte=start_date
            )
            
            cancelled_orders = Order.objects.filter(
                status='cancelled',
                created_at__gte=start_date
            )
            
            total_count = total_orders.count()
            cancelled_count = cancelled_orders.count()
            
            if total_count == 0:
                return {
                    'cancellation_rate': 0,
                    'cancelled_count': 0,
                    'total_count': 0,
                    'percentage': '0%'
                }
            
            percentage = (cancelled_count / total_count) * 100
            
            return {
                'cancellation_rate': round(percentage, 2),
                'cancelled_count': cancelled_count,
                'total_count': total_count,
                'percentage': f'{round(percentage, 2)}%'
            }
        except Exception as e:
            logger.error(f"Error in get_cancellation_rate: {str(e)}")
            return {
                'cancellation_rate': 0,
                'cancelled_count': 0,
                'total_count': 0,
                'percentage': '0%',
                'error': str(e)
            }
    
    @staticmethod
    def get_top_user_queries(limit=5):
        """ดึงคำค้นหาหลัก/คำถามของลูกค้า
        
        Note: ต้องดึงจาก log หรือ Vector DB
        สำหรับตอนนี้ ส่งคืนข้อมูลตัวอย่าง
        """
        try:
            from .models import ChatLog
            from django.db.models import Count
            from datetime import timedelta
            from django.utils import timezone
            
            # ดึงข้อมูลจาก 30 วันที่ผ่านมา
            thirty_days_ago = timezone.now() - timedelta(days=30)
            
            # ดึง ChatLog ทั้งหมดในช่วง 30 วัน
            chat_logs = ChatLog.objects.filter(
                created_at__gte=thirty_days_ago
            ).values('user_query').annotate(count=Count('id')).order_by('-count')[:limit]
            
            total_queries = ChatLog.objects.filter(
                created_at__gte=thirty_days_ago
            ).count()
            
            if not chat_logs and total_queries == 0:
                # ถ้าไม่มีข้อมูล ส่งข้อมูลตัวอย่าง
                sample_queries = [
                    {'query': 'ขนาดไหนคุ้มสุด', 'count': 15, 'percentage': 20},
                    {'query': 'มีรสชาติอะไรบ้าง', 'count': 12, 'percentage': 16},
                    {'query': 'ราคาเท่าไหร่', 'count': 10, 'percentage': 13},
                    {'query': 'สินค้าใหม่อะไร', 'count': 8, 'percentage': 11},
                    {'query': 'ส่วนลดเท่าไหร่', 'count': 6, 'percentage': 8},
                ]
                return {
                    'success': True,
                    'top_queries': sample_queries,
                    'total_queries': sum([q['count'] for q in sample_queries]),
                    'note': 'ข้อมูลตัวอย่าง (ยังไม่มีข้อมูลแชทจริง)'
                }
            
            # คำนวณเปอร์เซ็นต์ และสร้างรายการคำค้นหา
            result_queries = []
            for log in chat_logs:
                if log['user_query'].strip():  # ข้ามข้อความว่างเปล่า
                    percentage = round((log['count'] / total_queries) * 100) if total_queries > 0 else 0
                    result_queries.append({
                        'query': log['user_query'][:50],  # ตัดให้ 50 ตัวอักษร
                        'count': log['count'],
                        'percentage': percentage
                    })
            
            return {
                'success': True,
                'top_queries': result_queries,
                'total_queries': total_queries,
                'note': 'ข้อมูลจากประวัติแชทจริง'
            }
        except Exception as e:
            logger.error(f"Error in get_top_user_queries: {str(e)}")
            # ส่งข้อมูลตัวอย่างถ้ามีข้อผิดพลาด
            sample_queries = [
                {'query': 'ขนาดไหนคุ้มสุด', 'count': 15, 'percentage': 20},
                {'query': 'มีรสชาติอะไรบ้าง', 'count': 12, 'percentage': 16},
                {'query': 'ราคาเท่าไหร่', 'count': 10, 'percentage': 13},
                {'query': 'สินค้าใหม่อะไร', 'count': 8, 'percentage': 11},
                {'query': 'ส่วนลดเท่าไหร่', 'count': 6, 'percentage': 8},
            ]
            return {
                'success': False,
                'top_queries': sample_queries,
                'error': str(e)
            }
    
    @staticmethod
    def get_order_summary(days=30):
        """ได้รับสรุปข้อมูลออเดอร์"""
        try:
            start_date = timezone.now() - timedelta(days=days)
            
            summary = Order.objects.filter(
                created_at__gte=start_date
            ).aggregate(
                total_orders=Count('id'),
                completed_orders=Count('id', filter=Q(status='completed')),
                cancelled_orders=Count('id', filter=Q(status='cancelled')),
                pending_orders=Count('id', filter=Q(status='pending')),
                total_revenue=Sum('total_price', filter=Q(status='completed')),
                counter_orders=Count('id', filter=Q(order_type='counter')),
                online_orders=Count('id', filter=Q(order_type='online')),
            )
            
            return {
                **summary,
                'total_revenue': float(summary['total_revenue'] or 0),
                'average_order_value': float((summary['total_revenue'] or 0) / (summary['completed_orders'] or 1))
            }
        except Exception as e:
            logger.error(f"Error in get_order_summary: {str(e)}")
            return {
                'total_orders': 0,
                'completed_orders': 0,
                'cancelled_orders': 0,
                'pending_orders': 0,
                'total_revenue': 0,
                'counter_orders': 0,
                'online_orders': 0,
                'error': str(e)
            }


class ChatAnalyticsService:
    """ดึงข้อมูลจากประวัติแชท"""
    
    @staticmethod
    def extract_top_queries_from_logs(limit=5):
        """
        ดึงคำค้นหาจากประวัติแชทผู้ใช้
        ตัวอย่างวิธี: คำนวณจากความถี่ของลำดับคำแต่ละรายการ
        """
        # Note: ต้องเชื่อมต่อกับการจดบันทึกประวัติแชทหรือ vector DB
        # สำหรับตอนนี้ ส่งคืนข้อมูลตัวอย่าง
        return {
            'status': 'implemented_partially',
            'message': 'ต้องเชื่อมต่อกับระบบจดบันทึกประวัติแชทขั้นสูง'
        }

# aicashier/signals.py

import logging
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from .models import Product, Order

# Configure logging
logger = logging.getLogger(__name__)

# Import rag_service carefully with error handling
rag_service = None
try:
    from .rag_service import rag_service
except ImportError as e:
    logger.error(f"Could not import rag_service: {e}")
except Exception as e:
    logger.error(f"Error initializing rag_service: {e}")

@receiver(post_save, sender=Product)
def sync_product_to_rag(sender, instance, created, **kwargs):
    """
    Signal handler: Sync product to RAG when saved (create or update)
    Ensures database and RAG are always in sync
    """
    try:
        if not rag_service:
            logger.warning(f"RAG service not initialized when syncing Product {instance.id}")
            return
        
        action = "created" if created else "updated"
        print(f"Syncing Product ID {instance.id} ({instance.name}) - {action}...")
        
        rag_service.update_product_in_rag(instance)
        
        logger.info(f"Product {instance.id} ({instance.name}) synced to RAG - {action}")
        print(f"Product ID {instance.id} synced successfully")
        
    except Exception as e:
        logger.error(f"Error syncing Product {instance.id} to RAG: {e}", exc_info=True)
        print(f"Error syncing Product {instance.id}: {e}")
        # Don't re-raise here to prevent breaking Django ORM, but log clearly

@receiver(post_delete, sender=Product)
def remove_product_from_rag(sender, instance, **kwargs):
    """
    Signal handler: Remove product from RAG when deleted
    Ensures RAG doesn't contain deleted products
    """
    try:
        if not rag_service:
            logger.warning(f"RAG service not initialized when deleting Product {instance.id}")
            return
        
        print(f"Removing Product ID {instance.id} ({instance.name}) from RAG...")
        
        rag_service.delete_product_from_rag(instance.id)
        
        logger.info(f"Product {instance.id} ({instance.name}) removed from RAG")
        print(f"Product ID {instance.id} removed from RAG successfully")
        
    except Exception as e:
        logger.error(f"Error removing Product {instance.id} from RAG: {e}", exc_info=True)
        print(f"Error removing Product {instance.id}: {e}")
        # Don't re-raise here to prevent breaking Django ORM, but log clearly

@receiver(post_save, sender=Order)
def update_product_stock_on_order(sender, instance, created, **kwargs):
    """
    Signal handler: Update product stock when order is completed
    ลดจำนวนสินค้าในคลังเมื่อ Order สำเร็จ
    """
    try:
        # Only process when order status is completed
        if instance.status != 'completed':
            return
        
        product = instance.product
        
        # ตรวจสอบว่าสินค้าพอสต็อกไหม
        if product.quantity < instance.quantity:
            logger.error(f"Order {instance.id}: Insufficient stock for product {product.id}")
            print(f"Order {instance.id}: Insufficient stock!")
            return
        
        # ลดสต็อก
        product.quantity -= instance.quantity
        product.save()
        
        logger.info(f"Order {instance.id}: Stock updated for Product {product.id} ({product.name}). New quantity: {product.quantity}")
        print(f"Order {instance.id}: Reduced {product.name} stock by {instance.quantity}. New stock: {product.quantity}")
        
    except Exception as e:
        logger.error(f"Error updating product stock on order {instance.id}: {e}", exc_info=True)
        print(f"Error updating stock: {e}")

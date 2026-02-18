# aicashier/signals.py

import logging
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from .models import Product, Order, AISettings

# Configure logging
logger = logging.getLogger(__name__)

# rag_service instance - initialized lazily when first needed
_rag_service = None

def get_rag_service():
    """Get or initialize the RAG service instance"""
    global _rag_service
    if _rag_service is None:
        try:
            from . import rag_service as rag_module
            _rag_service = rag_module.rag_service
            print("[Signals] RAG service instance obtained")
        except Exception as e:
            logger.error(f"Error getting rag_service instance: {e}")
            print(f"[Signals] Error: {e}")
    return _rag_service

@receiver(post_save, sender=Product)
def sync_product_to_rag(sender, instance, created, **kwargs):
    try:
        rag_service = get_rag_service()
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
    try:
        rag_service = get_rag_service()
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

@receiver(post_save, sender=AISettings)
def reload_voice_commands_on_settings_change(sender, instance, created, **kwargs):
    try:
        rag_service = get_rag_service()
        if not rag_service:
            logger.warning("RAG service not initialized when AISettings changed")
            print("⚠ RAG service not initialized")
            return
        
        from .rag_service import VoiceCommandManager
        
        print(f"[Signal] AISettings updated - Reloading voice commands...")
        
        # Reload voice commands from database
        rag_service.voice_commands = VoiceCommandManager.get_voice_commands()
        
        logger.info(f"Voice commands reloaded: "
                   f"add={len(rag_service.voice_commands.get('add', []))}, "
                   f"decrease={len(rag_service.voice_commands.get('decrease', []))}, "
                   f"delete={len(rag_service.voice_commands.get('delete', []))}")
        print(f"✓ Voice commands reloaded successfully!")
        print(f"  ADD: {rag_service.voice_commands.get('add', [])}")
        print(f"  DECREASE: {rag_service.voice_commands.get('decrease', [])}")
        print(f"  DELETE: {rag_service.voice_commands.get('delete', [])}")
        
    except Exception as e:
        logger.error(f"Error reloading voice commands on AISettings change: {e}", exc_info=True)
        print(f" Error reloading voice commands: {e}")

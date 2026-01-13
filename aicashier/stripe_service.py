import os
import stripe
from django.conf import settings
import logging
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)


class StripeService:
    """Stripe Payment Gateway Service - Using Payment Links with QR Code"""

    def __init__(self):
        self.secret_key = os.getenv("STRIPE_SECRET_KEY", "")
        self.public_key = os.getenv("STRIPE_PUBLIC_KEY", "")
        
        # Initialize Stripe
        stripe.api_key = self.secret_key
        
        mode = "UNKNOWN"
        if self.secret_key.startswith("sk_test_"):
            mode = "TEST mode (sandbox)"
        elif self.secret_key.startswith("sk_live_"):
            mode = "LIVE mode (real charge)"

        logger.info(
            f"Stripe Service initialized | Mode: {mode}"
        )

    def create_payment_link(
        self, 
        amount: float, 
        description: str = "Payment",
        metadata: dict = None,
        success_url: str = None,
        cancel_url: str = None
    ) -> dict:
        try:
            amount_satang = int(float(amount) * 100)
            
            if metadata is None:
                metadata = {}
            
            # Default URLs
            if not success_url:
                # ใช้ full URL เสมอ เช่น http://localhost:8000/payment/success
                success_url = "http://127.0.0.1:8000/payment/success" 
            if not cancel_url:
                cancel_url = "http://127.0.0.1:8000/"
            
            # สร้าง Checkout Session
            session = stripe.checkout.Session.create(
                payment_method_types=["card", "promptpay"],
                line_items=[
                    {
                        "price_data": {
                            "currency": "thb",
                            "product_data": {
                                "name": description,
                            },
                            "unit_amount": amount_satang,
                        },
                        "quantity": 1,
                    }
                ],
                mode="payment",
                # ตรงนี้สำคัญ: เมื่อจ่ายเสร็จจะเด้งไปหน้านี้
                success_url=success_url + "?session_id={CHECKOUT_SESSION_ID}",
                cancel_url=cancel_url,
                metadata=metadata
            )
            
            logger.info(f" Checkout Session created: {session.id}")
            
            # Return URL ของ Session โดยตรง
            return {
                "success": True,
                "checkout_session_id": session.id,
                "payment_url": session.url, # ใช้ Link นี้ ลูกค้าจะถูก Redirect ได้
                "amount": amount_satang,
                "currency": "thb"
            }
            
        except Exception as e:
            logger.exception(f" Error: {str(e)}")
            return {"success": False, "error": str(e)}

    # ─────────────────────────────────────────────────────────────
    # Check Payment Link Status
    # ─────────────────────────────────────────────────────────────
    def get_payment_link_status(self, payment_link_id: str) -> dict:
        """
        ตรวจสอบสถานะของ Payment Link
        
        Args:
            payment_link_id: ID ของ Payment Link
            
        Returns:
            dict: สถานะและข้อมูล Payment Link
        """
        try:
            payment_link = stripe.PaymentLink.retrieve(payment_link_id)
            
            return {
                "success": True,
                "payment_link_id": payment_link.id,
                "status": payment_link.status,
                "url": payment_link.url,
                "raw": payment_link
            }
            
        except stripe.error.InvalidRequestError as e:
            logger.error(f" Payment Link not found: {e}")
            return {"success": False, "error": f"Payment Link not found"}
        except Exception as e:
            logger.exception(f"Error retrieving payment link: {str(e)}")
            return {"success": False, "error": str(e)}


stripe_service = StripeService()

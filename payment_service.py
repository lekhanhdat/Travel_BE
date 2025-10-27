"""
PayOS Payment Service
Handles payment creation, status checking, and webhook processing
"""
import os
import time
from typing import Optional, Dict, Any
from dotenv import load_dotenv
from payos import PayOS
from payos.types import CreatePaymentLinkRequest

load_dotenv()

# PayOS Configuration
PAYOS_CLIENT_ID = os.getenv("PAYOS_CLIENT_ID", "")
PAYOS_API_KEY = os.getenv("PAYOS_API_KEY", "")
PAYOS_CHECKSUM_KEY = os.getenv("PAYOS_CHECKSUM_KEY", "")
PUBLIC_BASE_URL = os.getenv("PUBLIC_BASE_URL", "https://digital-ocean-fast-api-h9zys.ondigitalocean.app")

# Initialize PayOS client
payos_client = PayOS(
    client_id=PAYOS_CLIENT_ID,
    api_key=PAYOS_API_KEY,
    checksum_key=PAYOS_CHECKSUM_KEY
)


def verify_webhook_signature(data: Dict[str, Any], received_signature: str) -> bool:
    """
    Verify webhook signature from PayOS using official SDK
    """
    try:
        payos_client.webhooks.verify(data, received_signature)
        return True
    except Exception:
        return False


def create_payment_link(amount: int, user_id: Optional[int] = None, description: Optional[str] = None) -> Dict[str, Any]:
    """
    Create a payment link with PayOS using official SDK

    Args:
        amount: Amount in VND
        user_id: User ID for tracking
        description: Payment description

    Returns:
        Dict with orderCode, paymentLinkId, qrCode, checkoutUrl
    """
    if not PAYOS_CLIENT_ID or not PAYOS_API_KEY:
        raise ValueError("PayOS credentials not configured")

    # Generate unique order code (timestamp-based)
    order_code = int(time.time())

    # Build description with user ID for webhook parsing
    if user_id:
        desc = description or f"Donation from user {user_id}"
    else:
        desc = description or "Donation"

    # Create payment request using PayOS SDK
    payment_data = CreatePaymentLinkRequest(
        order_code=order_code,
        amount=amount,
        description=desc,
        return_url=f"{PUBLIC_BASE_URL}/payment/return",
        cancel_url=f"{PUBLIC_BASE_URL}/payment/cancel",
    )

    try:
        # Call PayOS API using SDK
        response = payos_client.payment_requests.create(payment_data=payment_data)

        # Log response for debugging
        print(f"PayOS API Response: {response}")
        print(f"QR Code length: {len(response.qr_code) if response.qr_code else 0}")
        print(f"QR Code value: {response.qr_code}")

        # Extract response data
        result = {
            "orderCode": response.order_code,
            "paymentLinkId": response.payment_link_id or "",
            "qrCode": response.qr_code or "",  # QR code string (not base64)
            "checkoutUrl": response.checkout_url or "",
        }

        print(f"Result qrCode length: {len(result['qrCode'])}")

        return result

    except Exception as e:
        # Log detailed error for debugging
        error_msg = f"PayOS API Error: {str(e)}"
        print(f"Error creating payment: {error_msg}")
        raise ValueError(error_msg)


def get_payment_status(order_code: int) -> Dict[str, Any]:
    """
    Get payment status from PayOS using official SDK

    Args:
        order_code: Order code to check

    Returns:
        Dict with status, amountPaid, orderCode, paymentLinkId
    """
    if not PAYOS_CLIENT_ID or not PAYOS_API_KEY:
        raise ValueError("PayOS credentials not configured")

    try:
        # Get payment info using SDK
        response = payos_client.payment_requests.get(order_code)

        # Extract status info
        result = {
            "status": response.status or "PENDING",
            "amountPaid": response.amount_paid or 0,
            "orderCode": response.order_code,
            "paymentLinkId": response.id or "",
        }

        return result

    except Exception as e:
        # If payment not found, return PENDING status
        print(f"Error getting payment status: {str(e)}")
        return {
            "status": "PENDING",
            "orderCode": order_code,
        }


def confirm_webhook(webhook_url: str) -> Dict[str, Any]:
    """
    Register/confirm webhook URL with PayOS
    This replaces the manual webhook configuration in PayOS dashboard

    Args:
        webhook_url: Your webhook endpoint URL (e.g., https://your-domain.com/webhook/payos)

    Returns:
        Dict with confirmation result
    """
    if not PAYOS_CLIENT_ID or not PAYOS_API_KEY:
        raise ValueError("PayOS credentials not configured")

    headers = {
        "x-client-id": PAYOS_CLIENT_ID,
        "x-api-key": PAYOS_API_KEY,
        "Content-Type": "application/json",
    }

    # PayOS webhook confirmation endpoint
    url = "https://api.payos.vn/v2/webhook-url"

    payload = {
        "webhookUrl": webhook_url
    }

    response = requests.post(url, json=payload, headers=headers)
    response.raise_for_status()

    return response.json()


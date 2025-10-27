"""
PayOS Payment Service
Handles payment creation, status checking, and webhook processing
"""
import os
import time
import hmac
import hashlib
import requests
from typing import Optional, Dict, Any
from dotenv import load_dotenv

load_dotenv()

# PayOS Configuration
PAYOS_CLIENT_ID = os.getenv("PAYOS_CLIENT_ID", "")
PAYOS_API_KEY = os.getenv("PAYOS_API_KEY", "")
PAYOS_CHECKSUM_KEY = os.getenv("PAYOS_CHECKSUM_KEY", "")
PUBLIC_BASE_URL = os.getenv("PUBLIC_BASE_URL", "https://digital-ocean-fast-api-h9zys.ondigitalocean.app")

PAYOS_API_URL = "https://api-merchant.payos.vn/v2/payment-requests"


def generate_signature(data: Dict[str, Any]) -> str:
    """
    Generate HMAC SHA256 signature for PayOS
    Format: amount&cancelUrl&description&orderCode&returnUrl
    """
    if not PAYOS_CHECKSUM_KEY:
        raise ValueError("PAYOS_CHECKSUM_KEY is not configured")
    
    # Build signature string according to PayOS spec
    sig_string = (
        f"{data.get('amount', '')}&"
        f"{data.get('cancelUrl', '')}&"
        f"{data.get('description', '')}&"
        f"{data.get('orderCode', '')}&"
        f"{data.get('returnUrl', '')}"
    )
    
    signature = hmac.new(
        PAYOS_CHECKSUM_KEY.encode('utf-8'),
        sig_string.encode('utf-8'),
        hashlib.sha256
    ).hexdigest()
    
    return signature


def verify_webhook_signature(data: Dict[str, Any], received_signature: str) -> bool:
    """
    Verify webhook signature from PayOS
    """
    expected = generate_signature(data)
    return hmac.compare_digest(expected, received_signature)


def create_payment_link(amount: int, user_id: Optional[int] = None, description: Optional[str] = None) -> Dict[str, Any]:
    """
    Create a payment link with PayOS
    
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
    
    payload = {
        "orderCode": order_code,
        "amount": amount,
        "description": desc,
        "returnUrl": f"{PUBLIC_BASE_URL}/payment/return",
        "cancelUrl": f"{PUBLIC_BASE_URL}/payment/cancel",
    }
    
    # Generate signature
    payload["signature"] = generate_signature(payload)
    
    # Call PayOS API
    headers = {
        "x-client-id": PAYOS_CLIENT_ID,
        "x-api-key": PAYOS_API_KEY,
        "Content-Type": "application/json",
    }

    try:
        response = requests.post(
            PAYOS_API_URL,
            json=payload,
            headers=headers,
            timeout=30  # 30 seconds timeout
        )
        response.raise_for_status()
        data = response.json()

        # Log response for debugging
        print(f"PayOS API Response: {data}")

    except requests.exceptions.RequestException as e:
        # Log detailed error for debugging
        error_msg = f"PayOS API Error: {str(e)}"
        if hasattr(e, 'response') and e.response is not None:
            error_msg += f" | Status: {e.response.status_code} | Response: {e.response.text}"
        raise ValueError(error_msg)

    # PayOS response format: {"code": "00", "desc": "success", "data": {...}}
    # Extract data from nested structure
    if "data" in data:
        payment_data = data["data"]
    else:
        payment_data = data

    # Extract response data
    result = {
        "orderCode": payment_data.get("orderCode") or order_code,
        "paymentLinkId": payment_data.get("paymentLinkId", ""),
        "qrCode": payment_data.get("qrCode", ""),  # Base64 QR code
        "checkoutUrl": payment_data.get("checkoutUrl", ""),
    }

    return result


def get_payment_status(order_code: int) -> Dict[str, Any]:
    """
    Get payment status from PayOS

    Args:
        order_code: Order code to check

    Returns:
        Dict with status, amountPaid, orderCode, paymentLinkId
    """
    if not PAYOS_CLIENT_ID or not PAYOS_API_KEY:
        raise ValueError("PayOS credentials not configured")

    headers = {
        "x-client-id": PAYOS_CLIENT_ID,
        "x-api-key": PAYOS_API_KEY,
    }

    url = f"{PAYOS_API_URL}/{order_code}"
    response = requests.get(url, headers=headers)

    if response.status_code == 404:
        return {
            "status": "PENDING",
            "orderCode": order_code,
        }

    response.raise_for_status()
    data = response.json()

    # Map PayOS status to our status
    payos_status = data.get("status", "PENDING")
    status_map = {
        "PAID": "PAID",
        "PENDING": "PENDING",
        "PROCESSING": "PENDING",
        "CANCELLED": "CANCELLED",
        "EXPIRED": "EXPIRED",
    }

    return {
        "status": status_map.get(payos_status, "PENDING"),
        "amountPaid": data.get("amountPaid"),
        "orderCode": data.get("orderCode"),
        "paymentLinkId": data.get("paymentLinkId"),
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


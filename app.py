from fastapi import FastAPI, UploadFile, HTTPException, Request
from pydantic import BaseModel
from typing import Optional
import re
import os

# from service import get_full_description, get_object_name
from service import get_full_description, get_object_name
from payment_service import create_payment_link, get_payment_status, verify_webhook_signature, confirm_webhook
from nocodb_service import create_transaction, update_user_balance, get_user_by_id

app = FastAPI()


# Payment request models
class CreatePaymentRequest(BaseModel):
    amount: int
    userId: Optional[int] = None
    description: Optional[str] = None


@app.get("/")
async def root():
    return {"message": "Hello World"}


@app.post("/detect")
def detect(image_file: UploadFile):
    name = get_object_name(image_file)
    full_description = get_full_description(name)

    # return full_description
    return {
        "name": name,
        "description": full_description,
    }

@app.post('/detect/test')
def test_detect(image_file: UploadFile):
    return {"name": "test", "description": "# test description"}


# ============ Payment Endpoints ============

@app.post("/payments/create")
async def create_payment(req: CreatePaymentRequest):
    """
    Create a payment link with PayOS
    """
    try:
        if req.amount < 1000:
            raise HTTPException(status_code=400, detail="Amount must be at least 1,000 VND")

        result = create_payment_link(
            amount=req.amount,
            user_id=req.userId,
            description=req.description
        )

        return result
    except ValueError as e:
        raise HTTPException(status_code=500, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create payment: {str(e)}")


@app.get("/payments/status/{order_code}")
async def payment_status(order_code: int):
    """
    Get payment status from PayOS
    """
    try:
        result = get_payment_status(order_code)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get payment status: {str(e)}")


@app.post("/webhook/payos")
async def payos_webhook(request: Request):
    """
    Webhook endpoint for PayOS payment notifications
    """
    try:
        body = await request.json()
        data = body.get("data", body)

        # Verify signature (optional but recommended)
        signature = body.get("signature", "")
        # if signature and not verify_webhook_signature(data, signature):
        #     raise HTTPException(status_code=400, detail="Invalid signature")

        # Extract payment info
        order_code = data.get("orderCode")
        amount = data.get("amount")
        description = data.get("description", "")
        payment_link_id = data.get("paymentLinkId", "")
        status = data.get("status", "PAID")

        # Parse user ID from description (format: "Donation from user {userId}")
        user_id = None
        match = re.search(r"user (\d+)", description)
        if match:
            user_id = int(match.group(1))

        # Create transaction record in NocoDB
        transaction_id = create_transaction(
            account_id=user_id,
            amount=amount,
            description=description,
            order_code=order_code,
            payment_link_id=payment_link_id,
            status=status
        )

        # Update user balance if user_id exists and payment is successful
        if user_id and status == "PAID":
            new_balance = update_user_balance(user_id, amount)
            print(f"Updated balance for user {user_id}: {new_balance}")

        return {
            "received": True,
            "transactionId": transaction_id,
            "userId": user_id,
            "amount": amount
        }

    except Exception as e:
        print(f"Webhook error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Webhook processing failed: {str(e)}")


@app.get("/payment/return")
async def payment_return():
    """Return URL after successful payment"""
    return {"message": "Payment successful! You can close this page."}


@app.get("/payment/cancel")
async def payment_cancel():
    """Cancel URL after cancelled payment"""
    return {"message": "Payment cancelled."}


@app.get("/payment/setup-webhook")
@app.post("/payment/setup-webhook")
async def setup_webhook():
    """
    Setup/confirm webhook URL with PayOS
    This endpoint should be called once to register the webhook
    Supports both GET and POST methods for easy browser testing
    """
    try:
        webhook_url = f"{os.getenv('PUBLIC_BASE_URL', 'https://digital-ocean-fast-api-h9zys.ondigitalocean.app')}/webhook/payos"
        result = confirm_webhook(webhook_url)
        return {
            "success": True,
            "message": f"Webhook registered successfully: {webhook_url}",
            "data": result
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to setup webhook: {str(e)}")

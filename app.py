from fastapi import FastAPI, UploadFile, HTTPException, Request
from pydantic import BaseModel
from typing import Optional
from contextlib import asynccontextmanager
import re
import os

from service import get_full_description, get_object_name
from payment_service import create_payment_link, get_payment_status, verify_webhook_signature, confirm_webhook
from nocodb_service import create_transaction, update_user_balance, get_user_by_id

# Import semantic search routers
from routers import search_router, chat_router, memory_router, recommendations_router

# Import startup indexer for cost-optimized demo deployment
from utils.startup_indexer import check_and_rebuild_indexes_on_startup, get_index_stats


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan event handler for startup/shutdown"""
    # Startup: Build FAISS indexes if needed
    print("Starting up...")
    try:
        await check_and_rebuild_indexes_on_startup()
        stats = get_index_stats()
        print(f"Index stats: {stats}")
    except Exception as e:
        print(f"Warning: Index startup failed: {e}")
    
    yield  # App is running
    
    # Shutdown
    print("Shutting down...")


app = FastAPI(
    title="Travel App API",
    description="Backend API for Travel App with Semantic Search capabilities",
    version="2.0.0",
    lifespan=lifespan
)

# Include semantic search routers
app.include_router(search_router)
app.include_router(chat_router)
app.include_router(memory_router)
app.include_router(recommendations_router)


# Payment request models
class CreatePaymentRequest(BaseModel):
    amount: int
    userId: Optional[int] = None
    description: Optional[str] = None


@app.get("/")
async def root():
    return {"message": "Hello World", "version": "2.0.0", "features": ["semantic-search", "rag-chat", "recommendations"]}


@app.post("/detect")
def detect(image_file: UploadFile):
    name = get_object_name(image_file)
    full_description = get_full_description(name)
    return {"name": name, "description": full_description}

@app.post('/detect/test')
def test_detect(image_file: UploadFile):
    return {"name": "test", "description": "# test description"}


# ============ Payment Endpoints ============

@app.post("/payments/create")
async def create_payment(req: CreatePaymentRequest):
    try:
        if req.amount < 1000:
            raise HTTPException(status_code=400, detail="Amount must be at least 1,000 VND")
        result = create_payment_link(amount=req.amount, user_id=req.userId, description=req.description)
        return result
    except ValueError as e:
        raise HTTPException(status_code=500, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create payment: {str(e)}")


@app.get("/payments/status/{order_code}")
async def payment_status(order_code: int):
    try:
        result = get_payment_status(order_code)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get payment status: {str(e)}")


@app.post("/webhook/payos")
async def payos_webhook(request: Request):
    try:
        body = await request.json()
        data = body.get("data", body)
        order_code = data.get("orderCode")
        amount = data.get("amount")
        description = data.get("description", "")
        payment_link_id = data.get("paymentLinkId", "")
        status = data.get("status", "PAID")

        user_id = None
        user_name = None
        match = re.search(r"user (\d+)", description)
        if match:
            user_id = int(match.group(1))
            # Look up user to get their userName
            user_data = get_user_by_id(user_id)
            if user_data:
                user_name = user_data.get("userName")
                print(f"Found user {user_id} with userName: {user_name}")

        transaction_id = create_transaction(
            account_id=user_id, amount=amount, description=description,
            order_code=order_code, payment_link_id=payment_link_id, status=status,
            user_name=user_name
        )

        if user_id and status == "PAID":
            new_balance = update_user_balance(user_id, amount)
            print(f"Updated balance for user {user_id}: {new_balance}")

        return {"received": True, "transactionId": transaction_id, "userId": user_id, "amount": amount}
    except Exception as e:
        print(f"Webhook error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Webhook processing failed: {str(e)}")


@app.get("/payment/return")
async def payment_return():
    return {"message": "Payment successful! You can close this page."}


@app.get("/payment/cancel")
async def payment_cancel():
    return {"message": "Payment cancelled."}


@app.get("/payment/webhook-info")
async def webhook_info():
    webhook_url = f"{os.getenv('PUBLIC_BASE_URL', 'https://digital-ocean-fast-api-h9zys.ondigitalocean.app')}/webhook/payos"
    return {
        "success": True,
        "webhookUrl": webhook_url,
        "message": "Configure this webhook URL in PayOS dashboard at https://my.payos.vn",
        "instructions": [
            "1. Login to https://my.payos.vn",
            "2. Go to your payment channel settings",
            "3. Find 'Webhook URL' field",
            f"4. Enter: {webhook_url}",
            "5. Save settings"
        ]
    }


# ============ Health Check ============

@app.get("/health")
async def health_check():
    stats = get_index_stats()
    return {
        "status": "healthy",
        "version": "2.0.0",
        "index_stats": stats,
        "services": {
            "core": "operational",
            "semantic_search": "operational" if stats["text_vectors"] > 0 else "initializing",
            "rag_chat": "operational",
            "recommendations": "operational"
        }
    }

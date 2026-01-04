from fastapi import APIRouter, HTTPException, Request, Header
from app.order.models import Order, OrderStatus
from app.core.config import get_settings
import stripe

router = APIRouter()
settings = get_settings()

@router.post("/webhook")
async def payment_webhook(request: Request, stripe_signature: str = Header(None)):
    payload = await request.body()
    
    try:
        event = stripe.Webhook.construct_event(
            payload, stripe_signature, settings.STRIPE_WEBHOOK_SECRET
        )
    except ValueError as e:
        # Invalid payload
        raise HTTPException(status_code=400, detail="Invalid payload")
    except stripe.error.SignatureVerificationError as e:
        # Invalid signature
        raise HTTPException(status_code=400, detail="Invalid signature")

    if event["type"] == "payment_intent.succeeded":
        payment_intent = event["data"]["object"]
        order_id = payment_intent.get("metadata", {}).get("order_id")
        
        if order_id:
            order = await Order.get(order_id)
            if order:
                order.status = OrderStatus.PAID
                await order.save()
                
    elif event["type"] == "payment_intent.payment_failed":
        # Handle failure (stock rollback should happen here or via background task)
        # For now, we just log it
        print(f"Payment failed: {event['data']['object']['id']}")
        
    return {"status": "success"}

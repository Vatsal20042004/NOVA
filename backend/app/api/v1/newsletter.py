"""
Newsletter API Router
"""

from fastapi import APIRouter, status
from pydantic import BaseModel, EmailStr

router = APIRouter()


class SubscribeRequest(BaseModel):
    email: EmailStr


@router.post("/subscribe", status_code=status.HTTP_200_OK)
async def subscribe(data: SubscribeRequest):
    """
    Subscribe to newsletter (Mock implementation).
    """
    # In a real app, you would save to DB and send email via SMTP/SendGrid/SES
    print(f"Sending welcome email to {data.email}")
    return {"message": "Subscription successful", "email": data.email}

"""
Twilio WhatsApp webhook handlers
"""

from fastapi import APIRouter, Request, Response, HTTPException, Depends
from fastapi.responses import PlainTextResponse
from typing import Optional
import logging
from app.auth.twilio_auth import verify_twilio_signature
from app.services.message_processor import MessageProcessor
from app.models.twilio_models import TwilioWebhookPayload
from app.utils.logger import get_logger

router = APIRouter()
logger = get_logger(__name__)

# Initialize message processor
message_processor = MessageProcessor()


@router.post("/whatsapp", response_class=PlainTextResponse)
async def handle_whatsapp_message(
    request: Request,
    signature_valid: bool = Depends(verify_twilio_signature)
) -> str:
    """
    Handle incoming WhatsApp messages from Twilio.
    
    Args:
        request: FastAPI request object
        signature_valid: Whether the Twilio signature is valid
        
    Returns:
        TwiML response or plain text response
    """
    if not signature_valid:
        logger.warning("Invalid Twilio signature")
        raise HTTPException(status_code=403, detail="Invalid signature")
    
    try:
        # Parse form data from Twilio
        form_data = await request.form()
        
        # Create payload model
        payload = TwilioWebhookPayload(
            from_number=form_data.get("From", ""),
            to_number=form_data.get("To", ""),
            body=form_data.get("Body", ""),
            message_sid=form_data.get("MessageSid", ""),
            account_sid=form_data.get("AccountSid", ""),
            num_media=int(form_data.get("NumMedia", 0)),
            profile_name=form_data.get("ProfileName", "")
        )
        
        logger.info(f"Received message from {payload.from_number}: {payload.body[:50]}...")
        
        # Process the message
        response = await message_processor.process_message(payload)
        
        # Return TwiML response
        return f"""<?xml version="1.0" encoding="UTF-8"?>
<Response>
    <Message>{response}</Message>
</Response>"""
        
    except Exception as e:
        logger.error(f"Error processing WhatsApp message: {str(e)}", exc_info=True)
        return """<?xml version="1.0" encoding="UTF-8"?>
<Response>
    <Message>Sorry, I encountered an error processing your message. Please try again later.</Message>
</Response>"""


@router.post("/status")
async def handle_status_callback(
    request: Request,
    signature_valid: bool = Depends(verify_twilio_signature)
) -> Response:
    """
    Handle Twilio status callbacks for message delivery status.
    
    Args:
        request: FastAPI request object
        signature_valid: Whether the Twilio signature is valid
        
    Returns:
        Empty response with 204 status
    """
    if not signature_valid:
        logger.warning("Invalid Twilio signature for status callback")
        raise HTTPException(status_code=403, detail="Invalid signature")
    
    try:
        form_data = await request.form()
        
        message_sid = form_data.get("MessageSid", "")
        message_status = form_data.get("MessageStatus", "")
        
        logger.info(f"Status update for message {message_sid}: {message_status}")
        
        # You can add additional logic here to track message delivery status
        # For example, updating a database or sending notifications
        
        return Response(status_code=204)
        
    except Exception as e:
        logger.error(f"Error processing status callback: {str(e)}", exc_info=True)
        return Response(status_code=204)  # Return 204 even on error to prevent Twilio retries

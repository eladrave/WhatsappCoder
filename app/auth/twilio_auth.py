"""
Twilio authentication and authorization
"""

from fastapi import Request, HTTPException, Depends
from twilio.request_validator import RequestValidator
from functools import lru_cache
from app.utils.config import get_settings, Settings
from app.utils.logger import get_logger
import os

logger = get_logger(__name__)

@lru_cache()
def get_twilio_validator() -> RequestValidator:
    """Get Twilio request validator from environment variables"""
    auth_token = os.environ.get("TWILIO_AUTH_TOKEN")
    if not auth_token:
        raise ValueError("TWILIO_AUTH_TOKEN environment variable not set")
    return RequestValidator(auth_token)


async def verify_twilio_signature(request: Request) -> bool:
    """
    Verify the Twilio signature from the request headers.

    Args:
        request: FastAPI request object

    Returns:
        True if the signature is valid, otherwise raises HTTPException.
    """
    try:
        validator = get_twilio_validator()
        url = str(request.url)
        params = await request.form()
        signature = request.headers.get("X-Twilio-Signature", "")
        
        if validator.validate(url, params, signature):
            return True
        else:
            logger.warning("Invalid Twilio signature")
            raise HTTPException(status_code=403, detail="Invalid Twilio signature")
    except Exception as e:
        logger.error(f"Error validating Twilio signature: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Could not validate signature")


async def authorize_phone_number(
    request: Request, 
    settings: Settings = Depends(get_settings)
) -> bool:
    """
    Authorize the sender's phone number against a whitelist.

    Args:
        request: FastAPI request object
        settings: Application settings

    Returns:
        True if the phone number is authorized, otherwise raises HTTPException.
    """
    try:
        form_data = await request.form()
        from_number = form_data.get("From", "")
        
        # Standardize phone number format (e.g., remove 'whatsapp:' prefix)
        if from_number.startswith("whatsapp:"):
            from_number = from_number.replace("whatsapp:", "")
        
        if from_number in settings.ALLOWED_PHONE_NUMBERS:
            logger.debug(f"Authorized phone number: {from_number}")
            return True
        else:
            logger.warning(f"Unauthorized phone number: {from_number}")
            raise HTTPException(status_code=403, detail="Unauthorized phone number")
            
    except HTTPException: # Re-raise if it's already an HTTPException
        raise
    except Exception as e:
        logger.error(f"Error authorizing phone number: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Could not authorize phone number")


async def require_auth(
    signature_valid: bool = Depends(verify_twilio_signature),
    phone_authorized: bool = Depends(authorize_phone_number)
) -> bool:
    """
    Dependency that requires both Twilio signature verification and phone number authorization.

    Args:
        signature_valid: Result of Twilio signature verification
        phone_authorized: Result of phone number authorization

    Returns:
        True if both signature and phone number are valid.
    """
    return signature_valid and phone_authorized


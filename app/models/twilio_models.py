"""
Pydantic models for Twilio webhook payloads
"""

from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime


class TwilioWebhookPayload(BaseModel):
    """Model for incoming Twilio WhatsApp webhook payload"""
    
    from_number: str = Field(..., alias="From", description="Sender's WhatsApp number")
    to_number: str = Field(..., alias="To", description="Recipient's WhatsApp number")
    body: str = Field("", alias="Body", description="Message body text")
    message_sid: str = Field(..., alias="MessageSid", description="Unique message identifier")
    account_sid: str = Field(..., alias="AccountSid", description="Twilio account SID")
    num_media: int = Field(0, alias="NumMedia", description="Number of media attachments")
    profile_name: Optional[str] = Field(None, alias="ProfileName", description="Sender's WhatsApp profile name")
    
    class Config:
        populate_by_name = True


class MediaAttachment(BaseModel):
    """Model for media attachments in WhatsApp messages"""
    
    content_type: str = Field(..., alias="ContentType")
    url: str = Field(..., alias="Url")
    sid: str = Field(..., alias="Sid")
    
    class Config:
        populate_by_name = True


class TwilioStatusCallback(BaseModel):
    """Model for Twilio status callback payload"""
    
    message_sid: str = Field(..., alias="MessageSid")
    message_status: str = Field(..., alias="MessageStatus")
    to: str = Field(..., alias="To")
    from_: str = Field(..., alias="From")
    api_version: str = Field(..., alias="ApiVersion")
    account_sid: str = Field(..., alias="AccountSid")
    error_code: Optional[int] = Field(None, alias="ErrorCode")
    error_message: Optional[str] = Field(None, alias="ErrorMessage")
    
    class Config:
        populate_by_name = True


class WhatsAppMessage(BaseModel):
    """Internal model for WhatsApp messages"""
    
    phone_number: str
    message: str
    profile_name: Optional[str] = None
    media_attachments: List[MediaAttachment] = []
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    message_sid: str
    
    @property
    def has_media(self) -> bool:
        """Check if message has media attachments"""
        return len(self.media_attachments) > 0
    
    @property
    def is_command(self) -> bool:
        """Check if message starts with a command prefix"""
        return self.message.strip().startswith("/")
    
    def get_command(self) -> Optional[str]:
        """Extract command from message if it exists"""
        if self.is_command:
            parts = self.message.strip().split(maxsplit=1)
            return parts[0][1:].lower()  # Remove '/' prefix and lowercase
        return None
    
    def get_command_args(self) -> str:
        """Get arguments after the command"""
        if self.is_command:
            parts = self.message.strip().split(maxsplit=1)
            return parts[1] if len(parts) > 1 else ""
        return self.message

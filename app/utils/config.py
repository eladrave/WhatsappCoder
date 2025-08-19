"""
Configuration management using Pydantic Settings
"""

from pydantic_settings import BaseSettings
from functools import lru_cache
from typing import List, Set
import os


class Settings(BaseSettings):
    # Twilio Configuration
    TWILIO_ACCOUNT_SID: str
    TWILIO_AUTH_TOKEN: str
    TWILIO_PHONE_NUMBER: str

    # Security
    ALLOWED_PHONE_NUMBERS: Set[str] = set()

    # AutoCoder Integration
    AUTOCODER_API_URL: str = "http://localhost:8000/api"
    AUTOCODER_MCP_URL: str = "ws://localhost:5000/mcp"
    AUTOCODER_API_KEY: str = "your-autocoder-api-key"

    # Redis Configuration
    REDIS_URL: str = "redis://localhost:6379/0"

    # Application Settings
    LOG_LEVEL: str = "INFO"
    SESSION_TTL_HOURS: int = 24
    MAX_MESSAGE_LENGTH: int = 1600
    DEFAULT_AGENT_MODEL: str = "openai/gpt-4o"

    # Feature Flags
    ENABLE_RATE_LIMITING: bool = True
    ENABLE_VISION_SUPPORT: bool = False

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = True

    def __init__(self, **values):
        super().__init__(**values)
        # Convert comma-separated string from env to a set of strings
        allowed_numbers_str = os.getenv("ALLOWED_PHONE_NUMBERS", "")
        if allowed_numbers_str:
            self.ALLOWED_PHONE_NUMBERS = {f"whatsapp:{item.strip()}" for item in allowed_numbers_str.split(",")}


@lru_cache()
def get_settings() -> Settings:
    """Get application settings"""
    return Settings()


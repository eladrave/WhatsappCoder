"""
Conversation state management service
"""

import json
from typing import Optional, Dict, List, Any
from datetime import datetime, timedelta
import redis.asyncio as redis
from app.utils.config import get_settings
from app.utils.logger import get_logger
from app.state.models import ConversationState, UserSession

logger = get_logger(__name__)
settings = get_settings()


class ConversationManager:
    """Manages conversation state and history in Redis"""
    
    def __init__(self):
        self.redis_client = None
        self.ttl_seconds = settings.SESSION_TTL_HOURS * 3600
    
    async def _get_redis_client(self) -> redis.Redis:
        """Get or create Redis client"""
        if not self.redis_client:
            self.redis_client = await redis.from_url(
                settings.REDIS_URL,
                encoding="utf-8",
                decode_responses=True
            )
        return self.redis_client
    
    async def get_or_create_conversation(self, phone_number: str) -> Dict[str, Any]:
        """
        Get or create a conversation state for a phone number.
        
        Args:
            phone_number: User's phone number
            
        Returns:
            Conversation state dictionary
        """
        try:
            client = await self._get_redis_client()
            key = f"conversation:{phone_number}"
            
            # Try to get existing conversation
            data = await client.get(key)
            if data:
                conversation = json.loads(data)
                logger.debug(f"Retrieved existing conversation for {phone_number}")
            else:
                # Create new conversation
                conversation = {
                    "phone_number": phone_number,
                    "created_at": datetime.utcnow().isoformat(),
                    "last_activity": datetime.utcnow().isoformat(),
                    "active_project": None,
                    "history": [],
                    "context": {}
                }
                await client.setex(
                    key,
                    self.ttl_seconds,
                    json.dumps(conversation)
                )
                logger.info(f"Created new conversation for {phone_number}")
            
            return conversation
            
        except Exception as e:
            logger.error(f"Error getting/creating conversation: {str(e)}")
            # Return a default conversation if Redis fails
            return {
                "phone_number": phone_number,
                "created_at": datetime.utcnow().isoformat(),
                "last_activity": datetime.utcnow().isoformat(),
                "active_project": None,
                "history": [],
                "context": {}
            }
    
    async def add_message_to_history(
        self,
        phone_number: str,
        user_message: str,
        assistant_response: str
    ) -> None:
        """
        Add a message exchange to the conversation history.
        
        Args:
            phone_number: User's phone number
            user_message: User's message
            assistant_response: Assistant's response
        """
        try:
            client = await self._get_redis_client()
            key = f"conversation:{phone_number}"
            
            # Get current conversation
            data = await client.get(key)
            if data:
                conversation = json.loads(data)
            else:
                conversation = await self.get_or_create_conversation(phone_number)
            
            # Add to history (keep last 20 messages)
            conversation["history"].append({
                "timestamp": datetime.utcnow().isoformat(),
                "user": user_message,
                "assistant": assistant_response
            })
            
            # Keep only last 20 messages
            conversation["history"] = conversation["history"][-20:]
            
            # Update last activity
            conversation["last_activity"] = datetime.utcnow().isoformat()
            
            # Save back to Redis
            await client.setex(
                key,
                self.ttl_seconds,
                json.dumps(conversation)
            )
            
            logger.debug(f"Added message to history for {phone_number}")
            
        except Exception as e:
            logger.error(f"Error adding message to history: {str(e)}")
    
    async def set_active_project(self, phone_number: str, project_id: str) -> None:
        """
        Set the active project for a conversation.
        
        Args:
            phone_number: User's phone number
            project_id: Project ID to set as active
        """
        try:
            client = await self._get_redis_client()
            key = f"conversation:{phone_number}"
            
            # Get current conversation
            data = await client.get(key)
            if data:
                conversation = json.loads(data)
            else:
                conversation = await self.get_or_create_conversation(phone_number)
            
            # Set active project
            conversation["active_project"] = project_id
            conversation["last_activity"] = datetime.utcnow().isoformat()
            
            # Save back to Redis
            await client.setex(
                key,
                self.ttl_seconds,
                json.dumps(conversation)
            )
            
            logger.info(f"Set active project {project_id} for {phone_number}")
            
        except Exception as e:
            logger.error(f"Error setting active project: {str(e)}")
    
    async def get_conversation_history(
        self,
        phone_number: str,
        limit: int = 10
    ) -> List[Dict[str, str]]:
        """
        Get conversation history for a phone number.
        
        Args:
            phone_number: User's phone number
            limit: Maximum number of messages to return
            
        Returns:
            List of message exchanges
        """
        try:
            conversation = await self.get_or_create_conversation(phone_number)
            history = conversation.get("history", [])
            return history[-limit:] if history else []
            
        except Exception as e:
            logger.error(f"Error getting conversation history: {str(e)}")
            return []
    
    async def clear_conversation(self, phone_number: str) -> None:
        """
        Clear conversation history for a phone number.
        
        Args:
            phone_number: User's phone number
        """
        try:
            client = await self._get_redis_client()
            key = f"conversation:{phone_number}"
            
            # Get current conversation
            data = await client.get(key)
            if data:
                conversation = json.loads(data)
                # Clear history but keep active project
                conversation["history"] = []
                conversation["context"] = {}
                conversation["last_activity"] = datetime.utcnow().isoformat()
                
                # Save back to Redis
                await client.setex(
                    key,
                    self.ttl_seconds,
                    json.dumps(conversation)
                )
                
                logger.info(f"Cleared conversation history for {phone_number}")
            
        except Exception as e:
            logger.error(f"Error clearing conversation: {str(e)}")
    
    async def update_context(
        self,
        phone_number: str,
        context_updates: Dict[str, Any]
    ) -> None:
        """
        Update conversation context with additional information.
        
        Args:
            phone_number: User's phone number
            context_updates: Dictionary of context updates
        """
        try:
            client = await self._get_redis_client()
            key = f"conversation:{phone_number}"
            
            # Get current conversation
            data = await client.get(key)
            if data:
                conversation = json.loads(data)
            else:
                conversation = await self.get_or_create_conversation(phone_number)
            
            # Update context
            conversation["context"].update(context_updates)
            conversation["last_activity"] = datetime.utcnow().isoformat()
            
            # Save back to Redis
            await client.setex(
                key,
                self.ttl_seconds,
                json.dumps(conversation)
            )
            
            logger.debug(f"Updated context for {phone_number}")
            
        except Exception as e:
            logger.error(f"Error updating context: {str(e)}")

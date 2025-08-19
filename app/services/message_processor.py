"""
Message processing service for handling WhatsApp messages
"""

from typing import Optional
from app.models.twilio_models import TwilioWebhookPayload, WhatsAppMessage
from app.services.conversation_manager import ConversationManager
from app.services.langchain_service import LangChainService
from app.services.response_formatter import ResponseFormatter
from app.utils.logger import get_logger
from app.utils.config import get_settings

logger = get_logger(__name__)
settings = get_settings()


class MessageProcessor:
    """Process incoming WhatsApp messages and generate responses"""
    
    def __init__(self):
        self.conversation_manager = ConversationManager()
        self.langchain_service = LangChainService()
        self.response_formatter = ResponseFormatter()
    
    async def process_message(self, payload: TwilioWebhookPayload) -> str:
        """
        Process an incoming WhatsApp message and generate a response.
        
        Args:
            payload: Twilio webhook payload
            
        Returns:
            Formatted response message
        """
        try:
            # Convert Twilio payload to WhatsApp message
            message = self._create_whatsapp_message(payload)
            
            # Get or create conversation state
            conversation = await self.conversation_manager.get_or_create_conversation(
                message.phone_number
            )
            
            # Process command messages
            if message.is_command:
                response = await self._handle_command(message, conversation)
            else:
                # Process natural language messages with LangChain
                response = await self.langchain_service.process_message(
                    message=message.message,
                    conversation=conversation
                )
            
            # Update conversation history
            await self.conversation_manager.add_message_to_history(
                phone_number=message.phone_number,
                user_message=message.message,
                assistant_response=response
            )
            
            # Format response for WhatsApp
            formatted_response = self.response_formatter.format_for_whatsapp(response)
            
            return formatted_response
            
        except Exception as e:
            logger.error(f"Error processing message: {str(e)}", exc_info=True)
            return "Sorry, I encountered an error processing your message. Please try again."
    
    def _create_whatsapp_message(self, payload: TwilioWebhookPayload) -> WhatsAppMessage:
        """Convert Twilio payload to WhatsApp message model"""
        return WhatsAppMessage(
            phone_number=payload.from_number,
            message=payload.body,
            profile_name=payload.profile_name,
            message_sid=payload.message_sid,
            media_attachments=[]  # TODO: Handle media attachments
        )
    
    async def _handle_command(self, message: WhatsAppMessage, conversation: dict) -> str:
        """
        Handle command messages.
        
        Args:
            message: WhatsApp message
            conversation: Conversation state
            
        Returns:
            Command response
        """
        command = message.get_command()
        args = message.get_command_args()
        
        logger.info(f"Processing command: {command} with args: {args}")
        
        commands = {
            "help": self._handle_help_command,
            "new": self._handle_new_project_command,
            "list": self._handle_list_projects_command,
            "status": self._handle_status_command,
            "files": self._handle_files_command,
            "clear": self._handle_clear_command,
        }
        
        handler = commands.get(command)
        if handler:
            return await handler(args, conversation)
        else:
            return f"Unknown command: /{command}. Type /help to see available commands."
    
    async def _handle_help_command(self, args: str, conversation: dict) -> str:
        """Handle /help command"""
        return """📚 *Available Commands*

/help - Show this help message
/new [name] - Create a new project
/list - List all your projects
/status - Check current task status
/files - Get generated files
/clear - Clear conversation history

You can also just describe what you want to build in natural language!

Example: "Create a Python REST API with user authentication"
"""
    
    async def _handle_new_project_command(self, args: str, conversation: dict) -> str:
        """Handle /new command to create a new project"""
        if not args:
            return "Please provide a project name. Example: /new MyWebApp"
        
        try:
            result = await self.langchain_service.create_project(
                project_name=args,
                conversation=conversation
            )
            
            await self.conversation_manager.set_active_project(
                phone_number=conversation["phone_number"],
                project_id=result.get("project_id")
            )
            
            return f"✅ Project '{args}' created successfully!\n\nNow describe what you want to build."
            
        except Exception as e:
            logger.error(f"Error creating project: {str(e)}")
            return f"❌ Failed to create project: {str(e)}"
    
    async def _handle_list_projects_command(self, args: str, conversation: dict) -> str:
        """Handle /list command to list projects"""
        try:
            projects = await self.langchain_service.list_projects(conversation)
            
            if not projects:
                return "You don't have any projects yet. Use /new to create one."
            
            response = "📁 *Your Projects:*\n\n"
            for project in projects:
                response += f"• {project['name']} ({project['id']})\n"
                if project.get('description'):
                    response += f"  {project['description']}\n"
            
            return response
            
        except Exception as e:
            logger.error(f"Error listing projects: {str(e)}")
            return "❌ Failed to list projects."
    
    async def _handle_status_command(self, args: str, conversation: dict) -> str:
        """Handle /status command to check task status"""
        try:
            active_project = conversation.get("active_project")
            if not active_project:
                return "No active project. Use /new to create one or /list to see your projects."
            
            status = await self.langchain_service.get_task_status(
                project_id=active_project,
                conversation=conversation
            )
            
            return self.response_formatter.format_status(status)
            
        except Exception as e:
            logger.error(f"Error getting status: {str(e)}")
            return "❌ Failed to get status."
    
    async def _handle_files_command(self, args: str, conversation: dict) -> str:
        """Handle /files command to get generated files"""
        try:
            active_project = conversation.get("active_project")
            if not active_project:
                return "No active project. Use /new to create one or /list to see your projects."
            
            files = await self.langchain_service.get_project_files(
                project_id=active_project,
                conversation=conversation
            )
            
            if not files:
                return "No files generated yet."
            
            response = "📄 *Generated Files:*\n\n"
            for file in files:
                response += f"• {file['name']}\n"
                if file.get('url'):
                    response += f"  Download: {file['url']}\n"
            
            return response
            
        except Exception as e:
            logger.error(f"Error getting files: {str(e)}")
            return "❌ Failed to get files."
    
    async def _handle_clear_command(self, args: str, conversation: dict) -> str:
        """Handle /clear command to clear conversation history"""
        try:
            await self.conversation_manager.clear_conversation(
                conversation["phone_number"]
            )
            return "✅ Conversation history cleared."
        except Exception as e:
            logger.error(f"Error clearing conversation: {str(e)}")
            return "❌ Failed to clear conversation."

"""
Response formatting service for WhatsApp messages
"""

from typing import Dict, Any, List, Optional
from app.utils.config import get_settings
from app.state.models import TaskStatus
import re

settings = get_settings()


class ResponseFormatter:
    """Format responses for WhatsApp display"""
    
    def __init__(self):
        self.max_length = settings.MAX_MESSAGE_LENGTH
    
    def format_for_whatsapp(self, text: str) -> str:
        """
        Format text for WhatsApp display.
        
        Args:
            text: Text to format
            
        Returns:
            Formatted text suitable for WhatsApp
        """
        # Truncate if too long
        if len(text) > self.max_length:
            text = text[:self.max_length - 20] + "\n\n... (truncated)"
        
        # Ensure proper WhatsApp formatting
        # Bold: *text*
        # Italic: _text_
        # Monospace: ```text```
        
        return text
    
    def format_code_snippet(self, code: str, language: str = "") -> str:
        """
        Format code snippet for WhatsApp.
        
        Args:
            code: Code to format
            language: Programming language (optional)
            
        Returns:
            Formatted code snippet
        """
        # WhatsApp uses triple backticks for monospace blocks
        formatted = f"```{language}\n{code}\n```"
        
        # Truncate if too long
        if len(formatted) > self.max_length:
            lines = code.split('\n')
            truncated_code = '\n'.join(lines[:20])
            formatted = f"```{language}\n{truncated_code}\n... (truncated)\n```"
        
        return formatted
    
    def format_status(self, status_data: Dict[str, Any]) -> str:
        """
        Format task status for WhatsApp display.
        
        Args:
            status_data: Status information dictionary
            
        Returns:
            Formatted status message
        """
        status = status_data.get("status", TaskStatus.PENDING)
        project_name = status_data.get("project_name", "Unknown Project")
        task_description = status_data.get("task_description", "No description")
        
        # Status emoji
        status_emoji = {
            TaskStatus.PENDING: "⏳",
            TaskStatus.IN_PROGRESS: "🔄",
            TaskStatus.COMPLETED: "✅",
            TaskStatus.FAILED: "❌",
            TaskStatus.CANCELLED: "🚫"
        }.get(status, "❓")
        
        message = f"{status_emoji} *Task Status*\n\n"
        message += f"*Project:* {project_name}\n"
        message += f"*Task:* {task_description}\n"
        message += f"*Status:* {status.value if hasattr(status, 'value') else status}\n"
        
        # Add progress if available
        if status_data.get("progress"):
            progress = status_data["progress"]
            message += f"*Progress:* {progress}%\n"
        
        # Add recent logs if available
        if status_data.get("recent_logs"):
            message += "\n*Recent Activity:*\n"
            for log in status_data["recent_logs"][-3:]:  # Last 3 logs
                message += f"• {log}\n"
        
        # Add completion info if completed
        if status == TaskStatus.COMPLETED:
            if status_data.get("generated_files"):
                message += f"\n*Generated {len(status_data['generated_files'])} files*"
        
        return message
    
    def format_project_list(self, projects: List[Dict[str, Any]]) -> str:
        """
        Format project list for WhatsApp display.
        
        Args:
            projects: List of project dictionaries
            
        Returns:
            Formatted project list
        """
        if not projects:
            return "📂 You don't have any projects yet.\n\nUse `/new ProjectName` to create one."
        
        message = "📁 *Your Projects:*\n\n"
        
        for i, project in enumerate(projects[:10], 1):  # Show max 10 projects
            name = project.get("name", "Unnamed")
            project_id = project.get("id", "")
            description = project.get("description", "")
            
            message += f"{i}. *{name}*\n"
            if description:
                # Truncate description if too long
                desc_preview = description[:50] + "..." if len(description) > 50 else description
                message += f"   _{desc_preview}_\n"
            message += f"   ID: `{project_id}`\n\n"
        
        if len(projects) > 10:
            message += f"... and {len(projects) - 10} more projects"
        
        return message
    
    def format_error(self, error: Exception) -> str:
        """
        Format error message for WhatsApp display.
        
        Args:
            error: Exception object
            
        Returns:
            User-friendly error message
        """
        error_type = type(error).__name__
        error_message = str(error)
        
        # Create user-friendly error messages
        if "connection" in error_message.lower():
            return "❌ *Connection Error*\n\nI'm having trouble connecting to the AutoCoder service. Please try again in a moment."
        elif "timeout" in error_message.lower():
            return "⏱️ *Request Timeout*\n\nThe operation is taking longer than expected. Please check the status with `/status` in a few moments."
        elif "authorization" in error_message.lower() or "authentication" in error_message.lower():
            return "🔒 *Authorization Error*\n\nYour phone number is not authorized. Please contact the administrator."
        else:
            return f"❌ *Error*\n\nSomething went wrong: {error_message[:200]}\n\nPlease try again or type `/help` for assistance."
    
    def format_file_list(self, files: List[Dict[str, Any]]) -> str:
        """
        Format file list for WhatsApp display.
        
        Args:
            files: List of file dictionaries
            
        Returns:
            Formatted file list
        """
        if not files:
            return "📄 No files have been generated yet."
        
        message = "📄 *Generated Files:*\n\n"
        
        for file in files[:20]:  # Show max 20 files
            name = file.get("name", "unnamed")
            size = file.get("size", 0)
            url = file.get("url", "")
            
            message += f"• *{name}*"
            
            if size:
                # Format file size
                if size < 1024:
                    size_str = f"{size}B"
                elif size < 1024 * 1024:
                    size_str = f"{size / 1024:.1f}KB"
                else:
                    size_str = f"{size / (1024 * 1024):.1f}MB"
                message += f" ({size_str})"
            
            if url:
                message += f"\n  📥 {url}"
            
            message += "\n"
        
        if len(files) > 20:
            message += f"\n... and {len(files) - 20} more files"
        
        return message
    
    def format_welcome_message(self, user_name: Optional[str] = None) -> str:
        """
        Format welcome message for new users.
        
        Args:
            user_name: User's name (optional)
            
        Returns:
            Welcome message
        """
        greeting = f"Hello{' ' + user_name if user_name else ''}! " if user_name else "Hello! "
        
        message = f"{greeting}👋\n\n"
        message += "*Welcome to AutoCoder on WhatsApp!*\n\n"
        message += "I'm your AI coding assistant. I can help you:\n"
        message += "• 🚀 Create new coding projects\n"
        message += "• 💻 Generate code for any task\n"
        message += "• 🔧 Build complete applications\n"
        message += "• 📝 Write tests and documentation\n\n"
        message += "To get started, try:\n"
        message += "• `/new MyProject` - Create a new project\n"
        message += "• `/help` - See all commands\n"
        message += "• Or just describe what you want to build!\n\n"
        message += "_Example: \"Create a Python REST API with user authentication\"_"
        
        return message

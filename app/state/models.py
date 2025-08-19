"""
State models for conversation and session management
"""

from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum


class TaskStatus(str, Enum):
    """Enum for task execution status"""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class MessageRole(str, Enum):
    """Enum for message roles in conversation"""
    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"


class ConversationMessage(BaseModel):
    """Model for a single message in conversation history"""
    
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    role: MessageRole
    content: str
    metadata: Optional[Dict[str, Any]] = {}


class ProjectContext(BaseModel):
    """Model for project-specific context"""
    
    project_id: str
    project_name: str
    description: Optional[str] = None
    current_session_id: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    last_activity: datetime = Field(default_factory=datetime.utcnow)
    metadata: Dict[str, Any] = {}


class UserSession(BaseModel):
    """Model for user session state"""
    
    session_id: str
    phone_number: str
    created_at: datetime = Field(default_factory=datetime.utcnow)
    last_activity: datetime = Field(default_factory=datetime.utcnow)
    active_project: Optional[ProjectContext] = None
    conversation_history: List[ConversationMessage] = []
    context: Dict[str, Any] = {}
    
    def add_message(self, role: MessageRole, content: str, metadata: Dict[str, Any] = {}) -> None:
        """Add a message to conversation history"""
        message = ConversationMessage(
            role=role,
            content=content,
            metadata=metadata
        )
        self.conversation_history.append(message)
        self.last_activity = datetime.utcnow()
    
    def get_recent_messages(self, limit: int = 10) -> List[ConversationMessage]:
        """Get recent messages from conversation history"""
        return self.conversation_history[-limit:] if self.conversation_history else []
    
    def clear_history(self) -> None:
        """Clear conversation history"""
        self.conversation_history = []
        self.last_activity = datetime.utcnow()


class ConversationState(BaseModel):
    """Model for complete conversation state"""
    
    phone_number: str
    session: UserSession
    projects: List[ProjectContext] = []
    preferences: Dict[str, Any] = {}
    
    def get_active_project(self) -> Optional[ProjectContext]:
        """Get the active project"""
        return self.session.active_project
    
    def set_active_project(self, project: ProjectContext) -> None:
        """Set the active project"""
        self.session.active_project = project
        if project not in self.projects:
            self.projects.append(project)
    
    def get_project_by_id(self, project_id: str) -> Optional[ProjectContext]:
        """Get a project by ID"""
        for project in self.projects:
            if project.project_id == project_id:
                return project
        return None


class TaskExecution(BaseModel):
    """Model for task execution state"""
    
    task_id: str
    project_id: str
    session_id: str
    description: str
    status: TaskStatus = TaskStatus.PENDING
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    generated_files: List[str] = []
    logs: List[str] = []
    
    def start(self) -> None:
        """Mark task as started"""
        self.status = TaskStatus.IN_PROGRESS
        self.started_at = datetime.utcnow()
    
    def complete(self, result: Dict[str, Any]) -> None:
        """Mark task as completed"""
        self.status = TaskStatus.COMPLETED
        self.completed_at = datetime.utcnow()
        self.result = result
    
    def fail(self, error: str) -> None:
        """Mark task as failed"""
        self.status = TaskStatus.FAILED
        self.completed_at = datetime.utcnow()
        self.error = error
    
    def add_log(self, message: str) -> None:
        """Add a log message"""
        timestamp = datetime.utcnow().isoformat()
        self.logs.append(f"[{timestamp}] {message}")
    
    def add_file(self, file_path: str) -> None:
        """Add a generated file"""
        if file_path not in self.generated_files:
            self.generated_files.append(file_path)

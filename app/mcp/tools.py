"""
LangChain tool wrappers for AutoCoder MCP server tools.
"""

from typing import Dict, Any, List, Optional, Type
from pydantic import BaseModel, Field
from langchain.tools import BaseTool
from langchain.callbacks.manager import AsyncCallbackManagerForToolRun
from app.mcp.client import AutoCoderMCPClient
from app.utils.logger import get_logger

logger = get_logger(__name__)


# Pydantic models for tool inputs
class CreateProjectInput(BaseModel):
    """Input for creating a new project."""
    name: str = Field(description="Name of the project")
    description: str = Field(default="", description="Description of the project")


class ExecuteCodingTaskInput(BaseModel):
    """Input for executing a coding task."""
    project_id: str = Field(description="ID of the project")
    task_description: str = Field(description="Description of the task to execute")


class GetSessionDetailsInput(BaseModel):
    """Input for getting session details."""
    session_id: str = Field(description="ID of the session")


class GetSessionFilesInput(BaseModel):
    """Input for getting session files."""
    session_id: str = Field(description="ID of the session")


# LangChain Tool Implementations
class CreateProjectTool(BaseTool):
    """Tool for creating a new project in AutoCoder."""
    
    name = "create_project"
    description = "Create a new coding project with AutoCoder"
    args_schema: Type[BaseModel] = CreateProjectInput
    return_direct = False
    
    mcp_client: Optional[AutoCoderMCPClient] = None
    
    async def _arun(
        self,
        name: str,
        description: str = "",
        run_manager: Optional[AsyncCallbackManagerForToolRun] = None
    ) -> str:
        """Execute the tool asynchronously."""
        try:
            if not self.mcp_client:
                self.mcp_client = AutoCoderMCPClient()
            
            async with self.mcp_client as client:
                result = await client.create_project(name, description)
                
                if result.get("success"):
                    project_id = result.get("project_id", "unknown")
                    return f"Successfully created project '{name}' with ID: {project_id}"
                else:
                    error = result.get("error", "Unknown error")
                    return f"Failed to create project: {error}"
                    
        except Exception as e:
            logger.error(f"Error creating project: {e}")
            return f"Error creating project: {str(e)}"
    
    def _run(self, *args, **kwargs):
        """Synchronous execution not supported."""
        raise NotImplementedError("This tool only supports async execution")


class ListProjectsTool(BaseTool):
    """Tool for listing all projects."""
    
    name = "list_projects"
    description = "List all available coding projects"
    return_direct = False
    
    mcp_client: Optional[AutoCoderMCPClient] = None
    
    async def _arun(
        self,
        run_manager: Optional[AsyncCallbackManagerForToolRun] = None
    ) -> str:
        """Execute the tool asynchronously."""
        try:
            if not self.mcp_client:
                self.mcp_client = AutoCoderMCPClient()
            
            async with self.mcp_client as client:
                projects = await client.list_projects()
                
                if not projects:
                    return "No projects found."
                
                project_list = []
                for project in projects:
                    proj_id = project.get("id", "unknown")
                    proj_name = project.get("name", "Unnamed")
                    proj_desc = project.get("description", "No description")
                    project_list.append(f"- {proj_name} (ID: {proj_id}): {proj_desc}")
                
                return "Available projects:\n" + "\n".join(project_list)
                
        except Exception as e:
            logger.error(f"Error listing projects: {e}")
            return f"Error listing projects: {str(e)}"
    
    def _run(self, *args, **kwargs):
        """Synchronous execution not supported."""
        raise NotImplementedError("This tool only supports async execution")


class ExecuteCodingTaskTool(BaseTool):
    """Tool for executing a coding task on a project."""
    
    name = "execute_coding_task"
    description = "Execute a coding task for a specific project"
    args_schema: Type[BaseModel] = ExecuteCodingTaskInput
    return_direct = False
    
    mcp_client: Optional[AutoCoderMCPClient] = None
    
    async def _arun(
        self,
        project_id: str,
        task_description: str,
        run_manager: Optional[AsyncCallbackManagerForToolRun] = None
    ) -> str:
        """Execute the tool asynchronously."""
        try:
            if not self.mcp_client:
                self.mcp_client = AutoCoderMCPClient()
            
            async with self.mcp_client as client:
                result = await client.execute_coding_task(project_id, task_description)
                
                if result.get("success"):
                    session_id = result.get("session_id", "unknown")
                    status = result.get("status", "started")
                    return (f"Task execution started for project {project_id}.\n"
                           f"Session ID: {session_id}\n"
                           f"Status: {status}\n"
                           f"Use /status command to check progress.")
                else:
                    error = result.get("error", "Unknown error")
                    return f"Failed to execute task: {error}"
                    
        except Exception as e:
            logger.error(f"Error executing task: {e}")
            return f"Error executing task: {str(e)}"
    
    def _run(self, *args, **kwargs):
        """Synchronous execution not supported."""
        raise NotImplementedError("This tool only supports async execution")


class GetSessionDetailsTool(BaseTool):
    """Tool for getting session details."""
    
    name = "get_session_details"
    description = "Get details about a coding session including status and progress"
    args_schema: Type[BaseModel] = GetSessionDetailsInput
    return_direct = False
    
    mcp_client: Optional[AutoCoderMCPClient] = None
    
    async def _arun(
        self,
        session_id: str,
        run_manager: Optional[AsyncCallbackManagerForToolRun] = None
    ) -> str:
        """Execute the tool asynchronously."""
        try:
            if not self.mcp_client:
                self.mcp_client = AutoCoderMCPClient()
            
            async with self.mcp_client as client:
                details = await client.get_session_details(session_id)
                
                status = details.get("status", "unknown")
                progress = details.get("progress", 0)
                project_name = details.get("project_name", "Unknown")
                task = details.get("task_description", "No description")
                logs = details.get("recent_logs", [])
                
                response = (f"Session Details for {session_id}:\n"
                          f"Project: {project_name}\n"
                          f"Task: {task}\n"
                          f"Status: {status}\n"
                          f"Progress: {progress}%\n")
                
                if logs:
                    response += "\nRecent logs:\n"
                    for log in logs[-5:]:  # Show last 5 log entries
                        response += f"  - {log}\n"
                
                return response
                
        except Exception as e:
            logger.error(f"Error getting session details: {e}")
            return f"Error getting session details: {str(e)}"
    
    def _run(self, *args, **kwargs):
        """Synchronous execution not supported."""
        raise NotImplementedError("This tool only supports async execution")


class GetSessionFilesTool(BaseTool):
    """Tool for getting files from a session."""
    
    name = "get_session_files"
    description = "Get list of files generated in a coding session"
    args_schema: Type[BaseModel] = GetSessionFilesInput
    return_direct = False
    
    mcp_client: Optional[AutoCoderMCPClient] = None
    
    async def _arun(
        self,
        session_id: str,
        run_manager: Optional[AsyncCallbackManagerForToolRun] = None
    ) -> str:
        """Execute the tool asynchronously."""
        try:
            if not self.mcp_client:
                self.mcp_client = AutoCoderMCPClient()
            
            async with self.mcp_client as client:
                files = await client.get_session_files(session_id)
                
                if not files:
                    return f"No files found for session {session_id}"
                
                response = f"Files generated in session {session_id}:\n"
                for file in files:
                    file_name = file.get("name", "unknown")
                    file_size = file.get("size", 0)
                    file_url = file.get("url", "")
                    
                    response += f"- {file_name} ({file_size} bytes)"
                    if file_url:
                        response += f"\n  URL: {file_url}"
                    response += "\n"
                
                return response
                
        except Exception as e:
            logger.error(f"Error getting session files: {e}")
            return f"Error getting session files: {str(e)}"
    
    def _run(self, *args, **kwargs):
        """Synchronous execution not supported."""
        raise NotImplementedError("This tool only supports async execution")


def get_mcp_tools() -> List[BaseTool]:
    """
    Get all available MCP tools for LangChain.
    
    Returns:
        List of LangChain tools.
    """
    return [
        CreateProjectTool(),
        ListProjectsTool(),
        ExecuteCodingTaskTool(),
        GetSessionDetailsTool(),
        GetSessionFilesTool()
    ]


def get_mcp_tool_by_name(name: str) -> Optional[BaseTool]:
    """
    Get a specific MCP tool by name.
    
    Args:
        name: Name of the tool.
        
    Returns:
        The tool instance or None if not found.
    """
    tools = {
        "create_project": CreateProjectTool,
        "list_projects": ListProjectsTool,
        "execute_coding_task": ExecuteCodingTaskTool,
        "get_session_details": GetSessionDetailsTool,
        "get_session_files": GetSessionFilesTool
    }
    
    tool_class = tools.get(name)
    if tool_class:
        return tool_class()
    return None

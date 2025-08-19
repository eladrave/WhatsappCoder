"""
FastMCP 2.0 client for connecting to AutoCoder MCP server.
"""

import os
from typing import Optional, Dict, Any, List
from fastmcp import Client
from app.utils.logger import get_logger
from app.utils.config import get_settings

logger = get_logger(__name__)
settings = get_settings()


class AutoCoderMCPClient:
    """Client for interacting with AutoCoder MCP server using FastMCP 2.0."""
    
    def __init__(self, server_url: Optional[str] = None):
        """
        Initialize the MCP client.
        
        Args:
            server_url: URL of the AutoCoder MCP server. 
                       Defaults to AUTOCODER_MCP_URL from settings.
        """
        self.server_url = server_url or os.getenv("AUTOCODER_MCP_URL", "http://localhost:5000")
        self.client: Optional[Client] = None
        logger.info(f"AutoCoderMCPClient initialized with server URL: {self.server_url}")
    
    async def connect(self) -> None:
        """Establish connection to the MCP server."""
        try:
            # FastMCP 2.0 uses context manager pattern
            # Connection will be established when entering context
            logger.info(f"Preparing to connect to MCP server at {self.server_url}")
        except Exception as e:
            logger.error(f"Failed to prepare MCP client: {e}")
            raise
    
    async def __aenter__(self):
        """Async context manager entry."""
        try:
            # Create client with server URL
            self.client = Client(self.server_url)
            # Enter the client context
            await self.client.__aenter__()
            logger.info("Successfully connected to MCP server")
            
            # List available tools for debugging
            tools = await self.list_available_tools()
            logger.info(f"Available MCP tools: {[t.get('name') for t in tools]}")
            
            return self
        except Exception as e:
            logger.error(f"Failed to connect to MCP server: {e}")
            raise
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        if self.client:
            await self.client.__aexit__(exc_type, exc_val, exc_tb)
            logger.info("Disconnected from MCP server")
    
    async def list_available_tools(self) -> List[Dict[str, Any]]:
        """
        List all available tools from the MCP server.
        
        Returns:
            List of tool definitions.
        """
        if not self.client:
            raise RuntimeError("Client not connected. Use async with context manager.")
        
        try:
            # Get list of available tools
            tools = await self.client.list_tools()
            return tools
        except Exception as e:
            logger.error(f"Failed to list tools: {e}")
            return []
    
    async def call_tool(self, tool_name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """
        Call a tool on the MCP server.
        
        Args:
            tool_name: Name of the tool to call.
            arguments: Arguments to pass to the tool.
            
        Returns:
            Result from the tool execution.
        """
        if not self.client:
            raise RuntimeError("Client not connected. Use async with context manager.")
        
        try:
            logger.info(f"Calling MCP tool: {tool_name} with args: {arguments}")
            result = await self.client.call_tool(tool_name, arguments)
            logger.info(f"Tool {tool_name} completed successfully")
            return result
        except Exception as e:
            logger.error(f"Failed to call tool {tool_name}: {e}")
            raise
    
    async def create_project(self, name: str, description: str = "") -> Dict[str, Any]:
        """
        Create a new project using the MCP server.
        
        Args:
            name: Project name.
            description: Project description.
            
        Returns:
            Project creation result.
        """
        return await self.call_tool("create_project", {
            "name": name,
            "description": description
        })
    
    async def list_projects(self) -> List[Dict[str, Any]]:
        """
        List all projects.
        
        Returns:
            List of projects.
        """
        result = await self.call_tool("list_projects", {})
        return result.get("projects", [])
    
    async def execute_coding_task(self, project_id: str, task_description: str) -> Dict[str, Any]:
        """
        Execute a coding task for a project.
        
        Args:
            project_id: ID of the project.
            task_description: Description of the task to execute.
            
        Returns:
            Task execution result.
        """
        return await self.call_tool("execute_coding_task", {
            "project_id": project_id,
            "task_description": task_description
        })
    
    async def get_session_details(self, session_id: str) -> Dict[str, Any]:
        """
        Get details of a coding session.
        
        Args:
            session_id: ID of the session.
            
        Returns:
            Session details.
        """
        return await self.call_tool("get_session_details", {
            "session_id": session_id
        })
    
    async def get_session_files(self, session_id: str) -> List[Dict[str, Any]]:
        """
        Get files generated in a session.
        
        Args:
            session_id: ID of the session.
            
        Returns:
            List of generated files.
        """
        result = await self.call_tool("get_session_files", {
            "session_id": session_id
        })
        return result.get("files", [])


# Singleton instance management
_client_instance: Optional[AutoCoderMCPClient] = None


def get_mcp_client() -> AutoCoderMCPClient:
    """
    Get the singleton MCP client instance.
    
    Returns:
        AutoCoderMCPClient instance.
    """
    global _client_instance
    if _client_instance is None:
        _client_instance = AutoCoderMCPClient()
    return _client_instance

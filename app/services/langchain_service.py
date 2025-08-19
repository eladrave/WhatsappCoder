"""
LangChain service for interacting with AutoCoder MCP server
"""

from typing import Dict, Any, List, Optional
from langchain.agents import AgentExecutor, create_react_agent
from langchain.memory import ConversationBufferMemory
from langchain.prompts import PromptTemplate
from langchain_openai import ChatOpenAI
from app.mcp.client import AutoCoderMCPClient
from app.mcp.tools import get_mcp_tools
from app.utils.config import get_settings
from app.utils.logger import get_logger
from app.state.models import ConversationState
import os

logger = get_logger(__name__)
settings = get_settings()


class LangChainService:
    """Service for interacting with LangChain and AutoCoder MCP"""
    
    def __init__(self):
        # Initialize MCP client
        self.mcp_client = AutoCoderMCPClient()
        
        # Initialize LangChain components
        self.llm = self._initialize_llm()
        self.tools = get_mcp_tools()
        self.memory = ConversationBufferMemory(
            memory_key="chat_history",
            return_messages=True
        )
        self.agent = None
        self.agent_executor = None
        
        # Initialize agent if LLM is available
        if self.llm:
            self._initialize_agent()
        
        logger.info("LangChainService initialized with FastMCP client")
    
    def _initialize_llm(self):
        """Initialize the language model."""
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            logger.warning("OPENAI_API_KEY not set. LangChain agent will not be available.")
            return None
        
        try:
            return ChatOpenAI(
                temperature=0.7,
                model="gpt-4",
                api_key=api_key
            )
        except Exception as e:
            logger.error(f"Failed to initialize LLM: {e}")
            return None
    
    def _initialize_agent(self):
        """Initialize the LangChain agent with MCP tools."""
        if not self.llm:
            return
        
        # Create a prompt template for the agent
        prompt = PromptTemplate.from_template(
            """You are a helpful AI assistant integrated with AutoCoder, helping users create and manage coding projects via WhatsApp.
            
            You have access to the following tools:
            {tools}
            
            Use the following format:
            
            Thought: You should always think about what to do
            Action: the action to take, should be one of [{tool_names}]
            Action Input: the input to the action
            Observation: the result of the action
            ... (this Thought/Action/Action Input/Observation can repeat N times)
            Thought: I now know the final answer
            Final Answer: the final answer to the original input question
            
            Begin!
            
            Previous conversation history:
            {chat_history}
            
            Question: {input}
            Thought: {agent_scratchpad}
            """
        )
        
        try:
            # Create the agent
            self.agent = create_react_agent(
                llm=self.llm,
                tools=self.tools,
                prompt=prompt
            )
            
            # Create the agent executor
            self.agent_executor = AgentExecutor(
                agent=self.agent,
                tools=self.tools,
                memory=self.memory,
                verbose=True,
                handle_parsing_errors=True,
                max_iterations=5
            )
            
            logger.info("LangChain agent initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize agent: {e}")
            self.agent_executor = None
    
    async def process_message(self, message: str, conversation: Dict[str, Any]) -> str:
        """
        Process a natural language message using LangChain and MCP tools.
        
        Args:
            message: User's message
            conversation: Conversation state
            
        Returns:
            Response from the LangChain agent
        """
        logger.info(f"Processing message with LangChain: {message[:50]}...")
        
        # If agent is available, use it for processing
        if self.agent_executor:
            try:
                # Run the agent with the user's message
                response = await self.agent_executor.ainvoke({
                    "input": message
                })
                return response.get("output", "I'm processing your request. Please wait...")
            except Exception as e:
                logger.error(f"Error processing with agent: {e}")
                # Fall back to basic processing
        
        # Fallback to basic intent detection if agent is not available
        if "create" in message.lower() and "project" in message.lower():
            return "It looks like you want to create a project. You can use the `/new` command or tell me the project name and I'll create it for you."
        elif "list" in message.lower() and "project" in message.lower():
            return "To see your projects, use the `/list` command."
        elif "status" in message.lower() or "update" in message.lower():
            return "I can check the status for you. Use the `/status` command to get the latest update."
        elif "hello" in message.lower() or "hi" in message.lower():
            return "Hello! I'm your AI coding assistant. I can help you create projects, execute coding tasks, and check on their progress. How can I help you today?"
        else:
            return f"I've received your request: \"{message}\". You can use commands like `/new` to create a project, `/list` to see projects, or `/status` to check progress."
    
    async def create_project(self, project_name: str, conversation: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create a new project using the AutoCoder MCP tool.
        
        Args:
            project_name: Name for the new project
            conversation: Conversation state
            
        Returns:
            Result of the project creation
        """
        logger.info(f"Creating project: {project_name}")
        
        try:
            async with self.mcp_client as client:
                result = await client.create_project(
                    name=project_name,
                    description=f"Project created via WhatsApp by user {conversation.get('phone_number', 'unknown')}"
                )
                
                # Store project info in conversation state if successful
                if result.get("success"):
                    conversation["current_project_id"] = result.get("project_id")
                    conversation["current_project_name"] = project_name
                
                return result
        except Exception as e:
            logger.error(f"Failed to create project: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def list_projects(self, conversation: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        List all projects for the user.
        
        Args:
            conversation: Conversation state
            
        Returns:
            List of projects
        """
        logger.info("Listing projects")
        
        try:
            async with self.mcp_client as client:
                projects = await client.list_projects()
                return projects
        except Exception as e:
            logger.error(f"Failed to list projects: {e}")
            return []
    
    async def execute_task(self, project_id: str, task_description: str, conversation: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute a coding task for a project.
        
        Args:
            project_id: Project ID
            task_description: Description of the task
            conversation: Conversation state
            
        Returns:
            Task execution result
        """
        logger.info(f"Executing task for project {project_id}: {task_description}")
        
        try:
            async with self.mcp_client as client:
                result = await client.execute_coding_task(project_id, task_description)
                
                # Store session info in conversation state
                if result.get("success"):
                    conversation["current_session_id"] = result.get("session_id")
                
                return result
        except Exception as e:
            logger.error(f"Failed to execute task: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def get_task_status(self, session_id: str, conversation: Dict[str, Any]) -> Dict[str, Any]:
        """
        Get the status of a coding session.
        
        Args:
            session_id: Session ID
            conversation: Conversation state
            
        Returns:
            Session status information
        """
        logger.info(f"Getting status for session: {session_id}")
        
        try:
            async with self.mcp_client as client:
                details = await client.get_session_details(session_id)
                return details
        except Exception as e:
            logger.error(f"Failed to get session status: {e}")
            return {
                "status": "error",
                "error": str(e)
            }
    
    async def get_project_files(self, session_id: str, conversation: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Get the generated files for a session.
        
        Args:
            session_id: Session ID
            conversation: Conversation state
            
        Returns:
            List of generated files
        """
        logger.info(f"Getting files for session: {session_id}")
        
        try:
            async with self.mcp_client as client:
                files = await client.get_session_files(session_id)
                return files
        except Exception as e:
            logger.error(f"Failed to get session files: {e}")
            return []

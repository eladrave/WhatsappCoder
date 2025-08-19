#!/usr/bin/env python3
"""
Test script for FastMCP 2.0 integration with AutoCoder server.
Run this to verify the MCP client connection and basic operations.
"""

import asyncio
import os
import sys
from pathlib import Path

# Add the app directory to the Python path
sys.path.insert(0, str(Path(__file__).parent))

from app.mcp.client import AutoCoderMCPClient
from app.mcp.tools import get_mcp_tools
from app.services.langchain_service import LangChainService
from app.utils.logger import get_logger

logger = get_logger(__name__)


async def test_mcp_client():
    """Test the FastMCP client connection and basic operations."""
    print("\n" + "="*60)
    print("Testing FastMCP 2.0 Client Integration")
    print("="*60 + "\n")
    
    # Test 1: Initialize and connect to MCP server
    print("Test 1: Connecting to MCP server...")
    client = AutoCoderMCPClient()
    
    try:
        async with client as mcp:
            print("✓ Successfully connected to MCP server")
            
            # Test 2: List available tools
            print("\nTest 2: Listing available tools...")
            tools = await mcp.list_available_tools()
            if tools:
                print(f"✓ Found {len(tools)} tools:")
                for tool in tools:
                    print(f"  - {tool.get('name', 'unknown')}")
            else:
                print("⚠ No tools found or server not responding")
            
            # Test 3: Create a test project
            print("\nTest 3: Creating a test project...")
            project_result = await mcp.create_project(
                name="TestProject",
                description="Test project from MCP integration test"
            )
            
            if project_result.get("success"):
                project_id = project_result.get("project_id")
                print(f"✓ Project created successfully. ID: {project_id}")
                
                # Test 4: List projects
                print("\nTest 4: Listing projects...")
                projects = await mcp.list_projects()
                print(f"✓ Found {len(projects)} projects")
                for proj in projects[:3]:  # Show first 3 projects
                    print(f"  - {proj.get('name', 'unknown')} (ID: {proj.get('id', 'unknown')})")
                
                # Test 5: Execute a coding task
                if project_id:
                    print("\nTest 5: Executing a coding task...")
                    task_result = await mcp.execute_coding_task(
                        project_id=project_id,
                        task_description="Create a simple hello world Python script"
                    )
                    
                    if task_result.get("success"):
                        session_id = task_result.get("session_id")
                        print(f"✓ Task execution started. Session ID: {session_id}")
                        
                        # Test 6: Get session details
                        if session_id:
                            print("\nTest 6: Getting session details...")
                            await asyncio.sleep(2)  # Wait a bit for task to start
                            
                            details = await mcp.get_session_details(session_id)
                            status = details.get("status", "unknown")
                            progress = details.get("progress", 0)
                            print(f"✓ Session status: {status} ({progress}% complete)")
                            
                            # Test 7: Get session files
                            print("\nTest 7: Getting session files...")
                            files = await mcp.get_session_files(session_id)
                            if files:
                                print(f"✓ Found {len(files)} generated files:")
                                for file in files:
                                    print(f"  - {file.get('name', 'unknown')}")
                            else:
                                print("⚠ No files generated yet")
                    else:
                        print(f"✗ Failed to execute task: {task_result.get('error', 'Unknown error')}")
            else:
                print(f"✗ Failed to create project: {project_result.get('error', 'Unknown error')}")
                
    except Exception as e:
        print(f"\n✗ Error during testing: {e}")
        return False
    
    print("\n" + "="*60)
    print("MCP Client Integration Test Complete")
    print("="*60 + "\n")
    return True


async def test_langchain_tools():
    """Test LangChain tool wrappers."""
    print("\n" + "="*60)
    print("Testing LangChain MCP Tools")
    print("="*60 + "\n")
    
    tools = get_mcp_tools()
    print(f"Available LangChain tools: {[tool.name for tool in tools]}")
    
    # Test the create project tool
    print("\nTesting CreateProjectTool...")
    create_tool = tools[0]  # CreateProjectTool
    try:
        result = await create_tool._arun(
            name="LangChainTestProject",
            description="Test project from LangChain tool"
        )
        print(f"Result: {result}")
    except Exception as e:
        print(f"Error: {e}")
    
    print("\n" + "="*60)
    print("LangChain Tools Test Complete")
    print("="*60 + "\n")


async def test_langchain_service():
    """Test the complete LangChain service integration."""
    print("\n" + "="*60)
    print("Testing LangChain Service Integration")
    print("="*60 + "\n")
    
    # Initialize the service
    service = LangChainService()
    
    # Test conversation state
    conversation = {
        "phone_number": "+1234567890",
        "user_name": "Test User"
    }
    
    # Test message processing
    print("Testing message processing...")
    
    test_messages = [
        "Hello",
        "I want to create a new project called MyApp",
        "Show me my projects",
        "What's the status of my current task?"
    ]
    
    for message in test_messages:
        print(f"\nUser: {message}")
        response = await service.process_message(message, conversation)
        print(f"Bot: {response[:200]}...")  # Show first 200 chars
    
    # Test direct project creation
    print("\n\nTesting direct project creation...")
    result = await service.create_project("DirectTestProject", conversation)
    if result.get("success"):
        print(f"✓ Project created: {result.get('project_id')}")
    else:
        print(f"✗ Failed to create project: {result.get('error')}")
    
    print("\n" + "="*60)
    print("LangChain Service Test Complete")
    print("="*60 + "\n")


async def main():
    """Run all integration tests."""
    print("\n🚀 Starting MCP Integration Tests")
    print("Make sure the AutoCoder MCP server is running on localhost:5000")
    print("-" * 60)
    
    # Check environment
    mcp_url = os.getenv("AUTOCODER_MCP_URL", "http://localhost:5000")
    openai_key = os.getenv("OPENAI_API_KEY")
    
    print(f"MCP Server URL: {mcp_url}")
    print(f"OpenAI API Key: {'Set' if openai_key else 'Not set (LangChain agent will be disabled)'}")
    print("-" * 60)
    
    try:
        # Run tests
        await test_mcp_client()
        await test_langchain_tools()
        await test_langchain_service()
        
        print("\n✅ All tests completed!")
        
    except KeyboardInterrupt:
        print("\n\n⚠ Tests interrupted by user")
    except Exception as e:
        print(f"\n\n❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())

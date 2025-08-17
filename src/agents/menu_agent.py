import os
import asyncio
from typing import Dict, Any, List
from dotenv import load_dotenv

from agents import Agent, Runner, OpenAIChatCompletionsModel
from ..client.delta_client import DeltaMenuClient
from ..tools.menu_tools import MenuTools
from ..tools.debug_tools import DebugTools

# Load environment variables
load_dotenv()


class MenuAgent:
    """Main Delta menu chat agent using OpenAI Agents SDK with Kimi"""
    
    def __init__(self):
        self.client = DeltaMenuClient()
        self.menu_tools = MenuTools(self.client)
        self.debug_tools = DebugTools(self.client)
        
        # Get Kimi configuration from environment
        self.kimi_api_key = os.getenv("KIMI_API_KEY")
        self.kimi_base_url = os.getenv("KIMI_BASE_URL")
        
        if not self.kimi_api_key:
            raise ValueError("KIMI_API_KEY not found in environment variables")
        
        # Create Kimi model instance
        kimi_model = OpenAIChatCompletionsModel(
            model="moonshot-v1-8k",
            api_key=self.kimi_api_key,
            base_url=self.kimi_base_url,
        )
        
        # Create the main agent
        self.agent = Agent(
            name="Delta Menu Assistant",
            instructions=self._get_system_instructions(),
            model=kimi_model,
            tools=[
                self.menu_tools.get_menu_by_flight,
                self.menu_tools.check_menu_availability,
                self.debug_tools.validate_api_health,
                self.debug_tools.validate_flight_request,
                self.debug_tools.trace_api_call,
                self.debug_tools.diagnose_error
            ]
        )
    
    def _get_system_instructions(self) -> str:
        """System instructions for the agent"""
        return """You are a helpful Delta Airlines flight menu assistant. Your role is to help users understand what meals and beverages are served on Delta flights across different cabin classes.

Key capabilities:
- Query flight menus by flight number, date, and departure airport
- Check menu availability before fetching actual menu data
- Provide detailed information about specific cabin classes (First, Business, Economy)
- Compare menus across different cabin classes
- Help troubleshoot API issues and validate requests
- Provide clear, structured responses

Guidelines:
1. Always use the provided tools to fetch accurate data
2. Use availability check when users want to verify menu availability
3. Format responses in a clear, human-readable way
4. Include key details like flight info, cabin class, and menu items
5. When troubleshooting, use debug tools to help identify issues
6. If no menu data is found, check availability first and explain possible reasons
7. Be concise but comprehensive in your responses

Response format:
- Always start with flight information
- Organize menu items by category (appetizers, entrees, desserts, beverages)
- Highlight special dietary options when mentioned
- Include service times if available
- Note any special remarks or service details
- Indicate when menus are not available for specific menu_services

Example queries you can handle:
- "What's on the menu for DL30 tomorrow?"
- "Check if DL30 has menus available on 2025-08-16"
- "Show me business class meals on DL123 from Atlanta to LAX on 2025-08-15"
- "Compare first and business class menus on DL30"
- "I'm getting an error with my request, can you help debug?"
"""
    
    async def process_message(self, message: str, debug: bool = False) -> Dict[str, Any]:
        """
        Process a user message and return a structured response
        
        Args:
            message: User's message/question
            debug: Whether to include debug information
            
        Returns:
            Structured response with conversation context
        """
        try:
            # Run the agent
            result = await Runner.run(self.agent, message)
            
            # Format the response
            response = {
                "success": True,
                "response": result.messages[-1].content if result.messages else "No response generated",
                "debug_info": None
            }
            
            if debug:
                response["debug_info"] = {
                    "tools_used": [tool.name for tool in result.tools_used],
                    "messages": [msg.content for msg in result.messages],
                    "raw_response": str(result)
                }
            
            return response
            
        except Exception as e:
            return {
                "success": False,
                "response": f"I encountered an error: {str(e)}",
                "debug_info": {"error": str(e)} if debug else None
            }
    
    async def process_conversation(self, messages: List[Dict[str, str]], debug: bool = False) -> Dict[str, Any]:
        """
        Process a conversation with multiple messages
        
        Args:
            messages: List of message dictionaries with 'role' and 'content'
            debug: Whether to include debug information
            
        Returns:
            Structured response with conversation context
        """
        try:
            # Build conversation context
            conversation = "\n".join([f"{msg['role']}: {msg['content']}" for msg in messages])
            
            result = await Runner.run(self.agent, conversation)
            
            response = {
                "success": True,
                "response": result.messages[-1].content if result.messages else "No response generated",
                "debug_info": None
            }
            
            if debug:
                response["debug_info"] = {
                    "tools_used": [tool.name for tool in result.tools_used],
                    "conversation_context": conversation
                }
            
            return response
            
        except Exception as e:
            return {
                "success": False,
                "response": f"I encountered an error: {str(e)}",
                "debug_info": {"error": str(e)} if debug else None
            }
    
    async def close(self):
        """Clean up resources"""
        await self.client.close()


class SimpleMenuAgent:
    """Simplified agent for quick queries without async"""
    
    def __init__(self):
        self.client = DeltaMenuClient()
        self.menu_tools = MenuTools(self.client)
    
    async def get_menu_by_flight_sync(self, departure_date: str, flight_number: int, **kwargs) -> Dict[str, Any]:
        """Synchronous wrapper for menu queries"""
        result = await self.menu_tools.get_menu_by_flight(
            departure_date=departure_date,
            flight_number=flight_number,
            **kwargs
        )
        return result
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        asyncio.create_task(self.client.close())
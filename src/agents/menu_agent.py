import os
import asyncio
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
from dotenv import load_dotenv

from agents import Agent, Runner, OpenAIChatCompletionsModel
from openai import AsyncOpenAI

from ..client.delta_client import DeltaMenuClient
from ..tools.menu_tools import MenuTools
from ..tools.debug_tools import DebugTools
from ..utils.logging_config import setup_logging, get_logger

# Setup logging
setup_logging(log_file='gradio_app.log')
logger = get_logger(__name__)

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
        self.kimi_base_url = os.getenv("KIMI_BASE_URL", "https://api.moonshot.ai/v1")
        
        if not self.kimi_api_key:
            raise ValueError("KIMI_API_KEY not found in environment variables")
        
        # Configure OpenAI client for Kimi
        kimi_client = AsyncOpenAI(
            api_key=self.kimi_api_key,
            base_url=self.kimi_base_url
        )

        # Create Kimi model instance
        kimi_model = OpenAIChatCompletionsModel(
            model="moonshot-v1-32k",
            openai_client=kimi_client,
        )
        
        # Create the main agent with tracing enabled
        self.agent = Agent(
            name="Delta Menu Assistant",
            instructions=self._get_system_instructions(),
            model=kimi_model,
            tools=[
                self.menu_tools.get_menu_by_flight_tool()
            ]
        )
        logger.info("MenuAgent initialized successfully")
        logger.info(self.agent)

    
    def _get_system_instructions(self) -> str:
        """System instructions for the agent"""
        current_date = datetime.now().strftime("%Y-%m-%d")
        return f"""You are a helpful Delta Airlines flight menu assistant. Your role is to help users understand what meals and beverages are served on Delta flights across different cabin classes.
        
Current date:  {current_date}

When users ask about "today", "tomorrow", or relative dates, use this current date as reference.
- Today: {current_date}

Key capabilities:
- Query flight menus by flight number, date, and departure airport
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
6. If no menu data is found, pleasantly inform the user
7. Be concise but comprehensive in your responses

Response format:
- Always start with flight information

Example queries you can handle:
<example>
user: "What's on the menu for DL30 tomorrow?"
assistant: I'm going to use the "get_menu_by_flight" tool to find out the menu for DL30 on 2025-08-15.
Once I get the response, I'll summarize the menu services, menus and menu items for each cabin classes available.
</example>

<example>
user: "Show me business class meals on DL123 from Atlanta to LAX on 2025-08-15"
assistant: I'll use the "get_menu_by_flight" tool to retrieve the menu for flight DL123 on 2025-08-15 departing from Atlanta (ATL).
After getting the response, I'll summarize only the business class menu service, menus and menu items.
</example>

<example>
user: "Compare first and business class menus on DL30"
assistant: I'll use the "get_menu_by_flight" tool to get the menu for DL30 on 2025-08-15 from ATL.
Then, I'll compare the first and business class menu services, menus and menu items and summarise them.
</example>

<example>
user: "Is there a vegan option in economy class on DL30 from ATL to LAX on 2025-08-15?"
assistant: I'll use the "get_menu_by_flight" tool to find the menu for DL30 on 2025-08-15 from ATL.
Then, I'll check the economy class menu for vegan options and summarize them.
</example>
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
                "response": result.final_output or "No response generated",
                "debug_info": None
            }
            
            if debug:
                response["debug_info"] = {
                    "raw_response": str(result)
                }
            
            return response
            
        except Exception as e:
            logger.error(e)
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
                "response": result.final_output or "No response generated",
                "debug_info": None
            }
            
            if debug:
                response["debug_info"] = {
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
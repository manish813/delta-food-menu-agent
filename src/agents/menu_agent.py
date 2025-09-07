import os
import asyncio
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
from dotenv import load_dotenv

from agents import Agent, Runner, OpenAIChatCompletionsModel, ModelSettings
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
        logger.info("Initializing MenuAgent...")
        
        self.client = DeltaMenuClient()
        self.menu_tools = MenuTools(self.client)
        self.debug_tools = DebugTools(self.client)
        logger.debug("Client and tools initialized")
        
        # Get Kimi configuration from environment
        self.kimi_api_key = os.getenv("KIMI_API_KEY")
        self.kimi_base_url = os.getenv("KIMI_BASE_URL", "https://api.moonshot.ai/v1")
        
        if not self.kimi_api_key:
            logger.error("KIMI_API_KEY not found in environment variables")
            raise ValueError("KIMI_API_KEY not found in environment variables")
        
        # Configure OpenAI client for Kimi
        kimi_client = AsyncOpenAI(
            api_key=self.kimi_api_key,
            base_url=self.kimi_base_url
        )
        logger.debug("Kimi client configured")

        # Create Kimi model instance
        kimi_model = OpenAIChatCompletionsModel(
            model="kimi-k2-0905-preview",
            openai_client=kimi_client,
        )
        logger.debug("Kimi model instance created")
        
        # Create the main agent with tracing enabled
        self.agent = Agent(
            name="Delta Menu Assistant",
            instructions=self._get_system_instructions(),
            model=kimi_model,
            model_settings=ModelSettings(temperature=0.6),
            tools=[
                self.menu_tools.get_menu_by_flight_tool(),
                self.menu_tools.check_menu_availability_tool()
            ]
        )
        logger.info("MenuAgent initialized successfully with 2 tools")

    
    def _get_system_instructions(self) -> str:
        """System instructions for the agent"""
        current_date = datetime.now().strftime("%Y-%m-%d")
        return f"""You are a helpful Delta Airlines flight menu assistant. Your goal is to help users understand what meals and beverages are served on Delta flights across different cabin classes.
        
Current date:  {current_date}

When users ask about "today", "tomorrow", or relative dates, use this current date as reference.
- Today: {current_date}


# Instructions:
- Always greet the user at the start of the conversation with "Hi, you've reached Delta Flight Menu agent, how can I help you?"
- NEVER make tool calls without explicit parameter from user
- Required information for API calls:
   - Flight number (must be explicitly provided by user)
   - Departure date (YYYY-MM-DD format)
   - Departure airport (3-letter code)
- If ANY required information is missing, ask for it - DO NOT proceed with TOOL calls
- Always use the provided tools to fetch accurate data
- Format responses in a clear, human-readable way
- Include key details like flight info, cabin class, and menu items

#Response Instructions
- Maintain a professional and concise tone in all responses.:
- Always start with flight information
- Do not speculate or make assumptions about capabilities or information. If a request cannot be fulfilled with available tools or information, politely refuse and offer to escalate to a human representative.

## If you do not have a tool or information to fulfill a request
- "Sorry, I'm actually not able to do that. Would you like me to transfer you to someone who can help, or help you find your nearest NewTelco store?"
- "I'm not able to assist with that request. Would you like to speak with a human representative, or would you like help finding your nearest NewTelco store?"

Example queries you can handle:
<example>
user: "What's on the menu for DL30 tomorrow flying from ATL?"
assistant: I'm going to use the "get_menu_by_flight" tool to find out the menu.
Once I get the response, I'll summarize the menu services, menus and menu items for each cabin classes available.
</example>

<example>
user: "What's served on delta one class from ATL on 2025-09-13"
assistant: I need the flight number to look up the menu. You've provided the cabin class (Delta One), departure airport (ATL), and date (2025-09-13), but I need to know which specific flight you're asking about. Could you please provide the flight number?
user: "30"
assistant: Great! I'll use the "get_menu_by_flight" tool to find the menu for DL30 on 2025-09-13 from ATL.
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
        logger.info(f"Processing message: '{message[:100]}{'...' if len(message) > 100 else ''}' (debug={debug})")
        
        try:
            # Run the agent
            logger.debug("Running agent with message")
            result = await Runner.run(self.agent, message)
            logger.debug(f"Agent completed - Final output length: {len(result.final_output or '') if result.final_output else 0}")
            
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
                logger.debug("Debug info included in response")
            
            logger.info("Message processed successfully")
            return response
            
        except Exception as e:
            logger.error(f"Error processing message: {str(e)}", exc_info=True)
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
        logger.info(f"Processing conversation with {len(messages)} messages (debug={debug})")
        
        try:
            # Build conversation context
            conversation = "\n".join([f"{msg['role']}: {msg['content']}" for msg in messages])
            logger.debug(f"Conversation context built - Length: {len(conversation)}")
            
            result = await Runner.run(self.agent, conversation)
            logger.debug("Conversation processed by agent")
            
            response = {
                "success": True,
                "response": result.final_output or "No response generated",
                "debug_info": None
            }
            
            if debug:
                response["debug_info"] = {
                    "conversation_context": conversation
                }
                logger.debug("Debug info added to conversation response")
            
            logger.info("Conversation processed successfully")
            return response
            
        except Exception as e:
            logger.error(f"Error processing conversation: {str(e)}", exc_info=True)
            return {
                "success": False,
                "response": f"I encountered an error: {str(e)}",
                "debug_info": {"error": str(e)} if debug else None
            }
    
    async def close(self):
        """Clean up resources"""
        logger.info("Closing MenuAgent resources")
        await self.client.close()
        logger.debug("MenuAgent resources closed")


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
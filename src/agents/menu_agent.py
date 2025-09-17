import os
import asyncio
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
from dotenv import load_dotenv

from agents import Agent, Runner, OpenAIChatCompletionsModel, ModelSettings
from openai import AsyncOpenAI
from openai.types.responses import ResponseTextDeltaEvent

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
            model_settings=ModelSettings(temperature=0.5),
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
        
Current date: {current_date}

# Date Handling Rules:
- Always compare it to the current date ({current_date}) before answering.
- If the user asks about a specific date (e.g., "30th September"), determine whether it is in the past, present, or future relative to {current_date}.
- If the user uses relative terms like "today," "tomorrow," or "next week," resolve them based on {current_date}.
- Never assume the date context from training data; always use {current_date} as the reference point.

# Tense Rules:
- If the event date is in the future, use **future tense** (e.g., "will open", "will close").
- If the event date is in the past, use **past tense** (e.g., "opened", "closed").
- If the event is today, use **present tense** (e.g., "opens today", "is currently open")

# CRITICAL INSTRUCTIONS:
- Always greet the user at the start of the conversation with "Hi, you've reached Delta Flight Menu agent"
- When user asks for menu information and you have all required parameters, ALWAYS call the tools
- ONLY provide menu information that comes directly from tool responses - NEVER make up or invent menu details
- If tool returns no menu data or empty results, clearly state that no menu information is available
- Required information for API calls:
   - Flight number (must be explicitly provided by user)
   - Departure date (YYYY-MM-DD format)
   - Departure airport (3-letter code)
- If ANY required information is missing, ask for it - DO NOT proceed with tool calls
- Always use the provided tools to fetch accurate data

# Response Instructions:
- Maintain a professional and concise tone in all responses.:
- ONLY present menu information that exists in the tool response data
- If menu_services is empty or contains no menu items, state "No menu information is currently available for this flight"
- When presenting menus, only show actual menu_item_desc values from the API response
- Do not add fictional menu items, descriptions, or details not present in the tool response
- Always start responses with flight information
- Format responses clearly but only with real data
- If a request cannot be fulfilled with available tools or information, politely refuse and offer to escalate

## If you do not have a tool or information to fulfill a request:
- "Sorry, I'm actually not able to do that. Would you like me to transfer you to someone who can help?"
- "I'm not able to assist with that request. Would you like to speak with a human representative?"

Example queries you can handle:
<example>
user: "What's on the menu for DL30 tomorrow flying from ATL?"
assistant: I'll look up the menu for DL30 using the get_menu_by_flight tool.
[After tool call] Based on the menu data retrieved, here's what's available... [only show actual menu items from response]
</example>

<example>
user: "What's served on delta one class from ATL on 2025-09-13"
assistant: I need the flight number to look up the menu. You've provided the cabin class (Delta One), departure airport (ATL), and date (2025-09-13), but I need to know which specific flight you're asking about. Could you please provide the flight number?
user: "30"
assistant: I'll look up the Delta One menu for DL30 on 2025-09-13 from ATL.
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

    async def process_conversation_stream(self, messages: List[Dict[str, str]], debug: bool = False):
        """
        Process a conversation with streaming response using OpenAI Agents SDK
        
        Args:
            messages: List of message dictionaries with 'role' and 'content'
            debug: Whether to include debug information
            
        Yields:
            Partial responses as they are generated
        """
        logger.info(f"Processing conversation with streaming for {len(messages)} messages (debug={debug})")
        
        try:

            # Build conversation context
            conversation = "\n".join([f"{msg['role']}: {msg['content']}" for msg in messages])
            logger.debug(f"Conversation context built - Length: {len(conversation)}")
            
            # Use Runner.run_streamed for proper SDK streaming
            result = Runner.run_streamed(self.agent, conversation)
            
            full_response = ""
            async for event in result.stream_events():
                # Stream raw LLM text deltas
                if event.type == "raw_response_event" and isinstance(event.data, ResponseTextDeltaEvent):
                    if event.data.delta:
                        full_response += event.data.delta
                        yield full_response
            
            logger.info("Streaming conversation processed successfully")
            
        except Exception as e:
            logger.error(f"Error processing streaming conversation: {str(e)}", exc_info=True)
            yield f"I encountered an error: {str(e)}"

    async def process_conversation(self, messages: List[Dict[str, str]], debug: bool = False) -> Dict[str, Any]:
        """
        Process a conversation with multiple messages (non-streaming)
        
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
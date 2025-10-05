import asyncio
import os
from datetime import datetime
from typing import Dict, Any, List

from agents import Agent, Runner, OpenAIChatCompletionsModel, ModelSettings, SQLiteSession
from dotenv import load_dotenv
from openai import AsyncOpenAI
from openai.types.responses import ResponseTextDeltaEvent

from ..client.delta_client import DeltaMenuClient
from ..tools.debug_tools import DebugTools
from ..tools.menu_tools import MenuTools
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
        
        # Create the main agent
        self.agent = Agent(
            name="Delta Menu Assistant",
            instructions=self._get_system_instructions(),
            model=kimi_model,
            model_settings=ModelSettings(temperature=0.2, include_usage=True),
            tools=[
                self.menu_tools.get_menu_by_flight_tool(),
                self.menu_tools.check_menu_availability_tool(),
                self.menu_tools.lookup_flights_tool()
            ]
        )
        logger.info("MenuAgent initialized successfully with 3 tools")

    
    def get_session(self, session_id: str) -> SQLiteSession:
        """Get or create a SQLite session for conversation management"""
        session = SQLiteSession(session_id, "menu_conversations.db")
        return session
    
    async def process_message(self, message: str, session_id: str = "default") -> Dict[str, Any]:
        """Process a message using session-based context management"""
        try:
            logger.info(f"Processing message with session {session_id}: {message[:100]}...")
            
            # Get or create session
            session = self.get_session(session_id)
            
            # Log existing session context before processing
            existing_items = await session.get_items()
            logger.info(f"Session {session_id} - Existing context items: {len(existing_items)}")
            for i, item in enumerate(existing_items[-5:]):  # Log last 5 items
                logger.debug(f"Session {session_id} - Context[{i}]: {item.get('role', 'unknown')} - {str(item.get('content', ''))[:100]}...")
            
            # Run agent with session for automatic context management
            logger.debug(f"Session {session_id} - Sending to agent: {message[:200]}...")
            result = await Runner.run(
                self.agent,
                message,
                session=session
            )
            
            # Log new session context after processing
            new_items = await session.get_items()
            logger.info(f"Session {session_id} - New context items: {len(new_items)} (added {len(new_items) - len(existing_items)} items)")
            if len(new_items) > len(existing_items):
                for item in new_items[len(existing_items):]:
                    logger.debug(f"Session {session_id} - Added: {item.get('role', 'unknown')} - {str(item.get('content', ''))[:100]}...")
            
            # Log usage information
            if result.context_wrapper.usage:
                usage = result.context_wrapper.usage
                logger.info(f"Session {session_id} - Usage: {usage.total_tokens} total tokens, {usage.requests} requests, {usage.input_tokens} input tokens, {usage.output_tokens} output tokens")
            
            logger.info(f"Agent response generated successfully for session {session_id}")
            
            return {
                "response": result.final_output,
                "usage": {
                    "total_tokens": result.context_wrapper.usage.total_tokens if result.context_wrapper.usage else 0,
                    "requests": result.context_wrapper.usage.requests if result.context_wrapper.usage else 0
                }
            }
            
        except Exception as e:
            logger.error(f"Error processing message: {str(e)}")
            return {
                "response": "I apologize, but I encountered an error processing your request. Please try again.",
                "error": str(e)
            }
    
    async def process_message_stream(self, message: str, session_id: str = "default"):
        """Process a message with streaming using session-based context management"""
        try:
            logger.info(f"Processing streaming message with session {session_id}: {message[:100]}...")
            
            # Get or create session
            session = self.get_session(session_id)
            
            # Log existing session context before processing
            existing_items = await session.get_items()
            logger.info(f"Session {session_id} - Streaming existing context items: {len(existing_items)} -------------")
            for i, item in enumerate(existing_items):  # Log last 3 items for streaming
                logger.info(f"Session {session_id} - Streaming Context[{i}]: {item.get('role', 'unknown')} - {str(item.get('content', ''))[:100]}...")
            
            # Use Runner.run_streamed with session
            logger.debug(f"Session {session_id} - Streaming to agent: {message[:200]}...")
            result = Runner.run_streamed(
                self.agent,
                message,
                session=session
            )
            
            full_response = ""
            temp_display = ""
            async for event in result.stream_events():
                if event.type == "raw_response_event":
                    if isinstance(event.data, ResponseTextDeltaEvent) and event.data.delta:
                        full_response += event.data.delta
                        yield full_response + temp_display
                elif event.type == "run_item_stream_event":
                    # Handle tool calls and outputs - show temporarily but don't add to final response
                    if event.item.type == "tool_call_item":
                        temp_display = "\n\n🔧 Calling tool...\n\n"
                        yield full_response + temp_display
                    elif event.item.type == "tool_call_output_item":
                        temp_display = "\n✅ Tool Call completed\n\n"
                        yield full_response + temp_display
                        # Clear temp display after tool completion
                        temp_display = ""

            # Log new session context after streaming completes
            new_items = await session.get_items()
            logger.info(f"Session {session_id} - Streaming new context items: {len(new_items)} (added {len(new_items) - len(existing_items)} items)")
            if len(new_items) > len(existing_items):
                for item in new_items[len(existing_items):]:
                    logger.info(f"Session {session_id} - {item}")
            
            # Log usage information after streaming completes
            if result.context_wrapper.usage:
                usage = result.context_wrapper.usage
                logger.info(f"Session {session_id} - Streaming Usage: {usage.total_tokens} total tokens, {usage.requests} requests, {usage.input_tokens} input tokens, {usage.output_tokens} output tokens")
            
            logger.info(f"Streaming response completed for session {session_id}")
            
        except Exception as e:
            logger.error(f"Error processing streaming message: {str(e)}")
            yield f"I encountered an error: {str(e)}"
    
    async def clear_session(self, session_id: str = "default") -> None:
        """Clear conversation history for a session"""
        session = self.get_session(session_id)
        
        # Log items before clearing
        items_before = await session.get_items()
        logger.info(f"Session {session_id} - Clearing {len(items_before)} items from session")
        
        await session.clear_session()
        
        # Verify clearing worked
        items_after = await session.get_items()
        logger.info(f"Session {session_id} - Cleared successfully. Items remaining: {len(items_after)}")
        logger.info(f"Cleared session: {session_id}")
    
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

# CABIN CLASS MAPPING (CRITICAL):
When users ask for specific cabin classes, use these cabin codes with the cabin_codes parameter:
- "Delta One" or "Business" or "Business Class" → cabin_codes="C"
- "Delta Premium Select" or "First" or "First Class" → cabin_codes="F" 
- "Comfort+" or "Comfort Plus" → cabin_codes="W"
- "Main Cabin" or "Economy" or "Coach" → cabin_codes="Y"

# CRITICAL INSTRUCTIONS:
- When user asks for menu information, be conversational and helpful:
  * If they provide flight number, departure date, and departure airport - get the menu directly
  * If they provide departure/arrival airports and date but no flight number - use lookup_flights to show options
  * If they're missing key information, ask for it politely
- ABSOLUTELY CRITICAL: ALWAYS call the appropriate tool - NEVER assume menu availability without checking
- ABSOLUTELY CRITICAL: ONLY provide menu information that comes directly from tool responses - NEVER make up or invent menu details
- Use EXACT menu_item_desc and menu_item_additional_desc values from API responses
- If tool returns no menu data or empty results, clearly state that no menu information is available
- Always use the provided tools to fetch accurate data
- When users specify a cabin class, ALWAYS use the cabin_codes parameter with the correct code
- NEVER create generic categories or summaries - show actual item names from tool responses
- NEVER say "no menu information is available" without first calling the get_flight_menu tool

# Response Instructions:
- Maintain a professional and concise tone in all responses
- ABSOLUTELY CRITICAL: ALWAYS call tools before making any statements about menu availability
- ABSOLUTELY CRITICAL: ONLY present menu information that exists in the tool response data
- If menu_services is empty or contains no menu items, state "No menu information is currently available for this flight"
- When presenting menus, only show actual menu_item_desc values from the API response
- Do not add fictional menu items, descriptions, or details not present in the tool response
- NEVER create generic categories like "Vodka, Gin, Whiskey" - show actual brand names from tool response
- Always start responses with flight information
- Format responses clearly but only with real data
- If a request cannot be fulfilled with available tools or information, politely refuse and offer to escalate
- When showing beverages, wines, or spirits, list the EXACT names from menu_item_desc field
- NEVER make assumptions about what's available - always verify with tool calls


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
user: "What's served on delta one class from ATL to LHR on 2025-09-13"
assistant: I'll look up available flights from ATL to LHR on 2025-09-13 first, then show you the Delta One menu options.
[After lookup_flights tool call] I found these flights from ATL to LHR on 2025-09-13:
- DL30 departing 8:00 AM
- DL32 departing 10:00 AM  
- DL34 departing 12:00 PM
Which flight would you like to see the Delta One menu for?
user: "DL30"
assistant: [After get_menu_by_flight tool call] Here's the Delta One menu for DL30...
</example>

<example>
user: "What's served on delta one class from ATL on 2025-09-13"
assistant: I need a bit more information to help you. You've provided the cabin class (Delta One), departure airport (ATL), and date (2025-09-13). Could you please provide either:
1. The flight number (like DL30), or
2. The arrival airport so I can look up available flights for you
user: "30"
assistant: I'll look up the Delta One menu for DL30 on 2025-09-13 from ATL.
[Calls get_flight_menu tool with cabin_codes="C"]
</example>

<example>
Consider today is 2025-09-15
user: Im not able to preselect menu for flight 30 departing from atl on 30th september? Could you please assist?
assistant: To assist you with preselecting a menu for flight DL30 on 2025-09-30 from ATL, I need to check the menu availability.
I'll use the check_menu_availability tool to see if the preselect window is currently open for that flight.
The preselect window will open on September 23rd, 2025 and will close on September 29th, 2025. Since today is September 15th, 2025, the preselect window is not yet open. You will be able to preselect your menu starting from September 23rd, 2025.
</example>
"""


    
    async def close(self):
        """Clean up resources"""
        logger.info("Closing MenuAgent resources")
        await self.client.close()
        logger.debug("MenuAgent resources closed")

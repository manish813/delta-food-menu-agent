import asyncio
import os
from datetime import datetime
from typing import Dict, Any, List

from agents import Agent, Runner, OpenAIChatCompletionsModel, ModelSettings
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
        
        # Create the main agent with tracing enabled
        self.agent = Agent(
            name="Delta Menu Assistant",
            instructions=self._get_system_instructions(),
            model=kimi_model,
            model_settings=ModelSettings(temperature=0.5),
            tools=[
                self.menu_tools.get_menu_by_flight_tool(),
                self.menu_tools.check_menu_availability_tool(),
                self.menu_tools.lookup_flights_tool()
            ]
        )
        logger.info("MenuAgent initialized successfully with 3 tools")

    
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

# Follow-up Detail Requests:
When users ask for specific details about menu items:
1. NEVER make up or invent any menu information
2. ONLY use exact data from tool responses - menu_item_desc and menu_item_additional_desc fields
3. If asking about beverages, wines, or specific categories, extract ONLY the actual items from the tool response
4. If detailed info isn't available in previous responses, make a new tool call
5. Present information exactly as returned by the API - do not summarize or categorize

<example>
user: "What's served in business class on DL30 from ATL on 2025-09-15?"
assistant: [After tool call] Here's the business class menu for DL30... [shows actual menu items from tool response]
user: "What wines are available?"
assistant: Based on the menu I retrieved, here are the specific wines available in Delta One:

**Champagne:**
- Taittinger Brut La Francaise NV

**White & Rosé:**
- Rippa Dorii Verdejo Ecologico DO Rueda, Spain
- Babich Black Label Sauvignon Blanc, Marlborough, New Zealand
- Sommelier's Selection

**Red:**
- Château Simard Saint-Émilion Grand Cru, Bordeaux, France
- Via Marichalar Reserva, Rioja, Spain

[Only shows actual wine names from tool response]
</example>

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
user: "Im flying from atlanta to fort myers florida on 30th what menu is available for delta one cabin"
assistant: [Calls lookup_flights tool first, then when user selects DL1110]
user: "DL1110"
assistant: I'll get the Delta One menu for DL1110 from Atlanta to Fort Myers on September 30th.
[Calls get_flight_menu(departure_date="2025-09-30", departure_airport="ATL", flight_number=1110, cabin_codes="C")]
[After tool response] Here's the Delta One menu for DL1110... [shows actual menu items from tool response]
user: "can you check for comfort plus"
assistant: I'll check the Comfort+ menu for DL1110 from Atlanta to Fort Myers on September 30th.
[Calls get_flight_menu(departure_date="2025-09-30", departure_airport="ATL", flight_number=1110, cabin_codes="W")]
[After tool response] Here's what's available in Comfort+ for DL1110... [shows actual menu items from tool response]
user: "What about first class menu?"
assistant: I'll get the first class menu for the same flight.
[Calls get_flight_menu(departure_date="2025-09-30", departure_airport="ATL", flight_number=1110, cabin_codes="F")]
[After tool response] Here's the first class menu for DL1110... [shows actual menu items]
user: "Is there any menu for economy?"
assistant: Let me check the Main Cabin menu for DL1110.
[Calls get_flight_menu(departure_date="2025-09-30", departure_airport="ATL", flight_number=1110, cabin_codes="Y")]
[After tool response] Based on the results... [only shows what tool returned]
</example>

<example>
Consider today is 2025-09-15
user: Im not able to preselect menu for flight 30 departing from atl on 30th september? Could you please assist?
assistant: To assist you with preselecting a menu for flight DL30 on 2025-09-30 from ATL, I need to check the menu availability.
I'll use the check_menu_availability tool to see if the preselect window is currently open for that flight.
The preselect window will open on September 23rd, 2025 and will close on September 29th, 2025. Since today is September 15th, 2025, the preselect window is not yet open. You will be able to preselect your menu starting from September 23rd, 2025.
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
            temp_display = ""
            async for event in result.stream_events():
                # Handle different event types
                if event.type == "raw_response_event" and isinstance(event.data, ResponseTextDeltaEvent):
                    # Stream raw LLM text deltas
                    if event.data.delta:
                        full_response += event.data.delta
                        yield full_response + temp_display
                elif event.type == "run_item_stream_event":
                    # Handle tool calls and outputs - show temporarily but don't add to final response
                    if event.item.type == "tool_call_item":
                        temp_display = "\n\n🔧 Calling tool...\n\n"
                        yield full_response + temp_display
                    elif event.item.type == "tool_call_output_item":
                        temp_display = "\n✅ Tool completed\n\n"
                        yield full_response + temp_display
                        # Clear temp display after tool completion
                        temp_display = ""
            
            # Final yield with just the actual response content
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
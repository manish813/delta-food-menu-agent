import asyncio
import os
from typing import List, Dict

import gradio as gr

from ..agents.menu_agent import MenuAgent
from ..utils.logging_config import setup_logging, get_logger

# Setup logging
setup_logging(log_file='gradio_app.log')
logger = get_logger(__name__)


class GradioInterface:
    """Gradio interface for the Delta Menu Assistant"""
    
    def __init__(self):
        self.agent = MenuAgent()
    
    async def chat_response_stream(self, message: str, session_id: str = "gradio_session", debug_mode: bool = False):
        """Process chat message with streaming using session-based management"""
        logger.info(f"Processing message: {message[:100]}...")
        try:
            # Use session-based streaming - no need to manage history manually
            async for partial_response in self.agent.process_message_stream(message, session_id):
                yield partial_response
                
        except Exception as e:
            logger.error(f"Error processing message: {str(e)}", exc_info=True)
            error_msg = f"I encountered an error: {str(e)}"
            if debug_mode:
                error_msg += f"\n\nDebug: {str(e)}"
            yield error_msg
    
    def format_examples(self) -> List[str]:
        """Return example queries"""
        return [
            "What's served in delta one class on DL30 from ATL on 2025-09-30?",
            "Show me first class menu for DL30",
            "Compare business and first class meals on DL30"
        ]


def create_gradio_app() -> gr.Blocks:
    """Create the Gradio interface"""
    interface = GradioInterface()
    
    with gr.Blocks(
        title="Delta Menu Assistant",
        theme=gr.themes.Soft(),
        css="""
        .gradio-container {
            max-width: 1200px;
            margin: 0 auto;
        }
        .chat-message {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
        }
        .message.bot {
            background-color: #f8f9fa;
        }
        .message.user {
            background-color: #e3f2fd;
        }
        .avatar {
            width: 32px;
            height: 32px;
            border-radius: 50%;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 18px;
            background-color: #007bff;
            color: white;
            font-weight: bold;
        }
        .avatar.user {
            background-color: #28a745;
        }
        .avatar.user::before {
            content: "U";
        }
        .avatar.bot::before {
            content: "🤖";
        }
        .message .avatar {
            margin-right: 8px;
        }
        """
    ) as app:
        gr.Markdown("""
        # 🛫 Delta Flight Menu Assistant
        
        Ask about flight menus, compare cabin classes, or debug API issues. 
        Powered by Kimi AI and Delta's flight menu API.
        """)
        
        with gr.Row():
            with gr.Column(scale=3):
                chatbot = gr.Chatbot(
                    height=500,
                    type="messages",
                    avatar_images=("user_avatar.svg", "bot_avatar.svg"),
                    label="Conversation",
                    show_copy_button=True
                )
                
                with gr.Row():
                    msg_input = gr.Textbox(
                        placeholder="Ask about flight menus...",
                        container=False,
                        scale=4,
                        lines=1,
                        max_lines=3
                    )
                    submit_btn = gr.Button("Send", variant="primary", scale=1)
                
                with gr.Row():
                    debug_mode = gr.Checkbox(label="Debug Mode", value=False)
                    clear_btn = gr.Button("Clear", variant="secondary")
            
            with gr.Column(scale=1):
                gr.Markdown("### Quick Examples")
                examples = interface.format_examples()
                
                example_btns = []
                for i, example in enumerate(examples):
                    btn = gr.Button(example, size="sm", variant="secondary")
                    example_btns.append(btn)
        
        # Event handlers
        def user(user_message, history):
            return "", history + [{"role": "user", "content": user_message}]
        
        async def bot(history, debug_mode):
            user_message = history[-1]["content"]
            
            # Add empty assistant message to show streaming
            history.append({"role": "assistant", "content": ""})
            
            # Stream the response using session-based management
            async for partial_response in interface.chat_response_stream(user_message, "gradio_session", debug_mode):
                history[-1]["content"] = partial_response
                yield history
        
        # Button click handler for examples
        def example_click(example_text):
            return example_text
        
        # Connect events with streaming
        msg_input.submit(user, [msg_input, chatbot], [msg_input, chatbot], queue=False).then(
            bot, [chatbot, debug_mode], chatbot
        )
        
        submit_btn.click(user, [msg_input, chatbot], [msg_input, chatbot], queue=False).then(
            bot, [chatbot, debug_mode], chatbot
        )
        
        # Example button clicks
        for i, btn in enumerate(example_btns):
            btn.click(example_click, inputs=[btn], outputs=[msg_input])
        
        async def clear_conversation():
            await interface.agent.clear_session("gradio_session")
            return None
        
        clear_btn.click(clear_conversation, None, chatbot, queue=False)
        
        gr.Markdown("""
        ### Usage Tips:
        - **Flight Info**: Include flight number, date (YYYY-MM-DD), departure airport and arrival Airport
        - **Cabin Classes**: F=Delta Premium Select, C=Delta One, W=Comfort, Y=Coach
        - **Examples**: Use quick buttons for common queries
        """)
    
    return app


# Simple chat interface alternative
def create_simple_chat():
    """Create a simple chat interface"""
    interface = GradioInterface()
    
    async def chat_fn(message, history, debug_mode):
        result = await interface.agent.process_message(message, "simple_chat_session")
        return result["response"]
    
    return gr.ChatInterface(
        fn=chat_fn,
        title="Delta Menu Assistant",
        description="Ask about flight menus and cabin classes",
        additional_inputs=[
            gr.Checkbox(label="Debug Mode", value=False)
        ],
        examples=[
            "What's served in business class on DL30 from ATL on 2025-08-13?",
            "Show me first class menu for DL30",
            "Compare business and first class meals",
            "Is the Delta menu API working?"
        ],
        theme=gr.themes.Soft(),
        css=".gradio-container { max-width: 1200px; margin: 0 auto; }"
    )


# Main entry point
if __name__ == "__main__":
    # Check for required environment variables
    if not os.getenv("KIMI_API_KEY"):
        logger.warning("KIMI_API_KEY not found in environment variables")
        print("⚠️  Warning: KIMI_API_KEY not found in environment variables")
        print("Please set KIMI_API_KEY in your .env file")
    
    # Launch the app
    logger.info("Starting Gradio app...")
    app = create_gradio_app()
    logger.info("Launching app on http://localhost:7860")
    app.launch(
        server_name="0.0.0.0",
        server_port=7860,
        share=False,
        debug=True
    )
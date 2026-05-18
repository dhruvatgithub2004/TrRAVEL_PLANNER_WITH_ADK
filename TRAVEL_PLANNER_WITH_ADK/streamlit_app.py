import streamlit as st
import os
from dotenv import load_dotenv
from google.adk.models.lite_llm import LiteLlm
from google.adk.models.llm_request import LlmRequest
from google.genai.types import Content, Part
import asyncio
from datetime import datetime

# Load environment variables
load_dotenv()
load_dotenv(os.path.join(os.path.dirname(__file__), "travel_planner", ".env"))

# API Keys
DEEPSEEK_API_KEY = st.secrets.get("DEEPSEEK_API_KEY", None) or os.getenv("DEEPSEEK_API_KEY")
if DEEPSEEK_API_KEY:
    os.environ["DEEPSEEK_API_KEY"] = DEEPSEEK_API_KEY

TAVILY_API_KEY = st.secrets.get("TAVILY_API_KEY", None) or os.getenv("TAVILY_API_KEY")
if TAVILY_API_KEY:
    os.environ["TAVILY_API_KEY"] = TAVILY_API_KEY

from travel_planner.tools import web_search, find_nearby_places_open

# Initialize LLM
llm = LiteLlm(model="deepseek/deepseek-chat")

if not DEEPSEEK_API_KEY:
    st.set_page_config(page_title="Travel Planner Chatbot", page_icon="🌍", layout="wide")
    st.title("🌍 Travel Planner Chatbot")
    st.error("DEEPSEEK_API_KEY is missing.")
    st.stop()

def _build_system_prompt() -> str:
    now = datetime.now()
    return f"""You are an exclusive travel concierge agent. You help users discover their dream holiday destinations and plan their vacations.
TODAY'S DATE: {now.strftime("%A, %B %d, %Y")}. Current time: {now.strftime("%H:%M")}.

Your role:
- Provide personalized travel recommendations
- Suggest nearby attractions, hotels, cafes, and points of interest
- Use tools for real-time information
- Be informative, concise, and professional
"""

class SimpleTravelAgent:
    def __init__(self, llm):
        self.llm = llm

    async def _gather_context(self, message: str) -> str:
        import re
        message_lower = message.lower()
        parts = []

        # Web Search
        search_triggers = ["event", "news", "current", "latest", "weather", "visa", "flight", 
                          "festival", "trending", str(datetime.now().year)]
        if any(w in message_lower for w in search_triggers):
            try:
                result = web_search(message)
                if result and "No results found" not in result:
                    parts.append(f"WEB SEARCH RESULTS:\n{result}")
            except Exception as e:
                parts.append(f"(Web search failed: {e})")

        # Location Search
        location_triggers = ["near", "nearby", "around", "hotel", "restaurant", "cafe", 
                           "beach", "attraction"]
        if any(w in message_lower for w in location_triggers):
            location = self._extract_location(message)
            if location:
                place_query = self._extract_place_query(message)
                try:
                    result = find_nearby_places_open(place_query, location)
                    if result and "No results found" not in result:
                        parts.append(f"NEARBY PLACES:\n{result}")
                except Exception as e:
                    parts.append(f"(Location search failed: {e})")

        return "\n\n".join(parts)

    def _extract_location(self, message: str) -> str:
        import re
        match = re.search(r'\b(?:in|near|around|close to)\s+([A-Z][a-zA-Z\s]{1,40}?)', 
                         message, re.IGNORECASE)
        return match.group(1).strip().title() if match else ""

    def _extract_place_query(self, message: str) -> str:
        place_types = ["hotel", "restaurant", "cafe", "beach", "attraction"]
        msg_lower = message.lower()
        for p in place_types:
            if p in msg_lower:
                return p
        return "attraction"

    async def generate_stream(self, user_message: str, tool_context: str, conversation_history: list = None):
        """Async generator for streaming"""
        try:
            if tool_context:
                enriched_message = f"[Real-time data retrieved]\n\n{tool_context}\n\n---\nUser question: {user_message}"
            else:
                enriched_message = user_message

            contents = [
                Content(role="user", parts=[Part(text=_build_system_prompt())]),
                Content(role="model", parts=[Part(text="Understood.")]),
            ]

            if conversation_history:
                for msg in conversation_history[-8:]:
                    role = "user" if msg["role"] == "user" else "model"
                    contents.append(Content(role=role, parts=[Part(text=msg["content"])]))

            contents.append(Content(role="user", parts=[Part(text=enriched_message)]))

            llm_request = LlmRequest(
                contents=contents,
                config={"temperature": 0.7, "max_output_tokens": 1500}
            )

            response_generator = self.llm.generate_content_async(llm_request)
            async for resp in response_generator:
                if hasattr(resp, "content") and resp.content and resp.content.parts:
                    for part in resp.content.parts:
                        if hasattr(part, "text") and part.text:
                            yield part.text

        except Exception as e:
            yield f"\n\nI apologize, an error occurred: {str(e)}"


# Initialize Agent
travel_agent = SimpleTravelAgent(llm)

# ====================== STREAMLIT UI ======================
st.set_page_config(page_title="Travel Planner Chatbot", page_icon="🌍", layout="wide")
st.title("🌍 Travel Planner Chatbot")
st.markdown("Powered by Google ADK & DeepSeek • Real-time streaming")

if "messages" not in st.session_state:
    st.session_state.messages = []
if "debug_mode" not in st.session_state:
    st.session_state.debug_mode = False

# Sidebar
with st.sidebar:
    st.header("⚙️ Settings")
    st.session_state.debug_mode = st.checkbox("Debug Mode", value=st.session_state.debug_mode)
    
    if st.button("🗑️ Clear Chat History"):
        st.session_state.messages = []
        st.rerun()

# Display previous messages
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# Chat Input
if prompt := st.chat_input("Ask about your travel plans..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        message_placeholder = st.empty()
        status_placeholder = st.empty()
        
        status_placeholder.info("🔄 Thinking...")

        try:
            conversation_history = st.session_state.messages[:-1]

            # Run async parts
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)

            tool_context = loop.run_until_complete(travel_agent._gather_context(prompt))

            status_placeholder.info("✍️ Generating response...")

            full_response = ""
            # Stream tokens
            async_gen = travel_agent.generate_stream(prompt, tool_context, conversation_history)
            
            for chunk in loop.run_until_complete(asyncio.gather(async_gen.__anext__())):  # Better way below
                pass  # We'll replace this with proper streaming

            # === Proper Streaming Fix ===
            full_response = ""
            try:
                while True:
                    chunk = loop.run_until_complete(async_gen.__anext__())
                    if chunk:
                        full_response += chunk
                        message_placeholder.markdown(full_response + " ▌")
            except StopAsyncIteration:
                pass

            # Final output
            message_placeholder.markdown(full_response)
            st.session_state.messages.append({"role": "assistant", "content": full_response})

            if st.session_state.debug_mode and tool_context:
                with st.expander("Debug Info"):
                    st.code(tool_context, language="text")

        except Exception as e:
            message_placeholder.error(f"Error: {str(e)}")
        finally:
            status_placeholder.empty()
            loop.close()

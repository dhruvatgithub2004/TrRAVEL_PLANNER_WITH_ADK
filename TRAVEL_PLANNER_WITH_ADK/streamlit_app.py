import streamlit as st
import os
from dotenv import load_dotenv
from google.adk.models.lite_llm import LiteLlm
from google.adk.models.llm_request import LlmRequest
from google.genai.types import Content, Part
import asyncio
import json
from datetime import datetime

# Load environment variables
load_dotenv()
load_dotenv(os.path.join(os.path.dirname(__file__), "travel_planner", ".env"))

# Resolve API keys
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
    st.error("DEEPSEEK_API_KEY is missing. Please add it to .env or Streamlit secrets.")
    st.stop()

def _build_system_prompt() -> str:
    now = datetime.now()
    return f"""You are an exclusive travel concierge agent. You help users discover their dream holiday destinations and plan their vacations.
TODAY'S DATE: {now.strftime("%A, %B %d, %Y")}. Current time: {now.strftime("%H:%M")}.

Your role:
- Help users find destinations and activities they would enjoy
- Provide personalized travel recommendations
- Suggest nearby attractions, hotels, cafes, and points of interest
- Use available tools to search for current information
- Be informative but concise
- Always respond in a helpful, professional manner

When users ask about specific locations or places, use the location search tool. 
When users ask about current events, news, weather, visa, or general travel info, use the web search tool.
"""

class SimpleTravelAgent:
    def __init__(self, llm):
        self.llm = llm

    async def run_with_context(self, user_message: str, conversation_history: list = None):
        tool_context = await self._gather_context(user_message)
        response = await self._generate(user_message, tool_context, conversation_history)
        return response, tool_context

    async def _gather_context(self, message: str) -> str:
        """Run all relevant tools and return combined context string."""
        import re
        message_lower = message.lower()
        parts = []

        # Web search
        search_triggers = [
            "event", "news", "current", "happening", "trending", "festival", "latest", 
            "recent", "development", "update", "visa", "entry", "weather", "season", 
            "travel", "flight", "tour", "guide", "what", "how", "when", "where", 
            "why", "tell me", "best time", str(datetime.now().year)
        ]
        if any(w in message_lower for w in search_triggers):
            try:
                result = web_search(message)
                if result and "No results found" not in result:
                    parts.append(f"WEB SEARCH RESULTS:\n{result}")
            except Exception as e:
                parts.append(f"(Web search failed: {e})")

        # Location search
        location_triggers = ["near", "nearby", "around", "close to", "hotel", "restaurant", 
                           "cafe", "bar", "museum", "park", "beach", "attraction", "shop"]
        if any(w in message_lower for w in location_triggers):
            location = self._extract_location(message)
            if location:
                place_query = self._extract_place_query(message)
                try:
                    result = find_nearby_places_open(place_query, location)
                    if result and "No results found" not in result:
                        parts.append(f"NEARBY PLACES ({place_query} near {location}):\n{result}")
                except Exception as e:
                    parts.append(f"(Location search failed: {e})")

        return "\n\n".join(parts)

    def _extract_location(self, message: str) -> str:
        import re
        match = re.search(
            r'\b(?:in|near|around|close to)\s+([A-Z][a-zA-Z\s]{1,40}?)(?:\?|,|\.| hotel| restaurant| cafe|$)',
            message, re.IGNORECASE
        )
        if match:
            loc = match.group(1).strip()
            if len(loc) > 2:
                return loc.title()
        return ""

    def _extract_place_query(self, message: str) -> str:
        place_types = ["hotel", "restaurant", "cafe", "bar", "museum", "park", "beach", 
                      "attraction", "shop", "store"]
        message_lower = message.lower()
        for p in place_types:
            if p in message_lower:
                return p
        return "attraction"

    async def _generate(self, user_message: str, tool_context: str, conversation_history: list = None):
        """Generator that yields chunks for streaming"""
        try:
            if tool_context:
                enriched_message = (
                    f"[Real-time data retrieved for your question — use this to answer accurately]\n\n"
                    f"{tool_context}\n\n"
                    f"---\n"
                    f"User question: {user_message}"
                )
            else:
                enriched_message = user_message

            contents = [
                Content(role="user", parts=[Part(text=_build_system_prompt())]),
                Content(role="model", parts=[Part(text="Understood. I am your travel concierge and will use the provided real-time data to answer accurately.")]),
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
            full_response = ""

            async for resp in response_generator:
                if hasattr(resp, "content") and resp.content and resp.content.parts:
                    for part in resp.content.parts:
                        if hasattr(part, "text") and part.text:
                            chunk = part.text
                            full_response += chunk
                            yield chunk  # Yield for streaming
                            break

            if not full_response:
                yield "I apologize, but I couldn't generate a response. Please try again."

        except Exception as e:
            yield f"I apologize, but I encountered an error: {str(e)}. Please try again."


# Initialize agent
travel_agent = SimpleTravelAgent(llm)

# Page setup
st.set_page_config(page_title="Travel Planner Chatbot", page_icon="🌍", layout="wide", initial_sidebar_state="expanded")
st.title("🌍 Travel Planner Chatbot")
st.markdown("Powered by Google ADK & DeepSeek - Your personal travel concierge")

# Session state
if "messages" not in st.session_state:
    st.session_state.messages = []
if "debug_mode" not in st.session_state:
    st.session_state.debug_mode = False

# Sidebar
with st.sidebar:
    st.header("⚙️ Settings")
    st.session_state.debug_mode = st.checkbox("🐛 Debug Mode", value=st.session_state.debug_mode)

    if st.button("🗑️ Clear Chat History"):
        st.session_state.messages = []
        st.rerun()

    st.markdown("---")
    st.markdown("""
    ### 💡 Tips
    - Ask about destinations you'd like to visit
    - Request recommendations for activities
    - Ask for nearby attractions and amenities
    - Get travel tips and current events info
    """)

# Display chat messages
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# Chat input
if prompt := st.chat_input("Ask about your travel plans... 🎒"):
    # Add user message
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # Assistant response with streaming
    with st.chat_message("assistant"):
        message_placeholder = st.empty()
        status_placeholder = st.empty()
        
        status_placeholder.info("🔄 Thinking and searching...")

        try:
            conversation_history = st.session_state.messages[:-1] if len(st.session_state.messages) > 1 else None

            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
            try:
                # Gather context
                tool_context = loop.run_until_complete(travel_agent._gather_context(prompt))
                
                # Stream response
                full_response = ""
                stream = travel_agent._generate(prompt, tool_context, conversation_history)
                
                async for chunk in stream:
                    full_response += chunk
                    message_placeholder.markdown(full_response + "▌")  # Cursor effect
                
                # Final output
                message_placeholder.markdown(full_response)
                
                # Save to history
                st.session_state.messages.append({"role": "assistant", "content": full_response})
                
                # Debug
                if st.session_state.debug_mode:
                    with st.expander("📋 Debug Info"):
                        st.write("**Tool Context:**")
                        st.code(tool_context or "(No context retrieved)", language="text")
                        
            finally:
                loop.close()

        except Exception as e:
            message_placeholder.error(f"❌ Error: {str(e)}")

        finally:
            status_placeholder.empty()

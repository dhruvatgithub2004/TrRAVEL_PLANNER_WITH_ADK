import streamlit as st
import os
from dotenv import load_dotenv
from google.adk.models.lite_llm import LiteLlm
from google.adk.models.llm_request import LlmRequest
from google.genai.types import Content, Part
import asyncio
import json
from datetime import datetime

# Load environment variables from .env files (local development only)
load_dotenv()
load_dotenv(os.path.join(os.path.dirname(__file__), "travel_planner", ".env"))

# Resolve API key: Streamlit Cloud secrets take priority, then env/dotenv
DEEPSEEK_API_KEY = st.secrets.get("DEEPSEEK_API_KEY", None) or os.getenv("DEEPSEEK_API_KEY")
if DEEPSEEK_API_KEY:
    os.environ["DEEPSEEK_API_KEY"] = DEEPSEEK_API_KEY


from travel_planner.tools import web_search, find_nearby_places_open

# Initialize the LLM
llm = LiteLlm(model="deepseek/deepseek-chat")

if not DEEPSEEK_API_KEY:
    st.set_page_config(
        page_title="Travel Planner Chatbot",
        page_icon="🌍",
        layout="wide",
        initial_sidebar_state="expanded"
    )
    st.title("🌍 Travel Planner Chatbot")
    st.error(
        "DEEPSEEK_API_KEY is missing. Please add it to `.env` at the project root or `travel_planner/.env`, then restart Streamlit."
    )
    st.stop()

def _build_system_prompt() -> str:
    now = datetime.now()
    return f"""
You are an exclusive travel concierge agent. You help users discover their dream holiday destinations and plan their vacations.

TODAY'S DATE: {now.strftime("%A, %B %d, %Y")}. Current time: {now.strftime("%H:%M")}. Always use this as the reference for "current", "latest", "recent", or "new" information.

Your role:
- Help users find destinations and activities they would enjoy
- Provide personalized travel recommendations
- Suggest nearby attractions, hotels, cafes, and points of interest
- Use available tools to search for current information and locations
- Be informative but concise in your responses
- Always respond in a helpful, professional manner
- When mentioning recent developments, events, or news, always use {now.year} as the current year

Available tools:
- Web search for current travel information and events
- Location search for nearby places and attractions

When users ask about specific locations or places, use the location search tool.
When users ask about current events, news, latest developments, or general travel information, use the web search tool.
"""

class SimpleTravelAgent:
    def __init__(self, llm):
        self.llm = llm

    async def run_with_context(self, user_message: str, conversation_history: list = None):
        """Returns (response_text, tool_context) for debug visibility."""
        tool_context = await self._gather_context(user_message)
        response = await self._generate(user_message, tool_context, conversation_history)
        return response, tool_context

    async def run(self, user_message: str, conversation_history: list = None) -> str:
        response, _ = await self.run_with_context(user_message, conversation_history)
        return response

    async def _generate(self, user_message: str, tool_context: str, conversation_history: list = None) -> str:
        try:
            # Inject search results directly into the user message so the LLM
            # always receives a user turn last (required by the chat API contract)
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
                            full_response = part.text
                            break
                    if full_response:
                        break

            return full_response or "I apologize, but I couldn't generate a response. Please try again."

        except Exception as e:
            return f"I apologize, but I encountered an error: {str(e)}. Please try again."

    async def _gather_context(self, message: str) -> str:
        """Run all relevant tools and return combined context string."""
        import re
        message_lower = message.lower()
        parts = []

        # Web search — broad triggers so current-info queries always fire
        search_triggers = [
            "event", "news", "current", "happening", "trending", "festival",
            "latest", "recent", "development", "update", "visa", "entry",
            "weather", "season", "travel", "flight", "tour", "guide",
            "what", "how", "when", "where", "why", "tell me", "best time",
            str(datetime.now().year),
        ]
        if any(w in message_lower for w in search_triggers):
            try:
                result = web_search(message)
                if result and "No results found" not in result:
                    parts.append(f"WEB SEARCH RESULTS:\n{result}")
            except Exception as e:
                parts.append(f"(Web search failed: {e})")

        # Location search — only when user wants nearby places
        location_triggers = [
            "near", "nearby", "around", "close to",
            "hotel", "restaurant", "cafe", "bar", "museum",
            "park", "beach", "attraction", "shop",
        ]
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
        # Pattern: "in/near/around <Location>" — grab up to 4 words
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
        place_types = [
            "hotel", "restaurant", "cafe", "bar", "museum", "park",
            "beach", "attraction", "shop", "store", "gym", "hospital",
        ]
        message_lower = message.lower()
        for p in place_types:
            if p in message_lower:
                return p
        return "attraction"

# Initialize the travel agent
travel_agent = SimpleTravelAgent(llm)

# Page setup
st.set_page_config(
    page_title="Travel Planner Chatbot",
    page_icon="🌍",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.title("🌍 Travel Planner Chatbot")
st.markdown("*Powered by Google ADK & AI - Your personal travel concierge*")

# Initialize session state
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
    # Add user message to chat
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)
    
    # Get bot response
    with st.chat_message("assistant"):
        message_placeholder = st.empty()
        status_placeholder = st.empty()
        
        try:
            status_placeholder.info("🔄 Processing your request...")
            
            # Call the travel agent asynchronously with conversation history
            # Get conversation history (all messages except the current user message)
            conversation_history = st.session_state.messages[:-1] if len(st.session_state.messages) > 1 else None
            
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                full_response, tool_context = loop.run_until_complete(
                    travel_agent.run_with_context(prompt, conversation_history)
                )
            finally:
                loop.close()

            status_placeholder.empty()
            message_placeholder.markdown(full_response)
            
            # Add assistant message to chat history
            st.session_state.messages.append({"role": "assistant", "content": full_response})
            
            # Debug info
            if st.session_state.debug_mode:
                with st.expander("📋 Debug Info"):
                    st.write("**Current Query:**", prompt)
                    st.write("**Tool Context Retrieved:**")
                    st.code(tool_context or "(no search performed)", language="text")
                    st.write("**Full Response:**", full_response)
        
        except Exception as e:
            status_placeholder.empty()
            error_msg = f"❌ Error: {str(e)}"
            message_placeholder.error(error_msg)
            if st.session_state.debug_mode:
                with st.expander("📋 Error Details"):
                    st.error(str(e), icon="🚨")

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

    async def run(self, user_message: str, conversation_history: list = None) -> str:
        """Run the travel agent with the user's message and conversation history"""
        try:
            # Build the system prompt fresh so date/time is always current
            contents = [
                Content(
                    role="user",
                    parts=[Part(text=_build_system_prompt())]
                ),
                Content(
                    role="model",
                    parts=[Part(text="I understand. I'm a travel concierge ready to help you plan your perfect vacation.")]
                )
            ]

            # Add conversation history if provided
            if conversation_history:
                for msg in conversation_history[-10:]:  # Keep last 10 messages to avoid token limits
                    if msg["role"] == "user":
                        contents.append(Content(
                            role="user",
                            parts=[Part(text=msg["content"])]
                        ))
                    elif msg["role"] == "assistant":
                        contents.append(Content(
                            role="model",
                            parts=[Part(text=msg["content"])]
                        ))

            # Add current user message
            contents.append(Content(
                role="user",
                parts=[Part(text=user_message)]
            ))
            
            # Check if we need to use tools
            tool_response = await self._check_and_use_tools(user_message)
            if tool_response:
                contents.append(Content(
                    role="model",
                    parts=[Part(text=f"Based on my search: {tool_response}")]
                ))
            
            # Create LlmRequest
            llm_request = LlmRequest(
                contents=contents,
                config={"temperature": 0.7, "max_output_tokens": 1000}
            )
            
            # Generate response
            response_generator = self.llm.generate_content_async(llm_request)
            
            # Extract text from response
            full_response = ""
            async for resp in response_generator:
                if hasattr(resp, 'content') and resp.content and resp.content.parts:
                    for part in resp.content.parts:
                        if hasattr(part, 'text') and part.text:
                            full_response = part.text
                            break
                    if full_response:
                        break
            
            if not full_response:
                return "I apologize, but I couldn't generate a response. Please try again."
            
            return full_response
            
        except Exception as e:
            return f"I apologize, but I encountered an error: {str(e)}. Please try again."
    
    async def _check_and_use_tools(self, message: str) -> str:
        """Check if tools should be used and return results"""
        message_lower = message.lower()
        
        # Check for location-related queries
        location_keywords = ["near", "nearby", "around", "close to", "find", "search", "hotels", "restaurants", "cafes", "attractions"]
        if any(keyword in message_lower for keyword in location_keywords):
            # Try to extract location from message
            location = self._extract_location(message)
            if location:
                query = self._extract_place_query(message)
                if query:
                    try:
                        result = find_nearby_places_open(query, location)
                        return f"Location search results for '{query}' near {location}: {result}"
                    except Exception as e:
                        return f"Location search failed: {str(e)}"

        # Check for general search queries
        search_keywords = ["events", "news", "current", "happening", "trending", "festival", "what's",
                           "latest", "recent", "developments", "new", "update",
                           str(datetime.now().year)]
        if any(keyword in message_lower for keyword in search_keywords):
            try:
                result = web_search(message)
                return f"Web search results: {result}"
            except Exception as e:
                return f"Web search failed: {str(e)}"
        
        return ""

    def _extract_location(self, message: str) -> str:
        """Extract location from message"""
        # Simple extraction - look for common city names or "in [location]"
        cities = ["paris", "london", "tokyo", "new york", "rome", "barcelona", "amsterdam", "berlin", "miami", "los angeles", "chicago", "san francisco"]
        
        message_lower = message.lower()
        for city in cities:
            if city in message_lower:
                return city.title()
        
        # Look for "in [location]" pattern
        import re
        match = re.search(r'\b(?:in|near|around)\s+([a-zA-Z\s]+)', message, re.IGNORECASE)
        if match:
            location = match.group(1).strip()
            if len(location) > 2:  # Avoid short words
                return location.title()
        
        return ""

    def _extract_place_query(self, message: str) -> str:
        """Extract what the user is looking for"""
        place_types = ["hotel", "restaurant", "cafe", "bar", "museum", "park", "beach", "attraction", "shop", "store", "gym", "hospital"]
        
        message_lower = message.lower()
        for place_type in place_types:
            if place_type in message_lower:
                return place_type
        
        # Default to restaurant if no specific type found
        return "restaurant"

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
                full_response = loop.run_until_complete(travel_agent.run(prompt, conversation_history))
            finally:
                loop.close()
            
            status_placeholder.empty()
            message_placeholder.markdown(full_response)
            
            # Add assistant message to chat history
            st.session_state.messages.append({"role": "assistant", "content": full_response})
            
            # Debug info
            if st.session_state.debug_mode:
                with st.expander("📋 Debug Info"):
                    st.write(f"Response type: {type(full_response)}")
                    st.write("**Conversation History Sent to LLM:**")
                    if conversation_history:
                        for i, msg in enumerate(conversation_history[-5:]):  # Show last 5 messages
                            st.write(f"{i+1}. **{msg['role'].title()}**: {msg['content'][:100]}{'...' if len(msg['content']) > 100 else ''}")
                    else:
                        st.write("No previous conversation history")
                    st.write("**Current Query:**", prompt)
                    st.write("**Full Response:**", full_response)
        
        except Exception as e:
            status_placeholder.empty()
            error_msg = f"❌ Error: {str(e)}"
            message_placeholder.error(error_msg)
            if st.session_state.debug_mode:
                with st.expander("📋 Error Details"):
                    st.error(str(e), icon="🚨")

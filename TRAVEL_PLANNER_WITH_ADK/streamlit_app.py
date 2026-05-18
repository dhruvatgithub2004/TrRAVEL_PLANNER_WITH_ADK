import streamlit as st
import os
from dotenv import load_dotenv
from google.adk.models.lite_llm import LiteLlm
from google.adk.models.llm_request import LlmRequest
from google.genai.types import Content, Part
import asyncio
from datetime import datetime

# ====================== CONFIG ======================
load_dotenv()
load_dotenv(os.path.join(os.path.dirname(__file__), "travel_planner", ".env"))

DEEPSEEK_API_KEY = st.secrets.get("DEEPSEEK_API_KEY") or os.getenv("DEEPSEEK_API_KEY")
if DEEPSEEK_API_KEY:
    os.environ["DEEPSEEK_API_KEY"] = DEEPSEEK_API_KEY

TAVILY_API_KEY = st.secrets.get("TAVILY_API_KEY") or os.getenv("TAVILY_API_KEY")
if TAVILY_API_KEY:
    os.environ["TAVILY_API_KEY"] = TAVILY_API_KEY

from travel_planner.tools import web_search, find_nearby_places_open

llm = LiteLlm(model="deepseek/deepseek-chat")

if not DEEPSEEK_API_KEY:
    st.error("DEEPSEEK_API_KEY is missing!")
    st.stop()

# ====================== AGENT CLASS ======================
class SimpleTravelAgent:
    def __init__(self, llm):
        self.llm = llm

    async def _gather_context(self, message: str) -> str:
        message_lower = message.lower()
        parts = []

        # Web Search
        if any(word in message_lower for word in ["event", "news", "current", "latest", "weather", "visa", "flight", "festival", "what", "how", "best"]):
            try:
                result = web_search(message)
                if result and "No results found" not in str(result):
                    parts.append(f"WEB SEARCH:\n{result}")
            except:
                pass

        # Nearby Places
        if any(word in message_lower for word in ["near", "nearby", "around", "hotel", "restaurant", "cafe", "beach"]):
            location = self._extract_location(message)
            if location:
                try:
                    result = find_nearby_places_open("attraction", location)
                    if result:
                        parts.append(f"NEARBY PLACES near {location}:\n{result}")
                except:
                    pass

        return "\n\n".join(parts)

    def _extract_location(self, message: str) -> str:
        import re
        match = re.search(r'\b(?:in|near|around|close to)\s+([A-Za-z\s]+)', message, re.IGNORECASE)
        return match.group(1).strip().title() if match else ""

    async def generate_stream(self, user_message: str, tool_context: str, history: list = None):
        """Async generator for streaming"""
        try:
            enriched = user_message
            if tool_context:
                enriched = f"[Real-time context]\n{tool_context}\n\nUser: {user_message}"

            contents = [
                Content(role="user", parts=[Part(text=_build_system_prompt())]),
                Content(role="model", parts=[Part(text="Understood.")]),
            ]

            if history:
                for msg in history[-6:]:
                    role = "user" if msg["role"] == "user" else "model"
                    contents.append(Content(role=role, parts=[Part(text=msg["content"])]))

            contents.append(Content(role="user", parts=[Part(text=enriched)]))

            request = LlmRequest(contents=contents, config={"temperature": 0.7, "max_output_tokens": 2000})

            response_gen = self.llm.generate_content_async(request)
            async for response in response_gen:
                if response.content and response.content.parts:
                    for part in response.content.parts:
                        if part.text:
                            yield part.text

        except Exception as e:
            yield f"\n\nError: {str(e)}"


def _build_system_prompt() -> str:
    now = datetime.now()
    return f"""You are a helpful travel concierge. Today's date is {now.strftime("%A, %B %d, %Y")}.
Be friendly, concise and useful."""


# ====================== INITIALIZE ======================
travel_agent = SimpleTravelAgent(llm)

st.set_page_config(page_title="Travel Planner", page_icon="🌍", layout="wide")
st.title("🌍 Travel Planner Chatbot")
st.caption("Streaming enabled • Powered by DeepSeek")

if "messages" not in st.session_state:
    st.session_state.messages = []

# Sidebar
with st.sidebar:
    if st.button("Clear Chat"):
        st.session_state.messages = []
        st.rerun()
    st.checkbox("Debug Mode", key="debug_mode")

# Display messages
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# ====================== CHAT INPUT ======================
if prompt := st.chat_input("Where do you want to go?"):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        message_placeholder = st.empty()
        status = st.empty()
        status.info("🔍 Searching & thinking...")

        try:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)

            history = st.session_state.messages[:-1]
            tool_context = loop.run_until_complete(travel_agent._gather_context(prompt))

            status.info("✍️ Generating response...")

            full_response = ""
            stream = travel_agent.generate_stream(prompt, tool_context, history)

            # Proper streaming in Streamlit
            while True:
                try:
                    chunk = loop.run_until_complete(stream.__anext__())
                    full_response += chunk
                    message_placeholder.markdown(full_response + "▌")
                except StopAsyncIteration:
                    break
                except Exception:
                    break

            message_placeholder.markdown(full_response)

            st.session_state.messages.append({"role": "assistant", "content": full_response})

            # Debug
            if st.session_state.debug_mode and tool_context:
                with st.expander("Debug - Tool Context"):
                    st.code(tool_context)

        except Exception as e:
            message_placeholder.error(f"Error: {str(e)}")
        finally:
            status.empty()
            try:
                loop.close()
            except:
                pass

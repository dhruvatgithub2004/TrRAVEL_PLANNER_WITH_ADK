# 🌍 Travel Planner Chatbot - Streamlit App

A modern, interactive chatbot interface for the Travel Planner application powered by Google ADK and AI.

## Features

✨ **Key Capabilities:**
- 💬 **Interactive Chat Interface** - Conversational UI for travel planning
- 🤖 **Google ADK Integration** - Uses Google's Agent Development Kit with LiteLlm
- 🌐 **Web Search** - DuckDuckGo-powered travel information retrieval
- 📍 **Location Search** - Find nearby places and attractions using OpenStreetMap
- 📰 **Travel News & Events** - Get current travel events and recommendations
- 💾 **Chat History** - Persistent conversation history within the session
- 🐛 **Debug Mode** - View raw responses and troubleshoot issues

## Prerequisites

Make sure you have:
1. **Python 3.8+** installed
2. **Required environment variable:** `DEEPSEEK_API_KEY` - Get it from https://platform.deepseek.com/
3. **All dependencies installed** - See [Installation](#installation)

## Installation

1. **Install Python dependencies:**
   ```bash
   pip install streamlit google-adk litellm duckduckgo-search geopy requests python-dotenv openai
   ```

2. **Create a `.env` file in the project root:**
   ```bash
   DEEPSEEK_API_KEY=your_deepseek_api_key_here
   ```

3. **Verify the travel_planner module is properly set up:**
   - Ensure `travel_planner/` folder contains:
     - `agent.py` - Main agent configuration
     - `supporting_agents.py` - News and places agents
     - `tools.py` - Web search and location search tools

## Running the App

### Start the Streamlit App:
```bash
streamlit run streamlit_app.py
```

The app will open in your default browser at `http://localhost:8501`

## How to Use

1. **Type your travel question** in the chat input box
   - Examples:
     - "I want to visit Paris in summer, what activities should I do?"
     - "Find me beaches near Miami"
     - "What events are happening in Tokyo next month?"

2. **Wait for the AI response** - The agent will:
   - Process your request using the travel concierge agent
   - Consult supporting agents for travel inspiration, news, and places
   - Search the web for current information
   - Provide recommendations

3. **View Chat History** - All messages are stored in the session
   - Clear history with the "🗑️ Clear Chat History" button in the sidebar

4. **Enable Debug Mode** - For development/troubleshooting:
   - Toggle "🐛 Debug Mode" in the sidebar
   - View raw response objects and error details

## Project Structure

```
travel_planner/
├── agent.py                 # Root travel planner agent
├── supporting_agents.py     # News and places agents
└── tools.py                 # Search and location tools

streamlit_app.py             # This Streamlit application
```

## Architecture

```
User Input (Chat)
        ↓
streamlit_app.py (Streamlit UI)
        ↓
SimpleTravelAgent (LiteLlm + Tools)
        ↓
External APIs:
  ├── DuckDuckGo (web search)
  ├── OpenStreetMap/Nominatim (geocoding)
  ├── Overpass API (place discovery)
  └── Deepseek Chat API (LLM)
```

## Configuration

### Sidebar Options
- **🐛 Debug Mode** - Toggle to see technical details about responses
- **🗑️ Clear Chat History** - Remove all messages and start fresh
- **💡 Tips** - Usage suggestions

## Troubleshooting

### "Error: DEEPSEEK_API_KEY not set"
- Ensure you have a `.env` file with your Deepseek API key
- The key must be valid and active: https://platform.deepseek.com/

### "Module not found: travel_planner"
- Ensure you're running streamlit from the project root directory
- Verify the `travel_planner/` folder exists with all required files

### Slow responses
- Initial setup can be slower as models are loaded
- Complex queries may take longer - this is normal
- Check internet connection for web search operations

### No response from agent
- Check if `DEEPSEEK_API_KEY` is valid
- Verify all dependencies are installed: `pip install -r requirements.txt`
- Enable Debug Mode to see detailed error information

## Advanced Usage

### Customizing the Agent Instructions

Edit `travel_planner/agent.py` to modify the root agent's behavior:
```python
root_agent = Agent(
    name="travel_planner_main",
    model=LiteLlm(model="deepseek/deepseek-chat"),
    description="Your custom description",
    instruction="Your custom instructions",  # <- Modify here
    sub_agents=[travel_inspiration_agent]
)
```

### Adding New Tools

In `travel_planner/tools.py`, create new FunctionTools:
```python
new_tool = FunctionTool(func=your_function)
search_agent.tools.append(new_tool)
```

## Performance Notes

- First run may take longer as models initialize
- Web searches use DuckDuckGo (no API key needed)
- Location searches use free OpenStreetMap APIs
- All API calls are rate-limited for stability

## License

Your project license here

## Support

For issues or questions:
1. Check the troubleshooting section above
2. Enable Debug Mode for detailed error information
3. Verify all environment variables are set correctly
4. Review your Deepseek API quota at https://platform.deepseek.com/

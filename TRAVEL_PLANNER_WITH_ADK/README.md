# 🌍 Travel Planner with Google ADK

An intelligent travel planning assistant powered by Google's Agent Development Kit (ADK) with Streamlit UI.

## Overview

This project provides a comprehensive travel planning system with two interfaces:
- **Streamlit Chatbot** (NEW) - Interactive chat interface for travel planning
- **FastAPI Backend** - API-based travel planning service

### Key Features

🤖 **AI-Powered Travel Agent**
- Personalized travel recommendations
- Destination inspiration and discovery
- Activity suggestions based on preferences

🌐 **Multi-Agent Architecture**
- Main Travel Planning Agent (Concierge)
- Travel Inspiration Agent
- News & Events Agent
- Place Discovery Agent

🔍 **Integrated Search Capabilities**
- Web search via DuckDuckGo
- Location search using OpenStreetMap
- Real-time travel information
- Event recommendations

💬 **User Interfaces**
- **Streamlit App** - Modern, interactive chat interface
- **FastAPI** - RESTful API for integration

## Project Structure

```
TRAVEL_PLANNER_WITH_ADK/
├── travel_planner/                 # Core module
│   ├── agent.py                    # Main travel concierge agent
│   ├── supporting_agents.py        # News, places, inspiration agents
│   └── tools.py                    # Search and location tools
├── streamlit_app.py                # 🆕 Streamlit chatbot interface
├── fastapi_api.py                  # FastAPI backend
├── requirements_streamlit.txt      # Streamlit dependencies
├── run_streamlit.ps1               # Windows startup script
├── run_streamlit.sh                # Linux/Mac startup script
├── STREAMLIT_APP_GUIDE.md          # Detailed Streamlit documentation
├── package.json                    # Node.js configuration
├── pyproject.toml                  # Python project metadata
└── README.md                       # This file
```

## Quick Start

### Option 1: Streamlit App (Recommended)

1. **Setup environment:**
   ```bash
   # Create Python environment
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   
   # Install dependencies
   pip install -r requirements_streamlit.txt
   ```

2. **Configure API key:**
   - Create a `.env` file in the project root
   - Add: `DEEPSEEK_API_KEY=your_key_from_deepseek.com`

3. **Run the app:**
   ```bash
   # Windows (PowerShell)
   .\run_streamlit.ps1
   
   # Linux/Mac (Bash)
   bash run_streamlit.sh
   
   # Or directly
   streamlit run streamlit_app.py
   ```

The app opens at `http://localhost:8501`

### Option 2: FastAPI Backend

```bash
pip install -r requirements.txt
python fastapi_api.py
```

API available at `http://localhost:8001`

## Prerequisites

- **Python 3.8+**
- **Deepseek API Key** - Get from https://platform.deepseek.com/
- **Internet connection** - For web search and APIs

## Technology Stack

### Backend
- **Google ADK** - Agent Development Kit for multi-agent systems
- **LiteLlm** - LLM abstraction layer
- **Deepseek Chat** - Primary LLM model
- **FastAPI** - API framework (optional)

### Frontend
- **Streamlit** - Interactive web framework
- **Python 3.8+** - Core language

### External APIs
- **DuckDuckGo** - Web search (free, no API key)
- **OpenStreetMap** - Geolocation services
- **Nominatim** - Geocoding service
- **Overpass** - Place discovery

## Agent Architecture

### Root Agent (Travel Concierge)
```
Role: Main travel planning coordinator
Description: Exclusive travel concierge helping users plan vacations
Model: Deepseek Chat
Sub-agents: travel_inspiration_agent
```

### Travel Inspiration Agent
```
Role: Destination and activity discovery
Tools:
  - news_agent (current events)
  - places_agent (location search)
```

### Supporting Agents
- **News Agent**: Travel events and recommendations
- **Places Agent**: Nearby attractions and amenities

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

## Usage Examples

### Example Queries

📍 **Destination Planning:**
```
"I want to visit Paris in summer. What activities should I do?"
"Find me a beach destination for my family vacation."
"What's the best time to visit Tokyo?"
```

🏨 **Place Discovery:**
```
"Find hotels near Eiffel Tower"
"What restaurants are popular near Times Square?"
"Show me cafes in Barcelona"
```

📰 **Travel News:**
```
"What events are happening in Miami next month?"
"What's trending in travel destinations?"
"Any festivals coming up in Europe?"
```

## Configuration

### Environment Variables
```bash
DEEPSEEK_API_KEY=your_api_key_here
```

### Customize Agent Behavior

Edit `travel_planner/agent.py`:
```python
root_agent = Agent(
    name="travel_planner_main",
    model=LiteLlm(model="deepseek/deepseek-chat"),
    instruction="Your custom instructions here",
    sub_agents=[travel_inspiration_agent]
)
```

### Modify Search Tools

Edit `travel_planner/tools.py` to:
- Add new search providers
- Modify search radius or result limits
- Customize place discovery queries

## API Reference (FastAPI)

### Endpoint: POST /chat
```json
{
  "message": "What destinations would you recommend for a beach vacation?",
  "thread_id": "unique-conversation-id"
}
```

### Response
```json
{
  "response": "Based on your preferences...",
  "thread_id": "unique-conversation-id"
}
```

## Troubleshooting

### Issue: "DEEPSEEK_API_KEY not found"
**Solution:** Create a `.env` file with your API key
```bash
echo "DEEPSEEK_API_KEY=your_key" > .env
```

### Issue: "Module not found: travel_planner"
**Solution:** Ensure you're in the project root directory
```bash
cd TRAVEL_PLANNER_WITH_ADK
python -m streamlit run streamlit_app.py
```

### Issue: Slow responses
**Normal behavior** - Initial setup loads models. Web searches and agent reasoning take time.

### Issue: "Connection refused" at localhost:8501
**Solution:** Streamlit is already running or port is in use
```bash
# Kill existing process
lsof -ti:8501 | xargs kill -9  # Mac/Linux
Get-Process | Where-Object {$_.Port -eq 8501}  # Windows
```

### Issue: No results from location search
**Check:**
- Internet connection is active
- Location name is spelled correctly
- OpenStreetMap API is reachable

## Performance Optimization

1. **Cache responses** - Session state retains chat history
2. **Rate limiting** - DuckDuckGo search is rate-limited
3. **Async operations** - Streamlit handles UI responsiveness
4. **Lazy loading** - Models load on first request

## Development

### Adding New Tools

1. Create a function in `travel_planner/tools.py`:
```python
def new_tool_function(query: str) -> str:
    """Tool description"""
    return result

new_tool = FunctionTool(func=new_tool_function)
```

2. Add to an agent:
```python
agent.tools.append(new_tool)
```

### Adding New Agents

```python
from google.adk.agents import Agent
from google.adk.models.lite_llm import LiteLlm

my_agent = Agent(
    name="my_agent",
    model=LiteLlm(model="deepseek/deepseek-chat"),
    description="Agent description",
    instruction="Agent instructions",
    tools=[...relevant_tools...]
)
```

## Advanced Features

### Debug Mode
Enable in Streamlit sidebar to:
- View raw agent responses
- See error details
- Inspect response types
- Troubleshoot issues

### Chat History
- Persistent within session
- Cleared on browser refresh or "Clear Chat History" button
- Not saved to disk by default

### Custom Instructions
Modify agent instructions in `travel_planner/agent.py` to:
- Change personality/tone
- Add specific travel expertise
- Restrict certain queries
- Add domain knowledge

## Contributing

1. Fork the repository
2. Create feature branch: `git checkout -b feature/your-feature`
3. Commit changes: `git commit -am 'Add feature'`
4. Push to branch: `git push origin feature/your-feature`
5. Submit a pull request

## License

[Your License Here]

## Support & Documentation

- **Streamlit App Guide**: See [STREAMLIT_APP_GUIDE.md](STREAMLIT_APP_GUIDE.md)
- **Google ADK Docs**: https://google.dev/generative-ai/docs/
- **Deepseek API**: https://platform.deepseek.com/

## Roadmap

- [ ] Multi-language support
- [ ] Integration with booking APIs
- [ ] User preferences persistence
- [ ] Real-time availability checking
- [ ] Price comparison tools
- [ ] Travel insurance recommendations
- [ ] Weather forecasting integration
- [ ] Mobile app

## FAQ

**Q: Can I use a different LLM model?**
A: Yes, modify the model in `LiteLlm(model="...")` in agent.py

**Q: How do I save chat history?**
A: Implement a database backend in streamlit_app.py

**Q: Can I deploy this to production?**
A: Yes, use Streamlit Cloud, Heroku, or AWS with proper security setup

**Q: Is my API key secure?**
A: Keep it in `.env` (not tracked in git). Use environment-specific secrets in production.

## Credits

- Built with [Google ADK](https://google.dev/generative-ai/docs/)
- Frontend: [Streamlit](https://streamlit.io/)
- Search: [DuckDuckGo](https://duckduckgo.com/)
- Geolocation: [OpenStreetMap](https://www.openstreetmap.org/)
- LLM: [Deepseek Chat](https://www.deepseek.com/)

---

**Last Updated**: April 2026
**Status**: Active Development ✅

# Travel Planner with Google ADK

An AI-powered travel planning chatbot built with Google's Agent Development Kit (ADK), Streamlit, and DeepSeek Chat.

## Features

- Conversational travel concierge powered by DeepSeek Chat
- Real-time web search via Tavily for current travel info, events, and news
- Nearby place discovery using OpenStreetMap (no API key required)
- Multi-agent architecture: inspiration, news, and places agents
- Interactive Streamlit chat UI with conversation history
- Optional FastAPI backend for AG-UI integration

## Project Structure

```
TRAVEL_PLANNER_WITH_ADK/
├── streamlit_app.py          # Main Streamlit chatbot interface
├── fastapi_api.py            # FastAPI + AG-UI backend
├── requirements.txt          # Python dependencies
├── runtime.txt               # Python version (3.12)
├── pyproject.toml            # Project metadata
└── travel_planner/
    ├── agent.py              # Root travel concierge agent
    ├── supporting_agents.py  # News, places, inspiration sub-agents
    └── tools.py              # Web search and location tools
```

## Agent Architecture

```
root_agent (travel_planner_main)
└── travel_inspiration_agent
    ├── news_agent       → Tavily web search
    └── places_agent     → OpenStreetMap / Overpass API
```

The Streamlit app uses a lighter `SimpleTravelAgent` that calls the same tools directly for faster responses.

## Prerequisites

- Python 3.12
- [DeepSeek API key](https://platform.deepseek.com/) — free tier available
- [Tavily API key](https://app.tavily.com/) — free tier (1,000 searches/month)

## Local Setup

```bash
# 1. Clone and enter the project
git clone <repo-url>
cd TRAVEL_PLANNER_WITH_ADK

# 2. Create and activate a virtual environment
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Add API keys to a .env file
echo "DEEPSEEK_API_KEY=your_deepseek_key" > .env
echo "TAVILY_API_KEY=your_tavily_key"    >> .env

# 5. Run the Streamlit app
streamlit run streamlit_app.py
```

App opens at `http://localhost:8501`.

To run the FastAPI backend instead:

```bash
python fastapi_api.py
# API available at http://localhost:8001
```

## Deploying to Streamlit Cloud

1. Push the repository to GitHub.
2. Go to [share.streamlit.io](https://share.streamlit.io) and connect the repo.
3. Set the main file to `streamlit_app.py`.
4. Under **Settings → Secrets**, add:

```toml
DEEPSEEK_API_KEY = "your_deepseek_key"
TAVILY_API_KEY   = "your_tavily_key"
```

5. Deploy — the app will install dependencies from `requirements.txt` automatically.

## Environment Variables

| Variable | Required | Description |
|---|---|---|
| `DEEPSEEK_API_KEY` | Yes | DeepSeek Chat API key |
| `TAVILY_API_KEY` | Yes | Tavily Search API key |

## Example Queries

**Destination planning**
- "What's the best time to visit Japan?"
- "Suggest a beach destination for a family trip."

**Place discovery**
- "Find restaurants near the Eiffel Tower."
- "Show me hotels in Barcelona."

**Travel news & events**
- "What festivals are happening in Europe this summer?"
- "Any travel advisories for Thailand right now?"

## Tech Stack

| Layer | Technology |
|---|---|
| LLM | DeepSeek Chat via LiteLLM |
| Agent framework | Google ADK |
| UI | Streamlit |
| API backend | FastAPI + AG-UI ADK |
| Web search | Tavily |
| Geocoding | Nominatim (OpenStreetMap) |
| Place discovery | Overpass API |


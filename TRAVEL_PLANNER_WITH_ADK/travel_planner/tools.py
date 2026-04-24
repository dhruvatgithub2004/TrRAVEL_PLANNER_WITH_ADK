from google.adk.tools.agent_tool import AgentTool
from google.adk.agents import Agent
import os
from geopy.geocoders import Nominatim
import requests
from google.adk.models.lite_llm import LiteLlm
from duckduckgo_search import DDGS
from google.adk.tools import FunctionTool
from dotenv import load_dotenv
from datetime import datetime

# Load .env from the project root and fallback to the travel_planner subfolder.
load_dotenv()
load_dotenv(os.path.join(os.path.dirname(__file__), ".env"))

DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY")
if DEEPSEEK_API_KEY:
    os.environ["DEEPSEEK_API_KEY"] = DEEPSEEK_API_KEY

def web_search(query: str) -> str:
    """Search the web using DuckDuckGo."""
    current_year = str(datetime.now().year)
    recency_words = ["latest", "recent", "current", "new", "developments", "update", current_year]
    if any(w in query.lower() for w in recency_words) and current_year not in query:
        query = f"{query} {current_year}"
    with DDGS() as ddgs:
        results = [r for r in ddgs.text(query, max_results=5)]
    formatted = []
    for r in results:
        formatted.append(f"**{r['title']}** ({r['href']}): {r['body'][:300]}...")
    return "\n\n".join(formatted) or "No results found."

google_search = FunctionTool(
    func=web_search
)



_search_agent= Agent(
    name="google_search_wrapped_agent",
    model = LiteLlm(model="deepseek/deepseek-chat"),
    description="An agent providing Google-search grounding capability",
    instruction= f"""
        TODAY'S DATE: {datetime.now().strftime("%A, %B %d, %Y")}. Always treat {datetime.now().year} as the current year when searching or answering.
        Answer the user's question directly using google_search grounding tool; Provide a brief but concise response.
        Rather than a detail response, provide the immediate actionable item for a tourist or traveler, in a single sentence.
        Do not ask the user to check or look up information for themselves, that's your role; do your best to be informative.
        When searching for latest/recent/current information, always include "{datetime.now().year}" in your search query.
        IMPORTANT:
        - Always return your response in bullet points
        - Specify what matters to the user
        - Do not reference {datetime.now().year - 1} as the current year; it is {datetime.now().year}
    """,
    tools=[google_search]
)
google_search_grounding = AgentTool(agent=_search_agent)



def find_nearby_places_open(query: str, location: str, radius: int = 3000, limit: int = 5) -> str:
    """
    Finds nearby places for any text query using ONLY free OpenStreetMap APIs (no API key needed).
    
    Args:
        query (str): What you’re looking for (e.g., "restaurant", "hospital", "gym", "bar").
        location (str): The city or area to search in.
        radius (int): Search radius in meters (default: 3000).
        limit (int): Number of results to show (default: 5).
    
    Returns:
        str: List of matching place names and addresses.
    """

    try:
        # Step 1: Geocode the location to get coordinates
        geolocator = Nominatim(user_agent="open_place_finder")
        loc = geolocator.geocode(location)
        if not loc:
            return f"Could not find location '{location}'."

        lat, lon = loc.latitude, loc.longitude

        # Step 2: Query Overpass API for matching places
        overpass_url = "https://overpass-api.de/api/interpreter"
        overpass_query = f"""
        [out:json][timeout:25];
        (
          node["name"~"{query}", i](around:{radius},{lat},{lon});
          node["amenity"~"{query}", i](around:{radius},{lat},{lon});
          node["shop"~"{query}", i](around:{radius},{lat},{lon});
        );
        out body {limit};
        """

        response = requests.get(overpass_url, params={"data": overpass_query})
        if response.status_code != 200:
            return f"Overpass API error: {response.status_code}"

        data = response.json()
        elements = data.get("elements", [])
        if not elements:
            return f"No results found for '{query}' near {location}."

        # Step 3: Format results
        output = [f"Top results for '{query}' near {location}:"]
        for el in elements[:limit]:
            name = el.get("tags", {}).get("name", "Unnamed place")
            street = el.get("tags", {}).get("addr:street", "")
            city = el.get("tags", {}).get("addr:city", "")
            full_addr = ", ".join(filter(None, [street, city]))
            output.append(f"- {name} | {full_addr if full_addr else 'Address not available'}")

        return "\n".join(output)

    except Exception as e:
        return f"Error searching for '{query}' near '{location}': {str(e)}"


location_search_tool = FunctionTool(func=find_nearby_places_open)

places_agent = Agent(
    model = LiteLlm(model="deepseek/deepseek-chat"),
    name="places_agent",
    description="Suggests locations based on user preferences",
    instruction="""
            You are responsible for making suggestions on actual places based on the user's query. Limit the choices to 10 results.
            Each place must have a name, location, and address.
            You can use the places_tool to find the latitude and longitude of the place and address.
        """,
    tools=[location_search_tool]    
)
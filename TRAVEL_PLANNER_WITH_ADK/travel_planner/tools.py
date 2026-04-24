from google.adk.tools.agent_tool import AgentTool
from google.adk.agents import Agent
import os
import requests
from math import radians, cos, sin, asin, sqrt
from geopy.geocoders import Nominatim
from google.adk.models.lite_llm import LiteLlm
from tavily import TavilyClient
from google.adk.tools import FunctionTool
from dotenv import load_dotenv
from datetime import datetime

# Load environment variables
load_dotenv()
load_dotenv(os.path.join(os.path.dirname(__file__), ".env"))

DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY")
if DEEPSEEK_API_KEY:
    os.environ["DEEPSEEK_API_KEY"] = DEEPSEEK_API_KEY

# --- HELPER FUNCTIONS ---

def calculate_distance(lat1, lon1, lat2, lon2):
    """Calculate the great circle distance in kilometers."""
    R = 6371 # Earth radius in km
    dLat, dLon = radians(lat2 - lat1), radians(lon2 - lon1)
    a = sin(dLat/2)**2 + cos(radians(lat1)) * cos(radians(lat2)) * sin(dLon/2)**2
    return 2 * R * asin(sqrt(a))

# --- WEB SEARCH TOOL ---

def web_search(query: str) -> str:
    """Search the web using Tavily."""
    # FIX: Truncate query to stay under the 400 character limit
    safe_query = query[:390]
    
    api_key = os.getenv("TAVILY_API_KEY")
    if not api_key:
        return "Search unavailable: TAVILY_API_KEY is not set."
    
    current_year = str(datetime.now().year)
    recency_words = ["latest", "recent", "current", "new", "developments", "update", current_year]
    
    if any(w in safe_query.lower() for w in recency_words) and current_year not in safe_query:
        safe_query = f"{safe_query} {current_year}"
        
    client = TavilyClient(api_key=api_key)
    response = client.search(safe_query, max_results=5)
    results = response.get("results", [])
    
    formatted = []
    for r in results:
        # Keep content chunks concise
        formatted.append(f"**{r['title']}** ({r['url']}): {r['content'][:300]}...")
    
    return "\n\n".join(formatted) or "No results found."

google_search = FunctionTool(func=web_search)

# --- GOOGLE SEARCH AGENT ---

_search_agent = Agent(
    name="google_search_wrapped_agent",
    model=LiteLlm(model="deepseek/deepseek-chat"),
    description="An agent providing Google-search grounding capability",
    instruction=f"""
        TODAY'S DATE: {datetime.now().strftime("%A, %B %d, %Y")}. 
        Answer the user's question directly using the google_search tool.
        
        CRITICAL RULES:
        1. Your search queries MUST be short (keywords only, under 60 characters).
        2. Provide actionable items for travelers in bullet points.
        3. Always treat {datetime.now().year} as the current year.
        4. If a request has multiple parts (e.g., two cities), call the tool separately for each.
    """,
    tools=[google_search]
)
google_search_grounding = AgentTool(agent=_search_agent)

# --- NEARBY PLACES TOOL ---

def find_nearby_places_open(query: str, location: str, radius: int = 3000, limit: int = 5) -> str:
    """Finds nearby places using OpenStreetMap/Overpass API."""
    try:
        # Step 1: Geocode
        geolocator = Nominatim(user_agent="travel_planner_pro_agent")
        loc = geolocator.geocode(location)
        if not loc:
            return f"Could not find location '{location}'."

        lat, lon = loc.latitude, loc.longitude

        # Step 2: Overpass Query with headers to fix 406 Error
        overpass_url = "https://overpass-api.de/api/interpreter"
        
        # Improved query logic: searches name, amenity, and cuisine tags
        overpass_query = f"""
        [out:json][timeout:25];
        (
          node["name"~"{query}", i](around:{radius},{lat},{lon});
          node["amenity"~"{query}", i](around:{radius},{lat},{lon});
          node["cuisine"~"{query}", i](around:{radius},{lat},{lon});
          node["shop"~"{query}", i](around:{radius},{lat},{lon});
        );
        out body;
        """

        # FIX: Added User-Agent headers to prevent 406 errors
        headers = {'User-Agent': 'TravelPlannerApp/1.0 (contact@example.com)'}
        response = requests.get(overpass_url, params={"data": overpass_query}, headers=headers)
        
        if response.status_code != 200:
            return f"Overpass API error: {response.status_code}. Check if query is too complex."

        data = response.json()
        elements = data.get("elements", [])
        if not elements:
            return f"No results found for '{query}' within {radius}m of {location}."

        # Step 3: Format and calculate distance
        output = [f"Top results for '{query}' near {location}:"]
        
        # Sort by proximity
        results_list = []
        for el in elements:
            e_lat, e_lon = el.get("lat"), el.get("lon")
            dist = calculate_distance(lat, lon, e_lat, e_lon)
            
            tags = el.get("tags", {})
            name = tags.get("name", "Unnamed place")
            street = tags.get("addr:street", "")
            city = tags.get("addr:city", "")
            full_addr = ", ".join(filter(None, [street, city]))
            
            results_list.append({
                "name": name,
                "dist": dist,
                "addr": full_addr if full_addr else "Address not available"
            })

        # Sort by distance and apply limit
        sorted_results = sorted(results_list, key=lambda x: x['dist'])[:limit]

        for r in sorted_results:
            output.append(f"- {r['name']} | Distance: {r['dist']:.2f} km | Address: {r['addr']}")

        return "\n".join(output)

    except Exception as e:
        return f"Error searching for '{query}' near '{location}': {str(e)}"

location_search_tool = FunctionTool(func=find_nearby_places_open)

# --- PLACES AGENT ---

places_agent = Agent(
    model=LiteLlm(model="deepseek/deepseek-chat"),
    name="places_agent",
    description="Suggests locations based on user preferences",
    instruction="""
        You are a destination expert. Use the location_search_tool to find specific places.
        Always verify the distance provided by the tool before recommending a spot as "walking distance."
        - Walking distance: < 1.2 km
        - Short drive: 1.2 km - 5 km
        Each suggestion must include the name, the calculated distance, and the address.
    """,
    tools=[location_search_tool]    
)

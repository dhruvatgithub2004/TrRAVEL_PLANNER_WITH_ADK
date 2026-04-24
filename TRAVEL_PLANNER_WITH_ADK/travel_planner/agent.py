from google.adk.agents import Agent
import os
from openai import OpenAI
from google.adk.models.lite_llm import LiteLlm
from travel_planner.supporting_agents import travel_inspiration_agent
import os
DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY")
os.environ["DEEPSEEK_API_KEY"] = DEEPSEEK_API_KEY  
root_agent= Agent(
    name="travel_planner_main",
    model = LiteLlm(model="deepseek/deepseek-chat"),
    description = "An agent that helps users plan their travel itineraries.",
    instruction = """
     -You are an exclusive travel coincerge agent
     -You help users to discover their dream holiday destinations and plan their vacations
     -Use the inspiration_agent to get the best destination , news places nearby  e.g hotels , cafes etc near attractions and points of interest for the user.
     -You cannot use any tool dierectly
     """,
     sub_agents=[travel_inspiration_agent]
)
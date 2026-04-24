
from fastapi import FastAPI
from ag_ui_adk import ADKAgent, add_adk_fastapi_endpoint
from travel_planner.agent import root_agent

app = FastAPI()

@app.get("/")
def read_root():
    return {"message": "Welcome to the Travel Planner AG-UI API! Access the AG-UI at /ag-ui"}

adk_agent = ADKAgent(
    adk_agent=root_agent,
    app_name="travel_planner_app",
    user_id="default_user",
    use_in_memory_services=True
)

add_adk_fastapi_endpoint(app, adk_agent, path="/")
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="localhost", port=8001)

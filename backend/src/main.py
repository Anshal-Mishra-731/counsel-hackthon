import asyncio
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# Import Models for the background worker
from src.models.risk_agent import calculate_global_risk, master_routes
from src.models.disruption_sim import run_simulation

# Import the router from your exact folder structure
from src.api.routes import api_router

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("energy_twin_api")

def execute_pipeline_sync():
    """Synchronous execution of the 4-phase pipeline."""
    live_risk = calculate_global_risk(master_routes)
    return run_simulation(live_risk_report=live_risk)

async def periodic_pipeline_worker(app: FastAPI, interval_seconds: int = 3600):
    """Background loop that updates the simulation state every hour."""
    while True:
        try:
            logger.info("Starting background pipeline refresh...")
            loop = asyncio.get_running_loop()
            result = await loop.run_in_executor(None, execute_pipeline_sync)
            
            # Save the result to app state so the router can access it
            app.state.latest_simulation = result
            app.state.is_ready = True
            logger.info("Background pipeline refresh completed successfully.")
        except Exception as e:
            logger.error(f"Error during background pipeline update: {e}", exc_info=True)
            
        await asyncio.sleep(interval_seconds)

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan event to manage the startup and shutdown of the background worker."""
    logger.info("Starting National Energy Digital Twin API...")
    app.state.latest_simulation = {}
    app.state.is_ready = False
    
    worker_task = asyncio.create_task(periodic_pipeline_worker(app, interval_seconds=3600))
    
    yield
    
    logger.info("Shutting down background workers and server...")
    worker_task.cancel()
    try:
        await worker_task
    except asyncio.CancelledError:
        logger.info("Background worker stopped cleanly.")

# Initialize FastAPI App
app = FastAPI(
    title="National Energy Digital Twin",
    version="v1",
    lifespan=lifespan
)

# CORS Setup
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], 
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- ROUTER REGISTRATION ---
# This includes all endpoints from src/api/routes.py
app.include_router(api_router, prefix="/api/v1")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("src.main:app", host="0.0.0.0", port=8000, reload=True)
from fastapi import APIRouter, Request, HTTPException

# Initialize the router
api_router = APIRouter()

@api_router.get("/health", tags=["Health"])
async def health_check():
    """Simple filler health check."""
    return {"status": "online"}

@api_router.get("/simulation", tags=["Simulation"])
async def get_latest_simulation(request: Request):
    """Fetches the latest digital twin state from app memory."""
    if not getattr(request.app.state, "is_ready", False):
        raise HTTPException(status_code=503, detail="Simulation initializing. Try again shortly.")
    return request.app.state.latest_simulation
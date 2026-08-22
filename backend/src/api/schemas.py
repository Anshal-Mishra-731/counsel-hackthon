from typing import List, Optional, Dict, Any
from pydantic import BaseModel

class Destination(BaseModel):
    name: str
    port: str
    lat: float
    lng: float

class Supplier(BaseModel):
    country: str
    port: str
    lat: float
    lng: float

class MetaResponse(BaseModel):
    destination: Destination
    suppliers: List[Supplier]

class CorridorSummary(BaseModel):
    key: str
    name: str
    risk_score: int
    risk_bucket: str
    summary: str
    traffic_halted: bool
    waypoints: List[List[float]]

class CorridorsResponse(BaseModel):
    mode: str
    updated_at: int
    corridors: List[CorridorSummary]
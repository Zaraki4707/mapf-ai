from pydantic import BaseModel, Field
from typing import List, Optional


class Point(BaseModel):
    x: int
    y: int


class PathfinderRequest(BaseModel):
    grid_height: Optional[int] = Field(default=None, gt=0, description="Grid height (rows) - required if not using map_path")
    grid_width: Optional[int] = Field(default=None, gt=0, description="Grid width (columns) - required if not using map_path")
    map_path: Optional[str] = Field(default=None, description="Path to map file (alternative to grid dimensions)")
    algorithm: str = Field(default="independent_astar", description="Algorithm: independent_astar, cooperative_astar, hill_climbing, cbs, optimized_hc")
    num_agents: Optional[int] = Field(default=None, gt=0, le=50, description="Number of agents - will auto-generate positions if provided")
    obstacles: List[List[int]] = Field(default_factory=list, description="List of obstacle coordinates [x, y]")
    start: Optional[List[List[int]]] = Field(default=None, description="List of start positions [x, y]")
    pick: Optional[List[List[int]]] = Field(default=None, description="List of pickup positions for full mode")
    drop: Optional[List[List[int]]] = Field(default=None, description="List of drop positions for full mode")
    destination: Optional[List[List[int]]] = Field(default=None, description="List of destination positions [x, y]")


class PathfinderResponse(BaseModel):
    success: bool
    grid_height: Optional[int] = None
    grid_width: Optional[int] = None
    num_agents: Optional[int] = None
    total_cost: Optional[int] = None
    paths: Optional[List[List[List[int]]]] = None
    obstacles: Optional[List[List[int]]] = None
    message: Optional[str] = None


class MapInfo(BaseModel):
    id: str
    name: str
    category: str


class MapData(BaseModel):
    grid_height: int
    grid_width: int
    obstacles: List[List[int]]

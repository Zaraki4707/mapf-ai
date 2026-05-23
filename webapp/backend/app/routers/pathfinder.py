import sys
import os
from pathlib import Path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from fastapi import APIRouter, HTTPException
from typing import List, Tuple

from app.models import PathfinderRequest, PathfinderResponse, MapInfo, MapData
from algorithms import GridEnvironment, PathPlanner
from app.utils import map_loader

router = APIRouter()


@router.get("/maps", response_model=List[MapInfo])
async def get_maps():
    """Get list of available predefined maps."""
    maps = map_loader.list_predefined_maps()
    return [MapInfo(**m) for m in maps]


@router.get("/maps/{map_id}", response_model=MapData)
async def get_map_data(map_id: str):
    """Get grid dimensions and obstacles for a specific map."""
    maps = map_loader.list_predefined_maps()
    target_map = next((m for m in maps if m['id'] == map_id), None)
    
    if not target_map:
        raise HTTPException(status_code=404, detail="Map not found")
        
    data = map_loader.parse_map_file(target_map['path'])
    if not data:
        raise HTTPException(status_code=500, detail="Failed to parse map file")
        
    return MapData(**data)


def _load_map_from_file(map_path: str) -> Tuple[int, int, List[Tuple[int, int]]]:
    """Load map from file and return (height, width, obstacles)"""
    path = Path(map_path)
    if not path.exists():
        raise ValueError(f"Map file not found: {map_path}")

    # Use a consistent parser that matches map_loader and works for calculations
    with open(path, 'r') as f:
        lines = [line.strip() for line in f if line.strip()]
        height = len(lines)
        width = max(len(line) for line in lines) if lines else 0
        
        obstacles = []
        for y, line in enumerate(lines):
            for x, char in enumerate(line):
                if char == 'T':
                    obstacles.append((x, y)) # (col, row) for internal algorithm

    return height, width, obstacles


def _convert_coords(coords: List[List[int]]) -> List[Tuple[int, int]]:
    """Convert [row, col] to (col, row) for grid internal operations."""
    return [(c[1], c[0]) for c in coords]


def _convert_output(path: List[Tuple[int, int]]) -> List[List[int]]:
    """Convert (col, row) back to [row, col] for frontend."""
    return [[p[1], p[0]] for p in path]


def _generate_agent_positions(height: int, width: int, num_agents: int, obstacles: List[Tuple[int, int]]) -> Tuple[List[Tuple[int, int]], List[Tuple[int, int]], List[Tuple[int, int]], List[Tuple[int, int]]]:
    """Auto-generate start, pick, drop, destination positions for agents."""
    import random

    obstacle_set = set(obstacles)
    available_cells = [(x, y) for x in range(width) for y in range(height) if (x, y) not in obstacle_set]

    if len(available_cells) < num_agents * 4:
        raise ValueError(f"Not enough free cells for {num_agents} agents")

    random.shuffle(available_cells)

    starts = []
    picks = []
    drops = []
    destinations = []

    for i in range(num_agents):
        starts.append(available_cells[i])
        picks.append(available_cells[num_agents + i])
        drops.append(available_cells[num_agents * 2 + i])
        destinations.append(available_cells[num_agents * 3 + i])

    return starts, picks, drops, destinations


def _validate_input(request: PathfinderRequest) -> str:
    """Validate input and return error message if invalid."""
    if request.map_path:
        return None

    if not request.grid_height or not request.grid_width:
        return "Either provide grid_height/grid_width or map_path"

    if request.num_agents:
        return None

    if not request.start or not request.destination:
        return "Either provide num_agents or start/destination positions"

    n_agents = len(request.start)

    if n_agents != len(request.destination):
        return "Number of start positions must match number of destinations"

    if request.pick is not None and len(request.pick) != n_agents:
        return "Number of pickup positions must match number of start positions"

    if request.drop is not None and len(request.drop) != n_agents:
        return "Number of drop positions must match number of start positions"

    for name, coord_list in [
        ("obstacles", request.obstacles),
        ("start", request.start),
        ("destination", request.destination),
        ("pick", request.pick),
        ("drop", request.drop)
    ]:
        if not coord_list:
            continue
        for coord in coord_list:
            if len(coord) != 2:
                return f"Invalid coordinate format: {coord}"
            # Frontend/User provides [row, col]
            # Backends validates against [grid_height, grid_width]
            row, col = coord[0], coord[1]
            if not (0 <= row < request.grid_height and 0 <= col < request.grid_width):
                return f"Coordinate {coord} in {name} is out of bounds (Grid: {request.grid_height}x{request.grid_width})"

            # Obstacle check: Convert current grid obstacles to a set for O(1) lookup
            # If map_path is provided, we check against file_obstacles later, but 
            # for manual grid input or user-provided obstacles, we should check here.
            # However, start/goal should NOT be on existing obstacles.
            if name != "obstacles" and request.obstacles:
                if coord in request.obstacles:
                    return f"{name.capitalize()} position {coord} is an obstacle!"

    return None


@router.post("/find-path", response_model=PathfinderResponse)
async def find_path(request: PathfinderRequest):
    """
    Full route: Start → Pick → Drop → Destination
    """
    # 1. Load map first to get accurate obstacles if map_path is provided
    file_obstacles = []
    if request.map_path:
        try:
            height, width, file_obstacles = _load_map_from_file(request.map_path)
            # Update request with actual grid dimensions from file
            request.grid_height = height
            request.grid_width = width
            
            # Map file obstacles are internally (col, row), convert to [row, col] for validation
            # though we could just use them directly. Let's make a set for [row, col]
            map_obstacle_set = set((o[1], o[0]) for o in file_obstacles)
        except Exception as e:
            return PathfinderResponse(success=False, message=f"Failed to load map: {str(e)}")
    else:
        map_obstacle_set = set(tuple(o) for o in request.obstacles) if request.obstacles else set()

    # 2. Validate input against final dimensions and obstacles
    error = _validate_input(request)
    if error:
        return PathfinderResponse(success=False, message=error)

    # 3. Specific check for points hitting map obstacles (T cells)
    for name, points in [("start", request.start), ("destination", request.destination), 
                         ("pick", request.pick), ("drop", request.drop)]:
        if points:
            for p in points:
                if tuple(p) in map_obstacle_set:
                    return PathfinderResponse(success=False, message=f"{name.capitalize()} position {p} is an obstacle in the map!")

    # 4. Initialize grid and run
    if request.map_path:
        grid = GridEnvironment(request.grid_height, request.grid_width, file_obstacles)
    else:
        obstacles = _convert_coords(request.obstacles)
        grid = GridEnvironment(request.grid_height, request.grid_width, obstacles)
        file_obstacles = obstacles

    if request.num_agents:
        starts, picks, drops, destinations = _generate_agent_positions(
            grid.height, grid.width, request.num_agents, file_obstacles
        )
    else:
        starts = _convert_coords(request.start)
        picks = _convert_coords(request.pick) if request.pick else None
        drops = _convert_coords(request.drop) if request.drop else None
        destinations = _convert_coords(request.destination)

    import time
    start_time = time.time()
    
    planner = PathPlanner(grid)

    if request.pick and request.drop:
        result = planner.plan_full(starts, picks, drops, destinations, algorithm=request.algorithm)
    else:
        result = planner.plan_simple(starts, destinations, algorithm=request.algorithm)

    execution_time = time.time() - start_time
    print(f"\n[{request.algorithm}] Pathfinding Execution Time: {execution_time:.3f} seconds\n")

    if result.get('paths'):
        result['paths'] = [_convert_output(p) for p in result['paths']]
        # Pass obstacles back to frontend for visualization
        result['obstacles'] = [[o[1], o[0]] for o in file_obstacles]
    else:
        # result failed or is empty
        error_msg = result.get('message', "No valid paths found. Ensure points are reachable and not blocked by obstacles.")
        return PathfinderResponse(success=False, message=f"Pathfinding failed: {error_msg}")

    result['algorithm_used'] = request.algorithm

    return PathfinderResponse(**result)


@router.post("/find-simple-path", response_model=PathfinderResponse)
async def find_simple_path(request: PathfinderRequest):
    """
    Simple route: Start → Destination
    """
    error = _validate_input(request)
    if error:
        return PathfinderResponse(success=False, message=error)

    if request.map_path:
        height, width, file_obstacles = _load_map_from_file(request.map_path)
        grid = GridEnvironment(height, width, file_obstacles)
    else:
        obstacles = _convert_coords(request.obstacles)
        grid = GridEnvironment(request.grid_height, request.grid_width, obstacles)
        file_obstacles = obstacles

    if request.num_agents:
        starts, _, _, destinations = _generate_agent_positions(
            grid.height, grid.width, request.num_agents, file_obstacles
        )
    else:
        starts = _convert_coords(request.start)
        destinations = _convert_coords(request.destination)

    import time
    start_time = time.time()

    planner = PathPlanner(grid)

    result = planner.plan_simple(starts, destinations, algorithm=request.algorithm)
    
    execution_time = time.time() - start_time
    print(f"\n[{request.algorithm}] Simple Pathfinding Execution Time: {execution_time:.3f} seconds\n")

    if result.get('paths'):
        result['paths'] = [_convert_output(p) for p in result['paths']]
        # Pass obstacles back to frontend for visualization
        result['obstacles'] = [[o[1], o[0]] for o in file_obstacles]
    else:
        # result failed or is empty
        error_msg = result.get('message', "No valid paths found. Ensure points are reachable and not blocked by obstacles.")
        return PathfinderResponse(success=False, message=f"Pathfinding failed: {error_msg}")

    result['algorithm_used'] = request.algorithm

    return PathfinderResponse(**result)

    if result.get('paths'):
        result['paths'] = [_convert_output(p) for p in result['paths']]

    result['algorithm_used'] = request.algorithm

    return PathfinderResponse(**result)
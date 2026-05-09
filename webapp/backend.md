# Backend Plan for Multi-Agent Path Finding

## Project Overview
Build a FastAPI backend to serve the multi-robot pathfinding algorithms (originally in Jupyter notebooks) to the React frontend.

## Frontend API Contract

The frontend expects these endpoints (from `App.js`):

```
POST /find-path     - Full route (Start → Pick → Drop → Dest)
POST /find-simple-path - Simple route (Start → Dest)
```

### Request/Response Format

**Request (InputForm.js)**:
```json
{
  "grid_height": 6,
  "grid_width": 17,
  "obstacles": [[0, 13], [2, 1], [2, 15], [4, 10], [5, 3]],
  "start": [[0, 0], [5, 9], [1, 7]],
  "pick": [[5, 0], [4, 6], [1, 12]],
  "drop": [[0, 8], [5, 5], [3, 15]],
  "destination": [[3, 12], [0, 10], [0, 5]]
}
```

**Response**:
```json
{
  "success": true,
  "grid_height": 6,
  "grid_width": 17,
  "num_agents": 3,
  "total_cost": 45,
  "paths": [
    [[0,0], [1,0], [2,0], [3,0], ...],
    [[5,9], [4,9], [3,9], ...],
    [[1,7], [1,8], [1,9], ...]
  ]
}
```

## Architecture

```
backend/
├── main.py              # FastAPI app entry point
├── requirements.txt     # Dependencies
├── app/
│   ├── __init__.py
│   ├── models.py        # Pydantic models
│   ├── routers/
│   │   ├── __init__.py
│   │   └── pathfinder.py   # API endpoints
│   └── core/
│       ├── __init__.py
│       └── config.py    # Configuration
└── algorithms/          # Converted from notebooks
    ├── __init__.py
    ├── node.py          # Node class
    ├── grid.py         # GridEnvironment
    ├── robot.py        # Robot class
    ├── independent_astar.py
    ├── conflict_detector.py
    ├── cooperative_astar.py
    └── planner.py      # High-level planner
```

## Implementation Plan

### Step 1: Project Setup
- Create virtual environment
- Install: `fastapi`, `uvicorn`, `pydantic`, `pydantic-settings`, `python-multipart`
- Create `requirements.txt`

### Step 2: Data Models (models.py)
Define Pydantic models:
- `PathfinderRequest` - Input request
- `PathfinderResponse` - Output response
- `Point` - (x, y) coordinate

### Step 3: Algorithm Conversion (algorithms/)
Convert Jupyter notebook code to Python modules:

| File | Notebook Content |
|------|-----------------|
| `node.py` | `Node` class - position, parent, g/h/f costs |
| `grid.py` | `GridEnvironment` class - grid, obstacles, neighbors |
| `robot.py` | `Robot` class - robot_id, start, goal, path |
| `independent_astar.py` | `IndependentAStarPlanner` |
| `conflict_detector.py` | `ConflictDetector` - detect conflicts |
| `cooperative_astar.py` | `CooperativeAStarPlanner` with reservations |
| `planner.py` | High-level planner combining algorithms |

### Step 4: API Endpoints (routers/pathfinder.py)

```python
@router.post("/find-path")
async def find_path(request: PathfinderRequest):
    # Full mode: Start → Pick → Drop → Destination
    # Plan path for each agent: start → pick → drop → destination
    # Use cooperative A* with conflict detection
    
@router.post("/find-simple-path")
async def find_simple_path(request: PathfinderRequest):
    # Simple mode: Start → Destination
    # Direct path planning without pickup/drop
```

### Step 5: Main App (main.py)
- CORS configuration for frontend
- Include routers
- Run with uvicorn

### Step 6: Testing
- Test with example data from InputForm.js
- Verify response format matches frontend expectations

## Algorithm Details

### Full Mode Logic
For each agent, plan a sequence:
1. `start → pick`
2. `pick → drop`
3. `drop → destination`

Concatenate paths with wait actions at pick/drop locations.

### Mode Selection
- **Independent A\*** (baseline): Each robot planned independently
- **Cooperative A\*** (recommended): Sequential planning with reservation table

### Conflict Types
- **Vertex conflict**: Two robots at same position at same time
- **Edge conflict**: Two robots crossing same edge in opposite directions

## Example: Sample Flow

```
1. Receive request with 3 agents
2. Create GridEnvironment(size=6x17, obstacles)
3. For each agent:
   - Plan start→pick segment
   - Plan pick→drop segment  
   - Plan drop→destination segment
4. Detect conflicts, resolve using CooperativeA*
5. Return paths with cost
```
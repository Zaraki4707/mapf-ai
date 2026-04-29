# Full Implementation Plan: Independent A* and Cooperative A*

## Phase 1: Independent A* (Foundation)

This phase establishes the baseline multi-robot planning system where each robot is planned independently without awareness of others. It serves as the foundation for comparison and is typically the fastest approach, though it produces paths with collisions.

**Heuristic**: Manhattan distance (no diagonal movement, 4-directional neighbors only)

### Data Structure
```
robots = [
    {"id": "robot_1", "start": (0, 0), "goal": (5, 5)},
    {"id": "robot_2", "start": (5, 0), "goal": (0, 5)},
]

paths = {
    "robot_1": [(0,0), (1,0), (2,0), ...],
    "robot_2": [(5,0), (4,0), (3,0), ...],
}

# Waiting representation: repeat position to stay in place
# Example: Robot waits at (3,3) for 2 time steps
# path = [(0,0), (1,1), (2,2), (3,3), (3,3), (3,3), (4,4)]
#          t=0    t=1    t=2    t=3    t=4    t=5    t=6
```

### Execution Loop
- Run A* separately for each robot
- Collect all paths
- Return immediately (no conflict checking)
- **Problem**: Paths will likely have collisions

### Validation
- Test with 2-3 robots on small map
- Verify each robot gets a valid path to goal
- Measure: path length, time-to-plan

### Required Functions
- `MultiRobotPlanner` (class)
  - `plan_all_robots(robots)` - iterates and plans each robot sequentially
  - `run_independent_astar(robot, obstacles)` - single-robot A* execution

---

## Phase 2: Conflict Detection System

This phase implements the conflict detection system that identifies three types of collisions between robot paths. It is essential for validating solutions and understanding where cooperative planning needs to intervene.

### 2.1 Conflict Types
1. **Vertex Conflict**: Two robots occupy same position at same time step
2. **Edge Conflict**: Two robots traverse same edge in opposite directions
3. **Swap Conflict**: Robots moving in opposite directions on same edge

### 2.2 Detection Methods
- **Method 1**: Iterate all time steps, check all robot pair positions
- **Method 2**: Build time-space occupation map for each robot
- **Conflict Reporter**: Return list of (robot_id_1, robot_id_2, time_step, position/edge)

### 2.3 Data Structure
```
occupation_map = {
    (x, y, t): robot_id,
    # Example: (2, 3, 5) → "robot_1" means robot_1 is at (2,3) at time 5
}

conflict_report = [
    {"type": "vertex", "robot1": "r1", "robot2": "r2", "time": 3, "position": (5,5)},
    {"type": "edge", "robot1": "r1", "robot2": "r2", "time": 2, "edge": ((3,3), (3,4))},
]
```

### 2.4 Path Padding
- Extend shorter paths with "wait actions" at goal
- Enables fair comparison of post-goal positions

### Required Functions
- `ConflictDetector` (class)
  - `detect_vertex_conflicts(paths)` - find same position at same time
  - `detect_edge_conflicts(paths)` - find same edge traversal conflicts
  - `detect_swap_conflicts(paths)` - find opposite direction on same edge
  - `get_conflict_report(paths)` - returns list of (robot_id_1, robot_id_2, time_step, position/edge)
  - `pad_paths(paths)` - extend shorter paths with wait actions at goal
  - `build_occupation_map(paths)` - create (x,y,t) → robot_id mapping

---

## Phase 3: Cooperative A* (Main Algorithm)

This phase implements sequential cooperative planning where each robot considers previously planned robots' paths as obstacles. Robots reserve their positions in time-space, and subsequent robots add penalty costs to reserved cells. This approach guarantees collision-free paths but may produce suboptimal solutions.

### 3.1 Core Concept
- Plan robots **sequentially** (not simultaneously)
- Each robot aware of **previously planned robots' paths**
- Later robots adjust cost to avoid earlier robots
- Trade-off: Worse plan quality than optimal, but collision-free

### 3.2 Ordering Strategy
- **Simple approach**: Fixed order (Robot 1, Robot 2, 3...)
- **Advanced approach**: Sort by path length or conflict potential (later)
- **Decision**: Start with fixed order for simplicity

### 3.3 Modified A* for Cooperative Planning

**Standard A***: f(n) = g(n) + h(n)
**Cooperative A***: f(n) = g(n) + h(n) + penalty(n)

Where:
- g(n) = actual cost from start to current node
- h(n) = heuristic (Manhattan/Euclidean distance to goal)
- penalty(n) = RESERVATION_PENALTY if (node.x, node.y, time_step) is reserved

```
Pseudocode: Modified A* Node Expansion
----------------------------------------
function a_star_with_reservations(start, goal, reserved_positions, penalty=1000):
    open_set = PriorityQueue()
    open_set.add(start, priority=0)
    came_from = {}
    g_score = {start: 0}
    f_score = {start: heuristic(start, goal)}

    while open_set not empty:
        current = open_set.pop_lowest()

        if current.position == goal:
            return reconstruct_path(came_from, current)

        for neighbor in get_neighbors(current.position):
            time_step = current.time_step + 1

            # Calculate base cost
            tentative_g = g_score[current] + 1

            # Check if position is reserved at this time
            if (neighbor.x, neighbor.y, time_step) in reserved_positions:
                tentative_g += penalty  # Add penalty for reserved cell

            if tentative_g < g_score.get(neighbor, infinity):
                came_from[neighbor] = current
                g_score[neighbor] = tentative_g
                f_score[neighbor] = tentative_g + heuristic(neighbor, goal)
                open_set.add(neighbor, priority=f_score[neighbor])

    return None  # No path found
```

### 3.4 Time-Space Reservation
- **Data Structure**: Map of (x, y, t) → robot_id
- **Reserved Path**: For robot i's planned path [(x0,y0), (x1,y1), ...]:
  - (t=0, x0, y0) → robot_i
  - (t=1, x1, y1) → robot_i
  - etc.
  - Plus at-goal repetitions for padding

```
Pseudocode: get_reserved_positions()
----------------------------------------
function get_reserved_positions(planned_paths):
    # max_time = makespan (longest path among all planned robots)
    max_time = max(len(path) for path in planned_paths.values())
    reserved = {}  # (x, y, t) → robot_id

    for robot_id, path in planned_paths.items():
        for t, position in enumerate(path):
            reserved[(position.x, position.y, t)] = robot_id

        # Add padding for post-goal time steps (robot stays at goal)
        goal_pos = path[-1]
        path_length = len(path)
        for t in range(path_length, max_time):
            reserved[(goal_pos.x, goal_pos.y, t)] = robot_id

    return reserved
```

### 3.5 Cost Function Modification
**Option A: Penalty-based**
- If position reserved: g(n) += PENALTY (e.g., 1000)
- A* will prefer unreserved paths but accept if necessary

**Option B: Constraint-based (strict)**
- If position reserved: Don't expand node (hard constraint)
- May fail if impossible

**Decision**: Start with Option A (more flexible)

### 3.6 Execution Flow

```
Pseudocode: Main Execution Loop
----------------------------------------
function plan_robots_cooperatively(robots, grid):
    # Step 1: Sort robots by planning order (fixed or by path length)
    sorted_robots = sort_robots(robots, order="fixed")

    # Step 2: Initialize
    planned_paths = {}

    # Step 3: Plan each robot sequentially
    for robot in sorted_robots:
        # Get reserved positions from previously planned robots
        reserved = get_reserved_positions(planned_paths, max_time)

        # Run modified A* with reservations
        path = a_star_with_reservations(
            start=robot.start,
            goal=robot.goal,
            reserved_positions=reserved,
            penalty=1000
        )

        if path is None:
            # Handle failure: robot cannot find path
            # Options: (1) Try constraint-based, (2) Replan with higher penalty, (3) Fail
            raise PlanningFailure(f"No path found for {robot.id}")

        planned_paths[robot.id] = path

    return planned_paths
```

### 3.7 Handling A* Failure
If `a_star_with_reservations()` returns None (no path found):
1. **First attempt**: Retry with higher penalty (e.g., 2000, 5000)
2. **Second attempt**: Try constraint-based mode (strict blocking)
3. **Third attempt**: Replan earlier robots with different order
4. **Final**: Return partial results with error flag

### Required Functions
- `CooperativeAStarPlanner` (class)
  - `plan_robots_sequentially(robots, ordering=None)` - main execution method
  - `a_star_with_reservations(start, goal, reserved_positions, penalty=1000)` - modified A* considering reserved cells and adding penalty to g(n) when cell is reserved
  - `get_reserved_positions(planned_paths)` - builds time-space reservation map (x, y, t) → robot_id, includes post-goal padding up to makespan
  - `calculate_cooperative_cost(node, reserved_positions, penalty=1000)` - returns g + h + penalty if reserved
  - `sort_robots(robots, order)` - orders robots by "fixed", "path_length", or "conflict_potential"
  - `retry_with_higher_penalty(robot, reserved, multiplier)` - attempts planning with increased penalty

---

## Phase 4: Testing & Validation Strategy

This phase establishes a comprehensive testing framework with specific test scenarios, quantitative metrics, and expected results. It enables objective comparison between Independent and Cooperative approaches.

### 4.1 Test Cases
1. **No conflict case**: Robots going to opposite corners
2. **Simple conflict**: Robots crossing paths
3. **Ordering matters**: Same scenario, different planning order
4. **Deadlock scenario**: Robots reversing needed

### 4.2 Metrics to Measure
- **Path validity**: All cells walkable, reach goal?
- **Conflict count**: Should be 0 after cooperative planning
- **Path length**: Compare Independent vs Cooperative
- **Makespan**: Max path length across all robots
- **Flowtime**: Sum of all path lengths
- **Plan time**: How long did algorithm take?

### 4.3 Expected Results
- Independent A*: Fast, but conflicts present
- Cooperative A*: Slower, but conflict-free
- Order sensitivity: Results vary by robot order

### Required Functions
- `validate_paths(paths, grid)` - confirm all cells walkable, reach goals
- `count_conflicts(paths)` - return total conflict count
- `calculate_makespan(paths)` - max path length across all robots
- `calculate_flowtime(paths)` - sum of all path lengths
- `measure_plan_time(func)` - timing wrapper
- `compare_algorithms(robots, grid)` - runs both algorithms and returns comparison dict

---

## Phase 5: Integration Points

### Plan Description
This phase integrates all components into a unified system with a wrapper class that selects between Independent and Cooperative planning. It also defines the notebook structure for demonstration.

### 5.1 Build Order
1. Write `ConflictDetector` class → test with known paths
2. Write `IndependentPlanner` → plan multiple robots
3. Write `CooperativeAStarPlanner` → add reservation system
4. Wrap in `MultiRobotPlanner` that chooses algorithm

### 5.2 Notebook Structure
- Cell 1-3: Imports, GridEnvironment, Node, Robot (existing)
- Cell 4: ConflictDetector
- Cell 5: IndependentMultiRobotPlanner
- Cell 6: CooperativeAStarPlanner
- Cell 7: Example execution + comparison
- Cell 8: Results visualization (paths drawn on grid)

### 5.3 Demo Example

**Scenario**: 2 robots crossing paths on 10x10 grid
```
Grid: 10x10, no obstacles
Robot A: start (1, 5) → goal (8, 5)  # Moving right
Robot B: start (5, 1) → goal (5, 8)  # Moving up

Expected Paths (Independent):
- Robot A: (1,5) → (2,5) → (3,5) → ... → (8,5)
- Robot B: (5,1) → (5,2) → (5,3) → ... → (5,8)
- Conflict at (5,5) at time step 4

Expected Paths (Cooperative):
- Robot A plans first: Gets direct horizontal path
- Robot B plans second: Adds penalty to Robot A's cells
- Robot B either: (1) goes around, or (2) waits for Robot A to pass
- No conflicts in final solution

Alternative with different ordering:
- Robot B plans first: Gets direct vertical path
- Robot A plans second: Forced to route around or wait
- Different final paths, same guarantee of no collision
```

### Required Functions
- `MultiRobotPlanner` (wrapper class)
  - `choose_algorithm(algorithm_type)` - selector for "independent" vs "cooperative"
  - `execute(robots, grid, algorithm)` - main run method that orchestrates everything
  - `get_results_summary()` - returns dict with paths, metrics, conflicts

---

## Phase 6: Future Extensions (Post-MVP)

### Plan Description
This phase outlines advanced algorithms that build upon the Cooperative A* foundation, enabling priority-based planning, windowed replanning, and Conflict-Based Search for better optimality.

### 6.1 Priority-based Cooperative A*
- Assign priorities to robots
- Higher priority gets less constraint
- Replan lower-priority robots if conflict exists

### 6.2 Windowed Cooperative A*
- Plan only next K time steps to reduce branching
- Replan at each window

### 6.3 Conflict-Based Search (CBS) Foundation
- Detect conflicts in cooperative solution
- Split into constraint groups
- Recursively solve (later algorithm)

### Required Functions (Future)
- `PriorityCooperativePlanner` - handles priority levels and replanning
- `WindowedPlanner` - plans K-step windows with periodic replanning
- `CBSPlanner` - Conflict-Based Search for optimal solutions

---

## Summary: Expected Outcomes

| Aspect | Independent | Cooperative |
|--------|------------|-------------|
| **Speed** | ⚡ Fastest | 🔶 Slower |
| **Optimality** | ⭐ Individual | ⭐⭐ Collective |
| **Collisions** | ❌ Yes | ✅ No |
| **Failure Rate** | ✅ ~0% | 🔶 ~1-5% |
| **Use Case** | Baseline | Production |

---

## Quick Reference: Function Summary

| Phase | Function | Purpose |
|-------|----------|---------|
| 1 | `plan_all_robots()` | Run independent A* for all robots |
| 2 | `detect_vertex_conflicts()` | Find position overlaps |
| 2 | `detect_edge_conflicts()` | Find edge traversals in opposite directions |
| 2 | `pad_paths()` | Extend paths with wait actions |
| 3 | `plan_robots_sequentially()` | Main cooperative execution |
| 3 | `a_star_with_reservations()` | Modified A* with penalty costs |
| 3 | `get_reserved_positions()` | Build time-space reservation map |
| 3 | `calculate_cooperative_cost()` | Cost = g + h + penalty if reserved |
| 4 | `validate_paths()` | Check path validity |
| 4 | `count_conflicts()` | Count total collisions |
| 4 | `calculate_makespan()` | Max path length |
| 4 | `calculate_flowtime()` | Sum of path lengths |
| 5 | `choose_algorithm()` | Select planning mode |
| 5 | `execute()` | Run complete system |
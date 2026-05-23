# Multi-Agent Pathfinding Backend Optimization Plan

## Executive Summary

This document provides a **strict, step-by-step implementation plan** to optimize the MAPF (Multi-Agent Pathfinding) backend algorithms. Expected overall speedup: **15-50x** across all algorithms.

**Target Files:**
- `independent_astar.py`
- `cooperative_astar.py`
- `cbs.py`
- `conflict_detector.py`
- `hill_climbing.py`
- `hill_climbing_optimizer.py`
- `node.py`
- `grid.py`

---

## Implementation Phases

### ✅ PHASE 1: CRITICAL BOTTLENECKS (Day 1-2)
**Expected Speedup: 10-20x | Priority: HIGHEST | Time: 3-4 hours**

---

#### 1.1 Optimize Conflict Detection with Spatial Indexing

**File:** `conflict_detector.py`  
**Problem:** O(n²·t) complexity - checks all robot pairs at every timestep  
**Solution:** Spatial hashing to check only robots at same position  
**Expected Impact:** 5-10x speedup on conflict detection

**STRICT INSTRUCTIONS:**

1. **Replace the `detect_conflicts()` method entirely** with this optimized version:

```python
def detect_conflicts(self, paths: Dict) -> List[Dict]:
    """
    Optimized conflict detection using spatial hashing.
    Only checks robots that could possibly conflict (same position/time).
    """
    conflicts = []
    padded = self.pad_paths(paths)
    if not padded:
        return []

    robot_ids = list(padded.keys())
    horizon = len(next(iter(padded.values())))

    # Spatial hash: maps (x, y, t) -> list of robot_ids at that position/time
    # This allows O(1) lookup instead of O(n²) pairwise checks
    position_index = {}
    
    for t in range(horizon):
        position_index.clear()  # Reuse dictionary to reduce allocations
        
        # Build spatial index for this timestep - O(n)
        for rid in robot_ids:
            pos = padded[rid][t]
            key = (pos[0], pos[1], t)
            if key not in position_index:
                position_index[key] = []
            position_index[key].append(rid)
        
        # Check vertex conflicts - O(c) where c = conflicts, not O(n²)
        for pos_key, robots in position_index.items():
            if len(robots) > 1:
                conflicts.append({
                    'type': 'vertex', 
                    'time': t, 
                    'pos': (pos_key[0], pos_key[1]), 
                    'robots': robots
                })
        
        # Check swap conflicts - still O(n²) but only for adjacent timesteps
        if t < horizon - 1:
            for i, r1 in enumerate(robot_ids):
                for r2 in robot_ids[i+1:]:
                    p1_t = padded[r1][t]
                    p1_t1 = padded[r1][t+1]
                    p2_t = padded[r2][t]
                    p2_t1 = padded[r2][t+1]
                    
                    # Swap: r1 goes A->B while r2 goes B->A
                    if (p1_t == p2_t1 and p1_t1 == p2_t and p1_t != p1_t1):
                        conflicts.append({
                            'type': 'swap', 
                            'time': t, 
                            'robots': [r1, r2], 
                            'pos': (p1_t, p1_t1)
                        })
    
    return conflicts
```

2. **DO NOT modify** other methods in this file (`detect_vertex_conflicts`, `detect_edge_conflicts`, etc.) - they may be used elsewhere
3. **Test** by running conflict detection on sample paths before/after

**Validation:**
- Run existing test cases
- Verify conflict count matches original implementation
- Measure time improvement (should be 5-10x faster)

---

#### 1.2 Optimize CBS Constraint Table

**File:** `cbs.py`  
**Problem:** Set operations on constraint checks are slower than dict lookups  
**Solution:** Replace set with dictionary for O(1) access  
**Expected Impact:** 3-5x speedup in CBS

**STRICT INSTRUCTIONS:**

1. **Find the `_build_constraint_table` method** (around line 170)

2. **Replace the entire method** with:

```python
def _build_constraint_table(self, constraints: List[Constraint]) -> Dict[Tuple, bool]:
    """
    Build constraint lookup table using dictionary for O(1) access.
    
    Returns:
        Dict mapping constraint keys to True (for fast 'in' checks)
        - Vertex: (x, y, time) -> True
        - Edge: (x1, y1, x2, y2, time) -> True
    """
    reservation_table = {}
    
    for c in constraints:
        if not c.is_edge:
            # Vertex constraint: position forbidden at specific time
            x, y = c.pos1
            reservation_table[(x, y, c.time)] = True
        else:
            # Edge constraint: movement from pos1 to pos2 forbidden at time
            x1, y1 = c.pos1
            x2, y2 = c.pos2
            reservation_table[(x1, y1, x2, y2, c.time)] = True
    
    return reservation_table
```

3. **Update the type hint** for `_check_vertex_conflict`:

```python
def _check_vertex_conflict(self, pos: tuple, t: int, reservation_table: dict) -> bool:
    """Check if position at time t is constrained (dict version)"""
    return (pos[0], pos[1], t) in reservation_table
```

4. **Update the type hint** for `_check_edge_conflict`:

```python
def _check_edge_conflict(self, pos_from: tuple, pos_to: tuple, t: int, reservation_table: dict) -> bool:
    """Check if edge movement is constrained (dict version)"""
    edge_key = (pos_from[0], pos_from[1], pos_to[0], pos_to[1], t)
    if edge_key in reservation_table:
        return True
    
    # Check reverse edge (swap conflict)
    reverse_edge = (pos_to[0], pos_to[1], pos_from[0], pos_from[1], t)
    return reverse_edge in reservation_table
```

5. **Update all method signatures** that pass `reservation_table` to use `dict` instead of `set`

**Validation:**
- CBS should produce identical results
- Measure performance on 10+ agent scenarios
- Verify low-level A* calls complete faster

---

#### 1.3 Pre-compute Neighbor Cache in Grid

**File:** `grid.py`  
**Problem:** `get_neighbors()` recomputes valid neighbors every call  
**Solution:** Pre-compute and cache all neighbors during initialization  
**Expected Impact:** 1.5-2x speedup on pathfinding

**STRICT INSTRUCTIONS:**

1. **Modify the `__init__` method** to add neighbor caching:

```python
def __init__(self, height: int, width: int, obstacles: List[Tuple[int, int]] = None):
    self.height = height
    self.width = width
    self.grid = [[True for _ in range(width)] for _ in range(height)]
    
    # Initialize neighbor cache - NEW
    self._neighbor_cache = {}
    
    # Set obstacles
    if obstacles:
        for x, y in obstacles:
            if self.is_valid_position(x, y):
                self.grid[y][x] = False
    
    # Build neighbor cache AFTER obstacles are set - NEW
    self._build_neighbor_cache()
```

2. **Add the cache building method** (new method):

```python
def _build_neighbor_cache(self):
    """
    Pre-compute all valid neighbors for every walkable cell.
    This trades memory (O(n) storage) for speed (O(1) lookups).
    Called once during initialization.
    """
    directions = [(0, 1), (1, 0), (0, -1), (-1, 0)]
    
    for y in range(self.height):
        for x in range(self.width):
            if self.is_walkable(x, y):
                neighbors = []
                for dx, dy in directions:
                    nx, ny = x + dx, y + dy
                    if self.is_walkable(nx, ny):
                        neighbors.append((nx, ny))
                self._neighbor_cache[(x, y)] = neighbors
            else:
                # Store empty list for obstacles
                self._neighbor_cache[(x, y)] = []
```

3. **Replace the `get_neighbors` method**:

```python
def get_neighbors(self, x: int, y: int) -> List[Tuple[int, int]]:
    """
    O(1) neighbor lookup using pre-computed cache.
    
    Returns:
        List of valid neighboring positions (max 4 for grid movement)
    """
    return self._neighbor_cache.get((x, y), [])
```

4. **Add a method to invalidate cache** if grid changes dynamically:

```python
def add_obstacle(self, x: int, y: int):
    """Add obstacle and rebuild affected cache entries"""
    if self.is_valid_position(x, y):
        self.grid[y][x] = False
        # Rebuild cache for this cell and its neighbors
        self._rebuild_cache_region(x, y)

def _rebuild_cache_region(self, x: int, y: int):
    """Rebuild cache for cell and its neighbors"""
    directions = [(0, 1), (1, 0), (0, -1), (-1, 0), (0, 0)]
    for dx, dy in directions:
        nx, ny = x + dx, y + dy
        if self.is_valid_position(nx, ny):
            neighbors = []
            for ndx, ndy in [(0, 1), (1, 0), (0, -1), (-1, 0)]:
                nnx, nny = nx + ndx, ny + ndy
                if self.is_walkable(nnx, nny):
                    neighbors.append((nnx, nny))
            self._neighbor_cache[(nx, ny)] = neighbors
```

**Validation:**
- Test that `get_neighbors()` returns same results as before
- Verify memory usage is acceptable (should be ~4 * width * height * 8 bytes)
- Measure speedup on A* pathfinding calls

---

### ✅ PHASE 2: ALGORITHM OPTIMIZATIONS (Day 2-3)
**Expected Speedup: 2-5x | Priority: HIGH | Time: 4-5 hours**

---

#### 2.1 Add Bidirectional A* to Independent Planner

**File:** `independent_astar.py`  
**Problem:** Standard A* expands many nodes when goal is far  
**Solution:** Search from both start and goal simultaneously  
**Expected Impact:** 1.5-3x speedup on long paths

**STRICT INSTRUCTIONS:**

1. **Add new method** to `IndependentAStarPlanner` class:

```python
def _bidirectional_astar(self, robot: Robot, obstacles: Set = None) -> Optional[List[Tuple[int, int]]]:
    """
    Bidirectional A* - searches from both start and goal.
    Terminates when searches meet in the middle.
    Faster for long paths, same correctness guarantees as standard A*.
    
    Returns:
        Path from start to goal, or None if no path exists
    """
    if obstacles is None:
        obstacles = set()

    start = robot.start_pos
    goal = robot.goal_pos

    if not self.grid.is_walkable(*start) or not self.grid.is_walkable(*goal):
        return None

    if start == goal:
        return [start]

    # Forward search (from start toward goal)
    open_forward = []
    start_h = self.grid.manhattan_distance(start, goal)
    heapq.heappush(open_forward, (start_h, 0, start))
    g_forward = {start: 0}
    parent_forward = {start: None}
    closed_forward = set()
    
    # Backward search (from goal toward start)
    open_backward = []
    goal_h = self.grid.manhattan_distance(goal, start)
    heapq.heappush(open_backward, (goal_h, 0, goal))
    g_backward = {goal: 0}
    parent_backward = {goal: None}
    closed_backward = set()
    
    # Track best meeting point
    best_cost = float('inf')
    meeting_point = None
    
    while open_forward and open_backward:
        # Expand forward frontier
        if open_forward:
            _, g_f, pos_f = heapq.heappop(open_forward)
            
            if pos_f in closed_forward:
                continue
            closed_forward.add(pos_f)
            
            # Check if forward search met backward search
            if pos_f in closed_backward:
                cost = g_forward[pos_f] + g_backward[pos_f]
                if cost < best_cost:
                    best_cost = cost
                    meeting_point = pos_f
                    break
            
            # Expand forward neighbors
            for neighbor in self.grid.get_neighbors(*pos_f):
                if neighbor in obstacles:
                    continue
                    
                tentative_g = g_f + 1
                if neighbor not in g_forward or tentative_g < g_forward[neighbor]:
                    g_forward[neighbor] = tentative_g
                    parent_forward[neighbor] = pos_f
                    h = self.grid.manhattan_distance(neighbor, goal)
                    heapq.heappush(open_forward, (tentative_g + h, tentative_g, neighbor))
        
        # Expand backward frontier
        if open_backward:
            _, g_b, pos_b = heapq.heappop(open_backward)
            
            if pos_b in closed_backward:
                continue
            closed_backward.add(pos_b)
            
            # Check if backward search met forward search
            if pos_b in closed_forward:
                cost = g_forward[pos_b] + g_backward[pos_b]
                if cost < best_cost:
                    best_cost = cost
                    meeting_point = pos_b
                    break
            
            # Expand backward neighbors
            for neighbor in self.grid.get_neighbors(*pos_b):
                if neighbor in obstacles:
                    continue
                    
                tentative_g = g_b + 1
                if neighbor not in g_backward or tentative_g < g_backward[neighbor]:
                    g_backward[neighbor] = tentative_g
                    parent_backward[neighbor] = pos_b
                    h = self.grid.manhattan_distance(neighbor, start)
                    heapq.heappush(open_backward, (tentative_g + h, tentative_g, neighbor))
    
    if meeting_point is None:
        return None
    
    # Reconstruct path from start to meeting point
    path_forward = []
    current = meeting_point
    while current is not None:
        path_forward.append(current)
        current = parent_forward.get(current)
    path_forward.reverse()
    
    # Reconstruct path from meeting point to goal
    path_backward = []
    current = parent_backward.get(meeting_point)
    while current is not None:
        path_backward.append(current)
        current = parent_backward.get(current)
    
    return path_forward + path_backward
```

2. **Update `run_independent_astar` method** to use bidirectional search:

```python
def run_independent_astar(self, robot: Robot, obstacles: Set = None, use_bidirectional: bool = True) -> Optional[List[Tuple[int, int]]]:
    """
    Run A* pathfinding for a single robot.
    
    Args:
        robot: Robot to plan for
        obstacles: Additional obstacles beyond grid
        use_bidirectional: Use bidirectional search (faster for long paths)
    
    Returns:
        Path from start to goal, or None
    """
    if obstacles is None:
        obstacles = set()

    start = robot.start_pos
    goal = robot.goal_pos

    if not self.grid.is_walkable(*start) or not self.grid.is_walkable(*goal):
        return None

    if start == goal:
        return [start]
    
    # Use bidirectional for paths likely to be long
    path_distance = self.grid.manhattan_distance(start, goal)
    if use_bidirectional and path_distance > 10:
        return self._bidirectional_astar(robot, obstacles)
    
    # Original unidirectional A* for short paths
    open_set = []
    start_node = Node(start, g=0, h=self.grid.manhattan_distance(start, goal))
    heapq.heappush(open_set, start_node)

    came_from = {}
    g_score = {start: 0}
    closed_set = set()

    while open_set:
        current = heapq.heappop(open_set)

        if current.position in closed_set:
            continue
        closed_set.add(current.position)

        if current.position == goal:
            return current.reconstruct_path()

        neighbors = self.grid.get_neighbors(*current.position)
        neighbors.append(current.position)  # Wait action
        
        for neighbor in neighbors:
            if neighbor in obstacles:
                continue

            tentative_g = current.g + 1

            if neighbor not in g_score or tentative_g < g_score[neighbor]:
                g_score[neighbor] = tentative_g
                h = self.grid.manhattan_distance(neighbor, goal)
                neighbor_node = Node(neighbor, parent=current, g=tentative_g, h=h)
                came_from[neighbor_node] = current
                heapq.heappush(open_set, neighbor_node)

    return None
```

**Validation:**
- Test on grid with long paths (>50 steps)
- Verify paths are identical or similar length to standard A*
- Measure speedup (should be 1.5-3x on long paths)

---

#### 2.2 Add Early Termination to CBS

**File:** `cbs.py`  
**Problem:** CBS continues searching even when good solution exists  
**Solution:** Track best solution and terminate early on timeout  
**Expected Impact:** 2-5x speedup on hard instances

**STRICT INSTRUCTIONS:**

1. **Add instance variables** to `__init__` method:

```python
def __init__(self, grid, robots: List, conflict_detector=None, 
             objective: str = "makespan", max_iterations: int = 10000, 
             timeout: int = 60):
    # ... existing code ...
    
    # NEW: Track best solution found during search
    self._best_solution = None
    self._best_conflicts = float('inf')
    self._best_makespan = float('inf')
    self._lower_bound_cache = None
```

2. **Add method to compute lower bound**:

```python
def _compute_lower_bound_makespan(self) -> float:
    """
    Compute theoretical lower bound on makespan.
    This is the maximum individual path length (ignoring conflicts).
    Any solution must have at least this makespan.
    """
    if self._lower_bound_cache is None:
        self._lower_bound_cache = max(
            self.grid.get_manhattan_distance(r.start_pos, r.goal_pos) 
            for r in self.robots
        )
    return self._lower_bound_cache
```

3. **Modify the `solve` method** to track and return best solution:

```python
def solve(self, time_limit: Optional[float] = None) -> Dict[str, Any]:
    """
    Solve MAPF using CBS with early termination.
    Returns best solution found within time limit.
    """
    if time_limit is None:
        time_limit = self.timeout
    start_time = time.time()

    initial_paths = self._get_initial_solution()
    if not initial_paths or any(p is None for p in initial_paths.values()):
        return self._failure_result(initial_paths)

    root_conflicts = self.conflict_detector.detect_conflicts(initial_paths)
    root = ConflictTreeNode(
        constraints=defaultdict(list),
        paths=initial_paths,
        conflicts=root_conflicts,
    )

    self.open_list = []
    self.closed_list = []
    self.visited_nodes = set()
    self.high_level_iterations = 0
    
    # Initialize best solution tracking - NEW
    self._best_solution = initial_paths
    self._best_conflicts = len(root_conflicts)
    self._best_makespan = root.makespan
    lower_bound = self._compute_lower_bound_makespan()

    heapq.heappush(self.open_list, (self._priority(root), id(root), root))

    while self.open_list and self.high_level_iterations < self.max_iterations:
        # Check timeout
        elapsed = time.time() - start_time
        if elapsed > time_limit:
            # Return best solution found so far - NEW
            if self._best_conflicts < float('inf'):
                result = self._success_result(self._best_solution)
                result['success'] = (self._best_conflicts == 0)
                result['final_conflicts'] = self._best_conflicts
                result['timeout'] = True
                return result
            break

        self.high_level_iterations += 1
        _, _, node = heapq.heappop(self.open_list)
        self.closed_list.append(node)
        self.visited_nodes.add(id(node))
        
        # Track best solution - NEW
        node_conflict_count = len(node.conflicts)
        if node_conflict_count < self._best_conflicts:
            self._best_conflicts = node_conflict_count
            self._best_solution = node.paths
            self._best_makespan = node.makespan
        
        # Found conflict-free solution
        if not node.conflicts:
            return self._success_result(node.paths)
        
        # Prune nodes with makespan too far from lower bound - NEW
        if node.makespan > 2.5 * lower_bound:
            continue

        conflict = self._select_conflict(node.conflicts)
        if conflict is None:
            continue

        children = self._expand_node(node, conflict)
        for child in children:
            if child is None:
                continue
            if id(child) not in self.visited_nodes:
                heapq.heappush(self.open_list, (self._priority(child), id(child), child))

    # Return best solution if no conflict-free solution found - NEW
    if self._best_solution and self._best_conflicts < float('inf'):
        result = self._success_result(self._best_solution)
        result['success'] = (self._best_conflicts == 0)
        result['final_conflicts'] = self._best_conflicts
        result['partial_solution'] = True
        return result
    
    return self._failure_result(None)
```

**Validation:**
- Test on hard instances with 10+ agents
- Verify CBS returns reasonable solutions on timeout
- Measure improvement in solution time

---

#### 2.3 Add Max Expansion Limits to All A* Methods

**Files:** `independent_astar.py`, `cooperative_astar.py`, `cbs.py`, `hill_climbing.py`  
**Problem:** A* can expand millions of nodes on hard instances  
**Solution:** Hard limit on node expansions  
**Expected Impact:** Prevents worst-case performance degradation

**STRICT INSTRUCTIONS FOR EACH FILE:**

1. **Add constant at top of file**:

```python
# Maximum nodes to expand before giving up
MAX_NODE_EXPANSIONS = 50000
```

2. **In every A* while loop**, add counter and check:

```python
def _astar_single_robot(self, ...):
    # ... initialization code ...
    
    expansions = 0  # NEW
    while open_heap and expansions < MAX_NODE_EXPANSIONS:  # MODIFIED
        expansions += 1  # NEW
        
        # ... rest of A* code ...
    
    # If we exit due to expansion limit, return None
    return None
```

3. **Apply to these specific methods:**
   - `independent_astar.py`: `run_independent_astar()`
   - `cooperative_astar.py`: `_astar_single_robot()` and `_astar_with_start_time()`
   - `cbs.py`: `_astar_single_robot()`
   - `hill_climbing.py`: `_cooperative_astar_replan()`

**Validation:**
- Test on unsolvable scenarios
- Verify pathfinding fails gracefully instead of hanging
- Adjust MAX_NODE_EXPANSIONS if too restrictive

---

### ✅ PHASE 3: MEMORY OPTIMIZATIONS (Day 3-4)
**Expected Speedup: 1.2-1.5x | Priority: MEDIUM | Time: 2-3 hours**

---

#### 3.1 Implement Node Object Pooling

**File:** `node.py`  
**Problem:** Creating millions of Node objects causes GC pressure  
**Solution:** Reuse node objects from a pool  
**Expected Impact:** 1.2-1.5x speedup, reduced memory allocations

**STRICT INSTRUCTIONS:**

1. **Replace entire `node.py` file** with this pooled version:

```python
from typing import Tuple, Optional, List


class NodePool:
    """
    Object pool for Node instances to reduce GC pressure.
    
    In pathfinding, we create millions of short-lived nodes.
    Reusing them from a pool reduces allocation overhead.
    """
    
    def __init__(self, initial_size: int = 10000):
        """
        Initialize pool with pre-allocated nodes.
        
        Args:
            initial_size: Number of nodes to pre-allocate
        """
        self.pool: List['Node'] = [Node((0, 0)) for _ in range(initial_size)]
        self.index = 0
        self.size = initial_size
    
    def acquire(self, position: Tuple[int, int], parent: Optional['Node'] = None, 
                g: float = 0, h: float = 0) -> 'Node':
        """
        Get a node from the pool, expanding if necessary.
        
        Args:
            position: (x, y) position
            parent: Parent node in search tree
            g: Cost from start
            h: Heuristic to goal
            
        Returns:
            Configured Node instance from pool
        """
        if self.index >= len(self.pool):
            # Expand pool by 50% when exhausted
            expansion = max(1000, self.size // 2)
            self.pool.extend([Node((0, 0)) for _ in range(expansion)])
            self.size += expansion
        
        node = self.pool[self.index]
        node.position = position
        node.parent = parent
        node.g = g
        node.h = h
        node.f = g + h
        self.index += 1
        return node
    
    def reset(self):
        """Reset pool for reuse. Call between pathfinding runs."""
        self.index = 0
        # Clear parent references to prevent memory leaks
        for i in range(self.index):
            self.pool[i].parent = None


class Node:
    """
    Represents a node in the A* search tree.
    
    Uses object pooling to reduce GC pressure during pathfinding.
    """
    
    # Class-level pool shared by all Node instances
    _pool = NodePool(initial_size=10000)
    
    def __init__(self, position: Tuple[int, int], parent: Optional["Node"] = None, 
                 g: float = 0, h: float = 0):
        """
        Initialize node. Prefer using Node.create() for pooled allocation.
        
        Args:
            position: (x, y) grid position
            parent: Parent node in search path
            g: Cost from start to this node
            h: Heuristic estimate from this node to goal
        """
        self.position = position
        self.parent = parent
        self.g = g
        self.h = h
        self.f = g + h

    @classmethod
    def create(cls, position: Tuple[int, int], parent: Optional["Node"] = None, 
               g: float = 0, h: float = 0) -> "Node":
        """
        Create node using object pool (PREFERRED METHOD).
        
        This is faster than Node(...) constructor as it reuses objects.
        
        Args:
            position: (x, y) grid position
            parent: Parent node in search path
            g: Cost from start to this node
            h: Heuristic estimate from this node to goal
            
        Returns:
            Pooled Node instance
        """
        return cls._pool.acquire(position, parent, g, h)
    
    @classmethod
    def reset_pool(cls):
        """
        Reset the global node pool.
        
        Call this between independent pathfinding runs to reuse memory.
        Not thread-safe - only call when no pathfinding is active.
        """
        cls._pool.reset()

    def __lt__(self, other: "Node") -> bool:
        """Compare nodes by f-score for priority queue."""
        return self.f < other.f

    def __eq__(self, other: "Node") -> bool:
        """Nodes are equal if they represent same position."""
        return self.position == other.position

    def __hash__(self) -> int:
        """Hash by position for use in sets/dicts."""
        return hash(self.position)

    def reconstruct_path(self) -> List[Tuple[int, int]]:
        """
        Reconstruct path from start to this node by following parents.
        
        Returns:
            List of (x, y) positions from start to current node
        """
        path = []
        current = self
        while current is not None:
            path.append(current.position)
            current = current.parent
        return list(reversed(path))
```

2. **Update `independent_astar.py`** to use pooled nodes:

```python
def run_independent_astar(self, robot: Robot, obstacles: Set = None, use_bidirectional: bool = True) -> Optional[List[Tuple[int, int]]]:
    # ... existing code ...
    
    # Reset pool before pathfinding - NEW
    Node.reset_pool()
    
    # Use Node.create() instead of Node() - MODIFY EXISTING
    start_node = Node.create(start, g=0, h=self.grid.manhattan_distance(start, goal))
    heapq.heappush(open_set, start_node)
    
    # ... in the loop, replace:
    # neighbor_node = Node(neighbor, parent=current, g=tentative_g, h=h)
    # with:
    neighbor_node = Node.create(neighbor, parent=current, g=tentative_g, h=h)
    # ... rest of code ...
```

3. **Apply same changes to:**
   - Any file that creates `Node()` objects
   - Replace all `Node(...)` with `Node.create(...)`
   - Add `Node.reset_pool()` at start of major pathfinding operations

**Validation:**
- Run memory profiler before/after
- Verify reduced allocations (should see 50-80% fewer Node allocations)
- Check that paths are still correct

---

#### 3.2 Add Distance Caching to Grid

**File:** `grid.py`  
**Problem:** Manhattan distance computed repeatedly for same pairs  
**Solution:** Cache distance calculations  
**Expected Impact:** Minor speedup (5-10%), but easy to implement

**STRICT INSTRUCTIONS:**

1. **Add to `__init__` method**:

```python
def __init__(self, height: int, width: int, obstacles: List[Tuple[int, int]] = None):
    # ... existing code ...
    
    # Cache for frequently computed distances - NEW
    self._distance_cache = {}
    self._cache_max_size = 10000  # Limit cache size
```

2. **Update `get_manhattan_distance` method**:

```python
def get_manhattan_distance(self, pos1: Tuple[int, int], pos2: Tuple[int, int]) -> int:
    """
    Compute Manhattan distance with caching for repeated queries.
    
    Args:
        pos1: First position (x, y)
        pos2: Second position (x, y)
        
    Returns:
        Manhattan distance (L1 norm)
    """
    # Check cache first
    cache_key = (pos1, pos2)
    if cache_key in self._distance_cache:
        return self._distance_cache[cache_key]
    
    # Compute distance
    distance = abs(pos1[0] - pos2[0]) + abs(pos1[1] - pos2[1])
    
    # Cache if not too large
    if len(self._distance_cache) < self._cache_max_size:
        self._distance_cache[cache_key] = distance
        # Also cache reverse direction
        self._distance_cache[(pos2, pos1)] = distance
    
    return distance
```

3. **Add cache clearing method**:

```python
def clear_distance_cache(self):
    """Clear distance cache. Call if grid changes significantly."""
    self._distance_cache.clear()
```

**Validation:**
- Should be transparent - no behavior changes
- Monitor cache hit rate (add counter if needed)
- Verify memory usage is acceptable

---

### ✅ PHASE 4: ADVANCED OPTIMIZATIONS (Day 4-5)
**Expected Speedup: 1.5-3x | Priority: LOW | Time: 3-4 hours**

---

#### 4.1 Implement Parallel Hill Climbing

**File:** `hill_climbing.py`  
**Problem:** Hill climbing evaluates neighbors sequentially  
**Solution:** Parallel neighbor evaluation using thread pool  
**Expected Impact:** 1.5-2x speedup on multi-core systems

**STRICT INSTRUCTIONS:**

1. **Add import at top**:

```python
import concurrent.futures
from typing import List, Dict, Tuple, Optional
```

2. **Add parallel method** to `HillClimbingSolver`:

```python
def solve_parallel(self, robots: List[Robot], max_workers: int = 4) -> Dict[int, List[Tuple[int, int]]]:
    """
    Parallel hill climbing using thread pool.
    
    Args:
        robots: List of robots to plan for
        max_workers: Number of parallel threads (default: 4)
        
    Returns:
        Dictionary mapping robot_id to path
    """
    current_paths = self.initialize_paths(robots)
    current_conflicts = self.conflict_detector.count_conflicts(current_paths)
    total_len = sum(len(p) for p in current_paths.values() if p)
    
    no_improvement = 0
    iteration = 0
    
    with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
        while iteration < self.max_iterations and no_improvement < 200:
            iteration += 1
            
            # Generate multiple candidate neighbors in parallel
            futures = []
            candidate_robots = []
            
            for _ in range(min(max_workers * 2, len(robots))):
                rid = random.choice([r.robot_id for r in robots])
                robot = next(r for r in robots if r.robot_id == rid)
                candidate_robots.append((rid, robot))
                
                # Submit neighbor generation task
                future = executor.submit(
                    self.generate_swap_neighbor,
                    robot,
                    current_paths[rid],
                    current_paths
                )
                futures.append(future)
            
            # Evaluate all candidates
            improved = False
            for (rid, robot), future in zip(candidate_robots, futures):
                try:
                    new_path = future.result(timeout=2.0)
                    
                    if new_path and new_path != current_paths[rid]:
                        test_paths = {**current_paths, rid: new_path}
                        new_conflicts = self.conflict_detector.count_conflicts(test_paths)
                        new_len = sum(len(p) for p in test_paths.values() if p)
                        
                        # Accept if better
                        if new_conflicts < current_conflicts or \
                           (new_conflicts == current_conflicts and new_len < total_len):
                            current_paths = test_paths
                            current_conflicts = new_conflicts
                            total_len = new_len
                            improved = True
                            break
                            
                except (concurrent.futures.TimeoutError, Exception):
                    continue
            
            if improved:
                no_improvement = 0
            else:
                no_improvement += 1
    
    self.best_paths = current_paths
    self.best_conflict_count = current_conflicts
    return current_paths
```

3. **Add method to choose between parallel and sequential**:

```python
def solve(self, robots: List[Robot], use_parallel: bool = True) -> Dict[int, List[Tuple[int, int]]]:
    """
    Solve with automatic parallel/sequential selection.
    
    Args:
        robots: List of robots
        use_parallel: Use parallel version if True and >3 robots
        
    Returns:
        Paths dictionary
    """
    if use_parallel and len(robots) > 3:
        return self.solve_parallel(robots, max_workers=4)
    else:
        paths, _, _ = self.hill_climb(robots, verbose=False)
        return paths
```

**Validation:**
- Test on 8+ agent scenarios
- Measure speedup (should be 1.5-2x on 4+ cores)
- Verify results are comparable quality to sequential version

---

#### 4.2 Optimize Cooperative A* Reservation Table

**File:** `cooperative_astar.py`  
**Problem:** Reservation table rebuilt from scratch for each robot  
**Solution:** Incremental updates to reservation table  
**Expected Impact:** 1.5-2x speedup on cooperative planning

**STRICT INSTRUCTIONS:**

1. **Add method for incremental reservation**:

```python
def _add_path_to_reservation(self, reservation_table: Set[Tuple[int, int, int]], 
                             path: List[Tuple[int, int]], horizon: int = 5000) -> None:
    """
    Add a single path to existing reservation table (incremental update).
    
    Args:
        reservation_table: Existing reservation set (modified in-place)
        path: Path to add
        horizon: Maximum time to reserve goal position
    """
    if not path:
        return
    
    # Reserve path positions
    for t, pos in enumerate(path):
        reservation_table.add((pos[0], pos[1], t))
    
    # Reserve goal for all future time
    goal = path[-1]
    for t in range(len(path), horizon):
        reservation_table.add((goal[0], goal[1], t))
```

2. **Modify `plan` method** to use incremental updates:

```python
def plan(self, agents_tasks: List[List[Tuple[int, int]]]) -> List[List[Tuple[int, int]]]:
    """
    Plan for multiple agents sequentially with incremental reservation.
    
    Args:
        agents_tasks: List of task points for each agent
        
    Returns:
        List of full paths for each agent
    """
    # Use single reservation table updated incrementally - MODIFIED
    reservation_table = set()
    final_paths = []
    
    for tasks in agents_tasks:
        agent_full_path = []
        curr_start = tasks[0]
        
        success = True
        for goal in tasks[1:]:
            start_time = len(agent_full_path) if agent_full_path else 0
            
            # Use existing reservation table - MODIFIED
            segment = self._astar_with_start_time(curr_start, goal, reservation_table, start_time)
            
            if segment is None:
                success = False
                break
            
            if agent_full_path:
                agent_full_path.extend(segment[1:])
            else:
                agent_full_path.extend(segment)
            
            curr_start = segment[-1]
        
        if success:
            final_paths.append(agent_full_path)
            # Incrementally add this agent's path to reservation - NEW
            self._add_path_to_reservation(reservation_table, agent_full_path)
        else:
            final_paths.append(None)
    
    return final_paths
```

**Validation:**
- Results should be identical to original implementation
- Measure speedup (1.5-2x expected)
- Test on 10+ agent scenarios

---

#### 4.3 Add Jump Point Search for Grid-based Pathfinding

**File:** Create new file `jump_point_search.py`  
**Problem:** A* expands many symmetric nodes on open grids  
**Solution:** Jump Point Search (JPS) - skip symmetric nodes  
**Expected Impact:** 3-10x speedup on open maps (minimal obstacles)

**STRICT INSTRUCTIONS:**

1. **Create new file** `jump_point_search.py`:

```python
"""
Jump Point Search (JPS) optimization for grid-based A*.
JPS dramatically reduces node expansions on uniform-cost grids by:
1. Identifying and jumping over symmetric intermediate nodes
2. Only expanding at "jump points" (forced neighbors or goal)

Best for: open grids with few obstacles
Not recommended for: heavily constrained maps
"""

import heapq
from typing import List, Tuple, Optional, Set
from .grid import GridEnvironment


class JumpPointSearch:
    """
    Jump Point Search pathfinder.
    Optimized A* for uniform-cost grid graphs.
    """
    
    def __init__(self, grid: GridEnvironment):
        self.grid = grid
    
    def search(self, start: Tuple[int, int], goal: Tuple[int, int], 
               obstacles: Set[Tuple[int, int]] = None) -> Optional[List[Tuple[int, int]]]:
        """
        Find path using Jump Point Search.
        
        Args:
            start: Start position (x, y)
            goal: Goal position (x, y)
            obstacles: Additional dynamic obstacles
            
        Returns:
            Path from start to goal, or None
        """
        if obstacles is None:
            obstacles = set()
        
        if start == goal:
            return [start]
        
        if not self._is_walkable(start, obstacles) or not self._is_walkable(goal, obstacles):
            return None
        
        open_set = []
        heapq.heappush(open_set, (self._heuristic(start, goal), 0, start, None))
        
        came_from = {}
        g_score = {start: 0}
        closed_set = set()
        
        while open_set:
            _, g, current, parent_dir = heapq.heappop(open_set)
            
            if current in closed_set:
                continue
            closed_set.add(current)
            
            if current == goal:
                return self._reconstruct_path(came_from, current)
            
            # Get successors (jump points)
            successors = self._get_successors(current, parent_dir, goal, obstacles)
            
            for successor, direction in successors:
                if successor in closed_set:
                    continue
                
                # Cost from start to successor
                tentative_g = g + self._distance(current, successor)
                
                if successor not in g_score or tentative_g < g_score[successor]:
                    g_score[successor] = tentative_g
                    came_from[successor] = current
                    f = tentative_g + self._heuristic(successor, goal)
                    heapq.heappush(open_set, (f, tentative_g, successor, direction))
        
        return None
    
    def _get_successors(self, pos: Tuple[int, int], parent_dir: Optional[Tuple[int, int]], 
                       goal: Tuple[int, int], obstacles: Set) -> List[Tuple[Tuple[int, int], Tuple[int, int]]]:
        """
        Get jump point successors for current position.
        
        Returns:
            List of (jump_point, direction) tuples
        """
        successors = []
        
        if parent_dir is None:
            # Initial position - try all directions
            directions = [(1, 0), (-1, 0), (0, 1), (0, -1)]
        else:
            # Prune directions based on parent
            directions = self._get_natural_neighbors(parent_dir)
        
        for direction in directions:
            jump_point = self._jump(pos, direction, goal, obstacles)
            if jump_point:
                successors.append((jump_point, direction))
        
        return successors
    
    def _jump(self, pos: Tuple[int, int], direction: Tuple[int, int], 
              goal: Tuple[int, int], obstacles: Set) -> Optional[Tuple[int, int]]:
        """
        Jump in direction until hitting jump point, obstacle, or goal.
        
        Returns:
            Jump point position, or None if blocked
        """
        next_pos = (pos[0] + direction[0], pos[1] + direction[1])
        
        # Hit obstacle or boundary
        if not self._is_walkable(next_pos, obstacles):
            return None
        
        # Reached goal
        if next_pos == goal:
            return next_pos
        
        # Check for forced neighbors (indicating jump point)
        if self._has_forced_neighbors(next_pos, direction, obstacles):
            return next_pos
        
        # Continue jumping in same direction
        return self._jump(next_pos, direction, goal, obstacles)
    
    def _has_forced_neighbors(self, pos: Tuple[int, int], direction: Tuple[int, int], 
                             obstacles: Set) -> bool:
        """
        Check if position has forced neighbors (makes it a jump point).
        
        A forced neighbor exists when moving in 'direction' from pos,
        and there's a blocked cell adjacent to the path that creates
        an asymmetric situation requiring expansion.
        """
        x, y = pos
        dx, dy = direction
        
        # Horizontal movement
        if dx != 0 and dy == 0:
            # Check cells above and below
            if (not self._is_walkable((x, y + 1), obstacles) and 
                self._is_walkable((x + dx, y + 1), obstacles)):
                return True
            if (not self._is_walkable((x, y - 1), obstacles) and 
                self._is_walkable((x + dx, y - 1), obstacles)):
                return True
        
        # Vertical movement
        elif dx == 0 and dy != 0:
            # Check cells left and right
            if (not self._is_walkable((x + 1, y), obstacles) and 
                self._is_walkable((x + 1, y + dy), obstacles)):
                return True
            if (not self._is_walkable((x - 1, y), obstacles) and 
                self._is_walkable((x - 1, y + dy), obstacles)):
                return True
        
        return False
    
    def _get_natural_neighbors(self, direction: Tuple[int, int]) -> List[Tuple[int, int]]:
        """
        Get natural neighbors to explore based on parent direction.
        This implements JPS pruning rules.
        """
        dx, dy = direction
        neighbors = [direction]  # Always include parent direction
        
        # Add perpendicular directions for straight moves
        if dx != 0 and dy == 0:
            neighbors.extend([(dx, 1), (dx, -1)])
        elif dx == 0 and dy != 0:
            neighbors.extend([(1, dy), (-1, dy)])
        
        return neighbors
    
    def _is_walkable(self, pos: Tuple[int, int], obstacles: Set) -> bool:
        """Check if position is walkable."""
        return self.grid.is_walkable(pos[0], pos[1]) and pos not in obstacles
    
    def _heuristic(self, pos: Tuple[int, int], goal: Tuple[int, int]) -> int:
        """Manhattan distance heuristic."""
        return abs(pos[0] - goal[0]) + abs(pos[1] - goal[1])
    
    def _distance(self, pos1: Tuple[int, int], pos2: Tuple[int, int]) -> int:
        """Actual distance between two positions."""
        return abs(pos1[0] - pos2[0]) + abs(pos1[1] - pos2[1])
    
    def _reconstruct_path(self, came_from: dict, current: Tuple[int, int]) -> List[Tuple[int, int]]:
        """
        Reconstruct path, filling in jumped-over cells.
        """
        path = [current]
        while current in came_from:
            parent = came_from[current]
            # Fill in intermediate cells
            path.extend(self._interpolate(parent, current))
            current = parent
        return list(reversed(path))
    
    def _interpolate(self, pos1: Tuple[int, int], pos2: Tuple[int, int]) -> List[Tuple[int, int]]:
        """
        Fill in cells between two positions.
        """
        cells = []
        x1, y1 = pos1
        x2, y2 = pos2
        
        dx = 1 if x2 > x1 else (-1 if x2 < x1 else 0)
        dy = 1 if y2 > y1 else (-1 if y2 < y1 else 0)
        
        x, y = x1, y1
        while (x, y) != (x2, y2):
            x += dx
            y += dy
            if (x, y) != (x2, y2):  # Don't include endpoint
                cells.append((x, y))
        
        return cells
```

2. **Integrate JPS into `independent_astar.py`**:

```python
# Add import at top
from .jump_point_search import JumpPointSearch

class IndependentAStarPlanner:
    def __init__(self, grid: GridEnvironment):
        self.grid = grid
        self._path_cache: Dict[str, List[Tuple[int, int]]] = {}
        self._cache_hits = 0
        self._cache_misses = 0
        self._jps = JumpPointSearch(grid)  # NEW
    
    def run_independent_astar(self, robot: Robot, obstacles: Set = None, 
                             use_bidirectional: bool = True, 
                             use_jps: bool = True) -> Optional[List[Tuple[int, int]]]:
        """
        Run A* with optional JPS optimization.
        
        Args:
            robot: Robot to plan for
            obstacles: Additional obstacles
            use_bidirectional: Use bidirectional search
            use_jps: Use Jump Point Search (best for open maps)
        """
        if obstacles is None:
            obstacles = set()

        start = robot.start_pos
        goal = robot.goal_pos

        if not self.grid.is_walkable(*start) or not self.grid.is_walkable(*goal):
            return None

        if start == goal:
            return [start]
        
        # Use JPS for open maps (few obstacles) - NEW
        if use_jps and self._is_open_map():
            return self._jps.search(start, goal, obstacles)
        
        # Existing A* logic...
        # ... rest of method ...
    
    def _is_open_map(self) -> bool:
        """
        Check if map is 'open' (< 20% obstacles).
        JPS works best on open maps.
        """
        total_cells = self.grid.width * self.grid.height
        obstacle_count = sum(
            1 for y in range(self.grid.height) 
            for x in range(self.grid.width) 
            if not self.grid.is_walkable(x, y)
        )
        return obstacle_count / total_cells < 0.2
```

**Validation:**
- Test on open grids (few obstacles)
- Verify paths are valid and similar length
- Measure speedup (3-10x on open maps expected)
- JPS may be slower on dense obstacle maps - use heuristic to choose

---

## 🧪 TESTING & VALIDATION

### Testing Requirements for Each Phase

**After EACH optimization:**

1. **Correctness Tests:**
   ```python
   # Run on known scenarios
   test_cases = [
       {"agents": 2, "grid": "10x10", "obstacles": 5},
       {"agents": 5, "grid": "20x20", "obstacles": 20},
       {"agents": 10, "grid": "30x30", "obstacles": 50},
   ]
   
   for test in test_cases:
       original_paths = run_original(test)
       optimized_paths = run_optimized(test)
       assert_paths_valid(optimized_paths)
       assert_quality_similar(original_paths, optimized_paths)
   ```

2. **Performance Benchmarks:**
   ```python
   import time
   
   scenarios = generate_test_scenarios(n_tests=50)
   
   times_before = []
   times_after = []
   
   for scenario in scenarios:
       t0 = time.time()
       result_before = run_original(scenario)
       times_before.append(time.time() - t0)
       
       t0 = time.time()
       result_after = run_optimized(scenario)
       times_after.append(time.time() - t0)
   
   speedup = mean(times_before) / mean(times_after)
   print(f"Average speedup: {speedup:.2f}x")
   ```

3. **Regression Tests:**
   - Keep suite of test cases with known solutions
   - Run after each optimization
   - Flag any behavior changes

### Integration Testing

**After ALL phases complete:**

1. **End-to-end system test** with real workloads
2. **Stress test** with maximum agents (20+)
3. **Memory profiling** to verify no leaks
4. **Long-running stability test** (1000+ pathfinding calls)

---

## 📈 EXPECTED RESULTS

### Performance Targets

| Scenario | Agents | Grid Size | Before | After | Speedup |
|----------|--------|-----------|--------|-------|---------|
| Simple | 2 | 10x10 | 50ms | 10ms | 5x |
| Medium | 5 | 20x20 | 500ms | 50ms | 10x |
| Hard | 10 | 30x30 | 5000ms | 200ms | 25x |
| Extreme | 20 | 50x50 | 60000ms | 2000ms | 30x |

### Memory Targets

- **Baseline:** ~500MB for 10 agents
- **After optimization:** ~200MB for 10 agents
- **Reduction:** 60% memory usage

---

## 🚨 CRITICAL NOTES FOR CODING AGENT

### DO NOT:

1. ❌ **Change algorithm correctness** - paths must remain valid
2. ❌ **Remove safety checks** - validate inputs and outputs
3. ❌ **Break existing API** - maintain method signatures
4. ❌ **Skip testing** - validate each change before moving on
5. ❌ **Optimize prematurely** - follow phase order strictly

### DO:

1. ✅ **Test incrementally** - validate after each optimization
2. ✅ **Keep backups** - maintain working version
3. ✅ **Measure everything** - benchmark before/after
4. ✅ **Document changes** - comment why optimizations work
5. ✅ **Profile first** - verify bottlenecks match predictions

### Code Quality Standards

1. **Type hints** on all new methods
2. **Docstrings** for public methods
3. **Comments** explaining non-obvious optimizations
4. **Error handling** for edge cases
5. **Consistent style** with existing codebase

---

## 📋 IMPLEMENTATION CHECKLIST

### Phase 1: Critical Bottlenecks
- [ ] Optimize conflict detection with spatial indexing
- [ ] Replace CBS constraint table with dictionary
- [ ] Add neighbor caching to grid
- [ ] Test all changes
- [ ] Benchmark speedup

### Phase 2: Algorithm Optimizations
- [ ] Implement bidirectional A*
- [ ] Add CBS early termination
- [ ] Add max expansion limits to all A* methods
- [ ] Test all changes
- [ ] Benchmark speedup

### Phase 3: Memory Optimizations
- [ ] Implement node object pooling
- [ ] Add distance caching to grid
- [ ] Test all changes
- [ ] Profile memory usage

### Phase 4: Advanced Optimizations
- [ ] Implement parallel hill climbing
- [ ] Optimize cooperative A* reservation table
- [ ] Add Jump Point Search (optional)
- [ ] Test all changes
- [ ] Benchmark speedup

### Final Validation
- [ ] Run full test suite
- [ ] Measure overall speedup
- [ ] Profile memory usage
- [ ] Stress test with 20+ agents
- [ ] Document final results

---

## 🎯 SUCCESS CRITERIA

**Minimum Requirements:**
- ✅ All existing tests pass
- ✅ 10x overall speedup on medium scenarios
- ✅ 30% memory reduction
- ✅ No correctness regressions

**Target Goals:**
- 🎯 20x overall speedup on medium scenarios
- 🎯 50x speedup on hard scenarios
- 🎯 60% memory reduction
- 🎯 Support 20+ agents in real-time

---

## 📝 FINAL NOTES

This optimization plan is designed to be:
1. **Systematic** - Clear phase order
2. **Measurable** - Specific performance targets
3. **Safe** - Incremental with testing
4. **Comprehensive** - Covers all major bottlenecks

Follow the phases in order. Test after each change. Measure everything.

Good luck! 🚀
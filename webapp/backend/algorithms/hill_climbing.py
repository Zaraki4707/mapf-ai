import heapq
import random
import concurrent.futures
from typing import List, Dict, Tuple, Optional
from copy import deepcopy

from .grid import GridEnvironment
from .robot import Robot
from .conflict_detector import ConflictDetector
from .independent_astar import IndependentAStarPlanner

MAX_NODE_EXPANSIONS = 50000

class HillClimbingSolver:
    """
    Enhanced Multi-Robot Coordinator:
    Phase 1: Robust Prioritized Planning with backtrack capabilities.
    Phase 2: Constrained Hill Climbing to optimize path lengths while preserving validity.
    """

    def __init__(self, grid: GridEnvironment, max_iterations: int = 2000,
                 max_neighbors_per_iteration: int = 10, seed: int = None):
        self.grid = grid
        self.max_iterations = max_iterations
        self.max_neighbors_per_iteration = max_neighbors_per_iteration
        self.conflict_detector = ConflictDetector()
        self.best_paths = {}
        self.best_conflict_count = float('inf')
        self.astar_planner = IndependentAStarPlanner(grid)

        if seed is not None:
            random.seed(seed)

    def initialize_paths(self, robots: List[Robot]) -> Dict[int, List[Tuple[int, int]]]:
        """Initialize paths using Independent A*."""
        return self.astar_planner.plan_all_robots(robots)

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

    def generate_swap_neighbor(self, robot: Robot, current_path: List[Tuple[int, int]], 
                                other_paths: Dict[int, List[Tuple[int, int]]]) -> Optional[List[Tuple[int, int]]]:
        """
        True hill climbing: shorten path by swapping move orders.
        Takes existing path, tries to find shorter valid path via local modifications.
        """
        if len(current_path) < 4:
            return current_path
        
        best_path = list(current_path)
        best_len = len(current_path)
        
        # 1. Path smoothing: remove redundant intermediate waypoints
        smoothed = self._path_smoothing(current_path, other_paths, robot.robot_id)
        if self._is_valid_path(smoothed, other_paths, robot.robot_id):
            return smoothed
        
        # 2. Try swapping consecutive move segments
        for i in range(1, len(current_path) - 2):
            for j in range(i + 1, len(current_path)):
                # Swap segment [i:j] 
                candidate = current_path[:i] + current_path[i:j][::-1] + current_path[j:]
                if self._is_valid_path(candidate, other_paths, robot.robot_id):
                    if len(candidate) < best_len:
                        best_path = candidate
                        best_len = len(candidate)
        
        return best_path if len(best_path) < len(current_path) else current_path

    def _path_smoothing(self, path: List[Tuple[int, int]], 
                        other_paths: Dict, robot_id: int) -> List[Tuple[int, int]]:
        """Remove unnecessary waypoints that don't change direction"""
        if len(path) < 3:
            return path
        
        smoothed = [path[0]]
        for i in range(1, len(path) - 1):
            # Keep point if it changes direction
            if path[i-1] != path[i+1]:
                smoothed.append(path[i])
        smoothed.append(path[-1])
        
        return smoothed if self._is_valid_path(smoothed, other_paths, robot_id) else path

    def _is_valid_path(self, path: List[Tuple[int, int]], 
                       other_paths: Dict, robot_id: int) -> bool:
        """Check if path has no conflicts with other robots"""
        if not path:
            return False
        
        for t, pos in enumerate(path):
            # Check vertex conflicts
            for oid, opath in other_paths.items():
                if oid != robot_id and t < len(opath):
                    if opath[t] == pos:
                        return False
            
            # Check edge conflicts
            if t < len(path) - 1:
                for oid, opath in other_paths.items():
                    if oid != robot_id and t + 1 < len(opath):
                        if (opath[t] == path[t+1] and opath[t+1] == path[t]):
                            return False
        
        return True

    def hill_climb(self, robots: List[Robot], verbose: bool = True) -> Tuple[Dict, int, List]:
        """Main optimization loop with TRUE swap-based hill climbing"""
        current_paths = self.initialize_paths(robots)
        current_conflicts = self.conflict_detector.count_conflicts(current_paths)
        total_len = sum(len(p) for p in current_paths.values())
        
        if verbose:
            print(f"\nPhase 2: Swap-based Length Optimization... (Start: {current_conflicts} conflicts, {total_len} steps)")
        
        no_imp = 0
        for i in range(self.max_iterations):
            # Randomly pick robot to optimize
            rid = random.choice([r.robot_id for r in robots])
            robot = next(r for r in robots if r.robot_id == rid)
            
            # TRUE hill climbing neighbor generation (swap moves)
            new_p = self.generate_swap_neighbor(robot, current_paths[rid], current_paths)
            
            test_paths = {**current_paths, rid: new_p}
            new_conf = self.conflict_detector.count_conflicts(test_paths)
            new_len = sum(len(p) for p in test_paths.values())
            
            # Accept if: better conflicts OR same conflicts but shorter path
            if new_conf < current_conflicts:
                current_paths = test_paths
                current_conflicts = new_conf
                total_len = new_len
                no_imp = 0
            elif new_conf == current_conflicts and new_len < total_len:
                current_paths = test_paths
                total_len = new_len
                no_imp = 0
            else:
                no_imp += 1
            
            if no_imp > 200:
                break
        
        self.best_paths = current_paths
        self.best_conflict_count = current_conflicts
        return self.best_paths, self.best_conflict_count, []

    def _cooperative_astar_replan(self, robot: Robot, current_path: List[Tuple[int, int]], 
                                  other_paths: Dict, optimize: bool = False) -> List[Tuple[int, int]]:
        reserved = set()
        for oid, opath in other_paths.items():
            if oid != robot.robot_id:
                for t, pos in enumerate(opath):
                    reserved.add((pos[0], pos[1], t))
                if opath:
                    gl = opath[-1]
                    # Large horizon for stay-at-goal
                    for t in range(len(opath), 500):
                        reserved.add((gl[0], gl[1], t))

        start, goal = robot.start_pos, robot.goal_pos
        if not self.grid.is_walkable(*start) or not self.grid.is_walkable(*goal):
            return [start]

        open_set = []
        # (f, g, x, y, t)
        heapq.heappush(open_set, (self.grid.get_manhattan_distance(start, goal), 0, start[0], start[1], 0))
        
        g_score = {(start[0], start[1], 0): 0}
        parent_map = {(start[0], start[1], 0): None}
        closed_set = set()
        
        max_horizon = max(200, len(other_paths) * 20)
        
        expansions = 0
        while open_set and expansions < MAX_NODE_EXPANSIONS:
            expansions += 1
            f, g, cx, cy, ct = heapq.heappop(open_set)
            
            if (cx, cy, ct) in closed_set: continue
            closed_set.add((cx, cy, ct))
            
            if (cx, cy) == goal:
                # To avoid collisions with robots arriving later, we check if we can stay at goal
                can_stay = True
                for t_stay in range(ct + 1, max_horizon):
                    if (cx, cy, t_stay) in reserved:
                        can_stay = False
                        break
                
                if can_stay:
                    res_path = []
                    curr_state = (cx, cy, ct)
                    while curr_state:
                        res_path.append((curr_state[0], curr_state[1]))
                        curr_state = parent_map[curr_state]
                    return res_path[::-1]
            
            if ct >= max_horizon: continue

            # Wait action + 4 movements
            moves = self.grid.get_neighbors(cx, cy) + [(cx, cy)]
            for nx, ny in moves:
                nt = ct + 1
                if (nx, ny, nt) in reserved: continue
                
                # Swap conflict check
                is_edge = False
                for oid, opath in other_paths.items():
                    if oid != robot.robot_id and len(opath) > nt:
                        if opath[ct] == (nx, ny) and opath[nt] == (cx, cy):
                            is_edge = True
                            break
                if is_edge: continue

                ng = g + 1
                ns = (nx, ny, nt)
                if ns not in g_score or ng < g_score[ns]:
                    g_score[ns] = ng
                    nf = ng + self.grid.get_manhattan_distance((nx, ny), goal)
                    parent_map[ns] = (cx, cy, ct)
                    heapq.heappush(open_set, (nf, ng, nx, ny, nt))

        return current_path if current_path else [start]

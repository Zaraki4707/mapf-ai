import heapq
import time
import random
from collections import defaultdict
from typing import List, Dict, Tuple, Optional, Set
from copy import deepcopy

# Placeholder for dependencies assumed by HC.ipynb
class Robot:
    def __init__(self, robot_id: int, grid, start_pos: Tuple[int, int], goal_pos: Tuple[int, int]):
        self.robot_id = robot_id
        self.grid = grid
        self.start_pos = start_pos
        self.goal_pos = goal_pos

class Node:
    def __init__(self, position, parent=None, g=0, h=0):
        self.position = position
        self.parent = parent
        self.g = g
        self.h = h
        self.f = g + h

    def __lt__(self, other):
        return self.f < other.f

    def reconstruct_path(self):
        path = []
        current = self
        while current:
            path.append(current.position)
            current = current.parent
        return path[::-1]

class ConflictDetector:
    def __init__(self):
        pass

    def count_conflicts(self, paths: Dict[int, List[Tuple[int, int]]]) -> int:
        return len(self.get_conflict_report(paths))

    def get_conflict_report(self, paths: Dict[int, List[Tuple[int, int]]]) -> List[Dict]:
        conflicts = []
        if not paths: return []
        
        # Filter valid paths
        valid_paths = {rid: p for rid, p in paths.items() if p}
        if not valid_paths: return []
        
        robot_ids = list(valid_paths.keys())
        max_time = max(len(p) for p in valid_paths.values())
        
        # Pad paths to max length
        padded_paths = {}
        for rid, path in valid_paths.items():
            goal = path[-1]
            padded_paths[rid] = path + [goal] * (max_time - len(path))
            
        for t in range(max_time):
            # Vertex Detection
            pos_map = defaultdict(list)
            for rid in robot_ids:
                pos = padded_paths[rid][t]
                pos_map[pos].append(rid)
                
            for pos, r_list in pos_map.items():
                if len(r_list) > 1:
                    conflicts.append({'type': 'vertex', 'time': t, 'position': pos, 'robot1': r_list[0], 'robot2': r_list[1]})
            
            # Edge / Swap Detection
            if t < max_time - 1:
                for i, r1 in enumerate(robot_ids):
                    for r2 in robot_ids[i+1:]:
                        if (padded_paths[r1][t] == padded_paths[r2][t+1] and 
                            padded_paths[r1][t+1] == padded_paths[r2][t] and 
                            padded_paths[r1][t] != padded_paths[r1][t+1]):
                            edge = (padded_paths[r1][t], padded_paths[r1][t+1])
                            conflicts.append({'type': 'edge', 'time': t, 'edge': edge, 'robot1': r1, 'robot2': r2})
                            
        return conflicts


class GridEnvironment:
    """Warehouse grid representation"""
    def __init__(self, filename=None):
        self.grid = []
        self.height = 0
        self.width = 0
        if filename:
            self.load_from_file(filename)
    
    def load_from_file(self, filename):
        self.grid = []
        try:
            with open(filename, 'r') as f:
                for line in f:
                    row = [char == '.' for char in line.strip() if char in '.T']
                    if row:
                        self.grid.append(row)
            
            if self.grid:
                max_w = max(len(row) for row in self.grid)
                for i in range(len(self.grid)):
                    if len(self.grid[i]) < max_w:
                        self.grid[i].extend([False] * (max_w - len(self.grid[i])))
                
            self.height = len(self.grid)
            self.width = len(self.grid[0]) if self.height > 0 else 0
            print(f"✓ Grid loaded: {self.width}x{self.height}")
        except Exception as e:
            print(f"✗ Error loading grid: {e}")
    
    def is_valid_position(self, x, y):
        return 0 <= y < self.height and 0 <= x < self.width
    
    def is_walkable(self, x, y):
        if not self.is_valid_position(x, y):
            return False
        return self.grid[y][x]
    
    def get_neighbors(self, x, y):
        neighbors = []
        for dx, dy in [(0, 1), (1, 0), (0, -1), (-1, 0)]:
            nx, ny = x + dx, y + dy
            if self.is_walkable(nx, ny):
                neighbors.append((nx, ny))
        return neighbors
    
    def manhattan_distance(self, pos1, pos2):
        return abs(pos1[0] - pos2[0]) + abs(pos1[1] - pos2[1])


class AStarPlanner:
    """A* pathfinding wrapper for independent robot planning"""
    def __init__(self, grid: GridEnvironment):
        self.grid = grid
    
    def plan_path(self, robot: Robot) -> Optional[List[Tuple[int, int]]]:
        start = robot.start_pos
        goal = robot.goal_pos
        
        if not self.grid.is_walkable(*start) or not self.grid.is_walkable(*goal):
            return None
        
        if start == goal:
            return [start]
        
        open_set = []
        start_node = Node(start, g=0, h=self.grid.manhattan_distance(start, goal))
        heapq.heappush(open_set, start_node)
        
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
            for neighbor in neighbors:
                tentative_g = current.g + 1
                
                if neighbor not in g_score or tentative_g < g_score[neighbor]:
                    g_score[neighbor] = tentative_g
                    h = self.grid.manhattan_distance(neighbor, goal)
                    neighbor_node = Node(neighbor, parent=current, g=tentative_g, h=h)
                    heapq.heappush(open_set, neighbor_node)
        
        return None
    
    def plan_all_robots_independent(self, robots: List[Robot]) -> Dict[int, List[Tuple[int, int]]]:
        paths = {}
        for robot in robots:
            path = self.plan_path(robot)
            paths[robot.robot_id] = path if path else [robot.start_pos]
        return paths


class HillClimbingSolver:
    """
    Enhanced Two-Phase Multi-Robot Coordinator:
    Phase 1: Robust Prioritized Planning with backtrack capabilities.
    Phase 2: Constrained Hill Climbing to optimize path lengths while preserving validity.
    """

    def __init__(self, grid: GridEnvironment, max_iterations: int = 5000, 
                 max_neighbors_per_iteration: int = 20, seed: int = None):
        self.grid = grid
        self.max_iterations = max_iterations
        self.max_neighbors_per_iteration = max_neighbors_per_iteration
        self.conflict_detector = ConflictDetector()
        self.a_star_planner = AStarPlanner(grid)
        self.robots = []
        self.best_paths = {}
        self.best_conflict_count = float('inf')
        
        if seed is not None:
            random.seed(seed)

    def initialize_paths(self, robots: List[Robot]) -> Dict[int, List[Tuple[int, int]]]:
        self.robots = robots
        best_init_paths = {}
        min_init_conflicts = float('inf')
        
        for attempt in range(5):
            print(f"Phase 1 - Attempt {attempt + 1}: Searching for valid initial configuration...")
            shuffled_robots = list(robots)
            random.shuffle(shuffled_robots)
            
            current_init_paths = {}
            for robot in shuffled_robots:
                path = self._cooperative_astar_replan(robot, [], current_init_paths)
                current_init_paths[robot.robot_id] = path
            
            conflicts = self.conflict_detector.count_conflicts(current_init_paths)
            if conflicts < min_init_conflicts:
                min_init_conflicts = conflicts
                best_init_paths = deepcopy(current_init_paths)
                
            if conflicts == 0:
                print("✓ Found zero-conflict initial solution.")
                break
                
        return best_init_paths

    def generate_neighbor_path(self, robot: Robot, current_path: List[Tuple[int, int]], 
                               other_paths: Dict[int, List[Tuple[int, int]]]) -> Optional[List[Tuple[int, int]]]:
        return self._cooperative_astar_replan(robot, current_path, other_paths, optimize=True)

    def _cooperative_astar_replan(self, robot: Robot, current_path: List[Tuple[int, int]], 
                                  other_paths: Dict, optimize: bool = False) -> List[Tuple[int, int]]:
        reserved = set()
        for oid, opath in other_paths.items():
            if oid != robot.robot_id:
                for t, pos in enumerate(opath):
                    reserved.add((pos[0], pos[1], t))
                if opath:
                    gl = opath[-1]
                    for t in range(len(opath), 1000):
                        reserved.add((gl[0], gl[1], t))

        start, goal = robot.start_pos, robot.goal_pos
        if not self.grid.is_walkable(*start) or not self.grid.is_walkable(*goal):
            return [start]

        open_set = []
        heapq.heappush(open_set, (self.grid.manhattan_distance(start, goal), 0, start[0], start[1], 0))
        
        g_score = {(start[0], start[1], 0): 0}
        parent_map = {(start[0], start[1], 0): None}
        closed_set = set()
        
        max_horizon = max(200, len(other_paths) * 10)
        
        while open_set:
            f, g, cx, cy, ct = heapq.heappop(open_set)
            
            if (cx, cy, ct) in closed_set: continue
            closed_set.add((cx, cy, ct))
            
            if (cx, cy) == goal:
                res_path = []
                curr_state = (cx, cy, ct)
                while curr_state:
                    res_path.append((curr_state[0], curr_state[1]))
                    curr_state = parent_map[curr_state]
                return res_path[::-1]
            
            if ct >= max_horizon: continue

            moves = self.grid.get_neighbors(cx, cy) + [(cx, cy)]
            for nx, ny in moves:
                nt = ct + 1
                if (nx, ny, nt) in reserved: continue
                
                is_edge = False
                for oid, opath in other_paths.items():
                    if oid != robot.robot_id and len(opath) > nt:
                        if opath[ct] == (nx, ny) and opath[nt] == (cx, cy):
                            is_edge = True; break
                if is_edge: continue

                ng = g + 1
                ns = (nx, ny, nt)
                if ns not in g_score or ng < g_score[ns]:
                    g_score[ns] = ng
                    nf = ng + self.grid.manhattan_distance((nx, ny), goal)
                    parent_map[ns] = (cx, cy, ct)
                    heapq.heappush(open_set, (nf, ng, nx, ny, nt))

        return current_path if current_path else [start]

    def hill_climb(self, robots: List[Robot], verbose: bool = True) -> Tuple[Dict, int, List]:
        current_paths = self.initialize_paths(robots)
        current_conflicts = self.conflict_detector.count_conflicts(current_paths)
        
        total_len = sum(len(p) for p in current_paths.values())
        
        if verbose:
            print(f"\nPhase 2: Length Optimization... (Start Conflicts: {current_conflicts})")

        no_imp = 0
        for i in range(self.max_iterations):
            rid = random.choice([r.robot_id for r in robots])
            robot = next(r for r in robots if r.robot_id == rid)
            
            new_p = self.generate_neighbor_path(robot, current_paths[rid], current_paths)
            
            test_paths = {**current_paths, rid: new_p}
            new_conf = self.conflict_detector.count_conflicts(test_paths)
            new_len = sum(len(p) for p in test_paths.values())

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

            if no_imp > 200: break

        self.best_paths = current_paths
        self.best_conflict_count = current_conflicts
        return self.best_paths, self.best_conflict_count, []


def validate_paths(paths: Dict[int, List[Tuple[int, int]]], 
                   grid: GridEnvironment, robots: List[Robot]) -> Tuple[bool, List[str]]:
    errors = []
    for robot in robots:
        path = paths.get(robot.robot_id)
        if path is None or len(path) == 0:
            errors.append(f"Robot {robot.robot_id}: No path found")
            continue
        if path[0] != robot.start_pos:
            errors.append(f"Robot {robot.robot_id}: Path does not start at start position")
        if path[-1] != robot.goal_pos:
            errors.append(f"Robot {robot.robot_id}: Path does not end at goal position")
        for i, (x, y) in enumerate(path):
            if not grid.is_walkable(x, y):
                errors.append(f"Robot {robot.robot_id}: Position ({x},{y}) at step {i} is not walkable")
        for i in range(len(path) - 1):
            x1, y1 = path[i]
            x2, y2 = path[i + 1]
            distance = abs(x2 - x1) + abs(y2 - y1)
            if distance > 1:
                errors.append(f"Robot {robot.robot_id}: Invalid move from {path[i]} to {path[i+1]} at step {i}")
    return len(errors) == 0, errors


def detect_deadlocks(paths: Dict[int, List[Tuple[int, int]]], robots: List[Robot]) -> List[Dict]:
    deadlocks = []
    robot_map = {r.robot_id: r for r in robots}
    
    for rid, path in paths.items():
        robot = robot_map[rid]
        if path[-1] != robot.goal_pos:
            deadlocks.append({
                'type': 'incomplete_path',
                'robot': rid,
                'last_pos': path[-1],
                'goal': robot.goal_pos,
                'message': f"Robot {rid} stopped at {path[-1]} without reaching goal {robot.goal_pos}"
            })
            
    stuck_robots = []
    for rid, path in paths.items():
        robot = robot_map[rid]
        final_pos = path[-1]
        if final_pos != robot.goal_pos:
            stuck_robots.append(rid)
            
    if len(stuck_robots) > 1:
        for i in range(len(stuck_robots)):
            for j in range(i + 1, len(stuck_robots)):
                r1_id = stuck_robots[i]
                r2_id = stuck_robots[j]
                p1 = paths[r1_id][-1]
                p2 = paths[r2_id][-1]
                
                dist = abs(p1[0]-p2[0]) + abs(p1[1]-p2[1])
                if dist <= 1:
                    deadlocks.append({
                        'type': 'mutual_blockage',
                        'robots': [r1_id, r2_id],
                        'positions': [p1, p2],
                        'message': f"Robots {r1_id} and {r2_id} are stuck adjacent to each other at {p1} and {p2}"
                    })
                    
    return deadlocks

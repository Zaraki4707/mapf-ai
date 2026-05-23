import heapq
from typing import List, Tuple, Dict, Set, Optional

from .node import Node
from .grid import GridEnvironment
from .robot import Robot
from .jump_point_search import JumpPointSearch

MAX_NODE_EXPANSIONS = 50000

class IndependentAStarPlanner:
    """
    Independent A* planner - each robot is planned independently without awareness of others.
    """

    def __init__(self, grid: GridEnvironment):
        self.grid = grid
        self._path_cache: Dict[str, List[Tuple[int, int]]] = {}
        self._cache_hits = 0
        self._cache_misses = 0
        self._jps = JumpPointSearch(grid)

    def _get_cache_key(self, start: Tuple[int, int], goal: Tuple[int, int], obstacles: Set) -> str:
        obs_hash = frozenset(obstacles) if obstacles else frozenset()
        return f"{start}-{goal}-{obs_hash}"
        
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
        
        expansions = 0
        while open_forward and open_backward and expansions < MAX_NODE_EXPANSIONS:
            expansions += 1
            # Expand forward frontier
            if open_forward:
                _, g_f, pos_f = heapq.heappop(open_forward)
                
                if pos_f in closed_forward:
                    pass
                else:
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
                    pass
                else:
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

    def run_independent_astar(self, robot: Robot, obstacles: Set = None, 
                             use_bidirectional: bool = True, 
                             use_jps: bool = False) -> Optional[List[Tuple[int, int]]]:
        if obstacles is None:
            obstacles = set()

        start = robot.start_pos
        goal = robot.goal_pos

        if not self.grid.is_walkable(*start) or not self.grid.is_walkable(*goal):
            return None

        if start == goal:
            return [start]
            
        Node.reset_pool()

        # Use JPS for open maps (few obstacles)
        if use_jps and self._is_open_map():
            return self._jps.search(start, goal, obstacles)

        # Use bidirectional for paths likely to be long
        path_distance = self.grid.manhattan_distance(start, goal)
        if use_bidirectional and path_distance > 10:
            return self._bidirectional_astar(robot, obstacles)

        open_set = []
        start_node = Node.create(start, g=0, h=self.grid.manhattan_distance(start, goal))
        heapq.heappush(open_set, start_node)

        came_from = {}
        g_score = {start: 0}
        closed_set = set()

        expansions = 0
        while open_set and expansions < MAX_NODE_EXPANSIONS:
            expansions += 1
            current = heapq.heappop(open_set)

            if current.position in closed_set:
                continue
            closed_set.add(current.position)

            if current.position == goal:
                return current.reconstruct_path()

            neighbors = self.grid.get_neighbors(*current.position)
            neighbors.append(current.position)
            for neighbor in neighbors:
                if neighbor in obstacles:
                    continue

                tentative_g = current.g + 1

                if neighbor not in g_score or tentative_g < g_score[neighbor]:
                    g_score[neighbor] = tentative_g
                    h = self.grid.manhattan_distance(neighbor, goal)
                    neighbor_node = Node.create(neighbor, parent=current, g=tentative_g, h=h)
                    came_from[neighbor_node] = current
                    heapq.heappush(open_set, neighbor_node)

        return None

    def plan_all_robots(self, robots: List[Robot]) -> Dict[int, Optional[List[Tuple[int, int]]]]:
        paths = {}

        for robot in robots:
            cache_key = self._get_cache_key(robot.start_pos, robot.goal_pos, None)
            if cache_key in self._path_cache:
                self._cache_hits += 1
                paths[robot.robot_id] = self._path_cache[cache_key].copy()
                continue
            self._cache_misses += 1
            path = self.run_independent_astar(robot)
            if path:
                self._path_cache[cache_key] = path.copy()
            paths[robot.robot_id] = path

        return paths

    def get_cache_stats(self) -> Dict:
        total = self._cache_hits + self._cache_misses
        hit_rate = self._cache_hits / total if total > 0 else 0
        return {'hits': self._cache_hits, 'misses': self._cache_misses, 'hit_rate': hit_rate}

    def clear_cache(self) -> None:
        self._path_cache.clear()
        self._cache_hits = 0
        self._cache_misses = 0
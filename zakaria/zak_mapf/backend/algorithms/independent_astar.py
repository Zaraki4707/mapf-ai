import heapq
from typing import List, Tuple, Dict, Set, Optional

from .node import Node
from .grid import GridEnvironment
from .robot import Robot


class IndependentAStarPlanner:
    """
    Independent A* planner - each robot is planned independently without awareness of others.
    This serves as the baseline for comparison.
    """

    def __init__(self, grid: GridEnvironment):
        self.grid = grid
        self._path_cache: Dict[str, List[Tuple[int, int]]] = {}
        self._cache_hits = 0
        self._cache_misses = 0

    def _get_cache_key(self, start: Tuple[int, int], goal: Tuple[int, int], obstacles: Set) -> str:
        obs_hash = frozenset(obstacles) if obstacles else frozenset()
        return f"{start}-{goal}-{obs_hash}"

    def run_independent_astar(self, robot: Robot, obstacles: Set = None) -> Optional[List[Tuple[int, int]]]:
        if obstacles is None:
            obstacles = set()

        start = robot.start_pos
        goal = robot.goal_pos

        if not self.grid.is_walkable(*start) or not self.grid.is_walkable(*goal):
            return None

        if start == goal:
            return [start]

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
            neighbors.append(current.position)
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
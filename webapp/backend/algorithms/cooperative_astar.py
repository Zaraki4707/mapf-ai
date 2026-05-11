import heapq
import copy
from typing import List, Tuple, Dict, Set, Optional

class CooperativeAStarPlanner:
    """
    Cooperative A* implementation based on HamamtiAsma's implementation.
    Plans robots sequentially using a reservation table to avoid vertex and edge conflicts.
    """

    def __init__(self, grid):
        self.grid = grid

    def heuristic(self, pos: Tuple[int, int], goal: Tuple[int, int]) -> int:
        return abs(pos[0] - goal[0]) + abs(pos[1] - goal[1])

    def _build_reservation_table(self, paths: List[List[Tuple[int, int]]], horizon: int = 5000) -> Set[Tuple[int, int, int]]:
        """
        Converts a list of planned paths into a reservation table (set of (x, y, t) tuples).
        """
        if not paths:
            return set()
        
        table = set()
        for path in paths:
            if not path:
                continue
            for t, pos in enumerate(path):
                table.add((pos[0], pos[1], t))
            
            # CRITICAL: After a robot reaches its final goal, it stays there FOREVER.
            # We reserve its destination cell for all future time steps.
            goal = path[-1]
            for t in range(len(path), horizon):
                table.add((goal[0], goal[1], t))
        return table

    def _check_vertex_conflict(self, pos: Tuple[int, int], t: int, reservation_table: Set[Tuple[int, int, int]]) -> bool:
        return (pos[0], pos[1], t) in reservation_table

    def _check_edge_conflict(self, pos_from: Tuple[int, int], pos_to: Tuple[int, int], t: int, reservation_table: Set[Tuple[int, int, int]]) -> bool:
        """
        Checks for swap (edge) conflicts.
        """
        other_was_at_to = (pos_to[0], pos_to[1], t - 1) in reservation_table
        other_goes_to_src = (pos_from[0], pos_from[1], t) in reservation_table
        return other_was_at_to and other_goes_to_src

    def _astar_single_robot(self, start: Tuple[int, int], goal: Tuple[int, int], reservation_table: Set[Tuple[int, int, int]], max_time: int = 1000) -> Optional[List[Tuple[int, int]]]:
        h0 = self.heuristic(start, goal)
        # (f, g, x, y, t)
        open_heap = [(h0, 0, start[0], start[1], 0)]
        
        came_from = {(start[0], start[1], 0): None}
        g_score = {(start[0], start[1], 0): 0}
        
        # Directions: Right, Down, Left, Up, Wait
        directions = [(0, 1), (1, 0), (0, -1), (-1, 0), (0, 0)]

        while open_heap:
            f, g, x, y, t = heapq.heappop(open_heap)

            if (x, y) == goal:
                return self._reconstruct_path(came_from, (x, y, t))

            if t >= max_time:
                continue

            if g > g_score.get((x, y, t), float('inf')):
                continue

            nt = t + 1
            for dx, dy in directions:
                nx, ny = x + dx, y + dy
                
                if not self.grid.is_walkable(nx, ny):
                    continue
                
                if self._check_vertex_conflict((nx, ny), nt, reservation_table):
                    continue
                
                if (dx, dy) != (0, 0):
                    if self._check_edge_conflict((x, y), (nx, ny), nt, reservation_table):
                        continue
                
                new_g = g + 1
                new_state = (nx, ny, nt)
                if new_g < g_score.get(new_state, float('inf')):
                    g_score[new_state] = new_g
                    came_from[new_state] = (x, y, t)
                    h = self.heuristic((nx, ny), goal)
                    heapq.heappush(open_heap, (new_g + h, new_g, nx, ny, nt))
        
        return None

    def _reconstruct_path(self, came_from: Dict, goal_state: Tuple[int, int, int]) -> List[Tuple[int, int]]:
        path = []
        current = goal_state
        while current is not None:
            path.append((current[0], current[1]))
            current = came_from[current]
        return path[::-1]

    def plan(self, agents_tasks: List[List[Tuple[int, int]]]) -> List[List[Tuple[int, int]]]:
        """
        Plans for multiple agents sequentially.
        agents_tasks: List of task points for each agent. e.g. [[start1, pick1, drop1, dest1], ...]
        """
        reservation_table = set()
        final_paths = []
        all_planned_paths = []

        for tasks in agents_tasks:
            agent_full_path = []
            curr_start = tasks[0]
            
            success = True
            for goal in tasks[1:]:
                # Note: The reservation table is time-indexed. 
                # When planning the next segment of an agent, we need to consider the time it starts.
                # Here we adjust A* to start at the current full path length.
                start_time = len(agent_full_path) if agent_full_path else 0
                
                # Update reservation table to include "stay-at-goal" positions for all PREVIOUSLY planned robots
                # for the duration of THIS robot's segment. 
                # We use a large enough horizon to cover the search.
                current_reservation = self._build_reservation_table(all_planned_paths)

                segment = self._astar_with_start_time(curr_start, goal, current_reservation, start_time)
                
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
                all_planned_paths.append(agent_full_path)
                # Wait for the next agent - reservation table is built inside the loop for segments
            else:
                final_paths.append(None)
        
        return final_paths

    def _astar_with_start_time(self, start: Tuple[int, int], goal: Tuple[int, int], reservation_table: Set[Tuple[int, int, int]], start_time: int, max_time: int = 1500) -> Optional[List[Tuple[int, int]]]:
        h0 = self.heuristic(start, goal)
        open_heap = [(start_time + h0, start_time, start[0], start[1])]
        
        came_from = {(start[0], start[1], start_time): None}
        g_score = {(start[0], start[1], start_time): start_time}
        
        directions = [(0, 1), (1, 0), (0, -1), (-1, 0), (0, 0)]

        # Adjust max_time to be relative to start_time
        absolute_max_time = start_time + max_time

        while open_heap:
            f, g, x, y = heapq.heappop(open_heap)
            t = g

            if (x, y) == goal:
                return self._reconstruct_path_with_time(came_from, (x, y, t))

            if t >= absolute_max_time:
                continue

            nt = t + 1
            for dx, dy in directions:
                nx, ny = x + dx, y + dy
                
                if not self.grid.is_walkable(nx, ny):
                    continue
                
                # Check for Vertex Conflict
                if (nx, ny, nt) in reservation_table:
                    continue
                
                # Check for Edge (swap) Conflict
                # robot A moves (x,y) -> (nx,ny) while robot B moves (nx,ny) -> (x,y)
                if (nx, ny, t) in reservation_table and (x, y, nt) in reservation_table:
                    continue
                
                new_g = g + 1
                new_state = (nx, ny, nt)
                if new_g < g_score.get(new_state, float('inf')):
                    g_score[new_state] = new_g
                    came_from[new_state] = (x, y, t)
                    h = self.heuristic((nx, ny), goal)
                    heapq.heappush(open_heap, (new_g + h, new_g, nx, ny))
        
        return None

    def _reconstruct_path_with_time(self, came_from: Dict, state_with_time: Tuple[int, int, int]) -> List[Tuple[int, int]]:
        path = []
        current = state_with_time
        while current is not None:
            path.append((current[0], current[1]))
            current = came_from[current]
        return path[::-1]

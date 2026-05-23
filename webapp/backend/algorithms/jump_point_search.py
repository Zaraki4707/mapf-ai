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
        For 4-connected grids, we continue straight or turn perpendicular.
        """
        dx, dy = direction
        neighbors = [direction]  # Always include parent direction
        
        # Add perpendicular directions for straight moves
        if dx != 0 and dy == 0:
            neighbors.extend([(0, 1), (0, -1)])
        elif dx == 0 and dy != 0:
            neighbors.extend([(1, 0), (-1, 0)])
        
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

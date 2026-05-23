from typing import List, Tuple, Set


class GridEnvironment:
    """Represents the grid map"""

    def __init__(self, height: int, width: int, obstacles: List[Tuple[int, int]] = None):
        self.height = height
        self.width = width
        self.grid = [[True for _ in range(width)] for _ in range(height)]
        
        # Initialize neighbor cache - NEW
        self._neighbor_cache = {}

        # Cache for frequently computed distances - NEW
        self._distance_cache = {}
        self._cache_max_size = 10000  # Limit cache size

        if obstacles:
            for x, y in obstacles:
                if self.is_valid_position(x, y):
                    self.grid[y][x] = False
                    
        # Build neighbor cache AFTER obstacles are set - NEW
        self._build_neighbor_cache()

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

    def is_valid_position(self, x: int, y: int) -> bool:
        return 0 <= x < self.width and 0 <= y < self.height

    def is_walkable(self, x: int, y: int) -> bool:
        return self.is_valid_position(x, y) and self.grid[y][x]

    def get_neighbors(self, x: int, y: int) -> List[Tuple[int, int]]:
        """
        O(1) neighbor lookup using pre-computed cache.
        
        Returns:
            List of valid neighboring positions (max 4 for grid movement)
        """
        return self._neighbor_cache.get((x, y), [])

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

    def clear_distance_cache(self):
        """Clear distance cache. Call if grid changes significantly."""
        self._distance_cache.clear()

    def manhattan_distance(self, pos1: Tuple[int, int], pos2: Tuple[int, int]) -> int:
        return self.get_manhattan_distance(pos1, pos2)
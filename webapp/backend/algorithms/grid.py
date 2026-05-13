from typing import List, Tuple, Set


class GridEnvironment:
    """Represents the grid map"""

    def __init__(self, height: int, width: int, obstacles: List[Tuple[int, int]] = None):
        self.height = height
        self.width = width
        self.grid = [[True for _ in range(width)] for _ in range(height)]

        if obstacles:
            for x, y in obstacles:
                if self.is_valid_position(x, y):
                    self.grid[y][x] = False

    def is_valid_position(self, x: int, y: int) -> bool:
        return 0 <= x < self.width and 0 <= y < self.height

    def is_walkable(self, x: int, y: int) -> bool:
        return self.is_valid_position(x, y) and self.grid[y][x]

    def get_neighbors(self, x: int, y: int) -> List[Tuple[int, int]]:
        directions = [(0, 1), (1, 0), (0, -1), (-1, 0)]
        neighbors = []

        for dx, dy in directions:
            nx, ny = x + dx, y + dy
            if self.is_walkable(nx, ny):
                neighbors.append((nx, ny))

        return neighbors

    def get_manhattan_distance(self, pos1: Tuple[int, int], pos2: Tuple[int, int]) -> int:
        return abs(pos1[0] - pos2[0]) + abs(pos1[1] - pos2[1])

    def manhattan_distance(self, pos1: Tuple[int, int], pos2: Tuple[int, int]) -> int:
        return self.get_manhattan_distance(pos1, pos2)
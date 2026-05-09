from typing import Tuple, Optional


class Node:
    """Represents a node in the search tree"""

    def __init__(self, position: Tuple[int, int], parent: Optional["Node"] = None, g: float = 0, h: float = 0):
        self.position = position
        self.parent = parent
        self.g = g
        self.h = h
        self.f = g + h

    def __lt__(self, other: "Node") -> bool:
        return self.f < other.f

    def __eq__(self, other: "Node") -> bool:
        return self.position == other.position

    def __hash__(self) -> int:
        return hash(self.position)

    def reconstruct_path(self) -> list:
        path = []
        current = self
        while current is not None:
            path.append(current.position)
            current = current.parent
        return list(reversed(path))
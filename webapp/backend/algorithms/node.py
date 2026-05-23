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
        self.pool: List['Node'] = []
        self.index = 0
        self.size = initial_size
        self._initialized = False
    
    def acquire(self, position: Tuple[int, int], parent: Optional['Node'] = None, 
                g: float = 0, h: float = 0) -> 'Node':
        """
        Get a node from the pool, expanding if necessary.
        """
        if not self._initialized:
            self.pool = [Node((0, 0)) for _ in range(self.size)]
            self._initialized = True

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
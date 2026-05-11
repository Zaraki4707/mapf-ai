import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from fastapi import APIRouter
from pydantic import BaseModel
from typing import List, Optional
from pathlib import Path

router = APIRouter()

# Get the base directory relative to this file
# In Vercel, the files are copied into the function directory
BASE_DIR = Path(__file__).resolve().parents[2] 
MAPS_DIR = BASE_DIR / "maps"


class MapInfo(BaseModel):
    name: str
    path: str
    source: str


@router.get("/maps", response_model=List[MapInfo])
async def get_maps():
    """Get list of available maps"""
    # Hardcoded list of maps that we KNOW exist in the project
    hardcoded_map_names = [
        "file", "grid", "large", "maze-128-128-2", "maze-32-32-2", 
        "medium", "small", "very-large", "very-small"
    ]
    
    maps = []
    
    # Try multiple filesystem locations
    search_paths = [
        Path(__file__).parent.parent / "maps",
        Path("app/maps"),
        Path("maps"),
    ]

    seen_files = set()
    for directory in search_paths:
        try:
            if directory.exists():
                for f in directory.iterdir():
                    if f.suffix == ".txt" and f.name not in seen_files:
                        maps.append(MapInfo(
                            name=f.stem, 
                            path=str(f.absolute()), 
                            source="filesystem"
                        ))
                        seen_files.add(f.name)
        except:
            pass
            
    # Always include the hardcoded ones if they weren't found via filesystem
    for m in hardcoded_map_names:
        if m not in seen_files:
            # We use a path that we know was bundled
            maps.append(MapInfo(
                name=m,
                path=f"app/maps/{m}.txt",
                source="hardcoded"
            ))

    return maps


@router.get("/maps/{map_path:path}")
async def load_map(map_path: str):
    """Load a specific map and return grid info"""
    full_path = Path(map_path)

    if not full_path.exists():
        return {"error": "Map not found"}

    grid = []
    obstacles = []
    width = 0

    with open(full_path, 'r') as f:
        for y, line in enumerate(f):
            row = []
            for x, char in enumerate(line.strip()):
                if char == '.':
                    row.append(True)
                elif char == 'T':
                    row.append(False)
                    obstacles.append([x, y])
            width = max(width, len(row))
            grid.append(row)

    height = len(grid)

    return {
        "name": full_path.stem,
        "path": str(full_path),
        "height": height,
        "width": width,
        "obstacles": obstacles,
        "total_cells": height * width,
        "obstacle_count": len(obstacles),
        "walkable_count": (height * width) - len(obstacles)
    }
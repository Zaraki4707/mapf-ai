import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from fastapi import APIRouter
from pydantic import BaseModel
from typing import List, Optional
from pathlib import Path

router = APIRouter()

MAPS_DIR = Path("E:/Intro_to_ai_Project/maps")
WIDJDANE_DIR = Path("E:/Intro_to_ai_Project/widjdane_chouali")


class MapInfo(BaseModel):
    name: str
    path: str
    source: str


@router.get("/maps", response_model=List[MapInfo])
async def get_maps():
    """Get list of available maps"""
    maps = []

    if MAPS_DIR.exists():
        for f in MAPS_DIR.glob("*.txt"):
            maps.append(MapInfo(name=f.stem, path=str(f), source="maps"))

    if WIDJDANE_DIR.exists():
        for f in WIDJDANE_DIR.glob("*.txt"):
            if f.stem != "file":
                maps.append(MapInfo(name=f.stem, path=str(f), source="widjdane_chouali"))

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
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


@router.get("/maps", response_model=List[dict])
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
        Path("webapp/backend/app/maps"),
        Path("app/maps"),
        Path("maps"),
    ]

    seen_files = set()
    for directory in search_paths:
        try:
            if directory.exists():
                for f in directory.iterdir():
                    if f.suffix == ".txt" and f.name not in seen_files:
                        maps.append({
                            "id": str(f.absolute()), 
                            "name": f.stem, 
                            "path": str(f.absolute()), 
                            "source": "filesystem",
                            "category": "Standard Maps"
                        })
                        seen_files.add(f.name)
        except:
            pass
            
    # Always include the hardcoded ones if they weren't found via filesystem
    for m in hardcoded_map_names:
        if m not in seen_files:
            maps.append({
                "id": m,
                "name": m,
                "path": f"app/maps/{m}.txt",
                "source": "hardcoded",
                "category": "Standard Maps"
            })

    return maps


@router.get("/get_map_details/{map_path:path}")
async def load_map(map_path: str):
    """Load a specific map and return grid info"""
    print(f"DEBUG: Loading map details for: {map_path}")
    # Fix for path resolution in different environments
    current_dir = Path(__file__).parent.parent.resolve() # webapp/backend/app
    
    # Try different possible paths for the map
    # We want to check:
    # 1. Absolute path (if map_path is absolute)
    # 2. Inside the current app directory / maps/
    # 3. Inside the local webapp directory
    # 4. Just the filename inside the maps folder
    
    clean_path = map_path.replace("\\", "/") # normalize
    filename = Path(clean_path).name
    if not filename.endswith('.txt'):
        filename += '.txt'

    possible_paths = [
        Path(clean_path),
        current_dir / "maps" / filename,
        Path("webapp/backend/app/maps") / filename,
        Path("app/maps") / filename,
        BASE_DIR / "maps" / filename
    ]

    full_path = None
    for p in possible_paths:
        try:
            print(f"DEBUG: Checking path: {p}")
            if p.exists() and p.is_file():
                full_path = p
                print(f"DEBUG: Found map at: {p}")
                break
        except Exception as e:
            print(f"DEBUG: Error checking {p}: {e}")
            continue

    if not full_path:
        return {
            "error": f"Map not found: {map_path}",
            "tried_paths": [str(p) for p in possible_paths],
            "current_working_dir": os.getcwd()
        }

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
        "id": map_path,
        "name": full_path.stem,
        "path": str(full_path),
        "height": height,
        "width": width,
        "obstacles": obstacles
    }

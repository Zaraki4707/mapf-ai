import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.core import settings
from app.routers import pathfinder
from app.routers import maps

app = FastAPI(
    title=settings.app_name,
    debug=True
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    print(f"Exception: {exc}")
    return JSONResponse(
        status_code=500,
        content={"detail": str(exc)}
    )


@app.get("/maps")
async def get_test_maps():
    return [
        {"name": "file", "path": "app/maps/file.txt", "source": "filesystem"},
        {"name": "grid", "path": "app/maps/grid.txt", "source": "filesystem"},
        {"name": "large", "path": "app/maps/large.txt", "source": "filesystem"},
        {"name": "maze-128-128-2", "path": "app/maps/maze-128-128-2.txt", "source": "filesystem"},
        {"name": "maze-32-32-2", "path": "app/maps/maze-32-32-2.txt", "source": "filesystem"},
        {"name": "medium", "path": "app/maps/medium.txt", "source": "filesystem"},
        {"name": "small", "path": "app/maps/small.txt", "source": "filesystem"},
        {"name": "very-large", "path": "app/maps/very-large.txt", "source": "filesystem"},
        {"name": "very-small", "path": "app/maps/very-small.txt", "source": "filesystem"}
    ]

app.include_router(pathfinder.router, prefix="", tags=["pathfinding"])
app.include_router(maps.router, tags=["maps"])


@app.get("/")
async def root():
    return {"message": "Multi-Agent Path Finding API", "status": "running"}


@app.get("/health")
async def health():
    return {"status": "healthy"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
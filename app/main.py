from fastapi import FastAPI
from app.api import admin, data, board
from app.db.database import init_db
from contextlib import asynccontextmanager

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Initialize database on startup
    await init_db()
    yield

app = FastAPI(
    title="DataMine-Hub",
    description="An agent-first collaboration platform for data mining.",
    version="1.0.0",
    lifespan=lifespan
)

# Include routers
app.include_router(admin.router)
app.include_router(data.router)
app.include_router(board.router)

@app.get("/")
async def root():
    return {"message": "Welcome to DataMine-Hub API"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)

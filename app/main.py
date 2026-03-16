from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse
from app.api import admin, data, board
from app.db.database import init_db
from app.core.ui import DASHBOARD_HTML
from app.core.websockets import manager
from contextlib import asynccontextmanager

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Initialize database on startup
    await init_db()
    yield

app = FastAPI(
    title="datamine-hub",
    description="An agent-first collaboration platform for data mining.",
    version="1.0.0",
    lifespan=lifespan
)

# Include routers
app.include_router(admin.router)
app.include_router(data.router)
app.include_router(board.router)

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while True:
            # Keep connection alive
            await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(websocket)

@app.get("/", response_class=HTMLResponse)
async def root():
    return DASHBOARD_HTML

@app.get("/hi")
async def hi():
    return {"message": "hi there citizenfour!"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)

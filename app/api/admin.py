from fastapi import APIRouter, Depends, HTTPException, status
import uuid
import secrets
import aiosqlite
from app.db.database import get_db
from app.core.security import verify_admin_key
from app.models.schemas import AgentCreateResponse

router = APIRouter(prefix="/api/admin", tags=["admin"])

@router.post("/agents", response_model=AgentCreateResponse, dependencies=[Depends(verify_admin_key)])
async def create_agent(db: aiosqlite.Connection = Depends(get_db)):
    agent_id = str(uuid.uuid4())
    api_key = secrets.token_urlsafe(32)
    
    try:
        await db.execute(
            "INSERT INTO agents (id, api_key) VALUES (?, ?)",
            (agent_id, api_key)
        )
        await db.commit()
        
        async with db.execute("SELECT id, api_key, created_at FROM agents WHERE id = ?", (agent_id,)) as cursor:
            row = await cursor.fetchone()
            return dict(row)
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

from fastapi import APIRouter, Depends, HTTPException, status
import aiosqlite
from typing import List
from app.db.database import get_db
from app.core.security import get_current_agent
from app.models.schemas import PostCreate, PostResponse

router = APIRouter(prefix="/api/channels", tags=["board"])

@router.get("/{name}/posts", response_model=List[PostResponse])
async def get_posts(
    name: str,
    db: aiosqlite.Connection = Depends(get_db)
):
    async with db.execute(
        "SELECT * FROM posts WHERE channel_name = ? ORDER BY created_at DESC", 
        (name,)
    ) as cursor:
        rows = await cursor.fetchall()
        return [dict(row) for row in rows]

@router.post("/{name}/posts", response_model=PostResponse)
async def create_post(
    name: str,
    post: PostCreate,
    agent_id: str = Depends(get_current_agent),
    db: aiosqlite.Connection = Depends(get_db)
):
    try:
        # Auto-create channel if it doesn't exist
        await db.execute(
            "INSERT OR IGNORE INTO channels (name) VALUES (?)",
            (name,)
        )
        
        # Insert post
        cursor = await db.execute(
            "INSERT INTO posts (channel_name, agent_id, content) VALUES (?, ?, ?)",
            (name, agent_id, post.content)
        )
        post_id = cursor.lastrowid
        await db.commit()
        
        async with db.execute("SELECT * FROM posts WHERE id = ?", (post_id,)) as cursor:
            row = await cursor.fetchone()
            return dict(row)
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

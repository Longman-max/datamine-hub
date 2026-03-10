from fastapi import Depends, HTTPException, Security, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from app.db.database import get_db
import aiosqlite

security = HTTPBearer()

async def get_current_agent(
    credentials: HTTPAuthorizationCredentials = Security(security),
    db: aiosqlite.Connection = Depends(get_db)
) -> str:
    api_key = credentials.credentials
    
    async with db.execute(
        "SELECT id FROM agents WHERE api_key = ?", (api_key,)
    ) as cursor:
        row = await cursor.fetchone()
        if row is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid API Key",
                headers={"WWW-Authenticate": "Bearer"},
            )
        return row["id"]

async def verify_admin_key(
    credentials: HTTPAuthorizationCredentials = Security(security)
):
    from app.core.config import ADMIN_KEY
    if credentials.credentials != ADMIN_KEY:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Invalid Admin Key",
        )

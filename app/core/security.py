from fastapi import Depends, HTTPException, Security, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import logging
import aiosqlite
from app.db.database import get_db

logger = logging.getLogger(__name__)

security = HTTPBearer()


async def get_current_agent(
    credentials: HTTPAuthorizationCredentials = Security(security),
    db: aiosqlite.Connection = Depends(get_db),
) -> str:
    api_key = credentials.credentials

    async with db.execute(
        "SELECT id FROM agents WHERE api_key = ?", (api_key,)
    ) as cursor:
        row = await cursor.fetchone()
        if row is None:
            logger.warning(
                f"Unauthorized access attempt with API Key: {api_key[:5]}..."
            )  # Log first 5 chars for security
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid API Key",
                headers={"WWW-Authenticate": "Bearer"},
            )
        return row["id"]


async def verify_admin_key(
    credentials: HTTPAuthorizationCredentials = Security(security),
):
    from app.core.config import ADMIN_KEY

    if credentials.credentials != ADMIN_KEY:
        logger.warning("Unauthorized admin access attempt.")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Invalid Admin Key",
        )

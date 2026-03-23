from fastapi import APIRouter, Depends, HTTPException, status
import uuid
import secrets
import aiosqlite
import subprocess
import os
import sys
import logging
from app.db.database import get_db
from app.models.schemas import JobSpawnRequest

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/jobs", tags=["jobs"])


@router.post("/spawn")
async def spawn_job(payload: JobSpawnRequest, db: aiosqlite.Connection = Depends(get_db)):
    """
    Spawns a new autonomous agent in the background.
    Automatically handles agent registration.
    """
    agent_id = str(uuid.uuid4())
    api_key = secrets.token_urlsafe(32)

    try:
        # 1. Register agent in DB
        await db.execute(
            "INSERT INTO agents (id, api_key) VALUES (?, ?)", (agent_id, api_key)
        )
        await db.commit()

        # 2. Prepare environment and spawn subprocess
        env = os.environ.copy()
        env["AGENT_API_KEY"] = api_key

        # Run agent_runner.py with the same interpreter as current process
        # Using Popen ensures it's non-blocking for the FastAPI event loop
        process = subprocess.Popen(
            [
                sys.executable,
                "agent_runner.py",
                "--role",
                payload.role,
                "--url",
                payload.target_url,
            ],
            env=env,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )

        logger.info(
            f"[DISPATCHER] Spawned {payload.role} agent (PID: {process.pid}) for target: {payload.target_url}"
        )

        return {
            "status": "spawned",
            "agent_id": agent_id,
            "pid": process.pid,
            "role": payload.role,
            "target_url": payload.target_url,
        }
    except Exception as e:
        logger.error(f"[DISPATCHER] Error spawning agent: {e}")
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e)
        )

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, status
from fastapi.responses import FileResponse
import hashlib
import json
import os
import aiosqlite
from typing import Optional
from pathlib import Path
from app.db.database import get_db
from app.core.security import get_current_agent
from app.core.config import STORAGE_DIR
from app.models.schemas import DataNodeResponse, LineageResponse

from app.core.websockets import manager

router = APIRouter(prefix="/api/data", tags=["data"])


@router.get("/graph")
async def get_data_graph(db: aiosqlite.Connection = Depends(get_db)):
    nodes = []
    async with db.execute("SELECT hash, metrics FROM data_nodes") as cursor:
        async for row in cursor:
            nodes.append(
                {
                    "id": row["hash"],
                    "label": f"{row['hash'][:8]}...",
                    "title": f"Metrics: {row['metrics']}",
                }
            )

    edges = []
    async with db.execute("SELECT parent_hash, child_hash FROM node_edges") as cursor:
        async for row in cursor:
            edges.append({"from": row["parent_hash"], "to": row["child_hash"]})

    return {"nodes": nodes, "edges": edges}


@router.get("/fetch/{hash}")
async def fetch_data(hash: str, db: aiosqlite.Connection = Depends(get_db)):
    async with db.execute(
        "SELECT storage_path FROM data_nodes WHERE hash = ?", (hash,)
    ) as cursor:
        row = await cursor.fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="Data node not found")

        storage_path = row["storage_path"]
        if not os.path.exists(storage_path):
            raise HTTPException(status_code=404, detail="File not found on disk")

        return FileResponse(storage_path, filename=f"{hash}.csv")


@router.post("/push", response_model=DataNodeResponse)
async def push_data(
    file: UploadFile = File(...),
    metrics: Optional[str] = Form(None),
    parent_hashes: Optional[str] = Form("[]"),
    agent_id: str = Depends(get_current_agent),
    db: aiosqlite.Connection = Depends(get_db),
):
    try:
        parents = json.loads(parent_hashes)
        if not isinstance(parents, list):
            parents = []
    except json.JSONDecodeError:
        parents = []

    content = await file.read()
    file_hash = hashlib.sha256(content).hexdigest()

    async with db.execute(
        "SELECT hash FROM data_nodes WHERE hash = ?", (file_hash,)
    ) as cursor:
        if not await cursor.fetchone():
            ext = Path(file.filename).suffix
            storage_path = str(STORAGE_DIR / f"{file_hash}{ext}")

            with open(storage_path, "wb") as f:
                f.write(content)

            for parent in parents:
                async with db.execute(
                    "SELECT hash FROM data_nodes WHERE hash = ?", (parent,)
                ) as cursor:
                    if not await cursor.fetchone():
                        raise HTTPException(
                            status_code=status.HTTP_400_BAD_REQUEST,
                            detail=f"Parent hash {parent} does not exist",
                        )

            try:
                await db.execute(
                    "INSERT INTO data_nodes (hash, agent_id, storage_path, metrics) VALUES (?, ?, ?, ?)",
                    (file_hash, agent_id, storage_path, metrics),
                )
                for parent in parents:
                    await db.execute(
                        "INSERT OR IGNORE INTO node_edges (parent_hash, child_hash) VALUES (?, ?)",
                        (parent, file_hash),
                    )
                await db.commit()

                # Broadcast new dataset
                await manager.broadcast(
                    {
                        "type": "new_dataset",
                        "data": {
                            "hash": file_hash,
                            "agent_id": agent_id,
                            "metrics": metrics,
                            "created_at": "just now",  # Simplifying for broadcast
                        },
                    }
                )
            except Exception as e:
                await db.rollback()
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e)
                )

    async with db.execute(
        "SELECT * FROM data_nodes WHERE hash = ?", (file_hash,)
    ) as cursor:
        row = await cursor.fetchone()
        data = dict(row)
        if data["metrics"]:
            try:
                data["metrics"] = json.loads(data["metrics"])
            except json.JSONDecodeError:
                pass
        return data


@router.get("/lineage/{hash}", response_model=LineageResponse)
async def get_lineage(hash: str, db: aiosqlite.Connection = Depends(get_db)):
    async with db.execute(
        "SELECT hash FROM data_nodes WHERE hash = ?", (hash,)
    ) as cursor:
        if not await cursor.fetchone():
            raise HTTPException(status_code=404, detail="Data node not found")

    query = """
    WITH RECURSIVE ancestry(parent, child) AS (
        SELECT parent_hash, child_hash FROM node_edges WHERE child_hash = ?
        UNION
        SELECT ne.parent_hash, ne.child_hash FROM node_edges ne
        JOIN ancestry ON ne.child_hash = ancestry.parent
    )
    SELECT * FROM ancestry;
    """

    edges = []
    ancestor_hashes = {hash}
    async with db.execute(query, (hash,)) as cursor:
        async for row in cursor:
            edges.append({"parent": row["parent"], "child": row["child"]})
            ancestor_hashes.add(row["parent"])

    nodes = []
    placeholders = ",".join(["?"] * len(ancestor_hashes))
    async with db.execute(
        f"SELECT * FROM data_nodes WHERE hash IN ({placeholders})",
        list(ancestor_hashes),
    ) as cursor:
        async for row in cursor:
            data = dict(row)
            if data["metrics"]:
                try:
                    data["metrics"] = json.loads(data["metrics"])
                except:
                    pass
            nodes.append(data)

    return {"nodes": nodes, "edges": edges}


@router.get("/recent")
async def get_recent_data(db: aiosqlite.Connection = Depends(get_db)):
    async with db.execute(
        "SELECT hash, agent_id, metrics, created_at FROM data_nodes ORDER BY created_at DESC LIMIT 10"
    ) as cursor:
        rows = await cursor.fetchall()
        result = []
        for row in rows:
            data = dict(row)
            if data["metrics"]:
                try:
                    data["metrics"] = json.loads(data["metrics"])
                except:
                    pass
            result.append(data)
        return result

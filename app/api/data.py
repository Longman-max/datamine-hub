from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, status
import hashlib
import json
import os
import aiosqlite
from typing import List, Optional
from pathlib import Path
from app.db.database import get_db
from app.core.security import get_current_agent
from app.core.config import STORAGE_DIR
from app.models.schemas import DataNodeResponse, LineageResponse

router = APIRouter(prefix="/api/data", tags=["data"])

@router.post("/push", response_model=DataNodeResponse)
async def push_data(
    file: UploadFile = File(...),
    metrics: Optional[str] = Form(None),
    parent_hashes: Optional[str] = Form("[]"),
    agent_id: str = Depends(get_current_agent),
    db: aiosqlite.Connection = Depends(get_db)
):
    # Parse parent_hashes from JSON string
    try:
        parents = json.loads(parent_hashes)
        if not isinstance(parents, list):
            parents = []
    except:
        parents = []

    # Read file and calculate SHA-256
    content = await file.read()
    file_hash = hashlib.sha256(content).hexdigest()
    
    # Check if already exists
    async with db.execute("SELECT hash FROM data_nodes WHERE hash = ?", (file_hash,)) as cursor:
        if await cursor.fetchone():
            # If exists, we still return it but don't re-save.
            # However, instructions say "Insert into data_nodes"
            # In a real app we might update metrics or just return 409/200.
            # I'll just skip saving and return existing to be idempotent-ish.
            pass
        else:
            # Save file
            ext = Path(file.filename).suffix
            storage_path = str(STORAGE_DIR / f"{file_hash}{ext}")
            
            with open(storage_path, "wb") as f:
                f.write(content)
            
            # Verify parents exist
            for parent in parents:
                async with db.execute("SELECT hash FROM data_nodes WHERE hash = ?", (parent,)) as cursor:
                    if not await cursor.fetchone():
                        raise HTTPException(
                            status_code=status.HTTP_400_BAD_REQUEST,
                            detail=f"Parent hash {parent} does not exist"
                        )
            
            try:
                # Insert data_node
                await db.execute(
                    "INSERT INTO data_nodes (hash, agent_id, storage_path, metrics) VALUES (?, ?, ?, ?)",
                    (file_hash, agent_id, storage_path, metrics)
                )
                
                # Insert edges
                for parent in parents:
                    await db.execute(
                        "INSERT OR IGNORE INTO node_edges (parent_hash, child_hash) VALUES (?, ?)",
                        (parent, file_hash)
                    )
                
                await db.commit()
            except Exception as e:
                await db.rollback()
                raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

    async with db.execute("SELECT * FROM data_nodes WHERE hash = ?", (file_hash,)) as cursor:
        row = await cursor.fetchone()
        data = dict(row)
        if data["metrics"]:
            data["metrics"] = json.loads(data["metrics"])
        return data

@router.get("/lineage/{hash}", response_model=LineageResponse)
async def get_lineage(hash: str, db: aiosqlite.Connection = Depends(get_db)):
    # Check if node exists
    async with db.execute("SELECT hash FROM data_nodes WHERE hash = ?", (hash,)) as cursor:
        if not await cursor.fetchone():
            raise HTTPException(status_code=404, detail="Data node not found")

    # Recursive CTE for ancestry
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
    
    # Fetch all nodes in the ancestry
    nodes = []
    placeholders = ",".join(["?"] * len(ancestor_hashes))
    async with db.execute(f"SELECT * FROM data_nodes WHERE hash IN ({placeholders})", list(ancestor_hashes)) as cursor:
        async for row in cursor:
            data = dict(row)
            if data["metrics"]:
                try:
                    data["metrics"] = json.loads(data["metrics"])
                except:
                    pass
            nodes.append(data)
            
    return {"nodes": nodes, "edges": edges}

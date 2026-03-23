import aiosqlite

from pathlib import Path

DB_PATH = Path("data/datamine.db")
SCHEMA_PATH = Path("app/db/schema.sql")


async def get_db():
    db = await aiosqlite.connect(DB_PATH)
    db.row_factory = aiosqlite.Row
    try:
        yield db
    finally:
        await db.close()


async def init_db():
    if not DB_PATH.parent.exists():
        DB_PATH.parent.mkdir(parents=True)

    try:
        async with aiosqlite.connect(DB_PATH) as db:
            with open(SCHEMA_PATH, "r") as f:
                schema = f.read()
            await db.executescript(schema)
            await db.commit()
    except FileNotFoundError:
        print(f"Error: Schema file not found at {SCHEMA_PATH}")
        raise
    except Exception as e:
        print(f"Error initializing database: {e}")
        raise

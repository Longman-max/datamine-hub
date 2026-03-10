import os
from dotenv import load_dotenv
from pathlib import Path

load_dotenv()

ADMIN_KEY = os.getenv("ADMIN_KEY", "super-secret-admin-key")
STORAGE_DIR = Path(os.getenv("STORAGE_DIR", "data/storage"))

if not STORAGE_DIR.exists():
    STORAGE_DIR.mkdir(parents=True)

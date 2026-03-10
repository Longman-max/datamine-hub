import os
from dotenv import load_dotenv, find_dotenv
from pathlib import Path

load_dotenv(find_dotenv(), override=True)

ADMIN_KEY = os.getenv("ADMIN_KEY", "super-secret-admin-key")
STORAGE_DIR = Path(os.getenv("STORAGE_DIR", "data/storage"))

if not STORAGE_DIR.exists():
    STORAGE_DIR.mkdir(parents=True)

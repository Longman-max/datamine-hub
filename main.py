import uvicorn
import os
from dotenv import load_dotenv

load_dotenv()

def main():
    """Entry point for the Datamine Hub server."""
    port = int(os.getenv("PORT", 8000))
    host = os.getenv("HOST", "0.0.0.0")
    
    print(f"--- Starting Datamine Hub on {host}:{port} ---")
    uvicorn.run("app.main:app", host=host, port=port, reload=True)

if __name__ == "__main__":
    main()

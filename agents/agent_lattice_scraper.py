import os
import requests
import pandas as pd
import json
from dotenv import load_dotenv

# 1. Setup & Authentication
load_dotenv()

HUB_URL = os.getenv("HUB_URL", "http://localhost:8000")
AGENT_API_KEY = os.getenv("AGENT_API_KEY")

if not AGENT_API_KEY:
    print("Error: AGENT_API_KEY not found in environment variables.")
    exit(1)

headers = {
    "Authorization": f"Bearer {AGENT_API_KEY}"
}

def run_lattice_scraper():
    """
    Simulates the Lattice-F scraper logic for university student data.
    Generates a sample student_admissions.csv file.
    """
    print("--- Lattice-F Scraper Starting ---")
    print("Harvesting student data from FUTO portal...")
    
    data = [
        {"student_id": "FUTO/2026/001", "name": "Alice Johnson", "department": "Computer Science", "admission_score": 320},
        {"student_id": "FUTO/2026/002", "name": "Bob Smith", "department": "Mechanical Engineering", "admission_score": 290},
        {"student_id": "FUTO/2026/003", "name": "Charlie Davis", "department": "Physics", "admission_score": 285},
        {"student_id": "FUTO/2026/004", "name": "Diana Prince", "department": "Civil Engineering", "admission_score": 310},
        {"student_id": "FUTO/2026/005", "name": "Ethan Hunt", "department": "Cybersecurity", "admission_score": 305}
    ]
    
    df = pd.DataFrame(data)
    
    # Ensure tmp directory exists
    tmp_dir = os.path.join("data", "tmp")
    os.makedirs(tmp_dir, exist_ok=True)
    filename = os.path.join(tmp_dir, "student_admissions.csv")
    
    df.to_csv(filename, index=False)
    
    print(f"Scrape complete. Generated {filename} with {len(df)} records.")
    return filename

def push_to_hub(file_path):
    """
    Pushes the scraped data to the DataMine-Hub as a root node (no parents).
    """
    print(f"Pushing {file_path} to Hub at {HUB_URL}...")
    
    metrics = {
        "rows_scraped": 5,
        "source": "FUTO_portal",
        "agent": "Lattice-F"
    }
    
    try:
        with open(file_path, "rb") as f:
            files = {"file": (file_path, f, "text/csv")}
            data = {
                "metrics": json.dumps(metrics),
                "parent_hashes": json.dumps([])  # Root node: no parents
            }
            
            response = requests.post(f"{HUB_URL}/api/data/push", headers=headers, files=files, data=data)
            response.raise_for_status()
            
            result = response.json()
            data_hash = result["hash"]
            print(f"Data push successful. Hash: {data_hash}")
            return data_hash
            
    except requests.exceptions.RequestException as e:
        print(f"Network error during push: {e}")
        return None

def broadcast_to_board(data_hash):
    """
    Broadcasts the scrape completion and data hash to the #scraping-ops channel.
    """
    if not data_hash:
        return
        
    print(f"Broadcasting results to #scraping-ops...")
    
    payload = {
        "content": f"Lattice-F scrape complete. 5 student records harvested. Root data hash: {data_hash}"
    }
    
    try:
        response = requests.post(
            f"{HUB_URL}/api/channels/scraping-ops/posts",
            headers=headers,
            json=payload
        )
        response.raise_for_status()
        print("Broadcast successful.")
        
    except requests.exceptions.RequestException as e:
        print(f"Network error during broadcast: {e}")

if __name__ == "__main__":
    # Execute the agent cycle
    scraped_file = run_lattice_scraper()
    root_hash = push_to_hub(scraped_file)
    broadcast_to_board(root_hash)
    
    # Optional cleanup
    if os.path.exists(scraped_file):
        os.remove(scraped_file)
        
    print("--- Agent Lattice Scraper Finished ---")

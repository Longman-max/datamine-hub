import os
import requests
import pandas as pd
import json
import re
from dotenv import load_dotenv
from pathlib import Path

# 1. Setup & Auth
load_dotenv()

HUB_URL = os.getenv("HUB_URL", "http://localhost:8000")
AGENT_API_KEY = os.getenv("AGENT_API_KEY")

if not AGENT_API_KEY:
    print("Error: AGENT_API_KEY not found in environment variables.")
    exit(1)

headers = {
    "Authorization": f"Bearer {AGENT_API_KEY}"
}

def agent_refiner():
    try:
        print(f"--- Agent Refiner Starting (Hub: {HUB_URL}) ---")

        # 2. Fetching Context (The Message Board)
        print(f"Fetching context from #scraping-ops...")
        response = requests.get(f"{HUB_URL}/api/channels/scraping-ops/posts", headers=headers)
        response.raise_for_status()
        posts = response.json()

        if not posts:
            print("No posts found in #scraping-ops. Nothing to refine.")
            return

        # Parse latest message for hash
        latest_post = posts[0]
        content = latest_post["content"]
        print(f"Latest post: {content}")

        # Regex to find "Data hash: <hash>"
        match = re.search(r"Data hash:\s*([a-fA-F0-9]{64})", content)
        if not match:
            print("Could not find a valid data hash in the latest post.")
            return

        original_hash = match.group(1)
        print(f"Extracted original hash: {original_hash}")

        # 3. Downloading the Data
        print(f"Downloading dataset {original_hash}...")
        fetch_url = f"{HUB_URL}/api/data/fetch/{original_hash}"
        data_response = requests.get(fetch_url, headers=headers)
        data_response.raise_for_status()

        # Save temporarily to load into pandas
        temp_file = "temp_raw_data.csv"
        with open(temp_file, "wb") as f:
            f.write(data_response.content)

        # 4. Processing (The Transformation)
        print("Loading and cleaning data...")
        df = pd.read_csv(temp_file)
        
        initial_rows = len(df)
        # Cleaning: drop missing, lowercase columns, add metadata
        df = df.dropna()
        df.columns = [c.lower() for c in df.columns]
        df["processed_by"] = "agent_refiner"
        
        final_rows = len(df)
        rows_removed = initial_rows - final_rows
        
        cleaned_file = "cleaned_dataset.csv"
        df.to_csv(cleaned_file, index=False)
        print(f"Cleaned data saved. Removed {rows_removed} rows.")

        # 5. Pushing Data & Building the DAG
        print("Pushing refined data to Hub...")
        metrics = {
            "initial_rows": initial_rows,
            "final_rows": final_rows,
            "rows_removed": rows_removed
        }
        
        with open(cleaned_file, "rb") as f:
            files = {"file": (cleaned_file, f, "text/csv")}
            data = {
                "metrics": json.dumps(metrics),
                "parent_hashes": json.dumps([original_hash])
            }
            push_response = requests.post(f"{HUB_URL}/api/data/push", headers=headers, files=files, data=data)
            push_response.raise_for_status()

        new_node = push_response.json()
        new_hash = new_node["hash"]
        print(f"Refined data pushed successfully. New hash: {new_hash}")

        # 6. Broadcasting Results
        print("Broadcasting results to #cleaning-ops...")
        broadcast_msg = {
            "content": f"Cleaning complete. Removed {rows_removed} invalid rows. New refined data hash: {new_hash}"
        }
        broadcast_response = requests.post(
            f"{HUB_URL}/api/channels/cleaning-ops/posts", 
            headers=headers, 
            json=broadcast_msg
        )
        broadcast_response.raise_for_status()
        
        print("Done! Agent Refiner cycle complete.")

        # Cleanup local files
        if os.path.exists(temp_file): os.remove(temp_file)
        if os.path.exists(cleaned_file): os.remove(cleaned_file)

    except requests.exceptions.RequestException as e:
        print(f"Network error: {e}")
    except Exception as e:
        print(f"An error occurred: {e}")

if __name__ == "__main__":
    agent_refiner()

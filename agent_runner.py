import argparse
import os
import sys
import time
import json
import re
import io
import pandas as pd
from agents.agent_base import LatticeScraperAgent, AutonomousAgent
from agents.agent_miner import ExtractionMinerAgent


class CleanerAgent(AutonomousAgent):
    """Refines and cleans raw datasets."""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.source_channel = "scraping-ops"
        self.output_channel = "cleaning-ops"

    def execute_task(self):
        print(f"--- [CLEANER] Cycle Started (Polling #{self.source_channel}) ---")

        # 1. Poll for new posts
        posts = self.api_get(f"/api/channels/{self.source_channel}/posts")
        if not posts:
            return

        last_id = self.state.get("last_processed_post_id", 0)
        new_posts = [p for p in posts if p["id"] > last_id]
        if not new_posts:
            return

        # Process the latest one
        latest_post = sorted(new_posts, key=lambda x: x["id"])[-1]
        content = latest_post["content"]
        post_id = latest_post["id"]

        # Regex to find hash
        match = re.search(r"hash:\s*([a-fA-F0-9]{64})", content)
        if not match:
            self.state["last_processed_post_id"] = post_id
            self.save_state()
            return

        original_hash = match.group(1)
        print(f"[CLEANER] Processing dataset: {original_hash}")

        # 2. Download Data
        fetch_url = f"{self.hub_url}/api/data/fetch/{original_hash}"
        headers = {"Authorization": f"Bearer {self.api_key}"}
        import requests

        try:
            response = requests.get(fetch_url, headers=headers, timeout=10)
            response.raise_for_status()

            # Save temporarily
            tmp_dir = os.path.join("data", "tmp")
            os.makedirs(tmp_dir, exist_ok=True)
            temp_raw = os.path.join(tmp_dir, f"raw_{original_hash[:8]}.csv")
            with open(temp_raw, "wb") as f:
                f.write(response.content)

            # 3. Clean with Pandas
            df = pd.read_csv(temp_raw)
            initial_rows = len(df)
            df = df.dropna()
            df.columns = [c.lower() for c in df.columns]
            df["processed_by"] = "cleaner_unit"
            
            cleaned_file = os.path.join(tmp_dir, f"clean_{original_hash[:8]}.csv")
            df.to_csv(cleaned_file, index=False)
            
            # 4. Push Refined Data
            metrics = {
                "initial_rows": initial_rows,
                "final_rows": len(df),
                "removed": initial_rows - len(df)
            }
            payload = {
                "metrics": json.dumps(metrics),
                "parent_hashes": json.dumps([original_hash])
            }
            
            result = self.api_post_file("/api/data/push", cleaned_file, data=payload)
            
            if result and "hash" in result:
                new_hash = result["hash"]
                # 5. Broadcast
                msg = f"Cleaned dataset. Removed {metrics['removed']} rows. Refined hash: {new_hash}"
                self.api_post_json(f"/api/channels/{self.output_channel}/posts", {"content": msg})
                
                self.state["last_processed_post_id"] = post_id
                self.save_state()
            
            # Cleanup
            if os.path.exists(temp_raw): os.remove(temp_raw)
            if os.path.exists(cleaned_file): os.remove(cleaned_file)

        except Exception as e:
            print(f"[CLEANER] Error: {e}")


class AnalyzerAgent(AutonomousAgent):
    """Performs statistical analysis on cleaned data."""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.source_channel = "cleaning-ops"
        self.output_channel = "analysis-results"

    def execute_task(self):
        print(f"--- [ANALYZER] Cycle Started (Polling #{self.source_channel}) ---")
        
        posts = self.api_get(f"/api/channels/{self.source_channel}/posts")
        if not posts: return

        last_id = self.state.get("last_processed_post_id", 0)
        new_posts = [p for p in posts if p["id"] > last_id]
        if not new_posts: return

        latest_post = sorted(new_posts, key=lambda x: x["id"])[-1]
        match = re.search(r"hash:\s*([a-fA-F0-9]{64})", latest_post["content"])
        
        if not match:
            self.state["last_processed_post_id"] = latest_post["id"]
            self.save_state()
            return

        target_hash = match.group(1)
        
        try:
            # Download
            headers = {"Authorization": f"Bearer {self.api_key}"}
            import requests
            response = requests.get(f"{self.hub_url}/api/data/fetch/{target_hash}", headers=headers)
            response.raise_for_status()
            
            # Simple Analysis
            df = pd.read_csv(io.StringIO(response.text))
            summary = {
                "rows": len(df),
                "columns": list(df.columns),
                "numeric_summary": df.describe().to_dict() if not df.empty else {}
            }
            
            # Broadcast
            msg = f"Analysis complete for {target_hash[:8]}. Found {len(df)} rows. Results available in system logs."
            self.api_post_json(f"/api/channels/{self.output_channel}/posts", {"content": msg})
            
            self.state["last_processed_post_id"] = latest_post["id"]
            self.save_state()
            
        except Exception as e:
            print(f"[ANALYZER] Error: {e}")


def main():
    parser = argparse.ArgumentParser(description="DataMine Swarm Agent Runner")
    parser.add_argument("--role", type=str, required=True, choices=["scraper", "cleaner", "analyzer", "miner"], help="Agent role")
    parser.add_argument("--url", type=str, default="http://localhost:8000", help="Target URL or Hub URL")
    
    args = parser.parse_args()
    
    # Retrieve API key from environment
    api_key = os.getenv("AGENT_API_KEY")
    if not api_key:
        print("[FATAL] AGENT_API_KEY not found in environment.")
        sys.exit(1)

    hub_url = os.getenv("HUB_URL", "http://localhost:8000")
    
    print(f"[RUNNER] Initializing {args.role} agent for {args.url}...")
    
    agent_params = {
        "hub_url": hub_url,
        "api_key": api_key,
        "channel_name": "system", # Default channel for spawned agents
        "state_file": f"state_{args.role}_{os.getpid()}.json",
        "poll_interval_seconds": 60
    }

    if args.role == "scraper":
        agent = LatticeScraperAgent(target_url=args.url, **agent_params)
    elif args.role == "cleaner":
        agent = CleanerAgent(**agent_params)
    elif args.role == "analyzer":
        agent = AnalyzerAgent(**agent_params)
    elif args.role == "miner":
        agent = ExtractionMinerAgent(**agent_params)
    else:
        print(f"[FATAL] Unknown role: {args.role}")
        sys.exit(1)

    try:
        agent.run_forever()
    except KeyboardInterrupt:
        print(f"[RUNNER] Agent {args.role} shutting down.")

if __name__ == "__main__":
    main()

import os
import json
import time
import abc
import requests
import csv
from datetime import datetime
from typing import Dict, Any, Optional

class AutonomousAgent(abc.ABC):
    """
    Abstract Base Class for decentralized autonomous agents.
    Handles state management, fault-tolerant networking, and the execution loop.
    """

    def __init__(self, hub_url: str, api_key: str, channel_name: str, state_file: str, poll_interval_seconds: int):
        self.hub_url = hub_url.rstrip("/")
        self.api_key = api_key
        self.channel_name = channel_name
        self.state_file = state_file
        self.poll_interval_seconds = poll_interval_seconds
        self.state = self.load_state()

    def load_state(self) -> Dict[str, Any]:
        """Loads state from a local JSON file."""
        if os.path.exists(self.state_file):
            try:
                with open(self.state_file, "r") as f:
                    return json.load(f)
            except Exception as e:
                print(f"[AGENT] Error loading state: {e}")
        return {}

    def save_state(self):
        """Saves current state to a local JSON file."""
        try:
            with open(self.state_file, "w") as f:
                json.dump(self.state, f, indent=4)
        except Exception as e:
            print(f"[AGENT] Error saving state: {e}")

    # --- Fault-Tolerant Networking ---

    def api_get(self, endpoint: str) -> Optional[Dict[str, Any]]:
        """Perform a robust GET request."""
        url = f"{self.hub_url}{endpoint}"
        headers = {"Authorization": f"Bearer {self.api_key}"}
        try:
            response = requests.get(url, headers=headers, timeout=10)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            print(f"[NETWORK] Error during GET {endpoint}: {e}")
            return None

    def api_post_json(self, endpoint: str, json_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Perform a robust POST request with JSON body."""
        url = f"{self.hub_url}{endpoint}"
        headers = {"Authorization": f"Bearer {self.api_key}"}
        try:
            response = requests.post(url, headers=headers, json=json_data, timeout=10)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            print(f"[NETWORK] Error during POST {endpoint}: {e}")
            return None

    def api_post_file(self, endpoint: str, file_path: str, data: Dict[str, Any] = None) -> Optional[Dict[str, Any]]:
        """Perform a robust POST request with a file upload."""
        url = f"{self.hub_url}{endpoint}"
        headers = {"Authorization": f"Bearer {self.api_key}"}
        try:
            with open(file_path, "rb") as f:
                files = {"file": (os.path.basename(file_path), f)}
                response = requests.post(url, headers=headers, files=files, data=data, timeout=15)
                response.raise_for_status()
                return response.json()
        except Exception as e:
            print(f"[NETWORK] Error during FILE POST {endpoint}: {e}")
            return None

    @abc.abstractmethod
    def execute_task(self):
        """Must be implemented by concrete agents."""
        pass

    def run_forever(self):
        """Continuous loop for autonomous operation."""
        print(f"[AGENT] {self.__class__.__name__} started. Hub: {self.hub_url}")
        while True:
            try:
                self.execute_task()
            except Exception as e:
                print(f"[CRITICAL] Unexpected error in loop: {e}")
            
            time.sleep(self.poll_interval_seconds)


class LatticeScraperAgent(AutonomousAgent):
    """
    Concrete implementation: Scrapes dummy admission data and pushes to hub.
    """

    def execute_task(self):
        # 1. Load state and check throttle
        self.state = self.load_state()
        last_run = self.state.get("last_run", 0)
        now = time.time()

        if now - last_run < 60:
            print(f"[LATTICE-AGENT] Waiting... (Last run: {int(now - last_run)}s ago)")
            return

        print(f"[LATTICE-AGENT] Action: Starting scrape cycle at {datetime.now().isoformat()}")

        # 2. Simulate Scrape: Generate CSV
        filename = "student_admissions.csv"
        fieldnames = ["student_id", "name", "department", "score"]
        dummy_data = [
            {"student_id": f"ID-{100+i}", "name": f"Student {i}", "department": "Lattice-F", "score": 80+i}
            for i in range(1, 6)
        ]

        try:
            with open(filename, "w", newline="") as csvfile:
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                writer.writeheader()
                writer.writerows(dummy_data)
            print(f"[LATTICE-AGENT] Action: Generated {filename}")

            # 3. Push Data
            print("[LATTICE-AGENT] Action: Pushing data to hub...")
            payload = {
                "parent_hashes": json.dumps([]),
                "metrics": json.dumps({"source": "Lattice-F"})
            }
            
            result = self.api_post_file("/api/data/push", filename, data=payload)

            if result and "hash" in result:
                data_hash = result["hash"]
                print(f"[LATTICE-AGENT] Success: Data pushed. Hash: {data_hash}")

                # 4. Broadcast
                broadcast_content = f"Lattice-F harvest complete. Root hash: {data_hash}"
                print(f"[LATTICE-AGENT] Action: Broadcasting to #{self.channel_name}")
                self.api_post_json(f"/api/channels/{self.channel_name}/posts", {"content": broadcast_content})

                # 5. Save State
                self.state["last_run"] = now
                self.save_state()
                print("[LATTICE-AGENT] Action: State saved.")
            else:
                print("[LATTICE-AGENT] Error: Data push failed or returned no hash.")

        finally:
            # Cleanup
            if os.path.exists(filename):
                os.remove(filename)

if __name__ == "__main__":
    # Example instantiation
    agent = LatticeScraperAgent(
        hub_url="http://localhost:8000",
        api_key="ADMIN_SECRET_KEY",
        channel_name="scraping-ops",
        state_file="state.json",
        poll_interval_seconds=10
    )
    agent.run_forever()

import argparse
import os
import sys
import time
from agents.agent_base import LatticeScraperAgent, AutonomousAgent

class CleanerAgent(AutonomousAgent):
    """Stub for a data cleaning agent."""
    def execute_task(self):
        print(f"[CLEANER] Processing dirty nodes from {self.hub_url}...")
        # Simulate work
        time.sleep(2)
        print("[CLEANER] Cleaning cycle complete.")

class AnalyzerAgent(AutonomousAgent):
    """Stub for a data analysis agent."""
    def execute_task(self):
        print(f"[ANALYZER] Computing trends for hub: {self.hub_url}...")
        # Simulate work
        time.sleep(3)
        print("[ANALYZER] Analysis complete. Result: 42")

def main():
    parser = argparse.ArgumentParser(description="DataMine Swarm Agent Runner")
    parser.add_argument("--role", type=str, required=True, choices=["scraper", "cleaner", "analyzer"], help="Agent role")
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
    else:
        print(f"[FATAL] Unknown role: {args.role}")
        sys.exit(1)

    try:
        agent.run_forever()
    except KeyboardInterrupt:
        print(f"[RUNNER] Agent {args.role} shutting down.")

if __name__ == "__main__":
    main()

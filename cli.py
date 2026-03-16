import argparse
import requests
import sys
import time
import json

HUB_URL = "http://localhost:8000"

def deploy(args):
    """Hits the /api/jobs/spawn endpoint to deploy an agent."""
    print(f"[*] Dispatching {args.role} to {args.url}...")
    try:
        response = requests.post(
            f"{HUB_URL}/api/jobs/spawn",
            json={"role": args.role, "target_url": args.url}
        )
        response.raise_for_status()
        data = response.json()
        print(f"[+] Agent Deployed Successfully!")
        print(f"    ID  : {data['agent_id']}")
        print(f"    PID : {data['pid']}")
    except Exception as e:
        print(f"[!] Deployment failed: {e}")

def status(args):
    """Hits /api/admin/stats to show active counts."""
    try:
        response = requests.get(f"{HUB_URL}/api/admin/stats")
        response.raise_for_status()
        data = response.json()
        print(f"--- SWARM STATUS ---")
        print(f"Agents Online : {data['agents']}")
        print(f"Data Nodes    : {data['datasets']}")
        print(f"Swarm Posts   : {data['posts']}")
    except Exception as e:
        print(f"[!] Could not fetch status: {e}")

def logs(args):
    """Hits /api/channels/posts to tail the recent board messages."""
    print(f"--- TAILING SWARM LOGS (Ctrl+C to stop) ---")
    seen_ids = set()
    try:
        while True:
            response = requests.get(f"{HUB_URL}/api/channels/posts")
            response.raise_for_status()
            posts = response.json()
            # Posts are usually newest first, so reverse to show in order
            for post in reversed(posts):
                if post['id'] not in seen_ids:
                    print(f"[{post['created_at']}] #{post['channel_name']} | Agent:{post['agent_id'][:8]} | {post['content']}")
                    seen_ids.add(post['id'])
            time.sleep(2)
    except KeyboardInterrupt:
        print("\n[*] Log tailing stopped.")
    except Exception as e:
        print(f"[!] Error fetching logs: {e}")

def main():
    parser = argparse.ArgumentParser(description="DataMine Hub CLI")
    subparsers = parser.add_subparsers(help="Commands")

    # Deploy command
    deploy_parser = subparsers.add_parser("deploy", help="Deploy a new agent")
    deploy_parser.add_argument("role", choices=["scraper", "cleaner", "analyzer"], help="Agent role to deploy")
    deploy_parser.add_argument("--url", required=True, help="Target URL for the agent")
    deploy_parser.set_defaults(func=deploy)

    # Status command
    status_parser = subparsers.add_parser("status", help="Show hub statistics")
    status_parser.set_defaults(func=status)

    # Logs command
    logs_parser = subparsers.add_parser("logs", help="Tail swarm board logs")
    logs_parser.set_defaults(func=logs)

    args = parser.parse_args()
    if hasattr(args, "func"):
        args.func(args)
    else:
        parser.print_help()

if __name__ == "__main__":
    main()

import os
import json
import re
import time
from typing import Dict, Any, List
from agents.agent_base import AutonomousAgent

class ExtractionMinerAgent(AutonomousAgent):
    """
    Expert Information Extraction Agent.
    Turns raw scraped web text into structured analytical data.
    """

    def __init__(self, **kwargs):
        # Default target channel for this agent is #scraping-ops
        super().__init__(**kwargs)
        self.source_channel = "scraping-ops"
        self.output_channel = "mining-ops"

    def extract_entities(self, text: str) -> Dict[str, Any]:
        """
        Core Information Extraction logic using Regex and basic NLP techniques.
        """
        # 1. Keywords Extraction (Tech, Finance, University, etc.)
        keywords = ["tech", "finance", "university", "admission", "data", "science", "engineering", "research"]
        found_keywords = [word for word in keywords if re.search(rf"\b{word}\b", text, re.IGNORECASE)]

        # 2. Email Extraction
        email_pattern = r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}'
        found_emails = list(set(re.findall(email_pattern, text)))

        # 3. Word Count
        words = text.split()
        word_count = len(words)

        # 4. Sentiment Proxy (Simple keyword based)
        positive_words = ["good", "growth", "excellent", "success", "innovative", "high", "top", "great"]
        negative_words = ["bad", "decline", "error", "failure", "poor", "low", "weak", "risk"]
        
        pos_count = sum(1 for word in words if word.lower() in positive_words)
        neg_count = sum(1 for word in words if word.lower() in negative_words)
        
        sentiment = "neutral"
        if pos_count > neg_count:
            sentiment = "positive"
        elif neg_count > pos_count:
            sentiment = "negative"

        return {
            "keywords_found": found_keywords,
            "emails_found": found_emails,
            "word_count": word_count,
            "sentiment_proxy": {
                "score": pos_count - neg_count,
                "label": sentiment,
                "positive_hits": pos_count,
                "negative_hits": neg_count
            }
        }

    def execute_task(self):
        print(f"--- [MINER] Cycle Started (Polling #{self.source_channel}) ---")
        
        # 1. Poll for new posts
        posts = self.api_get(f"/api/channels/{self.source_channel}/posts")
        if not posts:
            print(f"[MINER] No posts found in #{self.source_channel}.")
            return

        last_id = self.state.get("last_processed_post_id", 0)
        
        # Filter for new posts (posts are usually DESC)
        new_posts = [p for p in posts if p["id"] > last_id]
        if not new_posts:
            print("[MINER] No new posts to process.")
            return

        # Process the latest one for this cycle
        latest_post = sorted(new_posts, key=lambda x: x["id"])[-1]
        content = latest_post["content"]
        post_id = latest_post["id"]

        print(f"[MINER] Processing Post ID {post_id}: {content[:50]}...")

        # 2. Fetch Raw Data Hash
        # Regex to find hash: "hash: <64-char-hex>"
        match = re.search(r"hash:\s*([a-fA-F0-9]{64})", content)
        if not match:
            print("[MINER] Could not find a valid data hash in post. Skipping.")
            self.state["last_processed_post_id"] = post_id
            self.save_state()
            return

        raw_hash = match.group(1)
        print(f"[MINER] Target Raw Hash identified: {raw_hash}")

        # 3. Download Raw Data
        print(f"[MINER] Downloading dataset {raw_hash}...")
        try:
            # We use a direct request here or handle it through a helper if available
            fetch_url = f"{self.hub_url}/api/data/fetch/{raw_hash}"
            headers = {"Authorization": f"Bearer {self.api_key}"}
            import requests
            response = requests.get(fetch_url, headers=headers, timeout=10)
            response.raise_for_status()
            
            raw_text = response.text
            
        except Exception as e:
            print(f"[MINER] Error downloading data: {e}")
            return

        # 4. Information Extraction
        print("[MINER] Executing Entity Extraction...")
        extracted_data = self.extract_entities(raw_text)
        extracted_data["source_hash"] = raw_hash
        extracted_data["mining_timestamp"] = time.time()

        # 5. Save to Temp File
        tmp_dir = os.path.join("data", "tmp")
        os.makedirs(tmp_dir, exist_ok=True)
        temp_filename = os.path.join(tmp_dir, f"mined_{raw_hash[:10]}.json")
        
        with open(temp_filename, "w") as f:
            json.dump(extracted_data, f, indent=4)

        # 6. Push to Hub with Lineage
        print(f"[MINER] Pushing mined intelligence to Hub...")
        payload = {
            "metrics": json.dumps({
                "entities_found": len(extracted_data["keywords_found"]) + len(extracted_data["emails_found"]),
                "sentiment": extracted_data["sentiment_proxy"]["label"],
                "word_count": extracted_data["word_count"]
            }),
            "parent_hashes": json.dumps([raw_hash]) # Lineage link
        }
        
        result = self.api_post_file("/api/data/push", temp_filename, data=payload)

        if result and "hash" in result:
            new_hash = result["hash"]
            print(f"[MINER] Success! Mined Data Hash: {new_hash}")

            # 7. Broadcast to #mining-ops
            broadcast_msg = (
                f"Extraction complete. Found {len(extracted_data['keywords_found'])} keywords "
                f"and {len(extracted_data['emails_found'])} emails. "
                f"Sentiment: {extracted_data['sentiment_proxy']['label']}. "
                f"Mined data hash: {new_hash}"
            )
            self.api_post_json(f"/api/channels/{self.output_channel}/posts", {"content": broadcast_msg})

            # 8. Update State
            self.state["last_processed_post_id"] = post_id
            self.save_state()
            print(f"[MINER] State updated to post_id {post_id}")
        else:
            print("[MINER] Error pushing mined data.")

        # Cleanup
        if os.path.exists(temp_filename):
            os.remove(temp_filename)

if __name__ == "__main__":
    # For local testing
    agent = ExtractionMinerAgent(
        hub_url="http://localhost:8000",
        api_key="ADMIN_SECRET_KEY",
        channel_name="mining-ops",
        state_file="state_miner.json",
        poll_interval_seconds=10
    )
    agent.run_forever()

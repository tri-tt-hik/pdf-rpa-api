"""
Step 5 — Store

Saves the structured JSON output to:
  - A local JSON file in output_json/
  - MongoDB (if MONGO_URI is set in .env)

MongoDB is optional — the bot works without it.
"""

import os
import json
import logging
from datetime import datetime

log = logging.getLogger("rpa.storage")


def _save_to_file(data: dict, filename_base: str) -> str:
    """Save structured JSON to output_json/ folder."""
    os.makedirs("output_json", exist_ok=True)
    out_path = os.path.join("output_json", f"{filename_base}.json")

    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

    log.info(f"[STORE] Saved JSON → {out_path}")
    return out_path


def _save_to_mongo(data: dict):
    """Save to MongoDB if pymongo is available and MONGO_URI is configured."""
    try:
        from pymongo import MongoClient
        mongo_uri = os.getenv("MONGO_URI", "")
        if not mongo_uri:
            log.info("[STORE] MONGO_URI not set — skipping MongoDB.")
            return

        client = MongoClient(mongo_uri, serverSelectionTimeoutMS=3000)
        db = client["pdf_rpa"]
        collection = db["documents"]
        result = collection.insert_one(data)
        log.info(f"[STORE] Saved to MongoDB — id: {result.inserted_id}")
        client.close()

    except ImportError:
        log.warning("[STORE] pymongo not installed — skipping MongoDB.")
    except Exception as e:
        log.error(f"[STORE] MongoDB error: {e}")


def store(structured_data: dict) -> str:
    """
    Main storage function. Always saves to file; optionally to MongoDB.
    Returns the path to the saved JSON file.
    """
    # os.path.basename handles both Windows and Unix paths
    filename = os.path.basename(structured_data["metadata"]["filename"])
    # Strip .pdf extension, add timestamp to avoid collisions
    base = os.path.splitext(filename)[0]
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename_base = f"{base}_{timestamp}"

    # Always save to file
    out_path = _save_to_file(structured_data, filename_base)

    # Optionally save to MongoDB
    _save_to_mongo(structured_data)

    return out_path
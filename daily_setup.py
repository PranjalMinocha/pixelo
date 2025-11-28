import json
import shutil
import os
import logging
from datetime import date
from pathlib import Path
from redis import from_url

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Paths
BASE_DIR = Path(__file__).parent.resolve()
BACKEND_DIR = BASE_DIR / "backend"
PREGEN_DIR = BACKEND_DIR / "pregen_data"
LOOKUP_DIR = BACKEND_DIR / "lookup_files"
IMAGE_DIR = BACKEND_DIR / "static" / "images"
STATE_FILE = BASE_DIR / "daily_state.json"

def activate_next_game():
    """
    Activates the next pre-generated game for the current day and resets the leaderboard.
    This lightweight script is designed to be run by an automated scheduler (e.g., GitHub Actions).
    """
    logging.info("Starting daily game activation...")

    try:
        with open(STATE_FILE, 'r') as f:
            state = json.load(f)
        next_id = state.get("last_used_id", 0) + 1
    except (FileNotFoundError, json.JSONDecodeError):
        next_id = 1
    logging.info(f"Activating pre-generated game ID: {next_id}")

    source_dir = PREGEN_DIR / str(next_id)
    if not source_dir.exists():
        logging.error(f"Pre-generated game directory not found: {source_dir}. Please run pregenerate_data.py.")
        # Fallback to ID 1 if we run out of games, just to keep it running
        logging.warning("Falling back to game ID 1.")
        source_dir = PREGEN_DIR / "1"
        if not source_dir.exists():
             logging.error("Game ID 1 also not found. Cannot activate game.")
             return

    os.makedirs(LOOKUP_DIR, exist_ok=True)
    os.makedirs(IMAGE_DIR, exist_ok=True)
    current_date_str = str(date.today())

    shutil.copy(source_dir / "lookup.json", LOOKUP_DIR / f"lookup_{current_date_str}.json")
    shutil.copy(source_dir / "image.png", IMAGE_DIR / f"img_{current_date_str}.png")
    logging.info(f"Copied game files for {current_date_str}.")

    redis_url = os.getenv('KV_URL')
    if redis_url:
        logging.info("Connecting to Vercel KV to reset leaderboard...")
        try:
            redis_client = from_url(redis_url)
            redis_client.delete(f"leaderboard:{current_date_str}")
            logging.info("Leaderboard for today has been reset in Vercel KV.")
        except Exception as e:
            logging.error(f"Failed to reset leaderboard: {e}")
    else:
        logging.warning("KV_URL environment variable not set. Skipping leaderboard reset.")

    with open(STATE_FILE, 'w') as f:
        json.dump({"last_used_id": next_id}, f)
    logging.info(f"State updated. Last used ID is now {next_id}.")
    logging.info("Daily activation finished successfully.")

if __name__ == "__main__":
    activate_next_game()

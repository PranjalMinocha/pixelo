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

    logging.info("Starting daily game activation...")

    current_date_str = str(date.today())
    logging.info(f"Activating game for date: {current_date_str}")

    source_dir = PREGEN_DIR / current_date_str
    
    if not source_dir.exists():
        logging.error(f"Pre-generated game directory not found for {current_date_str}. Checking for fallback...")
        # Fallback to a 'default' or '1' folder if specific date is missing
        source_dir = PREGEN_DIR / "1" 
        if not source_dir.exists():
             logging.error("Fallback game data (ID 1) also not found. Cannot activate game.")
             return
        logging.warning(f"Using fallback game data from {source_dir}")

    os.makedirs(LOOKUP_DIR, exist_ok=True)
    os.makedirs(IMAGE_DIR, exist_ok=True)

    shutil.copy(source_dir / "lookup.json", LOOKUP_DIR / f"lookup_{current_date_str}.json")
    shutil.copy(source_dir / "image.png", IMAGE_DIR / f"img_{current_date_str}.png")
    logging.info(f"Copied game files for {current_date_str}.")

    redis_url = os.getenv('KV_URL')
    if redis_url:
        logging.info("Connecting to Vercel KV to reset leaderboard...")
        try:
            redis_client = from_url(redis_url)
            # We don't strictly need to delete it if we want to keep history, 
            # but for a daily reset it makes sense to ensure it's clean or just let it be.
            # If we want to persist past leaderboards, we just don't delete.
            # But the user said "daily game", implying new leaderboard each day.
            # The key includes the date, so it's naturally unique per day.
            # We only need to delete if we want to clear *today's* progress on restart.
            # Let's keep the delete for safety in case of re-runs/testing.
            redis_client.delete(f"leaderboard:{current_date_str}")
            logging.info("Leaderboard for today has been reset/ensured clean in Vercel KV.")
        except Exception as e:
            logging.error(f"Failed to reset leaderboard: {e}")
    else:
        logging.warning("KV_URL environment variable not set. Skipping leaderboard reset.")

    logging.info("Daily activation finished successfully.")

if __name__ == "__main__":
    activate_next_game()

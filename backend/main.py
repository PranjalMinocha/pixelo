import json
import os
from datetime import date
from pathlib import Path
from fastapi import FastAPI, HTTPException, Body
from functools import lru_cache
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from redis import from_url
from contextlib import asynccontextmanager
import subprocess

# --- Pydantic Models for Request/Response validation ---
class GuessRequest(BaseModel):
    word: str

class GameInfoResponse(BaseModel):
    imageUrl: str
    totalWords: int

class LeaderboardEntry(BaseModel):
    username: str
    score: int
    sessionId: str | None = None

class GuessResponse(BaseModel):
    status: str
    message: str | None = None
    rank: int | None = None
    isCorrect: bool | None = None

# --- Configuration & Helper Functions ---
BACKEND_ROOT = Path(__file__).parent.resolve()
LOOKUP_DIR = BACKEND_ROOT / "lookup_files"

# --- FastAPI App Initialization ---
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: Run daily setup if needed
    try:
        # Check if today's game exists
        current_date_str = str(date.today())
        lookup_path = LOOKUP_DIR / f"lookup_{current_date_str}.json"
        if not lookup_path.exists():
            print("Today's game not found. Running daily_setup.py...")
            # Assuming we are running from root
            subprocess.run(["python", "daily_setup.py"], check=True)
    except Exception as e:
        print(f"Error running daily setup: {e}")
    yield

app = FastAPI(title="Pixelo API", lifespan=lifespan)

# --- CORS (Cross-Origin Resource Sharing) ---
# Allow all origins for deployment flexibility, but you could restrict this.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- Redis Client (for Vercel KV) ---
redis_client = None
if os.getenv("KV_URL"):
    redis_client = from_url(os.getenv("KV_URL"))

# --- Static File Serving ---
# This makes the generated images accessible via a URL
STATIC_DIR = Path(__file__).parent / "static"
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

@lru_cache(maxsize=2) # Cache today's and yesterday's lookup for a short period after midnight
def get_daily_lookup():
    """Loads the lookup table for the current day."""
    current_date_str = str(date.today())
    lookup_path = LOOKUP_DIR / f"lookup_{current_date_str}.json"

    if not lookup_path.exists():
        return None

    with open(lookup_path, "r") as f:
        return json.load(f)

# --- API Routes ---

@app.get("/api/game/today", response_model=GameInfoResponse)
def get_game_info():
    """Provides the URL for today's image and total word count."""
    current_date_str = str(date.today())
    image_path_on_disk = STATIC_DIR / "images" / f"img_{current_date_str}.png"

    lookup = get_daily_lookup()

    if not image_path_on_disk.exists() or lookup is None:
        raise HTTPException(status_code=404, detail="Today's game has not been generated yet. Please run the daily_setup.py script.")

    image_url = f"/static/images/img_{current_date_str}.png"
    total_words = len(lookup)
    return {"imageUrl": image_url, "totalWords": total_words}

@app.post("/api/game/guess", response_model=GuessResponse)
def process_guess(guess_request: GuessRequest):
    """Processes a user's guess and returns its rank."""
    lookup = get_daily_lookup()
    if lookup is None:
        raise HTTPException(status_code=503, detail="Game data is not available for today. Please run daily_setup.py.")

    if guess_request.word not in lookup:
        return {"status": "not_in_list", "message": "Word not in our dictionary."}

    rank = lookup[guess_request.word]
    is_correct = (rank == 0)

    return {"status": "found", "rank": rank, "isCorrect": is_correct}

@app.get("/api/leaderboard/today", response_model=list[LeaderboardEntry])
def get_leaderboard():
    """Retrieves the leaderboard for the current day."""
    if not redis_client:
        # Return empty list if no DB configured, rather than erroring out for local dev
        return []
    
    leaderboard_key = f"leaderboard:{str(date.today())}"
    # ZRANGE with scores, from rank 0 to 9 (top 10)
    raw_leaderboard = redis_client.zrange(leaderboard_key, 0, -1, withscores=True)
    
    if not raw_leaderboard:
        return []

    # The member is stored as a JSON string: '{"username": "player1", "sessionId": "uuid"}'
    leaderboard = [
        {**json.loads(member), "score": int(score)}
        for member, score in raw_leaderboard
    ]
    return leaderboard

@app.post("/api/leaderboard/submit", response_model=list[LeaderboardEntry])
def submit_to_leaderboard(entry: LeaderboardEntry):
    """Submits a new entry to the daily leaderboard."""
    if not redis_client:
        # Mock return for local dev
        return []

    leaderboard_key = f"leaderboard:{str(date.today())}"
    
    # Store the non-score data as a JSON string in the Redis member
    member_data = json.dumps({"username": entry.username, "sessionId": entry.sessionId})
    
    # Add to sorted set: the score is the score, the member is the JSON data
    redis_client.zadd(leaderboard_key, {member_data: entry.score})

    return get_leaderboard()

@app.get("/healthz")
def health_check():
    """Health check endpoint for monitoring."""
    return {"status": "ok"}

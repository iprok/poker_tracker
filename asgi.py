import threading

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import uvicorn

from bot_main import run_bot_blocking
from engine import Session
from domain.repository.player_action_repository import PlayerActionRepository
from domain.service.player_statistics_service import PlayerStatisticsService
from domain.model.player_statistics import PlayerStatistics
from domain.model.user_info import UserList

# --- FastAPI app ---
app = FastAPI(
    title="Poker Bot API",
    description="Provides player data and statistics from the Telegram Poker Bot",
    version="1.0.0",
)

# --- CORS Middleware ---
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # allow all origins during development
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class PlayerStats(BaseModel):
    games_played: int
    total_buyin: int
    avg_buyins_per_game: float
    profit: int
    roi: float


# --- Routes ---
@app.get("/", tags=["Root"])
def read_root():
    return {"message": "Hello!"}


@app.get(
    "/api/users", response_model=UserList, summary="List all users", tags=["Users"]
)
def get_users():
    """
    Returns a list of all unique users with their Telegram IDs and usernames.
    """
    session = Session()
    repo = PlayerActionRepository(session)
    user_list = repo.get_distinct_users()
    session.close()
    return user_list


@app.get(
    "/api/stats/{user_id}",
    response_model=PlayerStats,
    summary="Get player statistics",
    tags=["Statistics"],
)
def get_player_stats(user_id: int):
    """
    Returns aggregated statistics for the specified user.
    """
    session = Session()
    stats_service = PlayerStatisticsService(session)
    stats: PlayerStatistics = stats_service.get_statistics_for_user(user_id)
    session.close()

    if stats.games_num == 0:
        raise HTTPException(
            status_code=404, detail="No statistics found for this user."
        )

    return {
        "games_played": stats.games_num,
        "total_buyin": stats.total_buyin_money,
        "avg_buyins_per_game": stats.average_buyin_number,
        "profit": stats.profit_money,
        "roi": stats.roi,
    }

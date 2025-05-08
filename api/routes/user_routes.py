from fastapi import APIRouter
from engine import Session
from domain.repository.player_action_repository import PlayerActionRepository
from api.model.user_list_schema import UserInfo, UserList
from cachetools import TTLCache
from config import STATS_BLOCKED_USER_IDS

# 100 — макс. количество записей, 1800 — TTL в секундах (30 минут)
users_cache = TTLCache(maxsize=100, ttl=1800)

router = APIRouter()


@router.get(
    "/api/users", response_model=UserList, summary="List all users", tags=["Users"]
)
def get_users():
    if "users" in users_cache:
        return users_cache["users"]

    session = Session()
    repo = PlayerActionRepository(session)
    user_entities = [
        u for u in repo.get_distinct_users() if u.user_id not in STATS_BLOCKED_USER_IDS
    ]
    session.close()

    response = UserList(users=[UserInfo(**u.__dict__) for u in user_entities])
    users_cache["users"] = response
    return response

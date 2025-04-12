from fastapi import APIRouter
from engine import Session
from domain.repository.player_action_repository import PlayerActionRepository
from domain.model.user_info import UserInfoEntity
from api.model.user_info import UserInfo, UserList

router = APIRouter()


@router.get(
    "/api/users", response_model=UserList, summary="List all users", tags=["Users"]
)
def get_users():
    session = Session()
    repo = PlayerActionRepository(session)
    user_entities: list[UserInfoEntity] = repo.get_distinct_users()
    session.close()

    users = [UserInfo(**user.__dict__) for user in user_entities]
    return UserList(users=users)

from pydantic import BaseModel
from typing import Optional, List


class UserInfo(BaseModel):
    user_id: int
    username: Optional[str] = None


class UserList(BaseModel):
    users: List[UserInfo]

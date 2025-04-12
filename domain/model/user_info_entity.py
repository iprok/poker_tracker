from dataclasses import dataclass
from typing import Optional


@dataclass
class UserInfoEntity:
    user_id: int
    username: Optional[str] = None

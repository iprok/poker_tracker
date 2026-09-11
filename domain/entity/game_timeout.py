from datetime import datetime
from sqlalchemy import DateTime, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column
from engine import Base


class GameTimeout(Base):
    __tablename__ = "game_timeouts"

    game_id: Mapped[int] = mapped_column(ForeignKey("games.id"), primary_key=True)
    next_check: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    deadline: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    buyin_id: Mapped[int] = mapped_column(default=0)

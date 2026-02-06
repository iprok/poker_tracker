from typing import Optional, TYPE_CHECKING
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import DateTime, ForeignKey
from datetime import datetime, timezone
from engine import Base, Engine
from domain.entity.player import Player


class Tournament(Base):
    __tablename__ = "tournaments"

    id: Mapped[int] = mapped_column(primary_key=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )
    start_time: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    end_time: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    is_shuffled: Mapped[bool] = mapped_column(default=False)

    created_player_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("players.id"), nullable=True
    )
    ended_player_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("players.id"), nullable=True
    )

    created_player: Mapped[Optional["Player"]] = relationship(
        "Player", foreign_keys=[created_player_id]
    )
    ended_player: Mapped[Optional["Player"]] = relationship(
        "Player", foreign_keys=[ended_player_id]
    )

    def get_duration_str(self) -> str:
        # Calculate duration
        if self.start_time.tzinfo is None:
            self.start_time = self.start_time.replace(tzinfo=timezone.utc)
        if self.end_time.tzinfo is None:
            self.end_time = self.end_time.replace(tzinfo=timezone.utc)

        duration_seconds = int((self.end_time - self.start_time).total_seconds())
        hours, remainder = divmod(duration_seconds, 3600)
        minutes, seconds = divmod(remainder, 60)
        return f"{hours:02}:{minutes:02}:{seconds:02}"

    def make_tournament_started(self) -> None:
        self.start_time = datetime.now(timezone.utc)
        self.is_shuffled = True

    def is_tournament_started(self) -> bool:
        return self.start_time is not None and self.is_shuffled

    def is_tournament_ended(self) -> bool:
        return self.end_time is not None

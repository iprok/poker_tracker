import enum
from datetime import datetime, timezone
from sqlalchemy import Integer, Enum, ForeignKey, DateTime
from sqlalchemy.orm import Mapped, mapped_column, relationship
from engine import Base, Engine
from domain.entity.player import Player


class PlayerTournamentAction(Base):
    __tablename__ = "player_tournament_actions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    tournament_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("tournaments.id"), nullable=False
    )
    player_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("players.id"), nullable=False
    )
    player: Mapped["Player"] = relationship("Player", foreign_keys=[player_id])
    rank: Mapped[int | None] = mapped_column(Integer, nullable=True)
    table_number: Mapped[int | None] = mapped_column(Integer, nullable=True)
    position_number: Mapped[int | None] = mapped_column(Integer, nullable=True)
    duration_seconds: Mapped[int | None] = mapped_column(Integer, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )
    ended_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    def get_duration_str(self) -> str:
        if self.duration_seconds is None:
            return "00:00:00"
        hours, remainder = divmod(self.duration_seconds, 3600)
        minutes, seconds = divmod(remainder, 60)
        return f"{hours:02}:{minutes:02}:{seconds:02}"

    def get_player(self) -> Player:
        return self.player


Base.metadata.create_all(Engine)

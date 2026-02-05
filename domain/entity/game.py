from sqlalchemy.orm import Mapped, mapped_column
from typing import Optional
from sqlalchemy import DateTime
from datetime import datetime, timezone
from engine import Base, Engine
from utils import ensure_aware


class Game(Base):
    __tablename__ = "games"

    id: Mapped[int] = mapped_column(primary_key=True)
    start_time: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )
    end_time: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)

    def get_duration(self):
        """Возвращает продолжительность игры в формате 'HH:MM:SS'"""
        end_time = ensure_aware(
            self.end_time if self.end_time is not None else datetime.now(timezone.utc)
        )
        start_time = ensure_aware(self.start_time)

        duration = end_time - start_time
        total_seconds = int(duration.total_seconds())
        hours = total_seconds // 3600
        minutes = (total_seconds % 3600) // 60
        seconds = total_seconds % 60
        return f"{hours:02d}:{minutes:02d}:{seconds:02d}"

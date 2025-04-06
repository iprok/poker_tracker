from sqlalchemy import Column, Integer, DateTime
from datetime import datetime, timezone
from engine import Base, Engine


class Game(Base):
    __tablename__ = "games"
    id = Column(Integer, primary_key=True)
    start_time = Column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )

    end_time = Column(DateTime, nullable=True)

    def get_duration(self):
        """Возвращает продолжительность игры в формате 'HH:MM:SS'"""
        end_time = (
            self.end_time if self.end_time is not None else datetime.now(timezone.utc)
        )
        duration = end_time - self.start_time
        total_seconds = int(duration.total_seconds())
        hours = total_seconds // 3600
        minutes = (total_seconds % 3600) // 60
        seconds = total_seconds % 60
        return f"{hours:02d}:{minutes:02d}:{seconds:02d}"


Base.metadata.create_all(Engine)

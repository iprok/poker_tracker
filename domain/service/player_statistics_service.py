# domain/service/player_statistics_service.py
from sqlalchemy.orm import Session

from domain.repository.player_action_repository import PlayerActionRepository
from domain.repository.game_repository import GameRepository
from domain.model.player_statistics import PlayerStatistics


class PlayerStatisticsService:
    def __init__(self, db: Session):
        self.db = db
        self.action_repo = PlayerActionRepository(db)
        self.game_repo = GameRepository(db)

    def get_statistics_for_user(self, user_id: int) -> PlayerStatistics:
        games_num = self.action_repo.count_distinct_games_by_user(user_id)
        total_buyin = self.action_repo.get_total_buyin_amount(user_id)
        total_quit = self.action_repo.get_total_quit_amount(user_id)
        total_buyin_count = self.action_repo.get_buyin_count(user_id)

        # Прибыль
        profit = total_quit - total_buyin

        # ROI
        roi = (profit / total_buyin * 100) if total_buyin else 0.0

        # Среднее число закупов на игру
        average_buyin_number = (total_buyin_count / games_num) if games_num else 0.0

        return PlayerStatistics(
            games_num=games_num,
            total_buyin_money=int(round(total_buyin)),
            average_buyin_number=round(average_buyin_number, 2),
            profit_money=int(round(profit)),
            roi=round(roi, 1),
        )

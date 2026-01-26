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
            total_buyin_money=round(total_buyin, 2),
            average_buyin_number=round(average_buyin_number, 2),
            profit_money=round(profit, 2),
            roi=round(roi, 1),
        )

    def get_daily_roi_history(self, user_id: int) -> list[dict]:
        actions = self.action_repo.get_all_user_actions(user_id)
        
        daily_roi = {}
        cumulative_buyin = 0.0
        cumulative_quit = 0.0
        
        # Sort actions just in case, though repo should handle it
        actions.sort(key=lambda x: x.timestamp)
        
        for action in actions:
            if action.action == "buyin":
                cumulative_buyin += (action.amount or 0)
            elif action.action == "quit":
                cumulative_quit += (action.amount or 0)
            
            # Update ROI for the day of this action
            # We overwrite previous values for the same day, so the last action of the day sets the final ROI
            current_date = action.timestamp.date().isoformat()
            
            if cumulative_buyin > 0:
                roi = ((cumulative_quit - cumulative_buyin) / cumulative_buyin) * 100
            else:
                roi = 0.0
                
            daily_roi[current_date] = round(roi, 1)
            
        # Convert to list of dicts
        return [{"date": k, "roi": v} for k, v in daily_roi.items()]

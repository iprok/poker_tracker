from dataclasses import dataclass


@dataclass
class PlayerStatistics:
    games_num: int  # Количество игр
    total_buyin_money: int  # Всего потрачено на закупы (в лева)
    average_buyin_number: float  # Среднее количество закупов за сессию
    profit_money: int  # Прибыль в лева
    roi: float  # ROI в процентах (с точностью до 0.1%)

from dataclasses import dataclass


@dataclass
class PlayerStatistics:
    games_num: int  # Количество игр
    total_buyin_money: float  # Всего потрачено на закупы (в eur)
    average_buyin_number: float  # Среднее количество закупов за сессию
    profit_money: float  # Прибыль (в eur)
    roi: float  # ROI в процентах (с точностью до 0.1%)

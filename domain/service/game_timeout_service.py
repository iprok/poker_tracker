"""Persistent cash-game timeout checks. The caller owns the transaction."""

from datetime import datetime, timedelta
from sqlalchemy import case, func
from domain.entity.game_timeout import GameTimeout
from domain.entity.player_action import PlayerAction
from domain.repository.game_repository import GameRepository
from utils import ensure_aware

INTERVAL = timedelta(minutes=30)
MAX_DURATION = timedelta(hours=12)


def check_game_timeout(session, now: datetime, announce_duration: bool = False):
    game = GameRepository(session).find_active_game()
    if game is None:
        return None, [], False
    state = session.get(GameTimeout, game.id)
    if state is None:
        state = GameTimeout(
            game_id=game.id,
            next_check=ensure_aware(game.start_time) + INTERVAL,
            buyin_id=0,
        )
        session.add(state)
    if now < ensure_aware(state.next_check):
        return game.id, [], False

    balance = (
        session.query(
            func.sum(
                case(
                    (PlayerAction.action == "buyin", PlayerAction.amount),
                    (PlayerAction.action == "quit", -PlayerAction.amount),
                    else_=0,
                )
            )
        )
        .filter_by(game_id=game.id)
        .scalar()
        or 0
    )
    latest_buyin = (
        session.query(func.max(PlayerAction.id))
        .filter_by(game_id=game.id, action="buyin")
        .scalar()
        or 0
    )
    duration = now - ensure_aware(game.start_time)
    overdue = duration > MAX_DURATION
    low_bank = balance < 2
    messages = []
    if announce_duration:
        minutes = int(duration.total_seconds() // 60)
        messages.append(f"⏱ Игра идёт {minutes // 60} ч {minutes % 60} мин.")

    state.next_check = now + INTERVAL
    if state.deadline is not None:
        if latest_buyin > state.buyin_id:
            state.deadline = None
            messages.append("Закуп получен: автоматическое завершение отменено.")
        elif now >= ensure_aware(state.deadline):
            game.end_time = now
            session.add(
                PlayerAction(
                    game_id=game.id,
                    user_id=0,
                    username="Бот",
                    action="end_game",
                    timestamp=now,
                )
            )
            state.deadline = None
            messages.append(
                "Игра автоматически завершена: после предупреждения не было закупов."
            )
            return game.id, messages, True
        else:
            state.next_check = min(state.next_check, ensure_aware(state.deadline))
            return game.id, messages, False

    if overdue or low_bank:
        reason = (
            "игра длится больше 12 часов" if overdue else "баланс банка меньше 2 евро"
        )
        messages.append(
            f"⚠️ {reason.capitalize()}. Игра завершится через 30 минут, если не будет закупов."
        )
        state.deadline = now + INTERVAL
        state.buyin_id = latest_buyin
    return game.id, messages, False

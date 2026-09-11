"""Persistent cash-game timeout checks. The caller owns the transaction."""

import logging
from datetime import datetime, timedelta
from sqlalchemy import case, func
from domain.entity.game_timeout import GameTimeout
from domain.entity.player_action import PlayerAction
from domain.repository.game_repository import GameRepository
from utils import ensure_aware

CHECK_INTERVAL = timedelta(minutes=5)
CLOSURE_GRACE = timedelta(minutes=30)
logger = logging.getLogger(__name__)
MAX_DURATION = timedelta(hours=12)


def check_game_timeout(session, now: datetime, announce_duration: bool = False):
    game = GameRepository(session).find_active_game()
    if game is None:
        logger.info("Timeout check: no active game")
        return None, [], False
    state = session.get(GameTimeout, game.id)
    if state is None:
        state = GameTimeout(
            game_id=game.id,
            next_check=ensure_aware(game.start_time) + CHECK_INTERVAL,
            buyin_id=0,
        )
        session.add(state)
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
    zero_bank = balance == 0
    due = now >= ensure_aware(state.next_check)
    logger.info(
        "Timeout check: game=%s bank=%s now=%s next_check=%s deadline=%s",
        game.id, balance, now, state.next_check, state.deadline,
    )
    if not due:
        return game.id, [], False

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
    if announce_duration and due:
        minutes = int(duration.total_seconds() // 60)
        messages.append(f"⏱ Игра идёт {minutes // 60} ч {minutes % 60} мин.")

    renewed = False
    state.next_check = now + CHECK_INTERVAL
    if state.deadline is not None:
        if latest_buyin > state.buyin_id:
            renewed = True
            state.deadline = None
            if not (overdue or low_bank):
                logger.info("Timeout cancelled by buy-in: game=%s buyin=%s", game.id, latest_buyin)
                messages.append("Банк пополнен. Автоматическое завершение отменено.")
        elif now >= ensure_aware(state.deadline):
            logger.info("Timeout closing game=%s", game.id)
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
        grace = CLOSURE_GRACE
        minutes = int(grace.total_seconds() // 60)
        delay_text = f"{minutes} минут"
        if renewed:
            remaining_reason = "банк снова пуст" if zero_bank and not overdue else reason
            messages.append(
                f"⚠️ После предупреждения был закуп, но {remaining_reason}. "
                f"Автозавершение отложено на {delay_text}, если не будет новых закупов."
            )
        else:
            messages.append(
                f"⚠️ {reason.capitalize()}. Игра завершится через {delay_text}, если не будет закупов."
            )
        state.deadline = now + grace
        state.next_check = min(state.next_check, state.deadline)
        logger.info("Timeout warning: game=%s reason=%s deadline=%s", game.id, reason, state.deadline)
        state.buyin_id = latest_buyin
    return game.id, messages, False

from datetime import datetime, timezone
from domain.entity.game import Game
from domain.entity.player_action import PlayerAction
from domain.service.message_sender import MessageSender
from domain.service.permission_checker import PermissionChecker
from telegram import (
    Update,
    ReplyKeyboardMarkup,
    KeyboardButton,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    ReplyKeyboardRemove,
    ForceReply,
)
from telegram.ext import ContextTypes
from sqlalchemy import desc, or_
from sqlalchemy.sql import func
from engine import Session
from domain.repository.game_repository import GameRepository
from domain.repository.player_action_repository import PlayerActionRepository
from utils import format_datetime, format_datetime_to_date, get_user_info
from config import (
    CHIP_VALUE,
    CHIP_COUNT,
    USE_TABLE,
    SHOW_SUMMARY_ON_BUYIN,
    SHOW_SUMMARY_ON_QUIT,
    LOG_AMOUNT_LAST_GAMES,
    LOG_AMOUNT_LAST_ACTIONS,
)
from decorators import restrict_to_members, restrict_to_members_and_private
from prettytable import PrettyTable
import re


class PlayerActions:

    @staticmethod
    @restrict_to_members_and_private
    async def buyin(update: Update, context: ContextTypes.DEFAULT_TYPE):
        session = Session()
        current_game_id = context.bot_data.get("current_game_id")

        if current_game_id is None:
            await MessageSender.send_to_current_channel(
                update, context, "Сначала начните игру командой /startgame."
            )

            session.close()
            return

        user = update.effective_user

        # Добавляем закуп
        action = PlayerAction(
            game_id=current_game_id,
            user_id=user.id,
            username=user.username,
            action="buyin",
            chips=CHIP_COUNT,
            amount=CHIP_VALUE,
            timestamp=datetime.now(timezone.utc),
        )
        PlayerActionRepository(session).save(action)

        # Подсчитываем общее количество закупов и сумму
        total_buyins = (
            session.query(PlayerAction)
            .filter_by(game_id=current_game_id, user_id=user.id, action="buyin")
            .with_entities(func.count(PlayerAction.id), func.sum(PlayerAction.amount))
            .first()
        )

        buyin_count = total_buyins[0] or 0
        buyin_total = total_buyins[1] or 0.0

        session.close()

        buyin_text = (
            f"Закуп на {CHIP_COUNT} фишек ({CHIP_VALUE} лева) записан.\n"
            f"Вы уже закупились {buyin_count} раз(а) на общую сумму {buyin_total:.2f} лева в этой игре."
        )

        await MessageSender.send_to_current_channel(update, context, buyin_text)
        await MessageSender.send_to_channel(
            update, context, f"@{update.effective_user.username}: " + buyin_text
        )

        if SHOW_SUMMARY_ON_BUYIN:
            await PlayerActions.summary(update, context)

    @staticmethod
    @restrict_to_members_and_private
    async def quit(update: Update, context: ContextTypes.DEFAULT_TYPE):
        session = Session()
        current_game_id = context.bot_data.get("current_game_id")

        if current_game_id is None:
            await MessageSender.send_to_current_channel(
                update, context, "Сначала начните игру командой /startgame."
            )
            session.close()
            return

        if not context.args:
            await MessageSender.send_to_current_channel(
                update,
                context,
                "Ошибка: Вы не указали количество фишек. Пример: /quit 1500",
            )
            session.close()
            return

        chips_left = int(context.args[0])

        # Проверяем кратность
        step = CHIP_COUNT / CHIP_VALUE
        if chips_left % step != 0:
            await MessageSender.send_to_current_channel(
                update,
                context,
                f"Ошибка: Количество фишек должно быть кратно {int(step)}.",
            )
            session.close()
            return

        total_buyins = (
            session.query(PlayerAction)
            .filter_by(game_id=current_game_id, action="buyin")
            .with_entities(func.sum(PlayerAction.chips))
            .scalar()
            or 0
        )

        total_quits = (
            session.query(PlayerAction)
            .filter_by(game_id=current_game_id, action="quit")
            .with_entities(func.sum(PlayerAction.chips))
            .scalar()
            or 0
        )

        max_chips = total_buyins - total_quits

        if chips_left < 0:
            await MessageSender.send_to_current_channel(
                update, context, "Ошибка: Количество фишек не может быть меньше 0."
            )

            session.close()
            return

        if chips_left > max_chips:
            await MessageSender.send_to_current_channel(
                update,
                context,
                f"Ошибка: Количество фишек не может быть больше доступных в банке: {max_chips}.",
            )
            session.close()
            return

        amount = (chips_left / CHIP_COUNT) * CHIP_VALUE

        # Подсчитываем баланс пользователя
        user = update.effective_user
        user_buyins = (
            session.query(PlayerAction)
            .filter_by(game_id=current_game_id, user_id=user.id, action="buyin")
            .with_entities(func.sum(PlayerAction.amount))
            .scalar()
            or 0
        )

        user_quits = (
            session.query(PlayerAction)
            .filter_by(game_id=current_game_id, user_id=user.id, action="quit")
            .with_entities(func.sum(PlayerAction.amount))
            .scalar()
            or 0
        )

        user_balance = user_buyins - (user_quits + amount)
        if user_balance > 0:
            balance_message = f"Вы должны в банк {int(abs(user_balance))} лева."
        elif user_balance < 0:
            balance_message = f"Банк должен вам {int(abs(user_balance))} лева."
        else:
            balance_message = "Никто никому ничего не должен."

        action = PlayerAction(
            game_id=current_game_id,
            user_id=user.id,
            username=user.username,
            action="quit",
            chips=chips_left,
            amount=amount,
            timestamp=datetime.now(timezone.utc),
        )
        session.add(action)
        session.commit()
        session.close()

        quit_text = (
            f"@{update.effective_user.username} - Выход записан. У вас осталось {chips_left} фишек, что эквивалентно {int(amount)} лева.\n"
            f"До этого закупов от вас было на {int(user_buyins)} лв, выходов - на {int(user_quits)}лв.\n{balance_message}\n\n"
        )
        await MessageSender.send_to_current_channel(
            update, context, quit_text, reply_markup=ReplyKeyboardRemove()
        )
        await MessageSender.send_to_channel(update, context, quit_text)

        if SHOW_SUMMARY_ON_QUIT:
            await PlayerActions.summary(update, context)

    @staticmethod
    @restrict_to_members
    async def quit_with_args(update: Update, context: ContextTypes.DEFAULT_TYPE):
        """
        Обрабатывает команду "выход <число>".
        """
        # Извлекаем текст сообщения
        message_text = update.message.text

        # Разделяем текст на команду и аргумент
        try:
            _, chips_arg = message_text.split(maxsplit=1)
            chips_left = int(chips_arg)
        except (ValueError, IndexError):
            await MessageSender.send_to_current_channel(
                update, context, "Ошибка: Укажите количество фишек. Пример: выход 1500"
            )
            return

        # Передаём аргумент в context.args и вызываем основной метод quit
        context.args = [chips_left]
        await PlayerActions.quit(update, context)

    @staticmethod
    @restrict_to_members
    async def log(update: Update, context: ContextTypes.DEFAULT_TYPE):
        session = Session()

        # Получаем последние записи, ограниченные конфигом
        actions = (
            session.query(PlayerAction)
            .order_by(
                PlayerAction.timestamp.desc()
            )  # Сортируем по времени (последние сначала)
            .limit(LOG_AMOUNT_LAST_ACTIONS)  # Ограничиваем количество записей
            .all()
        )

        log_text = f"Лог последних {LOG_AMOUNT_LAST_ACTIONS} действий:\n"
        for action in actions:
            formatted_timestamp = format_datetime(action.timestamp)
            amount = f"{action.amount:.2f}" if action.amount is not None else "None"
            log_text += (
                f"{formatted_timestamp}: {action.username} - {action.action} "
                f"({action.chips} фишек, {amount} лева)\n"
            )

        session.close()

        # Отправляем сообщение
        await MessageSender.send_to_current_channel(update, context, log_text)

    @staticmethod
    @restrict_to_members
    async def summary(update: Update, context: ContextTypes.DEFAULT_TYPE):
        session = Session()
        current_game_id = context.bot_data.get("current_game_id")
        if current_game_id is None:
            await MessageSender.send_to_current_channel(
                update, context, "Игра не начата."
            )
            session.close()
            return

        game = session.query(Game).filter_by(id=current_game_id).one()
        actions = PlayerActionRepository(session).find_actions_by_game(game.id)
        summary_text = await PlayerActions.summary_formatter(actions, game, context)

        await MessageSender.send_to_current_channel(
            update, context, summary_text, parse_mode="HTML"
        )

        session.close()

    @staticmethod
    @restrict_to_members
    async def summarygames(update: Update, context: ContextTypes.DEFAULT_TYPE):
        session = Session()
        games = GameRepository(session).get_games_by_limit(LOG_AMOUNT_LAST_GAMES)

        summary_text = f"<pre>Сводка последних {LOG_AMOUNT_LAST_GAMES} игр</pre>"
        for game in games:
            actions = PlayerActionRepository(session).find_actions_by_game(game.id)
            summary_text += await PlayerActions.summary_formatter(
                actions, game, context
            )

        await MessageSender.send_to_current_channel(
            update, context, summary_text, parse_mode="HTML"
        )
        session.close()

    @staticmethod
    @restrict_to_members
    async def help(update: Update, context: ContextTypes.DEFAULT_TYPE):
        help_text = (
            "Список команд:\n"
            "/summary - Показать сводку текущей игры.\n"
            "/summarygames - Показать сводку последних игр.\n"
            "/log - Показать лог всех действий.\n"
            "/help - Показать это сообщение.\n\n"
        )

        chat_id = update.effective_chat.id
        if await PermissionChecker.check_is_chat_private(update, context):
            help_text += (
                "/quit <фишки> - Выйти из игры, указав количество оставшихся фишек.\n"
                "/startgame - Начать новую игру.\n\n"
                "/buyin - Закупить фишки.\n\n"
                "/endgame - Завершить текущую игру.\n"
            )

        await MessageSender.send_to_current_channel(update, context, help_text)

    @staticmethod
    async def summary_formatter(
        actions, game, context: ContextTypes.DEFAULT_TYPE
    ) -> str:
        """
        Форматирует сводку игры, группируя игроков по их балансу:
        - Должны банку (отрицательный баланс).
        - Банк должен (положительный баланс).
        - Обрели гармонию (нулевой баланс).
        """
        player_stats = {}
        total_buyin = 0
        total_quit = 0

        # Собираем статистику по игрокам
        for action in actions:
            user_info = await get_user_info(action.user_id, context)

            if user_info not in player_stats:
                player_stats[user_info] = {"buyin": 0, "quit": 0}

            if action.action == "buyin":
                player_stats[user_info]["buyin"] += action.amount
                total_buyin += action.amount

            elif action.action == "quit":
                player_stats[user_info]["quit"] += action.amount
                total_quit += action.amount

        # Рассчитываем баланс для каждого игрока
        players_with_balance = []
        for username, stats in player_stats.items():
            balance = stats["quit"] - stats["buyin"]
            players_with_balance.append(
                (username, balance, abs(balance))
            )  # (имя, баланс, |баланс|)

        # Сортируем игроков по абсолютному значению баланса (от большего к меньшему)
        players_with_balance.sort(key=lambda x: x[2], reverse=True)

        # Группируем игроков по категориям
        debtors = []  # Должны банку (balance < 0)
        creditors = []  # Банк должен (balance > 0)
        balanced = []  # Обрели гармонию (balance == 0)

        for username, balance, _ in players_with_balance:
            if balance < 0:
                debtors.append((username, balance))
            elif balance > 0:
                creditors.append((username, balance))
            else:
                balanced.append((username, balance))

        # Формируем текст сводки
        summary_text = (
            f"Статистика игры за {format_datetime_to_date(game.start_time)}:\n\n"
        )

        # Должны банку
        if debtors:
            summary_text += "💸 <b>Должны банку:</b>\n"
            for username, balance in debtors:
                summary_text += f"{username}: {-balance:.2f} лева\n"
            summary_text += "\n"

        # Банк должен
        if creditors:
            summary_text += "💰 <b>Банк должен:</b>\n"
            for username, balance in creditors:
                summary_text += f"{username}: {balance:.2f} лева\n"
            summary_text += "\n"

        # Обрели гармонию
        if balanced:
            summary_text += "☯️ <b>Обрели гармонию:</b>\n"
            for username, balance in balanced:
                summary_text += f"{username}: {balance:.2f} лева\n"
            summary_text += "\n"

        # Общий баланс
        total_balance = total_buyin - total_quit
        summary_text += (
            f"💼 <b>Общее количество денег в банке:</b> {total_balance:.2f} лева.\n"
        )

        return summary_text

    async def show_menu(update, context):
        # Определяем, откуда пришло сообщение
        chat_id = update.effective_chat.id

        if (
            await PermissionChecker.check_is_chat_private(update, context) == False
        ):  # Если это группа
            keyboard = [
                [KeyboardButton("/summary"), KeyboardButton("/summarygames")],
                [KeyboardButton("/log"), KeyboardButton("/help")],
            ]
        else:  # Если это личный чат с ботом
            keyboard = [
                [KeyboardButton("/startgame"), KeyboardButton("/endgame")],
                [KeyboardButton("/buyin")],
                [KeyboardButton("/startexit")],
                [KeyboardButton("/summary"), KeyboardButton("/summarygames")],
                [KeyboardButton("/log"), KeyboardButton("/help")],
                [KeyboardButton("/close_menu")],
            ]

        reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
        await MessageSender.send_to_current_channel(
            update, context, "Выберите действие:", reply_markup=reply_markup
        )

    async def close_menu(update, context):
        await MessageSender.send_to_current_channel(
            update, context, "Меню закрыто", reply_markup=ReplyKeyboardRemove()
        )

    @staticmethod
    @restrict_to_members_and_private
    async def handle_quit_button(update, context):
        keyboard = []
        row = []
        for amount in range(0, 30001, 1500):
            row.append(KeyboardButton(f"/quit {amount}"))
            if len(row) == 2:
                keyboard.append(row)
                row = []

        if row:
            keyboard.append(row)

        reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
        await MessageSender.send_to_current_channel(
            update, context, "Выберите сумму вывода:", reply_markup=reply_markup
        )

    @staticmethod
    @restrict_to_members_and_private
    async def handle_quit_command(update, context):
        match = re.search(r"(?:@\w+\s+)?/quit\s+(\d+)", update.message.text)
        if match:
            amount = float(match.group(1))

            # Сохраняем сумму в контексте пользователя для подтверждения
            context.user_data["pending_quit_amount"] = amount

            # Создаем клавиатуру подтверждения
            confirm_keyboard = [
                [
                    KeyboardButton(f"Да, вывести {int(amount)}"),
                    KeyboardButton("Нет, отменить"),
                ],
            ]
            reply_markup = ReplyKeyboardMarkup(confirm_keyboard, resize_keyboard=True)

            await MessageSender.send_to_current_channel(
                update,
                context,
                f"Вы уверены, что хотите вывести {int(amount)}?",
                reply_markup=reply_markup,
            )

    @staticmethod
    @restrict_to_members_and_private
    async def handle_confirmation(update, context):
        if "pending_quit_amount" in context.user_data:
            amount = context.user_data["pending_quit_amount"]

            if "Да, вывести" in update.message.text:
                # Устанавливаем аргументы для команды quit
                context.args = [amount]
                await PlayerActions.quit(update, context)

                # Очищаем временные данные
                del context.user_data["pending_quit_amount"]

                # Возвращаем основное меню
                await PlayerActions.show_menu(update, context)
            elif "Нет, отменить" in update.message.text:
                await MessageSender.send_to_current_channel(
                    update,
                    context,
                    "Отмена вывода. Выберите новую сумму или другое действие.",
                    reply_markup=ReplyKeyboardRemove(),
                )
                await PlayerActions.show_menu(update, context)
                del context.user_data["pending_quit_amount"]
        else:
            await MessageSender.send_to_current_channel(
                update, context, "Не найдено ожидающих подтверждения действий."
            )

from datetime import datetime
import pytz
from config import TIMEZONE

def format_datetime(dt: datetime) -> str:
    """
    Форматирует дату и время в указанный временной пояс и возвращает строку формата DD-MM-YYYY HH:MM:SS.
    """
    timezone = pytz.timezone(TIMEZONE)
    if dt.tzinfo is None:
        dt = pytz.utc.localize(dt)  # Применяем UTC, если временная зона отсутствует
    return dt.astimezone(timezone).strftime("%d-%m-%Y %H:%M:%S")


def format_datetime_to_date(dt: datetime) -> str:
    """
    Форматирует дату и время в указанный временной пояс и возвращает строку формата DD-MM-YYYY.
    """
    timezone = pytz.timezone(TIMEZONE)
    if dt.tzinfo is None:
        dt = pytz.utc.localize(dt)  # Применяем UTC, если временная зона отсутствует
    return dt.astimezone(timezone).strftime("%d-%m-%Y")
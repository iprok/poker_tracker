from datetime import datetime
import pytz
from config import TIMEZONE

def format_datetime(dt: datetime) -> str:
    """
    Форматирует дату и время в указанный временной пояс и возвращает строку формата DD-MM-YYYY HH:MM:SS.
    """
    timezone = pytz.timezone(TIMEZONE)
    return dt.astimezone(timezone).strftime("%d-%m-%Y %H:%M:%S")
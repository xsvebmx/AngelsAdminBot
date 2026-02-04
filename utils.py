import secrets
import string
from datetime import datetime

ALPHABET = string.ascii_letters + string.digits + "_"


def generate_shortid(length=16) -> str:
    return "".join(secrets.choice(ALPHABET) for _ in range(length))


def format_datetime(dt: datetime | None) -> str:
    if not dt:
        return "НЕ ВЫБРАНО"
    return dt.strftime("%Y-%m-%d %H:%M:%S UTC")


def bytes_to_gb(value: int | None) -> str:
    if value is None:
        return "НЕ ВЫБРАНО"
    if value == 0:
        return "♾ Безлимит"
    return f"{value / 1024**3:.0f} GB"

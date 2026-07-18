"""Валидация initData из Telegram Mini App.

Схема из документации Telegram (Validating data received via the Mini App):
1. initData — это query string; поле hash извлекается, остальные пары
   сортируются по ключу и склеиваются через \n в data_check_string.
2. secret_key = HMAC_SHA256(key=b"WebAppData", msg=bot_token)
3. ожидаемый hash = HMAC_SHA256(key=secret_key, msg=data_check_string), hex
4. сравнение — только через constant-time compare_digest.
"""
import hashlib
import hmac
import json
import time
from urllib.parse import parse_qsl

from app.config import settings


class InitDataError(Exception):
    pass


def validate_init_data(init_data: str) -> dict:
    """Возвращает словарь с проверенными полями initData.

    Гарантирует подлинность (подпись бот-токеном) и свежесть (auth_date).
    """
    if settings.dev_mode:
        # Режим локальной разработки в браузере, где initData пустой.
        return {"user": {"id": 0, "first_name": "Dev"}}

    pairs = dict(parse_qsl(init_data, keep_blank_values=True))
    received_hash = pairs.pop("hash", None)
    if not received_hash:
        raise InitDataError("hash missing")

    data_check_string = "\n".join(
        f"{k}={v}" for k, v in sorted(pairs.items())
    )
    secret_key = hmac.new(
        b"WebAppData", settings.bot_token.encode(), hashlib.sha256
    ).digest()
    expected_hash = hmac.new(
        secret_key, data_check_string.encode(), hashlib.sha256
    ).hexdigest()

    if not hmac.compare_digest(expected_hash, received_hash):
        raise InitDataError("signature mismatch")

    auth_date = int(pairs.get("auth_date", "0"))
    if time.time() - auth_date > settings.init_data_max_age_sec:
        raise InitDataError("initData expired")

    if "user" in pairs:
        pairs["user"] = json.loads(pairs["user"])
    return pairs

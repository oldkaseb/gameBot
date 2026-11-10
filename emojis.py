# -*- coding: utf-8 -*-
"""emojis.py — مدیریت کامل کاستوم ایموجی‌های پریمیوم (رفع خطای ENTITY_TEXT_INVALID)"""

import re

EMOJI_ID_RE = re.compile(r"\[E:(\d+)\]")
TG_EMOJI_TAG_RE = re.compile(
    r'<tg-emoji\s+emoji-id=["\'](\d+)["\'][^>]*>.*?</tg-emoji>',
    re.DOTALL,
)

# آیدی‌های کاستوم ایموجی پریمیوم
EMOJI_MAP = {
    "GAME": "5368324170671202286",
    "PARTY": "5461151367559141950",
    "SPARK": "5472164874886846699",
    "PUZZLE": "5373098009640856781",
    "TARGET": "5382194935057372936",
    "CARD": "5373098009640856781",
    "BRAIN": "5443038326535759644",
    "MIC": "5443038326535759644",
    "CROSS": "5465665476971471368",
    "CHECK": "5427009714745517609",
    "OK2": "5427009714745517609",
    "CROWN": "5424818078833715060",
    "WAVE": "5472164874886846699",
    "HEART": "5438496463044752972",
    "PLUS": "5427009714745517609",
    "INFO": "5447644880824181073",
    "PLAY": "5368324170671202286",
    "STAR": "5438496463044752972",
    "ARROW": "5451646226975955576",
    "BACK": "5451646226975955576",
    "LEFT": "5451646226975955576",
    "RIGHT": "5451646226975955576",
    "LINK": "5341715473882955310",
    "REFRESH": "5451646226975955576",
    "WARN": "5447644880824181073",
    "BOT": "5373012449597351010",
    "HOURGLASS": "5447644880824181073",
    "CHART": "5409048419211682843",
    "TROPHY": "5409048419211682843",
    "SKULL": "5465665476971471368",
    "CAL": "5341715473882955310",
    "PEOPLE": "5373012449597351010",
    "USER": "5373012449597351010",
    "DISGUISE": "5373012449597351010",
    "GLOBE": "5472164874886846699",
    "SETTINGS": "5341715473882955310",
    "FIRE": "5368324170671202286",
    "DICE": "5382194935057372936",
    "LOCK": "5447644880824181073",
    "SEARCH": "5341715473882955310",
    "MEGA": "5443038326535759644",
    "BOX": "5373098009640856781",
    "PC": "5341715473882955310",
    "BLOCK": "5465665476971471368",
    "ROCKET": "5368324170671202286",
    "PIN": "5438496463044752972",
    "EYES": "5443038326535759644",
    "TRASH": "5465665476971471368",
    "SHIELD": "5424818078833715060",
    "DOWN": "5451646226975955576",
}

# کاراکتر ایموجی الزامی داخل تگ <tg-emoji> برای جلوگیری از خطای ENTITY_TEXT_INVALID در سرور تلگرام
BASE_MAP = {
    "5368324170671202286": "🎮",
    "5461151367559141950": "🎉",
    "5472164874886846699": "✨",
    "5373098009640856781": "🧩",
    "5382194935057372936": "🎯",
    "5443038326535759644": "🧠",
    "5465665476971471368": "❌",
    "5427009714745517609": "✅",
    "5424818078833715060": "👑",
    "5438496463044752972": "⭐",
    "5451646226975955576": "🔄",
    "5341715473882955310": "⚙️",
    "5447644880824181073": "⚠️",
    "5373012449597351010": "👤",
    "5409048419211682843": "🏆",
}


def _tok(emoji_id: str) -> str:
    return f"[E:{emoji_id}]"


class _EmojiNamespace:
    def __getattr__(self, name: str) -> str:
        eid = EMOJI_MAP.get(name.upper(), EMOJI_MAP["SPARK"])
        return _tok(eid)


E = _EmojiNamespace()


def render_emojis(text: str) -> str:
    """
    تبدیل توکن‌های [E:ID] به تگ استاندارد <tg-emoji emoji-id="ID">⚡</tg-emoji>.
    داشتن یک ایموجی پایه معتبر داخل تگ برای سرور تلگرام الزامی است تا ENTITY_TEXT_INVALID ندهد.
    """
    if not text:
        return text
    return EMOJI_ID_RE.sub(
        lambda m: f'<tg-emoji emoji-id="{m.group(1)}">{BASE_MAP.get(m.group(1), "⚡")}</tg-emoji>',
        text,
    )


def strip_custom_emoji_tags(text: str, keep_unicode: bool = False) -> str:
    """حذف کامل تگ‌های کاستوم ایموجی در صورت عدم پشتیبانی بدون باقی گذاشتن ایموجی یونیکد"""
    if not text:
        return text
    if keep_unicode:
        cleaned = TG_EMOJI_TAG_RE.sub(lambda m: BASE_MAP.get(m.group(1), ""), text)
    else:
        cleaned = TG_EMOJI_TAG_RE.sub("", text)
    cleaned = EMOJI_ID_RE.sub("", cleaned)
    return re.sub(r" +", " ", cleaned).strip()


def extract_emoji_ids(text: str) -> list[str]:
    if not text:
        return []
    ids = EMOJI_ID_RE.findall(text)
    ids.extend(TG_EMOJI_TAG_RE.findall(text))
    return ids

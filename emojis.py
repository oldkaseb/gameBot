from utils.premium import tg_emoji

# آیدی‌های عددی کاستوم ایموجی‌های پریمیوم تلگرام (قابل جایگزینی با آیدی‌های اختصاصی شما)
EMOJI_IDS = {
    "gamepad": "5368324170671202286",
    "fire": "5368324170671202286",
    "trophy": "5409048419211682843",
    "star": "5438496463044752972",
    "check": "5427009714745517609",
    "cross": "5465665476971471368",
    "warning": "5447644880824181073",
    "crown": "5424818078833715060",
    "dice": "5382194935057372936",
    "cards": "5373098009640856781",
    "chat": "5443038326535759644",
    "settings": "5341715473882955310",
    "user": "5373012449597351010",
    "back": "5451646226975955576",
    "sparkle": "5472164874886846699",
}

# تگ‌های آماده برای استفاده مستقیم در متن‌های ربات (HTML) بدون ایموجی یونیکد ساده
E_GAME = tg_emoji(EMOJI_IDS["gamepad"])
E_FIRE = tg_emoji(EMOJI_IDS["fire"])
E_TROPHY = tg_emoji(EMOJI_IDS["trophy"])
E_STAR = tg_emoji(EMOJI_IDS["star"])
E_CHECK = tg_emoji(EMOJI_IDS["check"])
E_CROSS = tg_emoji(EMOJI_IDS["cross"])
E_WARN = tg_emoji(EMOJI_IDS["warning"])
E_CROWN = tg_emoji(EMOJI_IDS["crown"])
E_DICE = tg_emoji(EMOJI_IDS["dice"])
E_CARDS = tg_emoji(EMOJI_IDS["cards"])
E_CHAT = tg_emoji(EMOJI_IDS["chat"])
E_SETTINGS = tg_emoji(EMOJI_IDS["settings"])
E_USER = tg_emoji(EMOJI_IDS["user"])
E_BACK = tg_emoji(EMOJI_IDS["back"])
E_SPARKLE = tg_emoji(EMOJI_IDS["sparkle"])

# استایل‌های استاندارد دکمه‌ها
STYLE_PRIMARY = "primary"
STYLE_SUCCESS = "success"
STYLE_DANGER = "danger"

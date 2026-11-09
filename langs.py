"""سیستم ترجمه ۷ زبانه"""

LANGS = {
    "fa": "🇮🇷 فارسی",
    "en": "🇬🇧 English",
    "ar": "🇸🇦 العربية",
    "tr": "🇹🇷 Türkçe",
    "ru": "🇷🇺 Русский",
    "de": "🇩🇪 Deutsch",
    "zh": "🇨🇳 中文",
}

# رشته‌های کلیدی (نمونه — به همین شکل بقیه اضافه می‌شوند)
T = {
    # ── عمومی
    "welcome": {
        "fa": "سلام {name} عزیز، به راینوبازی خوش آمدید!",
        "en": "Hello {name}, welcome to Rhino Games!",
        "ar": "مرحباً {name}، أهلاً بك في ألعاب رينو!",
        "tr": "Merhaba {name}, Rhino Oyunları'na hoş geldiniz!",
        "ru": "Привет, {name}, добро пожаловать в Rhino Games!",
        "de": "Hallo {name}, willkommen bei Rhino Games!",
        "zh": "你好 {name}，欢迎来到 Rhino Games！",
    },
    "choose_lang": {
        "fa": "لطفاً زبان خود را انتخاب کنید:",
        "en": "Please choose your language:",
        "ar": "الرجاء اختيار لغتك:",
        "tr": "Lütfen dilinizi seçin:",
        "ru": "Пожалуйста, выберите язык:",
        "de": "Bitte wählen Sie Ihre Sprache:",
        "zh": "请选择您的语言：",
    },
    "lang_saved": {
        "fa": "✅ زبان شما ذخیره شد.",
        "en": "✅ Your language has been saved.",
        "ar": "✅ تم حفظ لغتك.",
        "tr": "✅ Diliniz kaydedildi.",
        "ru": "✅ Ваш язык сохранён.",
        "de": "✅ Ihre Sprache wurde gespeichert.",
        "zh": "✅ 您的语言已保存。",
    },
    # ── منوی بازی‌ها
    "game_panel": {
        "fa": "🎮 {name} عزیز، به پنل بازی خوش آمدید.\n\nدسته‌بندی مورد نظر را انتخاب کنید:",
        "en": "🎮 Welcome {name} to the game panel.\n\nChoose a category:",
        "ar": "🎮 مرحباً {name} في لوحة الألعاب.\n\nاختر فئة:",
        "tr": "🎮 Oyun paneline hoş geldin {name}.\n\nBir kategori seç:",
        "ru": "🎮 Добро пожаловать в игровую панель, {name}.\n\nВыберите категорию:",
        "de": "🎮 Willkommen {name} im Spielbereich.\n\nWähle eine Kategorie:",
        "zh": "🎮 {name}，欢迎进入游戏面板。\n\n请选择类别：",
    },
    "btn_group": {
        "fa": "🏆 بازی‌های گروهی", "en": "🏆 Group Games",
        "ar": "🏆 ألعاب جماعية", "tr": "🏆 Grup Oyunları",
        "ru": "🏆 Групповые игры", "de": "🏆 Gruppenspiele",
        "zh": "🏆 群组游戏",
    },
    "btn_typing": {
        "fa": "✍️ بازی‌های تایپی", "en": "✍️ Typing Games",
        "ar": "✍️ ألعاب الكتابة", "tr": "✍️ Yazma Oyunları",
        "ru": "✍️ Игры на печать", "de": "✍️ Tippspiele",
        "zh": "✍️ 打字游戏",
    },
    "btn_anon": {
        "fa": "🤫 بازی‌های ناشناس", "en": "🤫 Anonymous Games",
        "ar": "🤫 ألعاب مجهولة", "tr": "🤫 Anonim Oyunlar",
        "ru": "🤫 Анонимные игры", "de": "🤫 Anonyme Spiele",
        "zh": "🤫 匿名游戏",
    },
    "btn_single": {
        "fa": "👤 بازی‌های تک‌نفره", "en": "👤 Single Player",
        "ar": "👤 لاعب فردي", "tr": "👤 Tek Oyuncu",
        "ru": "👤 Одиночная игра", "de": "👤 Einzelspieler",
        "zh": "👤 单人游戏",
    },
    "btn_close": {
        "fa": "✖️ بستن پنل", "en": "✖️ Close Panel",
        "ar": "✖️ إغلاق اللوحة", "tr": "✖️ Paneli Kapat",
        "ru": "✖️ Закрыть панель", "de": "✖️ Panel schließen",
        "zh": "✖️ 关闭面板",
    },
    "btn_back": {
        "fa": "🔙 بازگشت", "en": "🔙 Back",
        "ar": "🔙 رجوع", "tr": "🔙 Geri",
        "ru": "🔙 Назад", "de": "🔙 Zurück",
        "zh": "🔙 返回",
    },
    # ── بازی‌ها
    "join_game": {
        "fa": "✅ پیوستن به بازی", "en": "✅ Join Game",
        "ar": "✅ انضم إلى اللعبة", "tr": "✅ Oyuna Katıl",
        "ru": "✅ Присоединиться", "de": "✅ Beitreten",
        "zh": "✅ 加入游戏",
    },
    "game_full": {
        "fa": "ظرفیت بازی تکمیل است.", "en": "Game is full.",
        "ar": "اللعبة ممتلئة.", "tr": "Oyun dolu.",
        "ru": "Игра заполнена.", "de": "Spiel ist voll.",
        "zh": "游戏已满。",
    },
    "not_your_turn": {
        "fa": "نوبت شما نیست!", "en": "Not your turn!",
        "ar": "ليس دورك!", "tr": "Sıra sizde değil!",
        "ru": "Не ваш ход!", "de": "Nicht dein Zug!",
        "zh": "还没到你的回合！",
    },
    "already_joined": {
        "fa": "شما قبلاً پیوسته‌اید!", "en": "You already joined!",
        "ar": "لقد انضممت بالفعل!", "tr": "Zaten katıldınız!",
        "ru": "Вы уже присоединились!", "de": "Du bist schon dabei!",
        "zh": "你已经加入了！",
    },
    "cell_occupied": {
        "fa": "این خانه پر شده است!", "en": "Cell already taken!",
        "ar": "هذه الخلية مشغولة!", "tr": "Bu hücre dolu!",
        "ru": "Клетка занята!", "de": "Zelle ist belegt!",
        "zh": "这个格子已被占用！",
    },
    "game_winner": {
        "fa": "🏆 برنده: {name}", "en": "🏆 Winner: {name}",
        "ar": "🏆 الفائز: {name}", "tr": "🏆 Kazanan: {name}",
        "ru": "🏆 Победитель: {name}", "de": "🏆 Gewinner: {name}",
        "zh": "🏆 获胜者：{name}",
    },
    "game_draw": {
        "fa": "🤝 بازی مساوی شد!", "en": "🤝 It's a draw!",
        "ar": "🤝 تعادل!", "tr": "🤝 Berabere!",
        "ru": "🤝 Ничья!", "de": "🤝 Unentschieden!",
        "zh": "🤝 平局！",
    },
    # ── خطاها
    "need_join": {
        "fa": "❗️ برای استفاده ابتدا در کانال ما عضو شوید.",
        "en": "❗️ Please join our channel first.",
        "ar": "❗️ يرجى الانضمام إلى قناتنا أولاً.",
        "tr": "❗️ Lütfen önce kanalımıza katılın.",
        "ru": "❗️ Сначала подпишитесь на наш канал.",
        "de": "❗️ Bitte treten Sie zuerst unserem Kanal bei.",
        "zh": "❗️ 请先加入我们的频道。",
    },
    "banned": {
        "fa": "🚫 حساب شما مسدود است.",
        "en": "🚫 Your account is banned.",
        "ar": "🚫 حسابك محظور.",
        "tr": "🚫 Hesabınız yasaklandı.",
        "ru": "🚫 Ваш аккаунт заблокирован.",
        "de": "🚫 Ihr Konto ist gesperrt.",
        "zh": "🚫 您的账户已被禁止。",
    },
    # … ادامه بده به همین شکل برای بقیه کلیدها
}

# کش زبان‌ها در حافظه (برای سرعت)
_user_lang_cache: dict[int, str] = {}

def t(key: str, lang: str = "fa", **kwargs) -> str:
    """ترجمه یک کلید به زبان مشخص با فرمت‌دهی"""
    row = T.get(key, {})
    text = row.get(lang) or row.get("fa") or key
    return text.format(**kwargs) if kwargs else text

def get_user_lang(user_id: int) -> str:
    return _user_lang_cache.get(user_id, "fa")

def set_user_lang(user_id: int, lang: str) -> None:
    if lang in LANGS:
        _user_lang_cache[user_id] = lang

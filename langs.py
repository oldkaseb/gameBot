"""langs.py — سیستم ۷ زبانه با لحن صمیمی"""

LANGS = {
    "fa": "🇮🇷 فارسی",
    "en": "🇬🇧 English",
    "ar": "🇸🇦 العربية",
    "tr": "🇹🇷 Türkçe",
    "ru": "🇷🇺 Русский",
    "de": "🇩🇪 Deutsch",
    "zh": "🇨🇳 中文",
}

T = {
# ═══════════════════ عمومی
"welcome": {
    "fa": "سلام {name}! خوش اومدی به راینوبازی",
    "en": "Hey {name}! Welcome to Rhino Games",
    "ar": "أهلاً {name}! نوّرت ألعاب رينو",
    "tr": "Selam {name}! Rhino Oyunları'na hoş geldin",
    "ru": "Привет, {name}! Добро пожаловать в Rhino Games",
    "de": "Hey {name}! Willkommen bei Rhino Games",
    "zh": "嘿 {name}！欢迎来到 Rhino Games",
},
"choose_lang": {
    "fa": "زبونت چیه؟ انتخاب کن:",
    "en": "What's your language? Pick one:",
    "ar": "شو لغتك؟ اختار:",
    "tr": "Dilin ne? Seç bakalım:",
    "ru": "Какой у тебя язык? Выбирай:",
    "de": "Welche Sprache? Wähl aus:",
    "zh": "你用什么语言？选一个：",
},
"lang_saved": {
    "fa": "✅ زبونت ذخیره شد",
    "en": "✅ Language saved",
    "ar": "✅ تم حفظ لغتك",
    "tr": "✅ Dil kaydedildi",
    "ru": "✅ Язык сохранён",
    "de": "✅ Sprache gespeichert",
    "zh": "✅ 语言已保存",
},
"cancelled": {
    "fa": "✅ بیخیال شد",
    "en": "✅ Cancelled",
    "ar": "✅ تم الإلغاء",
    "tr": "✅ İptal edildi",
    "ru": "✅ Отменено",
    "de": "✅ Abgebrochen",
    "zh": "✅ 已取消",
},
# ═══════════════════ دکمه‌ها
"btn_back":       {"fa": "برگرد", "en": "Back", "ar": "رجوع", "tr": "Geri", "ru": "Назад", "de": "Zurück", "zh": "返回"},
"btn_cancel":     {"fa": "بیخیال", "en": "Cancel", "ar": "إلغاء", "tr": "İptal", "ru": "Отмена", "de": "Abbrechen", "zh": "取消"},
"btn_close":      {"fa": "ببند", "en": "Close", "ar": "إغلاق", "tr": "Kapat", "ru": "Закрыть", "de": "Schließen", "zh": "关闭"},
"btn_confirm":    {"fa": "آره", "en": "Yeah", "ar": "أكيد", "tr": "Evet", "ru": "Да", "de": "Ja", "zh": "好"},
"btn_yes":        {"fa": "آره", "en": "Yes", "ar": "نعم", "tr": "Evet", "ru": "Да", "de": "Ja", "zh": "是"},
"btn_no":         {"fa": "نه", "en": "No", "ar": "لا", "tr": "Hayır", "ru": "Нет", "de": "Nein", "zh": "否"},
"btn_group":      {"fa": "بازی گروهی", "en": "Group Games", "ar": "ألعاب جماعية", "tr": "Grup Oyunları", "ru": "Групповые", "de": "Gruppenspiele", "zh": "群组游戏"},
"btn_single":     {"fa": "بازی تنهایی", "en": "Solo Games", "ar": "ألعاب فردية", "tr": "Tek Oyunlar", "ru": "Одиночные", "de": "Solo-Spiele", "zh": "单人游戏"},
"btn_typing":     {"fa": "بازی تایپی", "en": "Typing Games", "ar": "ألعاب الكتابة", "tr": "Yazma Oyunları", "ru": "Печать", "de": "Tippspiele", "zh": "打字游戏"},
"btn_anon":       {"fa": "ناشناس", "en": "Anonymous", "ar": "مجهول", "tr": "Anonim", "ru": "Анонимно", "de": "Anonym", "zh": "匿名"},

# ═══════════════════ پنل بازی
"game_panel":         {"fa": "خب رفیق، پنل بازه. کدوم دسته؟", "en": "Panel's open. Which category?", "ar": "اللوحة مفتوحة. اختر فئة:", "tr": "Panel açık. Kategori seç:", "ru": "Панель открыта. Выбери:", "de": "Panel offen. Kategorie?", "zh": "面板开了，选个分类："},
"group_games_title":  {"fa": "بازی‌های کارتی و گروهی", "en": "Card & Group Games", "ar": "ألعاب جماعية", "tr": "Kart & Grup", "ru": "Карточные и групповые", "de": "Karten & Gruppe", "zh": "卡牌与群组"},
"single_games_title": {"fa": "بازی‌های تنهایی", "en": "Solo Games", "ar": "ألعاب فردية", "tr": "Tek Oyunlar", "ru": "Одиночные", "de": "Solo-Spiele", "zh": "单人游戏"},
"typing_games_title": {"fa": "بازی‌های تایپی و سرعتی", "en": "Typing & Speed", "ar": "ألعاب الكتابة والسرعة", "tr": "Yazma & Hız", "ru": "Печать и скорость", "de": "Tippen & Tempo", "zh": "打字与速度"},
"anon_games_title":   {"fa": "بازی‌های ناشناس (فقط ادمین)", "en": "Anonymous (Admin only)", "ar": "مجهولة (للمشرفين)", "tr": "Anonim (Yönetici)", "ru": "Анонимные (админ)", "de": "Anonym (nur Admin)", "zh": "匿名（仅管理员）"},

# ═══════════════════ نام بازی‌ها
"game_hokm":          {"fa": "حکم ۲ نفره", "en": "Hokm 2P", "ar": "حكم لاعبين", "tr": "Hokm 2K", "ru": "Хокм 2 игрока", "de": "Hokm 2P", "zh": "Hokm 双人"},
"game_hokm_4p":       {"fa": "حکم ۴ نفره", "en": "Hokm 4P", "ar": "حكم ٤ لاعبين", "tr": "Hokm 4K", "ru": "Хокм 4 игрока", "de": "Hokm 4P", "zh": "Hokm 四人"},
"game_dooz":          {"fa": "دوز ۲ نفره", "en": "Tic-Tac-Toe", "ar": "إكس أو", "tr": "XOX", "ru": "Крестики-нолики", "de": "Tic-Tac-Toe", "zh": "井字棋"},
"game_doz4p":         {"fa": "دوز ۴ نفره", "en": "Tic-Tac-Toe 4P", "ar": "إكس أو ٤ لاعبين", "tr": "XOX 4K", "ru": "Крестики-нолики 4", "de": "Tic-Tac-Toe 4P", "zh": "井字棋四人"},
"game_connect4":      {"fa": "چهار در ردیف", "en": "Connect Four", "ar": "أربعة في صف", "tr": "Dörtlü Bağla", "ru": "Четыре в ряд", "de": "Vier gewinnt", "zh": "四子棋"},
"game_rps":           {"fa": "سنگ کاغذ قیچی", "en": "Rock Paper Scissors", "ar": "حجر ورقة مقص", "tr": "Taş Kağıt Makas", "ru": "Камень ножницы бумага", "de": "Schere Stein Papier", "zh": "石头剪刀布"},
"game_memory":        {"fa": "بازی حافظه", "en": "Memory Game", "ar": "لعبة الذاكرة", "tr": "Hafıza Oyunu", "ru": "Игра памяти", "de": "Memory", "zh": "记忆游戏"},
"game_spuzzle":       {"fa": "پازل کشویی", "en": "Sliding Puzzle", "ar": "لغز منزلق", "tr": "Kaydırmalı Bulmaca", "ru": "Пятнашки", "de": "Schiebepuzzle", "zh": "滑动拼图"},
"game_samegame":      {"fa": "جفت‌ها", "en": "Same Game", "ar": "الأزواج", "tr": "Aynı Oyun", "ru": "Одинаковые", "de": "Gleiche", "zh": "消消乐"},
"game_hangman":       {"fa": "حدس کلمه", "en": "Hangman", "ar": "خمن الكلمة", "tr": "Adam Asmaca", "ru": "Виселица", "de": "Galgenmännchen", "zh": "猜词"},
"game_typing":        {"fa": "تایپ سرعتی", "en": "Typing Race", "ar": "سباق الكتابة", "tr": "Yazma Yarışı", "ru": "Гонка печати", "de": "Tipprennen", "zh": "打字比赛"},
"game_guess_num":     {"fa": "حدس عدد", "en": "Guess Number", "ar": "خمن الرقم", "tr": "Sayı Tahmin", "ru": "Угадай число", "de": "Zahl raten", "zh": "猜数字"},
"game_eteraf":        {"fa": "اعتراف پیش‌فرض", "en": "Confession (Default)", "ar": "اعتراف افتراضي", "tr": "İtiraf (Varsayılan)", "ru": "Признание (обычн.)", "de": "Geständnis (Standard)", "zh": "表白（默认）"},
"game_eteraf_custom": {"fa": "اعتراف سفارشی", "en": "Confession (Custom)", "ar": "اعتراف مخصص", "tr": "İtiraf (Özel)", "ru": "Признание (своё)", "de": "Geständnis (Eigen)", "zh": "表白（自定义）"},
"game_gharch":        {"fa": "قارچ ناشناس", "en": "Anonymous Mushroom", "ar": "فطر مجهول", "tr": "Anonim Mantar", "ru": "Анонимный гриб", "de": "Anonymer Pilz", "zh": "匿名蘑菇"},
"game_gardone":       {"fa": "گردونه شانس", "en": "Lucky Wheel", "ar": "عجلة الحظ", "tr": "Çarkıfelek", "ru": "Колесо удачи", "de": "Glücksrad", "zh": "幸运轮盘"},
"game_2048_title":    {"fa": "بازی 2048", "en": "2048", "ar": "لعبة 2048", "tr": "2048", "ru": "Игра 2048", "de": "2048", "zh": "2048"},
"game_disabled":      {"fa": "🔒 این بازی فعلاً خاموشه", "en": "🔒 This game is off", "ar": "🔒 اللعبة مقفلة", "tr": "🔒 Bu oyun kapalı", "ru": "🔒 Игра выключена", "de": "🔒 Spiel aus", "zh": "🔒 游戏已关闭"},

# ═══════════════════ پیام‌های مشترک
"join_game":              {"fa": "بیا تو", "en": "Join In", "ar": "انضم", "tr": "Katıl", "ru": "Зайти", "de": "Beitreten", "zh": "加入"},
"game_full":              {"fa": "جا پر شد", "en": "Full", "ar": "ممتلئة", "tr": "Dolu", "ru": "Полная", "de": "Voll", "zh": "满了"},
"not_your_turn":          {"fa": "الان نوبت تو نیست", "en": "Not your turn yet", "ar": "ليس دورك الآن", "tr": "Sıra sende değil", "ru": "Не твой ход", "de": "Nicht dein Zug", "zh": "还没轮到你"},
"already_joined":         {"fa": "تو که هستی، چرا دوباره؟", "en": "You're already in!", "ar": "أنت منضم بالفعل!", "tr": "Zaten girdin!", "ru": "Ты уже там!", "de": "Du bist schon drin!", "zh": "你已经在里面了！"},
"cell_occupied":          {"fa": "پره رفیق", "en": "Taken", "ar": "مشغول", "tr": "Dolu", "ru": "Занято", "de": "Belegt", "zh": "已占"},
"game_winner":            {"fa": "🏆 برنده: {name}", "en": "🏆 Winner: {name}", "ar": "🏆 الفائز: {name}", "tr": "🏆 Kazanan: {name}", "ru": "🏆 Победил: {name}", "de": "🏆 Gewinner: {name}", "zh": "🏆 获胜者：{name}"},
"game_draw":              {"fa": "🤝 مساوی شد رفیق", "en": "🤝 It's a tie!", "ar": "🤝 تعادل!", "tr": "🤝 Berabere!", "ru": "🤝 Ничья!", "de": "🤝 Unentschieden!", "zh": "🤝 平局！"},
"game_expired":           {"fa": "این بازی دیگه نیست، یکی جدید بساز", "en": "Game's gone, start a new one", "ar": "انتهت اللعبة، ابدأ واحدة جديدة", "tr": "Oyun gitti, yenisini aç", "ru": "Игра закончилась, начни новую", "de": "Spiel weg, neues starten", "zh": "游戏没了，开个新的"},
"game_not_active":        {"fa": "بازی فعال نیست", "en": "Game not active", "ar": "اللعبة غير نشطة", "tr": "Oyun aktif değil", "ru": "Игра не активна", "de": "Spiel inaktiv", "zh": "游戏未激活"},
"game_already_started":   {"fa": "بازی شروع شده", "en": "Game's already started", "ar": "بدأت اللعبة", "tr": "Oyun başladı", "ru": "Игра уже идёт", "de": "Spiel läuft", "zh": "游戏已开始"},
"game_already_running":   {"fa": "یه بازی دیگه تو این گروه فعاله", "en": "A game is already running here", "ar": "هناك لعبة نشطة هنا", "tr": "Burada aktif oyun var", "ru": "Здесь уже идёт игра", "de": "Hier läuft schon ein Spiel", "zh": "这里已有游戏在跑"},
"not_your_panel":         {"fa": "این پنل مال تو نیست رفیق", "en": "Not your panel, buddy", "ar": "هذه اللوحة ليست لك", "tr": "Bu panel senin değil", "ru": "Эта панель не твоя", "de": "Nicht dein Panel", "zh": "不是你的面板"},
"not_your_game":          {"fa": "این بازی مال تو نیست", "en": "Not your game", "ar": "هذه اللعبة ليست لك", "tr": "Bu oyun senin değil", "ru": "Это не твоя игра", "de": "Nicht dein Spiel", "zh": "不是你的游戏"},
"you_have_active_game":   {"fa": "یه بازی دیگه داری، اول اونو تموم کن", "en": "You have another game open", "ar": "لديك لعبة أخرى مفتوحة", "tr": "Başka oyunun açık", "ru": "У тебя уже есть игра", "de": "Du hast noch ein Spiel offen", "zh": "你还有一局没完"},
"wait_a_bit":             {"fa": "یه لحظه صبر کن", "en": "Hold on a sec", "ar": "استنى شوي", "tr": "Bir saniye", "ru": "Погоди секунду", "de": "Warte mal", "zh": "等等"},
"invalid_move":           {"fa": "این حرکت نمی‌شه", "en": "Invalid move", "ar": "حركة غير صالحة", "tr": "Olmaz bu hamle", "ru": "Неверный ход", "de": "Geht nicht", "zh": "无效移动"},
"game_closed":            {"fa": "بستیم", "en": "Closed", "ar": "أُغلق", "tr": "Kapattık", "ru": "Закрыли", "de": "Zu", "zh": "已关闭"},
"panel_closed":           {"fa": "پنل بسته شد", "en": "Panel closed", "ar": "اللوحة أُغلقت", "tr": "Panel kapandı", "ru": "Панель закрыта", "de": "Panel zu", "zh": "面板已关闭"},
"close_game":             {"fa": "ببند", "en": "Close", "ar": "إغلاق", "tr": "Kapat", "ru": "Закрыть", "de": "Schließen", "zh": "关闭"},
"score":                  {"fa": "امتیاز", "en": "Score", "ar": "النقاط", "tr": "Puan", "ru": "Счёт", "de": "Punkte", "zh": "分数"},
"finished":               {"fa": "تمومه", "en": "Done", "ar": "انتهى", "tr": "Bitti", "ru": "Готово", "de": "Fertig", "zh": "结束"},
"turn_of":                {"fa": "نوبت", "en": "Turn", "ar": "دور", "tr": "Sıra", "ru": "Ход", "de": "Zug", "zh": "轮到"},
"waiting_players":        {"fa": "منتظر بازیکن...", "en": "Waiting for players...", "ar": "بانتظار لاعبين...", "tr": "Oyuncu bekleniyor...", "ru": "Ждём игроков...", "de": "Warte auf Spieler...", "zh": "等待玩家..."},
"player":                 {"fa": "بازیکن", "en": "Player", "ar": "لاعب", "tr": "Oyuncu", "ru": "Игрок", "de": "Spieler", "zh": "玩家"},

# ═══════════════════ Hangman
"hangman_started":   {"fa": "حدس کلمه شروع شد!", "en": "Hangman started!", "ar": "بدأت لعبة الكلمة!", "tr": "Adam Asmaca başladı!", "ru": "Виселица началась!", "de": "Galgenmännchen gestartet!", "zh": "猜词开始！"},
"each_player_lives": {"fa": "هر بازیکن {n} جان داره", "en": "Each player has {n} lives", "ar": "كل لاعب لديه {n} أرواح", "tr": "Herkesin {n} canı var", "ru": "У каждого {n} жизней", "de": "Jeder hat {n} Leben", "zh": "每人 {n} 条命"},
"guess_one_letter":  {"fa": "یه حرف بزن (مثل: م)", "en": "Guess a letter (like: A)", "ar": "خمن حرفاً (مثل: م)", "tr": "Bir harf söyle (ör: A)", "ru": "Назови букву (напр: А)", "de": "Rate einen Buchstaben", "zh": "猜个字母"},
"letter_already":    {"fa": "این حرفو گفتن دیگه!", "en": "Already guessed that!", "ar": "هذا الحرف مُجرب!", "tr": "Bu harf denendi!", "ru": "Эту букву уже назвали!", "de": "Schon geraten!", "zh": "这个字母猜过了！"},
"no_lives_left":     {"fa": "جانت تموم شده رفیق", "en": "Out of lives, buddy", "ar": "خلصت أرواحك", "tr": "Canın bitti", "ru": "Жизни кончились", "de": "Keine Leben mehr", "zh": "命用完了"},
"word_winner":       {"fa": "{name} برنده شد! کلمه: {word}", "en": "{name} wins! Word: {word}", "ar": "{name} فاز! الكلمة: {word}", "tr": "{name} kazandı! Kelime: {word}", "ru": "{name} победил! Слово: {word}", "de": "{name} gewinnt! Wort: {word}", "zh": "{name} 赢了！单词：{word}"},
"wrong_guess_lives": {"fa": "نبود {name}! {n} جان مونده", "en": "Wrong, {name}! {n} lives left", "ar": "خطأ {name}! {n} أرواح", "tr": "Yanlış {name}! {n} can", "ru": "Мимо, {name}! Осталось {n}", "de": "Falsch, {name}! Noch {n}", "zh": "错了 {name}！还剩 {n} 条命"},
"player_eliminated": {"fa": "{name} حذف شد", "en": "{name} is out", "ar": "{name} خرج", "tr": "{name} elendi", "ru": "{name} выбыл", "de": "{name} ist raus", "zh": "{name} 出局"},
"all_lost_word_was": {"fa": "همه باختن! کلمه: {word}", "en": "All lost! Word: {word}", "ar": "خسر الجميع! الكلمة: {word}", "tr": "Herkes kaybetti! Kelime: {word}", "ru": "Все проиграли! Слово: {word}", "de": "Alle verloren! Wort: {word}", "zh": "都输了！单词：{word}"},

# ═══════════════════ 2048
"you_won_2048":  {"fa": "🏆 بردی رفیق!", "en": "🏆 You won!", "ar": "🏆 فزت!", "tr": "🏆 Kazandın!", "ru": "🏆 Победа!", "de": "🏆 Gewonnen!", "zh": "🏆 你赢了！"},
"you_lost_2048": {"fa": "💀 باختی، یه بار دیگه", "en": "💀 You lost, try again", "ar": "💀 خسرت، جرب تاني", "tr": "💀 Kaybettin, tekrar dene", "ru": "💀 Проиграл, попробуй ещё", "de": "💀 Verloren, nochmal", "zh": "💀 输了，再试试"},

# ═══════════════════ SameGame
"samegame_title":  {"fa": "جفت‌ها", "en": "Same Game", "ar": "الأزواج", "tr": "Aynı Oyun", "ru": "Одинаковые", "de": "Gleiche", "zh": "消消乐"},
"no_more_moves":   {"fa": "حرکتی نمونده، تمومه", "en": "No moves left, done", "ar": "لا حركات، انتهى", "tr": "Hamle kalmadı", "ru": "Ходов нет, конец", "de": "Keine Züge, fertig", "zh": "没步了，结束"},
"need_two_blocks": {"fa": "حداقل دو تا همرنگ کنار هم لازمه", "en": "Need at least 2 same-colored together", "ar": "تحتاج لونين متطابقين", "tr": "En az 2 aynı renk lazım", "ru": "Нужно 2 одинаковых рядом", "de": "Mindestens 2 gleiche nebeneinander", "zh": "至少两个同色相邻"},

# ═══════════════════ Spuzzle
"spuzzle_title":     {"fa": "پازل کشویی", "en": "Sliding Puzzle", "ar": "لغز منزلق", "tr": "Kaydırmalı Bulmaca", "ru": "Пятнашки", "de": "Schiebepuzzle", "zh": "滑动拼图"},
"sort_numbers":      {"fa": "اعدادو مرتب کن", "en": "Sort the numbers", "ar": "رتب الأرقام", "tr": "Sayıları sırala", "ru": "Расставь числа", "de": "Sortiere die Zahlen", "zh": "排列数字"},
"puzzle_solved":     {"fa": "آفرین {name}! حلش کردی", "en": "Nice {name}! Solved it", "ar": "أحسنت {name}! حليتها", "tr": "Helal {name}! Çözdün", "ru": "Красава {name}! Решил", "de": "Stark {name}! Gelöst", "zh": "厉害 {name}！解开了"},
"solved_in_seconds": {"fa": "تو {n} ثانیه", "en": "In {n} seconds", "ar": "في {n} ثانية", "tr": "{n} saniyede", "ru": "За {n} секунд", "de": "In {n} Sekunden", "zh": "{n} 秒"},

# ═══════════════════ Doz4p
"doz4p_title":   {"fa": "دوز ۴ نفره", "en": "Tic-Tac-Toe 4P", "ar": "إكس أو ٤ لاعبين", "tr": "XOX 4K", "ru": "Крестики-нолики 4", "de": "Tic-Tac-Toe 4P", "zh": "井字棋四人"},
"doz4p_created": {"fa": "{name} یه دوز ۴ نفره ساخت!", "en": "{name} made a 4P game!", "ar": "{name} أنشأ لعبة ٤ لاعبين!", "tr": "{name} 4K oyun kurdu!", "ru": "{name} создал игру на 4!", "de": "{name} hat 4P erstellt!", "zh": "{name} 开了四人局！"},

# ═══════════════════ Hokm
"hokm_title":          {"fa": "حکم", "en": "Hokm", "ar": "حكم", "tr": "Hokm", "ru": "Хокм", "de": "Hokm", "zh": "Hokm"},
"hokm_created":        {"fa": "{name} یه حکم {mode} نفره ساخت!", "en": "{name} made a {mode}P Hokm!", "ar": "{name} أنشأ حكم {mode} لاعبين!", "tr": "{name} {mode}K Hokm kurdu!", "ru": "{name} создал Хокм на {mode}!", "de": "{name} hat Hokm {mode}P erstellt!", "zh": "{name} 开了 {mode} 人 Hokm！"},
"hokm_choose_suit":    {"fa": "حاکم، حکمت چیه؟ انتخاب کن:", "en": "Hakem, what's trump? Pick:", "ar": "أيها الحاكم، اختر الحكم:", "tr": "Hakem, koz ne? Seç:", "ru": "Хакем, какой козырь?", "de": "Hakem, Trumpf?", "zh": "Hakem，选王牌："},
"hokm_hakem":          {"fa": "حاکم", "en": "Hakem", "ar": "الحاكم", "tr": "Hakem", "ru": "Хакем", "de": "Hakem", "zh": "Hakem"},
"hokm_trump":          {"fa": "حکم", "en": "Trump", "ar": "الحكم", "tr": "Koz", "ru": "Козырь", "de": "Trumpf", "zh": "王牌"},
"hokm_show_hand":      {"fa": "دستم رو نشونم بده (خصوصی)", "en": "Show my hand (private)", "ar": "اعرض يدي (خاص)", "tr": "Elimi göster (özel)", "ru": "Показать руку (лично)", "de": "Meine Hand (privat)", "zh": "看我的手牌（私密）"},
"hokm_your_hand":      {"fa": "دستت:\n{hand}", "en": "Your hand:\n{hand}", "ar": "يدك:\n{hand}", "tr": "Elin:\n{hand}", "ru": "Твоя рука:\n{hand}", "de": "Deine Hand:\n{hand}", "zh": "你的手牌：\n{hand}"},
"hokm_no_cards":       {"fa": "کارتی نداری", "en": "No cards", "ar": "لا بطاقات", "tr": "Kart yok", "ru": "Нет карт", "de": "Keine Karten", "zh": "没牌"},
"hokm_must_follow":    {"fa": "باید از خال {suit} بازی کنی!", "en": "You must play {suit}!", "ar": "يجب أن تلعب {suit}!", "tr": "{suit} oynamalısın!", "ru": "Играй {suit}!", "de": "Spiel {suit}!", "zh": "要出 {suit}！"},
"hokm_invalid_card":   {"fa": "شماره کارت غلطه", "en": "Wrong card number", "ar": "رقم خاطئ", "tr": "Yanlış kart no", "ru": "Неверный номер", "de": "Falsche Nummer", "zh": "牌号错"},
"hokm_not_hakem":      {"fa": "تو حاکم نیستی رفیق", "en": "You're not Hakem", "ar": "أنت لست الحاكم", "tr": "Sen Hakem değilsin", "ru": "Ты не хакем", "de": "Du bist nicht Hakem", "zh": "你不是 Hakem"},
"hokm_not_choosing":   {"fa": "الان وقت انتخاب نیست", "en": "Not pick time", "ar": "ليس وقت الاختيار", "tr": "Seçim zamanı değil", "ru": "Не время выбирать", "de": "Nicht Auswahlzeit", "zh": "不是选的时候"},
"hokm_won_trick":      {"fa": "این دست رفت به {name}", "en": "Trick to {name}", "ar": "الدور لـ{name}", "tr": "El {name}'in", "ru": "Взятка {name}", "de": "Stich an {name}", "zh": "{name} 拿下这墩"},
"hokm_round_finished": {"fa": "دست تموم شد! برنده: {name}\n\nحاکم جدید: {hakem}\nمنتظر انتخاب حکم...", "en": "Round done! Winner: {name}\n\nNew Hakem: {hakem}\nWaiting for trump...", "ar": "انتهى الدور! الفائز: {name}\n\nالحاكم الجديد: {hakem}\nفي انتظار الحكم...", "tr": "El bitti! Kazanan: {name}\n\nYeni Hakem: {hakem}\nKoz bekleniyor...", "ru": "Раунд готов! Победил: {name}\n\nНовый Хакем: {hakem}\nЖдём козырь...", "de": "Runde durch! Gewinner: {name}\n\nNeuer Hakem: {hakem}\nWarte auf Trumpf...", "zh": "本轮结束！赢家：{name}\n\n新 Hakem：{hakem}\n等待选王牌..."},
"hokm_team_a":         {"fa": "تیم ۱", "en": "Team 1", "ar": "الفريق ١", "tr": "Takım 1", "ru": "Команда 1", "de": "Team 1", "zh": "队伍 1"},
"hokm_team_b":         {"fa": "تیم ۲", "en": "Team 2", "ar": "الفريق ٢", "tr": "Takım 2", "ru": "Команда 2", "de": "Team 2", "zh": "队伍 2"},
"hokm_played_card":    {"fa": "کارت بازی‌شده", "en": "Played", "ar": "الملعوبة", "tr": "Oynanan", "ru": "Сыграно", "de": "Gespielt", "zh": "已出"},
"hokm_trick_score":    {"fa": "دست", "en": "Tricks", "ar": "الدورات", "tr": "Eller", "ru": "Взятки", "de": "Stiche", "zh": "墩数"},
"hokm_total_score":    {"fa": "کل", "en": "Total", "ar": "المجموع", "tr": "Toplam", "ru": "Итого", "de": "Gesamt", "zh": "总分"},
"hokm_game_won":       {"fa": "بازی تموم شد! {name} برد", "en": "Game done! {name} wins", "ar": "انتهت! {name} فاز", "tr": "Oyun bitti! {name} kazandı", "ru": "Игра окончена! {name} победил", "de": "Spiel vorbei! {name} gewinnt", "zh": "游戏结束！{name} 赢了"},
"hokm_wait":           {"fa": "صبر کن...", "en": "Wait...", "ar": "انتظر...", "tr": "Bekle...", "ru": "Погоди...", "de": "Warte...", "zh": "等等..."},

# ═══════════════════ Dooz
"dooz_title":     {"fa": "دوز", "en": "Tic-Tac-Toe", "ar": "إكس أو", "tr": "XOX", "ru": "Крестики-нолики", "de": "Tic-Tac-Toe", "zh": "井字棋"},
"dooz_created":   {"fa": "{name} یه دوز ساخت!", "en": "{name} made a Tic-Tac-Toe!", "ar": "{name} أنشأ إكس أو!", "tr": "{name} XOX kurdu!", "ru": "{name} создал крестики-нолики!", "de": "{name} hat Tic-Tac-Toe erstellt!", "zh": "{name} 开了井字棋！"},
"dooz_started":   {"fa": "{name1} ⚔️ {name2}\n\nبزن بریم!", "en": "{name1} ⚔️ {name2}\n\nLet's go!", "ar": "{name1} ⚔️ {name2}\n\nيلا!", "tr": "{name1} ⚔️ {name2}\n\nBaşlayalım!", "ru": "{name1} ⚔️ {name2}\n\nПогнали!", "de": "{name1} ⚔️ {name2}\n\nLos geht's!", "zh": "{name1} ⚔️ {name2}\n\n开打！"},
"dooz_your_turn": {"fa": "نوبت {name} ({symbol})", "en": "{name}'s turn ({symbol})", "ar": "دور {name} ({symbol})", "tr": "Sıra {name}'de ({symbol})", "ru": "Ход {name} ({symbol})", "de": "{name} dran ({symbol})", "zh": "轮到 {name}（{symbol}）"},
"dooz_won":       {"fa": "🏆 {name} برد!", "en": "🏆 {name} wins!", "ar": "🏆 {name} فاز!", "tr": "🏆 {name} kazandı!", "ru": "🏆 {name} победил!", "de": "🏆 {name} gewinnt!", "zh": "🏆 {name} 赢了！"},

# ═══════════════════ Connect4
"c4_title":     {"fa": "چهار در ردیف", "en": "Connect Four", "ar": "أربعة في صف", "tr": "Dörtlü Bağla", "ru": "Четыре в ряд", "de": "Vier gewinnt", "zh": "四子棋"},
"c4_created":   {"fa": "{name} یه چهار در ردیف ساخت!", "en": "{name} made a Connect Four!", "ar": "{name} أنشأ أربعة في صف!", "tr": "{name} Dörtlü Bağla kurdu!", "ru": "{name} создал Четыре в ряд!", "de": "{name} hat Vier gewinnt erstellt!", "zh": "{name} 开了四子棋！"},
"c4_col_full":  {"fa": "این ستون پره", "en": "This column is full", "ar": "هذا العمود ممتلئ", "tr": "Bu sütun dolu", "ru": "Столбец полон", "de": "Spalte voll", "zh": "这列满了"},

# ═══════════════════ RPS
"rps_title":           {"fa": "سنگ کاغذ قیچی", "en": "Rock Paper Scissors", "ar": "حجر ورقة مقص", "tr": "Taş Kağıt Makas", "ru": "Камень ножницы бумага", "de": "Schere Stein Papier", "zh": "石头剪刀布"},
"rps_ask_rounds":      {"fa": "چند راند برنده بشه؟ (۱ تا ۱۰) — یه عدد بفرست:", "en": "How many rounds to win? (1-10) — send a number:", "ar": "كم جولة للفوز؟ (1-10) — أرسل رقماً:", "tr": "Kaç tur kazanmalı? (1-10) — sayı gönder:", "ru": "Сколько раундов до победы? (1-10) — отправь число:", "de": "Wie viele Runden zum Sieg? (1-10) — send a number:", "zh": "多少轮获胜？（1-10）— 发数字："},
"rps_invalid_rounds":  {"fa": "بین ۱ تا ۱۰ بفرست رفیق!", "en": "Between 1 and 10, buddy!", "ar": "بين 1 و10 يا صاحبي!", "tr": "1-10 arası gönder!", "ru": "От 1 до 10, дружище!", "de": "Zwischen 1 und 10!", "zh": "1 到 10，兄弟！"},
"rps_created":         {"fa": "{name} یه سنگ کاغذ قیچی ساخت! ({n} راند) — بیا تو!", "en": "{name} started RPS! ({n} rounds) — jump in!", "ar": "{name} بدأ حجر ورقة مقص! ({n} جولات) — انضم!", "tr": "{name} TKM başlattı! ({n} tur) — katıl!", "ru": "{name} начал КНБ! ({n} раундов) — заходи!", "de": "{name} hat SSP gestartet! ({n} Runden) — mach mit!", "zh": "{name} 开了石头剪刀布！（{n} 轮）— 快来！"},
"rps_started":         {"fa": "{name1} ⚔️ {name2}\n\n{n} راند ببر تا ببری!", "en": "{name1} ⚔️ {name2}\n\nFirst to {n} rounds wins!", "ar": "{name1} ⚔️ {name2}\n\nافز {n} جولات!", "tr": "{name1} ⚔️ {name2}\n\n{n} tur kazanan alır!", "ru": "{name1} ⚔️ {name2}\n\nДо {n} побед!", "de": "{name1} ⚔️ {name2}\n\nBis {n} Runden!", "zh": "{name1} ⚔️ {name2}\n\n先到 {n} 轮者胜！"},
"rps_rock":            {"fa": "سنگ", "en": "Rock", "ar": "حجر", "tr": "Taş", "ru": "Камень", "de": "Stein", "zh": "石头"},
"rps_paper":           {"fa": "کاغذ", "en": "Paper", "ar": "ورقة", "tr": "Kağıt", "ru": "Бумага", "de": "Papier", "zh": "布"},
"rps_scissors":        {"fa": "قیچی", "en": "Scissors", "ar": "مقص", "tr": "Makas", "ru": "Ножницы", "de": "Schere", "zh": "剪刀"},
"rps_already_chosen":  {"fa": "قبلاً انتخاب کردی", "en": "Already chose!", "ar": "اخترت بالفعل", "tr": "Zaten seçtin", "ru": "Уже выбрал", "de": "Schon gewählt", "zh": "已选过了"},
"rps_chosen":          {"fa": "ثبت شد", "en": "Locked in", "ar": "تم", "tr": "Kaydedildi", "ru": "Принято", "de": "Gespeichert", "zh": "已记录"},
"rps_waiting":         {"fa": "بازی در جریانه...\n{name1}: {s1}\n{name2}: {s2}\nمنتظر حریف...", "en": "Game running...\n{name1}: {s1}\n{name2}: {s2}\nWaiting for opponent...", "ar": "اللعبة جارية...\n{name1}: {s1}\n{name2}: {s2}\nبانتظار الخصم...", "tr": "Oyun sürüyor...\n{name1}: {s1}\n{name2}: {s2}\nRakip bekleniyor...", "ru": "Игра идёт...\n{name1}: {s1}\n{name2}: {s2}\nЖдём соперника...", "de": "Spiel läuft...\n{name1}: {s1}\n{name2}: {s2}\nWarte auf Gegner...", "zh": "游戏进行中...\n{name1}: {s1}\n{name2}: {s2}\n等待对手..."},
"rps_result":          {"fa": "نتیجه:\n{name1}: {c1}\n{name2}: {c2}", "en": "Result:\n{name1}: {c1}\n{name2}: {c2}", "ar": "النتيجة:\n{name1}: {c1}\n{name2}: {c2}", "tr": "Sonuç:\n{name1}: {c1}\n{name2}: {c2}", "ru": "Результат:\n{name1}: {c1}\n{name2}: {c2}", "de": "Ergebnis:\n{name1}: {c1}\n{name2}: {c2}", "zh": "结果：\n{name1}: {c1}\n{name2}: {c2}"},
"rps_chosen_status":   {"fa": "✓", "en": "✓", "ar": "✓", "tr": "✓", "ru": "✓", "de": "✓", "zh": "✓"},
"rps_waiting_status":  {"fa": "...", "en": "...", "ar": "...", "tr": "...", "ru": "...", "de": "...", "zh": "..."},
"rps_score_line":      {"fa": "{n1}: {s1} | {n2}: {s2} — تا {needed}", "en": "{n1}: {s1} | {n2}: {s2} — first to {needed}", "ar": "{n1}: {s1} | {n2}: {s2} — حتى {needed}", "tr": "{n1}: {s1} | {n2}: {s2} — {needed} olan", "ru": "{n1}: {s1} | {n2}: {s2} — до {needed}", "de": "{n1}: {s1} | {n2}: {s2} — bis {needed}", "zh": "{n1}: {s1} | {n2}: {s2} — 先到 {needed}"},
"rps_next_round":      {"fa": "راند بعدی! دوباره انتخاب کن:", "en": "Next round! Pick again:", "ar": "الجولة التالية! اختر:", "tr": "Sonraki tur! Tekrar seç:", "ru": "Следующий раунд! Выбирай:", "de": "Nächste Runde! Wähle:", "zh": "下一轮！再选："},
"rps_game_winner":     {"fa": "🏆 {name} بازی رو برد!", "en": "🏆 {name} takes it!", "ar": "🏆 {name} فاز!", "tr": "🏆 {name} kazandı!", "ru": "🏆 {name} победил!", "de": "🏆 {name} gewinnt!", "zh": "🏆 {name} 拿下了！"},
"rps_final_score":     {"fa": "{n1}: {s1} | {n2}: {s2}", "en": "{n1}: {s1} | {n2}: {s2}", "ar": "{n1}: {s1} | {n2}: {s2}", "tr": "{n1}: {s1} | {n2}: {s2}", "ru": "{n1}: {s1} | {n2}: {s2}", "de": "{n1}: {s1} | {n2}: {s2}", "zh": "{n1}: {s1} | {n2}: {s2}"},

# ═══════════════════ Memory
"memory_title":           {"fa": "بازی حافظه", "en": "Memory Game", "ar": "لعبة الذاكرة", "tr": "Hafıza Oyunu", "ru": "Игра памяти", "de": "Memory", "zh": "记忆游戏"},
"memory_created":         {"fa": "{name} یه بازی حافظه ساخت ({size})!", "en": "{name} made a memory game ({size})!", "ar": "{name} أنشأ لعبة ذاكرة ({size})!", "tr": "{name} hafıza oyunu kurdu ({size})!", "ru": "{name} создал игру памяти ({size})!", "de": "{name} hat Memory erstellt ({size})!", "zh": "{name} 开了记忆游戏（{size}）！"},
"memory_already_flipped": {"fa": "این کارت باز شده", "en": "Card already flipped", "ar": "الكرت مفتوح", "tr": "Bu kart açık", "ru": "Карта открыта", "de": "Karte offen", "zh": "卡片已翻"},
"memory_matched":         {"fa": "✅ جفت شد!", "en": "✅ Matched!", "ar": "✅ تطابق!", "tr": "✅ Eşleşti!", "ru": "✅ Пара!", "de": "✅ Paar!", "zh": "✅ 配对！"},
"memory_no_match":        {"fa": "❌ جفت نشد", "en": "❌ No match", "ar": "❌ لا تطابق", "tr": "❌ Eşleşmedi", "ru": "❌ Не пара", "de": "❌ Kein Paar", "zh": "❌ 没配上"},
"memory_final_score":     {"fa": "امتیاز نهایی:\n{name1}: {s1}\n{name2}: {s2}", "en": "Final score:\n{name1}: {s1}\n{name2}: {s2}", "ar": "النتيجة النهائية:\n{name1}: {s1}\n{name2}: {s2}", "tr": "Son puan:\n{name1}: {s1}\n{name2}: {s2}", "ru": "Итог:\n{name1}: {s1}\n{name2}: {s2}", "de": "Endstand:\n{name1}: {s1}\n{name2}: {s2}", "zh": "最终比分：\n{name1}: {s1}\n{name2}: {s2}"},
"memory_turn":            {"fa": "نوبت {name}", "en": "{name}'s turn", "ar": "دور {name}", "tr": "Sıra {name}'de", "ru": "Ход {name}", "de": "{name} dran", "zh": "轮到 {name}"},
"memory_level_easy":      {"fa": "آسان", "en": "Easy", "ar": "سهل", "tr": "Kolay", "ru": "Легко", "de": "Leicht", "zh": "简单"},
"memory_level_med":       {"fa": "متوسط", "en": "Medium", "ar": "متوسط", "tr": "Orta", "ru": "Средне", "de": "Mittel", "zh": "中等"},
"memory_level_hard":      {"fa": "سخت", "en": "Hard", "ar": "صعب", "tr": "Zor", "ru": "Сложно", "de": "Schwer", "zh": "困难"},
"memory_level_pro":       {"fa": "حرفه‌ای", "en": "Pro", "ar": "محترف", "tr": "Pro", "ru": "Про", "de": "Profi", "zh": "专业"},
"memory_choose_mode":     {"fa": "تنهایی یا گروهی؟", "en": "Solo or with a friend?", "ar": "فردي أم جماعي؟", "tr": "Tek mi grup mu?", "ru": "Соло или с кем-то?", "de": "Solo oder mit jemand?", "zh": "单人还是多人？"},
"memory_solo_btn":        {"fa": "تنهایی (تمرین)", "en": "Solo (practice)", "ar": "فردي (تمرين)", "tr": "Tek (antrenman)", "ru": "Соло (практика)", "de": "Solo (Übung)", "zh": "单人（练习）"},
"memory_multi_btn":       {"fa": "گروهی (دونفره)", "en": "Multiplayer (1v1)", "ar": "جماعي (1 ضد 1)", "tr": "Grup (1v1)", "ru": "Группа (1 на 1)", "de": "Gruppe (1v1)", "zh": "多人（1v1）"},
"memory_moves":           {"fa": "حرکت: {n}", "en": "Moves: {n}", "ar": "حركات: {n}", "tr": "Hamle: {n}", "ru": "Ходы: {n}", "de": "Züge: {n}", "zh": "步数：{n}"},
"memory_solo_hint":       {"fa": "کارتا رو برگردون و جفت پیدا کن — هرچی کمتر حرکت، بهتر!", "en": "Flip cards, find pairs — fewer moves = better!", "ar": "اقلب وطابق — حركات أقل = أفضل!", "tr": "Kartları çevir, eşleri bul — az hamle = iyi!", "ru": "Переворачивай и находи пары — меньше ходов = лучше!", "de": "Karten umdrehen, Paare finden — weniger Züge = besser!", "zh": "翻牌找配对 — 步数越少越好！"},
"memory_solo_done":       {"fa": "تمومه! {moves} حرکت طول کشید", "en": "Done! Took {moves} moves", "ar": "خلصت! {moves} حركة", "tr": "Bitti! {moves} hamle", "ru": "Готово! {moves} ходов", "de": "Fertig! {moves} Züge", "zh": "完成！用了 {moves} 步"},

# ═══════════════════ Gardone
"gardone_title":          {"fa": "گردونه شانس", "en": "Lucky Wheel", "ar": "عجلة الحظ", "tr": "Çarkıfelek", "ru": "Колесо удачи", "de": "Glücksrad", "zh": "幸运轮盘"},
"gardone_active":         {"fa": "گردونه فعاله! بیا تو شانست رو امتحان کن", "en": "Wheel's live! Join and try your luck", "ar": "العجلة شغالة! انضم وجرب حظك", "tr": "Çark canlı! Gel şansını dene", "ru": "Колесо запущено! Зайди и испытай удачу", "de": "Rad läuft! Mach mit und probier dein Glück", "zh": "轮盘开转！进来碰碰运气"},
"gardone_join":           {"fa": "شرکت می‌کنم", "en": "I'm In", "ar": "أنا معك", "tr": "Buradayım", "ru": "Я в деле", "de": "Bin dabei", "zh": "我来"},
"gardone_spin":           {"fa": "بچرخون", "en": "Spin It", "ar": "أدرها", "tr": "Çevir", "ru": "Крути", "de": "Drehen", "zh": "转起来"},
"gardone_cancel":         {"fa": "لغو گردونه", "en": "Cancel Wheel", "ar": "إلغاء العجلة", "tr": "Çarkı İptal", "ru": "Отменить", "de": "Abbrechen", "zh": "取消轮盘"},
"gardone_joined":         {"fa": "ثبت شد! بمون تا قرعه‌کشی", "en": "You're in! Stick around", "ar": "تم! انتظر القرعة", "tr": "Girdin! Çekilişi bekle", "ru": "Ты в деле! Оставайся", "de": "Du bist drin! Bleib dran", "zh": "你进了！等着抽奖"},
"gardone_already_joined": {"fa": "تو که هستی دیگه", "en": "You're already in", "ar": "أنت منضم", "tr": "Zaten girdin", "ru": "Ты уже там", "de": "Schon dabei", "zh": "你已在里面"},
"gardone_winner":         {"fa": "🏆 برنده‌ها!", "en": "🏆 Winners!", "ar": "🏆 الفائزون!", "tr": "🏆 Kazananlar!", "ru": "🏆 Победители!", "de": "🏆 Gewinner!", "zh": "🏆 获胜者！"},
"gardone_empty":          {"fa": "هیچ‌کس نیومد تو", "en": "Nobody joined", "ar": "ما انضم أحد", "tr": "Kimse katılmadı", "ru": "Никто не зашёл", "de": "Niemand drin", "zh": "没人参加"},
"gardone_only_starter":   {"fa": "فقط سازنده می‌تونه بچرخونه", "en": "Only the starter can spin", "ar": "فقط المنشئ يديرها", "tr": "Sadece kuran çevirir", "ru": "Только создатель крутит", "de": "Nur der Ersteller dreht", "zh": "只有创建者能转"},
"gardone_spinning":       {"fa": "داره می‌چرخه...", "en": "Spinning...", "ar": "تدور...", "tr": "Dönüyor...", "ru": "Крутится...", "de": "Dreht...", "zh": "转着呢..."},
"gardone_cancelled":      {"fa": "گردونه لغو شد", "en": "Wheel cancelled", "ar": "العجلة أُلغيت", "tr": "Çark iptal edildi", "ru": "Колесо отменено", "de": "Rad abgebrochen", "zh": "轮盘已取消"},
"gardone_participants":   {"fa": "شرکت‌کننده‌ها ({n} نفر)", "en": "Players ({n})", "ar": "المشاركون ({n})", "tr": "Katılımcılar ({n})", "ru": "Участники ({n})", "de": "Teilnehmer ({n})", "zh": "参与者（{n} 位）"},
"gardone_nobody":         {"fa": "هنوز کسی نیست", "en": "Nobody yet", "ar": "لا أحد بعد", "tr": "Kimse yok", "ru": "Пока никого", "de": "Noch niemand", "zh": "还没人"},
"gardone_ask_count":      {"fa": "چند نفر برنده بشن؟ (۱ تا ۱۰) — عدد بفرست:", "en": "How many winners? (1-10) — send a number:", "ar": "كم فائزاً؟ (1-10) — أرسل رقماً:", "tr": "Kaç kazanan? (1-10) — sayı gönder:", "ru": "Сколько победителей? (1-10) — отправь число:", "de": "Wie viele Gewinner? (1-10) — send a number:", "zh": "几位获胜者？（1-10）— 发数字："},
"gardone_invalid_count":  {"fa": "بین ۱ تا ۱۰ بفرست!", "en": "Between 1 and 10!", "ar": "بين 1 و10!", "tr": "1-10 arası!", "ru": "От 1 до 10!", "de": "Zwischen 1 und 10!", "zh": "1 到 10！"},
"gardone_winner_count":   {"fa": "تعداد برنده: {n} نفر", "en": "Winners: {n}", "ar": "الفائزون: {n}", "tr": "Kazanan: {n}", "ru": "Победителей: {n}", "de": "Gewinner: {n}", "zh": "获胜者：{n}"},

# ═══════════════════ Anonymous
"eteraf_default_text":  {"fa": "یه اعتراف جدید شروع شد. بیا ناشناس حرفت رو بزن", "en": "New confession started. Speak anonymously", "ar": "اعتراف جديد بدأ. تكلم مجهولاً", "tr": "Yeni itiraf başladı. Anonim konuş", "ru": "Новое признание началось. Говори анонимно", "de": "Neues Geständnis. Sprich anonym", "zh": "新表白开始。匿名说吧"},
"eteraf_send_btn":      {"fa": "بفرست ناشناس", "en": "Send Anonymously", "ar": "أرسل مجهولاً", "tr": "Anonim Gönder", "ru": "Отправить анонимно", "de": "Anonym senden", "zh": "匿名发送"},
"eteraf_enter_text":    {"fa": "متن دلخواهت رو بفرست تا اعتراف شروع بشه.\nبرای لغو /cancel", "en": "Send your custom text to start confession.\n/cancel to cancel", "ar": "أرسل نصك للاعتراف.\n/cancel للإلغاء", "tr": "İtiraf metnini gönder.\n/cancel iptal", "ru": "Отправь свой текст для признания.\n/cancel отмена", "de": "Sende deinen Text.\n/cancel abbrechen", "zh": "发你的自定义文本。\n/cancel 取消"},
"eteraf_write":         {"fa": "حرفت رو بنویس تا ناشناس بره تو گروه...", "en": "Write your message to go anonymously...", "ar": "اكتب رسالتك لتذهب مجهولة...", "tr": "Mesajını yaz, anonim gitsin...", "ru": "Напиши сообщение, уйдёт анонимно...", "de": "Schreib deine Nachricht anonym...", "zh": "写下你的话匿名发出去..."},
"eteraf_sent":          {"fa": "✅ ناشناس فرستاده شد", "en": "✅ Sent anonymously", "ar": "✅ أُرسل مجهولاً", "tr": "✅ Anonim gönderildi", "ru": "✅ Отправлено анонимно", "de": "✅ Anonym gesendet", "zh": "✅ 已匿名发送"},
"eteraf_header":        {"fa": "#اعتراف_ناشناس 🤫", "en": "#Anonymous_Confession 🤫", "ar": "#اعتراف_مجهول 🤫", "tr": "#Anonim_İtiraf 🤫", "ru": "#Анонимное_Признание 🤫", "de": "#Anonymes_Geständnis 🤫", "zh": "#匿名表白 🤫"},
"gharch_send_btn":      {"fa": "بفرست ناشناس", "en": "Send Anonymously", "ar": "أرسل مجهولاً", "tr": "Anonim Gönder", "ru": "Отправить анонимно", "de": "Anonym senden", "zh": "匿名发送"},
"gharch_choose_god":    {"fa": "یوزرنیم گاد رو بفرست (مثل: @GodUsername).\nبرای لغو /cancel", "en": "Send God's username (e.g.: @GodUsername).\n/cancel to cancel", "ar": "أرسل معرف الإله (@GodUsername).\n/cancel للإلغاء", "tr": "God'un kullanıcı adını gönder (@GodUsername).\n/cancel iptal", "ru": "Отправь юзернейм Бога (@GodUsername).\n/cancel отмена", "de": "Sende God's Username (@GodUsername).\n/cancel abbrechen", "zh": "发上帝用户名（@GodUsername）。\n/cancel 取消"},
"gharch_confirm_god":   {"fa": "{god} جان، تو گاد شدی. تایید کن:", "en": "Hey {god}, you're the God. Confirm:", "ar": "{god}، أنت الإله. أكد:", "tr": "{god}, sen God'sun. Onayla:", "ru": "{god}, ты Бог. Подтверди:", "de": "{god}, du bist Gott. Bestätige:", "zh": "{god}，你是上帝。确认："},
"gharch_confirm_btn":   {"fa": "آره منم", "en": "Yep, that's me", "ar": "أكيد أنا", "tr": "Evet benim", "ru": "Да, это я", "de": "Ja, ich bin's", "zh": "对，是我"},
"gharch_you_are_god":   {"fa": "تو گاد شدی!", "en": "You're the God now!", "ar": "أنت الإله الآن!", "tr": "Artık God'sun!", "ru": "Теперь ты Бог!", "de": "Du bist jetzt Gott!", "zh": "你现在是上帝了！"},
"gharch_not_god":       {"fa": "این درخواست مال تو نیست یا یوزرنیمت ست نشده", "en": "Not for you or username not set", "ar": "ليس لك أو المعرف غير معد", "tr": "Senin için değil veya kullanıcı adı yok", "ru": "Не твоё или юзернейм не задан", "de": "Nicht für dich oder Username fehlt", "zh": "不是给你的或没设用户名"},
"gharch_started":       {"fa": "بازی قارچ شروع شد!\n\nدکمه رو بزن و حرفت رو ناشناس بگو!\n\nفقط گاد {god} می‌بینه کی هستی.", "en": "Mushroom game started!\n\nHit the button, speak anonymously!\n\nOnly God {god} sees who you are.", "ar": "لعبة الفطر بدأت!\n\nاضغط وتكلم مجهولاً!\n\nفقط {god} يرى من أنت.", "tr": "Mantar oyunu başladı!\n\nButona bas, anonim konuş!\n\nSadece {god} kim olduğunu görür.", "ru": "Грибная игра началась!\n\nЖми кнопку, говори анонимно!\n\nТолько {god} видит тебя.", "de": "Pilzspiel gestartet!\n\nDrück den Button, sprich anonym!\n\nNur {god} sieht wer du bist.", "zh": "蘑菇游戏开始！\n\n按按钮匿名说话！\n\n只有 {god} 能看到你是谁。"},
"gharch_sent":          {"fa": "✅ ناشناس رفت", "en": "✅ Sent anonymously", "ar": "✅ أُرسل مجهولاً", "tr": "✅ Anonim gitti", "ru": "✅ Ушло анонимно", "de": "✅ Anonym gesendet", "zh": "✅ 已匿名发出"},
"gharch_received":      {"fa": "#پیام_ناشناس 🍄", "en": "#Anonymous_Msg 🍄", "ar": "#رسالة_مجهولة 🍄", "tr": "#Anonim_Mesaj 🍄", "ru": "#Анонимное_Сообщение 🍄", "de": "#Anonyme_Nachricht 🍄", "zh": "#匿名消息 🍄"},
"gharch_god_report":    {"fa": "📝 پیام ناشناس جدید\n\n👤 فرستنده:\n- اسم: {name}\n- یوزر: @{uname}\n- آیدی: {uid}\n\n📜 متن:\n{msg}", "en": "📝 New anonymous message\n\n👤 Sender:\n- Name: {name}\n- Username: @{uname}\n- ID: {uid}\n\n📜 Text:\n{msg}", "ar": "📝 رسالة مجهولة جديدة\n\n👤 المرسل:\n- الاسم: {name}\n- المعرف: @{uname}\n- الآيدي: {uid}\n\n📜 النص:\n{msg}", "tr": "📝 Yeni anonim mesaj\n\n👤 Gönderen:\n- Ad: {name}\n- Kullanıcı: @{uname}\n- ID: {uid}\n\n📜 Metin:\n{msg}", "ru": "📝 Новое анонимное\n\n👤 Отправитель:\n- Имя: {name}\n- Юзер: @{uname}\n- ID: {uid}\n\n📜 Текст:\n{msg}", "de": "📝 Neue anonyme Nachricht\n\n👤 Absender:\n- Name: {name}\n- Username: @{uname}\n- ID: {uid}\n\n📜 Text:\n{msg}", "zh": "📝 新的匿名消息\n\n👤 发送者：\n- 姓名：{name}\n- 用户名：@{uname}\n- ID：{uid}\n\n📜 文本：\n{msg}"},
"gharch_not_active":    {"fa": "این قارچ دیگه فعال نیست", "en": "This mushroom is dead", "ar": "هذا الفطر ميت", "tr": "Bu mantar öldü", "ru": "Этот гриб мёртв", "de": "Dieser Pilz ist tot", "zh": "这个蘑菇凉了"},
"gharch_need_start":    {"fa": "اول از دکمه گروه شروع کن", "en": "Start from the group button first", "ar": "ابدأ من زر المجموعة", "tr": "Önce grup butonundan başla", "ru": "Начни с кнопки в группе", "de": "Starte über den Gruppen-Button", "zh": "先从群按钮开始"},
"gharch_only_admin":    {"fa": "فقط ادمین‌ها می‌تونن شروع کنن", "en": "Only admins can start", "ar": "فقط المشرفون يبدأون", "tr": "Sadece yöneticiler başlatır", "ru": "Только админы запускают", "de": "Nur Admins starten", "zh": "只有管理员能开"},
"gharch_invalid_username": {"fa": "فرمت غلطه، با @ بفرست", "en": "Wrong format, send with @", "ar": "تنسيق خاطئ، أرسل مع @", "tr": "Yanlış format, @ ile gönder", "ru": "Неверный формат, с @", "de": "Falsches Format, mit @", "zh": "格式错，带 @ 发"},

# ═══════════════════ Stop
"only_admin":       {"fa": "فقط ادمین‌ها", "en": "Admins only", "ar": "للمشرفين فقط", "tr": "Sadece yöneticiler", "ru": "Только админы", "de": "Nur Admins", "zh": "仅管理员"},
"stopped_n_games":  {"fa": "✅ {n} بازی لغو شد", "en": "✅ Stopped {n} games", "ar": "✅ أُوقفت {n} لعبة", "tr": "✅ {n} oyun durdu", "ru": "✅ Остановлено игр: {n}", "de": "✅ {n} Spiele gestoppt", "zh": "✅ 停止了 {n} 个游戏"},
"no_active_games":  {"fa": "بازی فعالی نیست", "en": "No active games", "ar": "لا ألعاب نشطة", "tr": "Aktif oyun yok", "ru": "Нет активных игр", "de": "Keine aktiven Spiele", "zh": "没有活跃游戏"},

# ═══════════════════ خطاها
"banned":          {"fa": "🚫 حسابت بسته‌ست", "en": "🚫 Account banned", "ar": "🚫 حسابك محظور", "tr": "🚫 Hesabın yasak", "ru": "🚫 Аккаунт заблокирован", "de": "🚫 Konto gesperrt", "zh": "🚫 账号被封"},
"need_join":       {"fa": "❗ اول بیا کانالمون", "en": "❗ Join our channel first", "ar": "❗ انضم لقناتنا أولاً", "tr": "❗ Önce kanala katıl", "ru": "❗ Сначала подпишись", "de": "❗ Tritt zuerst bei", "zh": "❗ 先加频道"},
"need_active_sub": {"fa": "اشتراکت تموم شده", "en": "Subscription expired", "ar": "انتهى اشتراكك", "tr": "Aboneliğin bitti", "ru": "Подписка истекла", "de": "Abo abgelaufen", "zh": "订阅已过期"},
"not_member":      {"fa": "هنوز عضو نشدی!", "en": "Not a member yet!", "ar": "لست عضواً بعد!", "tr": "Henüz üye değilsin!", "ru": "Ты ещё не вступил!", "de": "Noch nicht dabei!", "zh": "还不是成员！"},
"error_occured":   {"fa": "یه مشکلی پیش اومد، دوباره امتحان کن", "en": "Something broke, try again", "ar": "حدث خطأ، جرب مجدداً", "tr": "Bir sorun oldu, tekrar dene", "ru": "Что-то сломалось, попробуй ещё", "de": "Etwas ist schief, versuch nochmal", "zh": "出错了，再试试"},

# ═══════════════════ پنل ادمین
"admin_panel":    {"fa": "پنل ادمین", "en": "Admin Panel", "ar": "لوحة المشرف", "tr": "Yönetici Paneli", "ru": "Панель админа", "de": "Admin-Panel", "zh": "管理面板"},
"admin_only":     {"fa": "دسترسی نداری", "en": "No access", "ar": "لا وصول", "tr": "Erişim yok", "ru": "Нет доступа", "de": "Kein Zugriff", "zh": "无权限"},
"admin_stats":    {"fa": "آمار ربات", "en": "Bot Stats", "ar": "إحصائيات", "tr": "Bot İstatistik", "ru": "Статистика", "de": "Bot-Statistik", "zh": "机器人统计"},
"admin_users":    {"fa": "چک کاربر", "en": "Check User", "ar": "فحص مستخدم", "tr": "Kullanıcı", "ru": "Проверить юзера", "de": "Nutzer prüfen", "zh": "检查用户"},
"admin_defpacks": {"fa": "پک پیش‌فرض", "en": "Default Packs", "ar": "الباقات", "tr": "Varsayılan", "ru": "Пакеты", "de": "Packs", "zh": "默认包"},
"admin_filters":  {"fa": "فیلترها", "en": "Filters", "ar": "الفلاتر", "tr": "Filtreler", "ru": "Фильтры", "de": "Filter", "zh": "过滤器"},
"admin_locks":    {"fa": "قفل و اسپانسری", "en": "Locks & Sponsors", "ar": "الأقفال", "tr": "Kilitler", "ru": "Блокировки", "de": "Sperren", "zh": "锁定与赞助"},
"admin_bcast":    {"fa": "ارسال همگانی", "en": "Broadcast", "ar": "بث جماعي", "tr": "Yayın", "ru": "Рассылка", "de": "Rundsendung", "zh": "群发"},
"admin_refs":     {"fa": "زیرمجموعه‌ها", "en": "Referrals", "ar": "الإحالات", "tr": "Referanslar", "ru": "Рефералы", "de": "Empfehlungen", "zh": "推荐"},
"admin_settings": {"fa": "تنظیمات", "en": "Settings", "ar": "الإعدادات", "tr": "Ayarlar", "ru": "Настройки", "de": "Einstellungen", "zh": "设置"},
"admin_admins":   {"fa": "مدیریت ادمین‌ها", "en": "Manage Admins", "ar": "إدارة المشرفين", "tr": "Yöneticiler", "ru": "Управление админами", "de": "Admins verwalten", "zh": "管理员管理"},
"admin_backup":   {"fa": "بکاپ و ریستور", "en": "Backup & Restore", "ar": "نسخ احتياطي", "tr": "Yedekle", "ru": "Бэкап", "de": "Backup", "zh": "备份与恢复"},

# ═══════════════════ PM Welcome
"pm_welcome_title":       {"fa": "سلام {name}! خوش اومدی 👋", "en": "Hey {name}! Welcome aboard 👋", "ar": "أهلاً {name}! نورت 👋", "tr": "Selam {name}! Hoş geldin 👋", "ru": "Привет, {name}! Заходи 👋", "de": "Hey {name}! Willkommen 👋", "zh": "嘿 {name}！欢迎 👋"},
"pm_welcome_body":        {"fa": "برای شروع بازی، ربات رو ببر تو یه گروه. بازی‌ها فقط تو گروه کار می‌کنن.", "en": "To start playing, add the bot to a group. Games only work in groups.", "ar": "لبدء اللعب، أضف البوت لمجموعة. الألعاب تعمل في المجموعات فقط.", "tr": "Oynamak için botu gruba ekle. Oyunlar sadece gruplarda çalışır.", "ru": "Чтобы играть, добавь бота в группу. Игры работают только в группах.", "de": "Um zu spielen, füge den Bot einer Gruppe hinzu. Spiele laufen nur in Gruppen.", "zh": "要玩游戏，把机器人加到群组。游戏只在群里运行。"},
"pm_welcome_donate_hint": {"fa": "اگه دوست داشتی، با استارز حمایت کن ❤️", "en": "If you feel like it, support with Stars ❤️", "ar": "لو حابب، ادعم بالنجوم ❤️", "tr": "İstersen Yıldızla destekle ❤️", "ru": "Если хочешь, поддержи звёздами ❤️", "de": "Wenn du magst, unterstütz mit Sternen ❤️", "zh": "喜欢的话，用星星支持 ❤️"},
"btn_add_to_group":       {"fa": "ببر تو گروه", "en": "Add to Group", "ar": "أضف لمجموعة", "tr": "Gruba Ekle", "ru": "Добавить в группу", "de": "Zur Gruppe", "zh": "添加到群组"},
"btn_change_lang":        {"fa": "تغییر زبان", "en": "Change Language", "ar": "تغيير اللغة", "tr": "Dili Değiştir", "ru": "Сменить язык", "de": "Sprache ändern", "zh": "更改语言"},
"btn_donate":             {"fa": "حمایت با استارز", "en": "Support with Stars", "ar": "ادعم بالنجوم", "tr": "Yıldızla Destekle", "ru": "Поддержать звёздами", "de": "Mit Sternen unterstützen", "zh": "用星星支持"},

# ═══════════════════ Donate
"donate_title":           {"fa": "❤️ حمایت از راینوبازی\n\nممنون که هستی رفیق! 🙏\n\nچند تا ستاره می‌خوای هدیه بدی؟\n\n💡 پرداخت امن و سریع از تلگرام", "en": "❤️ Support Rhino Games\n\nThanks for being here, buddy! 🙏\n\nHow many Stars you wanna give?\n\n💡 Safe and fast via Telegram", "ar": "❤️ ادعم ألعاب رينو\n\nشكراً لوجودك يا صاحبي! 🙏\n\nكم نجمة تحب تهدي؟\n\n💡 آمن وسريع عبر تلغرام", "tr": "❤️ Rhino Oyunları'nı Destekle\n\nBurada olduğun için sağol! 🙏\n\nKaç Yıldız vermek istersin?\n\n💡 Telegram üzerinden güvenli", "ru": "❤️ Поддержи Rhino Games\n\nСпасибо, что ты здесь! 🙏\n\nСколько звёзд подаришь?\n\n💡 Безопасно через Telegram", "de": "❤️ Rhino Games unterstützen\n\nDanke, dass du da bist! 🙏\n\nWie viele Sterne willst du geben?\n\n💡 Sicher über Telegram", "zh": "❤️ 支持 Rhino Games\n\n感谢你的陪伴！🙏\n\n你想送几颗星星？\n\n💡 通过 Telegram 安全支付"},
"donate_custom":          {"fa": "✏️ مقدار دلخواه", "en": "✏️ Custom amount", "ar": "✏️ مبلغ مخصص", "tr": "✏️ Özel miktar", "ru": "✏️ Своя сумма", "de": "✏️ Eigener Betrag", "zh": "✏️ 自定义金额"},
"donate_custom_prompt":   {"fa": "چند تا ستاره؟ (۱ تا ۱۰۰۰۰)\nبرای لغو /cancel", "en": "How many Stars? (1-10000)\n/cancel to cancel", "ar": "كم نجمة؟ (1-10000)\n/cancel للإلغاء", "tr": "Kaç Yıldız? (1-10000)\n/cancel iptal", "ru": "Сколько звёзд? (1-10000)\n/cancel отмена", "de": "Wie viele Sterne? (1-10000)\n/cancel abbrechen", "zh": "多少星星？（1-10000）\n/cancel 取消"},
"donate_invoice_title":   {"fa": "حمایت از راینوبازی", "en": "Support Rhino Games", "ar": "ادعم ألعاب رينو", "tr": "Rhino Oyunları'nı Destekle", "ru": "Поддержать Rhino Games", "de": "Rhino Games unterstützen", "zh": "支持 Rhino Games"},
"donate_invoice_desc":    {"fa": "اهدا {n} ستاره", "en": "Donate {n} Stars", "ar": "تبرع بـ{n} نجمة", "tr": "{n} Yıldız bağışla", "ru": "Пожертвовать {n} звёзд", "de": "{n} Sterne spenden", "zh": "捐赠 {n} 星星"},
"donate_thanks":          {"fa": "🙏 دمت گرم رفیق!\n⭐ {n} ستاره", "en": "🙏 Legend! Thanks!\n⭐ {n} Stars", "ar": "🙏 يا بطل! شكراً!\n⭐ {n} نجمة", "tr": "🙏 Efsanesin! Sağol!\n⭐ {n} Yıldız", "ru": "🙏 Красава! Спасибо!\n⭐ {n} звёзд", "de": "🙏 Legende! Danke!\n⭐ {n} Sterne", "zh": "🙏 太给力了！谢谢！\n⭐ {n} 星星"},
"donate_amount_invalid":  {"fa": "❌ عددی بین ۱ تا ۱۰۰۰۰ بفرست", "en": "❌ Send a number between 1 and 10000", "ar": "❌ أرسل عدداً بين 1 و10000", "tr": "❌ 1-10000 arası sayı gönder", "ru": "❌ Отправь число от 1 до 10000", "de": "❌ Zahl zwischen 1 und 10000", "zh": "❌ 发 1 到 10000 之间的数字"},
"donate_invoice_error":   {"fa": "❌ یه مشکلی تو ساخت فاکتور پیش اومد", "en": "❌ Something went wrong creating invoice", "ar": "❌ خطأ في إنشاء الفاتورة", "tr": "❌ Fatura oluşturulamadı", "ru": "❌ Ошибка при создании счёта", "de": "❌ Fehler bei Rechnung", "zh": "❌ 创建发票失败"},
"donate_owner_notify":    {"fa": "💰 حمایت جدید!\n\n👤 {name}\n🆔 <code>{uid}</code>\n⭐ {n} ستاره", "en": "💰 New support!\n\n👤 {name}\n🆔 <code>{uid}</code>\n⭐ {n} Stars", "ar": "💰 دعم جديد!\n\n👤 {name}\n🆔 <code>{uid}</code>\n⭐ {n} نجمة", "tr": "💰 Yeni destek!\n\n👤 {name}\n🆔 <code>{uid}</code>\n⭐ {n} Yıldız", "ru": "💰 Новая поддержка!\n\n👤 {name}\n🆔 <code>{uid}</code>\n⭐ {n} звёзд", "de": "💰 Neue Unterstützung!\n\n👤 {name}\n🆔 <code>{uid}</code>\n⭐ {n} Sterne", "zh": "💰 新支持！\n\n👤 {name}\n🆔 <code>{uid}</code>\n⭐ {n} 星星"},

# ═══════════════════ Force join
"force_join_msg":     {"fa": "🔒 اول بیا تو کانال‌ها، بعدش بازی کنیم:", "en": "🔒 Join our channels first, then we play:", "ar": "🔒 انضم للقنوات أولاً ثم نلعب:", "tr": "🔒 Önce kanallara katıl, sonra oynarız:", "ru": "🔒 Сначала подпишись, потом играем:", "de": "🔒 Erst Kanäle joinen, dann spielen:", "zh": "🔒 先加频道，再玩："},
"force_join_btn":     {"fa": "عضویت", "en": "Join", "ar": "انضم", "tr": "Katıl", "ru": "Подписаться", "de": "Beitreten", "zh": "加入"},
"force_join_check":   {"fa": "عضو شدم", "en": "I'm In", "ar": "انضممت", "tr": "Katıldım", "ru": "Я подписался", "de": "Bin drin", "zh": "我加了"},
"force_join_alert":   {"fa": "🔒 اول عضو شو", "en": "🔒 Join first", "ar": "🔒 انضم أولاً", "tr": "🔒 Önce katıl", "ru": "🔒 Сначала подпишись", "de": "🔒 Erst joinen", "zh": "🔒 先加入"},
"panel_group_only":   {"fa": "🔒 پنل فقط تو گروه کار می‌کنه رفیق.\n\nربات رو ببر تو یه گروه", "en": "🔒 Panel only works in groups.\n\nAdd the bot to a group", "ar": "🔒 اللوحة فقط في المجموعات.\n\nأضف البوت لمجموعة", "tr": "🔒 Panel sadece gruplarda.\n\nBotu gruba ekle", "ru": "🔒 Панель только в группах.\n\nДобавь бота в группу", "de": "🔒 Panel nur in Gruppen.\n\nFüg den Bot hinzu", "zh": "🔒 面板只在群里。\n\n把机器人加到群"},

# ═══════════════════ Inline
"inline_join_required": {"fa": "🔒 اول عضو شو", "en": "🔒 Join first", "ar": "🔒 انضم أولاً", "tr": "🔒 Önce katıl", "ru": "🔒 Сначала подпишись", "de": "🔒 Erst joinen", "zh": "🔒 先加入"},
"inline_open_bot":      {"fa": "باز کن بریم", "en": "Open & Play", "ar": "افتح والعب", "tr": "Aç & Oyna", "ru": "Открыть и играть", "de": "Öffnen & Spielen", "zh": "打开开玩"},
"inline_game_open_btn": {"fa": "🎮 باز کن", "en": "🎮 Open", "ar": "🎮 افتح", "tr": "🎮 Aç", "ru": "🎮 Открыть", "de": "🎮 Öffnen", "zh": "🎮 打开"},

"choose_game_hint": {
    "fa": "👇 یک بازی انتخاب کنید:",
    "en": "👇 Pick a game:",
    "ar": "👇 اختر لعبة:",
    "tr": "👇 Bir oyun seç:",
    "ru": "👇 Выбери игру:",
    "de": "👇 Wähl ein Spiel:",
    "zh": "👇 选个游戏：",
},
"enter_game_table": {
    "fa": "ورود به میز بازی",
    "en": "Enter Game Table",
    "ar": "ادخل طاولة اللعب",
    "tr": "Oyun Masasına Gir",
    "ru": "Зайти за стол",
    "de": "Zum Spieltisch",
    "zh": "进入游戏桌",
},

# ═══════════════════ Typing
"typing_prompt": {"fa": "جمله رو سریع و درست تایپ کن!", "en": "Type the sentence fast and correct!", "ar": "اكتب الجملة بسرعة وصح!", "tr": "Cümleyi hızlı ve doğru yaz!", "ru": "Напечатай предложение быстро и точно!", "de": "Tippe den Satz schnell und richtig!", "zh": "快速准确地打出这句话！"},
}

# ═══════════════ کش و توابع
_user_lang_cache: dict[int, str] = {}


def t(key: str, lang: str = "fa", **kwargs) -> str:
    row = T.get(key, {})
    text = row.get(lang) or row.get("fa") or key
    return text.format(**kwargs) if kwargs else text


def get_user_lang(user_id: int) -> str:
    return _user_lang_cache.get(user_id, "fa")


def set_user_lang(user_id: int, lang: str) -> None:
    if lang in LANGS:
        _user_lang_cache[user_id] = lang


def load_lang_from_db(user_id: int, lang: str | None) -> None:
    if lang and lang in LANGS:
        _user_lang_cache[user_id] = lang

"""langs.py — سیستم ۷ زبانه کامل برای همه بازی‌ها و پنل"""

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
# ═══════════════ عمومی
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
# ═══════════════ دکمه‌ها
"btn_back":       {"fa": "بازگشت", "en": "Back", "ar": "رجوع", "tr": "Geri", "ru": "Назад", "de": "Zurück", "zh": "返回"},
"btn_cancel":     {"fa": "لغو", "en": "Cancel", "ar": "إلغاء", "tr": "İptal", "ru": "Отмена", "de": "Abbrechen", "zh": "取消"},
"btn_close":      {"fa": "بستن پنل", "en": "Close Panel", "ar": "إغلاق اللوحة", "tr": "Paneli Kapat", "ru": "Закрыть панель", "de": "Panel schließen", "zh": "关闭面板"},
"btn_confirm":    {"fa": "تایید", "en": "Confirm", "ar": "تأكيد", "tr": "Onayla", "ru": "Подтвердить", "de": "Bestätigen", "zh": "确认"},
"btn_yes":        {"fa": "بله", "en": "Yes", "ar": "نعم", "tr": "Evet", "ru": "Да", "de": "Ja", "zh": "是"},
"btn_no":         {"fa": "خیر", "en": "No", "ar": "لا", "tr": "Hayır", "ru": "Нет", "de": "Nein", "zh": "否"},
"btn_group":      {"fa": "بازی‌های گروهی", "en": "Group Games", "ar": "ألعاب جماعية", "tr": "Grup Oyunları", "ru": "Групповые игры", "de": "Gruppenspiele", "zh": "群组游戏"},
"btn_single":     {"fa": "بازی‌های تک‌نفره", "en": "Single Player", "ar": "لاعب فردي", "tr": "Tek Oyuncu", "ru": "Одиночная игра", "de": "Einzelspieler", "zh": "单人游戏"},
"btn_typing":     {"fa": "بازی‌های تایپی", "en": "Typing Games", "ar": "ألعاب الكتابة", "tr": "Yazma Oyunları", "ru": "Игры на печать", "de": "Tippspiele", "zh": "打字游戏"},
"btn_anon":       {"fa": "بازی‌های ناشناس", "en": "Anonymous Games", "ar": "ألعاب مجهولة", "tr": "Anonim Oyunlar", "ru": "Анонимные игры", "de": "Anonyme Spiele", "zh": "匿名游戏"},

# ═══════════════ پنل بازی
"game_panel":         {"fa": "به پنل بازی خوش آمدید.\nدسته‌بندی مورد نظر را انتخاب کنید:", "en": "Welcome to game panel.\nChoose a category:", "ar": "مرحباً في لوحة الألعاب.\nاختر فئة:", "tr": "Oyun paneline hoş geldin.\nBir kategori seç:", "ru": "Добро пожаловать в игровую панель.\nВыберите категорию:", "de": "Willkommen im Spielbereich.\nWähle eine Kategorie:", "zh": "欢迎来到游戏面板。\n请选择类别："},
"group_games_title":  {"fa": "بازی‌های کارتی و گروهی", "en": "Card & Group Games", "ar": "ألعاب جماعية", "tr": "Kart & Grup Oyunları", "ru": "Карточные и групповые игры", "de": "Karten- & Gruppenspiele", "zh": "卡牌与群组游戏"},
"single_games_title": {"fa": "بازی‌های تک‌نفره", "en": "Single Player Games", "ar": "ألعاب فردية", "tr": "Tek Oyunculu Oyunlar", "ru": "Одиночные игры", "de": "Einzelspieler-Spiele", "zh": "单人游戏"},
"typing_games_title": {"fa": "بازی‌های تایپی و سرعتی", "en": "Typing & Speed Games", "ar": "ألعاب الكتابة والسرعة", "tr": "Yazma ve Hız Oyunları", "ru": "Игры на скорость печати", "de": "Tipp- & Tempospiele", "zh": "打字与速度游戏"},
"anon_games_title":   {"fa": "بازی‌های ناشناس (ویژه ادمین)", "en": "Anonymous Games (Admin only)", "ar": "ألعاب مجهولة (للمشرفين)", "tr": "Anonim Oyunlar (Yönetici)", "ru": "Анонимные игры (только админ)", "de": "Anonyme Spiele (nur Admin)", "zh": "匿名游戏（仅管理员）"},

# ═══════════════ نام بازی‌ها
"game_hokm":          {"fa": "حکم ۲ نفره", "en": "Hokm 2P", "ar": "حكم ٢ لاعب", "tr": "Hokm 2K", "ru": "Хокм 2 игрока", "de": "Hokm 2P", "zh": "Hokm 双人"},
"game_hokm_4p":       {"fa": "حکم ۴ نفره", "en": "Hokm 4P", "ar": "حكم ٤ لاعب", "tr": "Hokm 4K", "ru": "Хокм 4 игрока", "de": "Hokm 4P", "zh": "Hokm 四人"},
"game_dooz":          {"fa": "دوز ۲ نفره", "en": "Tic-Tac-Toe", "ar": "إكس أو", "tr": "XOX", "ru": "Крестики-нолики", "de": "Tic-Tac-Toe", "zh": "井字棋"},
"game_doz4p":         {"fa": "دوز ۴ نفره", "en": "Tic-Tac-Toe 4P", "ar": "إكس أو ٤ لاعبين", "tr": "XOX 4K", "ru": "Крестики-нолики 4", "de": "Tic-Tac-Toe 4P", "zh": "井字棋四人"},
"game_connect4":      {"fa": "چهار در یک ردیف", "en": "Connect Four", "ar": "أربعة في صف", "tr": "Dörtlü Bağla", "ru": "Четыре в ряд", "de": "Vier gewinnt", "zh": "四子棋"},
"game_rps":           {"fa": "سنگ کاغذ قیچی", "en": "Rock Paper Scissors", "ar": "حجر ورقة مقص", "tr": "Taş Kağıt Makas", "ru": "Камень ножницы бумага", "de": "Schere Stein Papier", "zh": "石头剪刀布"},
"game_memory":        {"fa": "بازی حافظه", "en": "Memory Game", "ar": "لعبة الذاكرة", "tr": "Hafıza Oyunu", "ru": "Игра памяти", "de": "Memory-Spiel", "zh": "记忆游戏"},
"game_spuzzle":       {"fa": "پازل کشویی", "en": "Sliding Puzzle", "ar": "لغز منزلق", "tr": "Kaydırmalı Bulmaca", "ru": "Пятнашки", "de": "Schiebepuzzle", "zh": "滑动拼图"},
"game_samegame":      {"fa": "بازی جفت‌ها", "en": "Same Game", "ar": "لعبة الأزواج", "tr": "Aynı Oyun", "ru": "Одинаковые", "de": "Gleiche", "zh": "消消乐"},
"game_hangman":       {"fa": "حدس کلمه", "en": "Hangman", "ar": "خمن الكلمة", "tr": "Adam Asmaca", "ru": "Виселица", "de": "Galgenmännchen", "zh": "猜词"},
"game_typing":        {"fa": "تایپ سرعتی", "en": "Typing Race", "ar": "سباق الكتابة", "tr": "Yazma Yarışı", "ru": "Гонка печати", "de": "Tipprennen", "zh": "打字比赛"},
"game_guess_num":     {"fa": "حدس عدد", "en": "Guess Number", "ar": "خمن الرقم", "tr": "Sayı Tahmin", "ru": "Угадай число", "de": "Zahl raten", "zh": "猜数字"},
"game_eteraf":        {"fa": "اعتراف (پیش‌فرض)", "en": "Confession (Default)", "ar": "اعتراف (افتراضي)", "tr": "İtiraf (Varsayılan)", "ru": "Признание (по умолч.)", "de": "Geständnis (Standard)", "zh": "表白（默认）"},
"game_eteraf_custom": {"fa": "اعتراف (سفارشی)", "en": "Confession (Custom)", "ar": "اعتراف (مخصص)", "tr": "İtiraf (Özel)", "ru": "Признание (своё)", "de": "Geständnis (Eigen)", "zh": "表白（自定义）"},
"game_gharch":        {"fa": "قارچ ناشناس", "en": "Anonymous Mushroom", "ar": "فطر مجهول", "tr": "Anonim Mantar", "ru": "Анонимный гриб", "de": "Anonymer Pilz", "zh": "匿名蘑菇"},
"game_gardone":       {"fa": "گردونه شانس", "en": "Lucky Wheel", "ar": "عجلة الحظ", "tr": "Çarkıfelek", "ru": "Колесо удачи", "de": "Glücksrad", "zh": "幸运轮盘"},

# ═══════════════ پیام‌های مشترک بازی
"join_game":              {"fa": "پیوستن به بازی", "en": "Join Game", "ar": "انضم", "tr": "Katıl", "ru": "Присоединиться", "de": "Beitreten", "zh": "加入游戏"},
"game_full":              {"fa": "ظرفیت بازی تکمیل است.", "en": "Game is full.", "ar": "اللعبة ممتلئة.", "tr": "Oyun dolu.", "ru": "Игра заполнена.", "de": "Spiel ist voll.", "zh": "游戏已满。"},
"not_your_turn":          {"fa": "نوبت شما نیست!", "en": "Not your turn!", "ar": "ليس دورك!", "tr": "Sıra sizde değil!", "ru": "Не ваш ход!", "de": "Nicht dein Zug!", "zh": "还没到你的回合！"},
"already_joined":         {"fa": "شما قبلاً پیوسته‌اید!", "en": "Already joined!", "ar": "لقد انضممت!", "tr": "Zaten katıldınız!", "ru": "Вы уже присоединились!", "de": "Du bist schon dabei!", "zh": "你已加入！"},
"cell_occupied":          {"fa": "این خانه پر شده است!", "en": "Cell occupied!", "ar": "هذه الخلية مشغولة!", "tr": "Bu hücre dolu!", "ru": "Клетка занята!", "de": "Zelle belegt!", "zh": "格子已被占用！"},
"game_winner":            {"fa": "🏆 برنده: {name}", "en": "🏆 Winner: {name}", "ar": "🏆 الفائز: {name}", "tr": "🏆 Kazanan: {name}", "ru": "🏆 Победитель: {name}", "de": "🏆 Gewinner: {name}", "zh": "🏆 获胜者：{name}"},
"game_draw":              {"fa": "🤝 بازی مساوی شد!", "en": "🤝 It's a draw!", "ar": "🤝 تعادل!", "tr": "🤝 Berabere!", "ru": "🤝 Ничья!", "de": "🤝 Unentschieden!", "zh": "🤝 平局！"},
"game_expired":           {"fa": "این بازی دیگر فعال نیست.", "en": "Game expired.", "ar": "هذه اللعبة لم تعد نشطة.", "tr": "Bu oyun artık aktif değil.", "ru": "Игра истекла.", "de": "Spiel abgelaufen.", "zh": "游戏已过期。"},
"game_not_active":        {"fa": "بازی فعال نیست.", "en": "Game not active.", "ar": "اللعبة غير نشطة.", "tr": "Oyun aktif değil.", "ru": "Игра не активна.", "de": "Spiel nicht aktiv.", "zh": "游戏未激活。"},
"game_already_started":   {"fa": "بازی شروع شده است.", "en": "Game already started.", "ar": "بدأت اللعبة.", "tr": "Oyun başladı.", "ru": "Игра уже началась.", "de": "Spiel läuft bereits.", "zh": "游戏已开始。"},
"game_already_running":   {"fa": "یک بازی در این گروه فعال است.", "en": "A game is already active.", "ar": "هناك لعبة نشطة.", "tr": "Aktif bir oyun var.", "ru": "Игра уже идёт.", "de": "Ein Spiel läuft bereits.", "zh": "已有游戏在进行。"},
"not_your_panel":         {"fa": "این پنل برای شما نیست!", "en": "This panel isn't yours!", "ar": "هذه اللوحة ليست لك!", "tr": "Bu panel senin değil!", "ru": "Эта панель не ваша!", "de": "Dieses Panel gehört dir nicht!", "zh": "此面板不是你的！"},
"not_your_game":          {"fa": "این بازی برای شما نیست!", "en": "This game isn't yours!", "ar": "هذه اللعبة ليست لك!", "tr": "Bu oyun senin değil!", "ru": "Эта игра не ваша!", "de": "Dieses Spiel gehört dir nicht!", "zh": "此游戏不是你的！"},
"you_have_active_game":   {"fa": "شما یک بازی فعال دارید.", "en": "You already have an active game.", "ar": "لديك لعبة نشطة.", "tr": "Aktif bir oyunun var.", "ru": "У вас уже есть активная игра.", "de": "Du hast bereits ein aktives Spiel.", "zh": "你已有活跃游戏。"},
"wait_a_bit":             {"fa": "کمی صبر کنید...", "en": "Wait a bit...", "ar": "انتظر قليلاً...", "tr": "Biraz bekle...", "ru": "Подождите...", "de": "Warte kurz...", "zh": "请稍候..."},
"invalid_move":           {"fa": "حرکت غیرمجاز!", "en": "Invalid move!", "ar": "حركة غير صالحة!", "tr": "Geçersiz hamle!", "ru": "Неверный ход!", "de": "Ungültiger Zug!", "zh": "无效移动！"},
"game_closed":            {"fa": "بازی بسته شد.", "en": "Game closed.", "ar": "تم إغلاق اللعبة.", "tr": "Oyun kapatıldı.", "ru": "Игра закрыта.", "de": "Spiel geschlossen.", "zh": "游戏已关闭。"},
"panel_closed":           {"fa": "پنل بسته شد.", "en": "Panel closed.", "ar": "تم إغلاق اللوحة.", "tr": "Panel kapatıldı.", "ru": "Панель закрыта.", "de": "Panel geschlossen.", "zh": "面板已关闭。"},
"close_game":             {"fa": "بستن بازی", "en": "Close Game", "ar": "إغلاق اللعبة", "tr": "Oyunu Kapat", "ru": "Закрыть игру", "de": "Spiel schließen", "zh": "关闭游戏"},
"score":                  {"fa": "امتیاز", "en": "Score", "ar": "النقاط", "tr": "Puan", "ru": "Счёт", "de": "Punkte", "zh": "分数"},
"finished":               {"fa": "تمام شد", "en": "Finished", "ar": "انتهى", "tr": "Bitti", "ru": "Завершено", "de": "Beendet", "zh": "已结束"},
"turn_of":                {"fa": "نوبت", "en": "Turn", "ar": "دور", "tr": "Sıra", "ru": "Ход", "de": "Zug", "zh": "轮到"},
"waiting_players":        {"fa": "منتظر بازیکنان...", "en": "Waiting for players...", "ar": "في انتظار اللاعبين...", "tr": "Oyuncular bekleniyor...", "ru": "Ожидание игроков...", "de": "Warte auf Spieler...", "zh": "等待玩家..."},
"player":                 {"fa": "بازیکن", "en": "Player", "ar": "لاعب", "tr": "Oyuncu", "ru": "Игрок", "de": "Spieler", "zh": "玩家"},

# ═══════════════ Hangman
"hangman_started":   {"fa": "بازی حدس کلمه شروع شد!", "en": "Hangman started!", "ar": "بدأت لعبة تخمين الكلمة!", "tr": "Adam Asmaca başladı!", "ru": "Виселица началась!", "de": "Galgenmännchen gestartet!", "zh": "猜词游戏开始！"},
"each_player_lives": {"fa": "هر بازیکن {n} جان دارد.", "en": "Each player has {n} lives.", "ar": "كل لاعب لديه {n} أرواح.", "tr": "Her oyuncunun {n} canı var.", "ru": "У каждого игрока {n} жизней.", "de": "Jeder Spieler hat {n} Leben.", "zh": "每位玩家有 {n} 条命。"},
"guess_one_letter":  {"fa": "یک حرف حدس بزنید (مثال: م)", "en": "Guess one letter (e.g.: A)", "ar": "خمن حرفًا واحدًا", "tr": "Bir harf tahmin et", "ru": "Угадайте одну букву", "de": "Rate einen Buchstaben", "zh": "猜一个字母"},
"letter_already":    {"fa": "این حرف قبلاً گفته شده!", "en": "Letter already guessed!", "ar": "تم تخمين هذا الحرف!", "tr": "Bu harf zaten tahmin edildi!", "ru": "Буква уже была!", "de": "Buchstabe schon geraten!", "zh": "字母已猜过！"},
"no_lives_left":     {"fa": "شما تمام جان‌های خود را از دست داده‌اید!", "en": "You have no lives left!", "ar": "لا أرواح متبقية!", "tr": "Canınız kalmadı!", "ru": "У вас не осталось жизней!", "de": "Keine Leben mehr!", "zh": "你没有命了！"},
"word_winner":       {"fa": "{name} برنده شد! کلمه: {word}", "en": "{name} won! Word: {word}", "ar": "{name} فاز! الكلمة: {word}", "tr": "{name} kazandı! Kelime: {word}", "ru": "{name} победил! Слово: {word}", "de": "{name} hat gewonnen! Wort: {word}", "zh": "{name} 赢了！单词：{word}"},
"wrong_guess_lives": {"fa": "اشتباه بود {name}! {n} جان دیگر دارید.", "en": "Wrong, {name}! {n} lives left.", "ar": "خطأ {name}! {n} أرواح متبقية.", "tr": "Yanlış, {name}! {n} can kaldı.", "ru": "Неверно, {name}! Осталось {n} жизней.", "de": "Falsch, {name}! {n} Leben übrig.", "zh": "错了 {name}！还剩 {n} 条命。"},
"player_eliminated": {"fa": "{name} تمام جان‌های خود را از دست داد.", "en": "{name} is eliminated.", "ar": "{name} تم استبعاده.", "tr": "{name} elendi.", "ru": "{name} выбыл.", "de": "{name} ist raus.", "zh": "{name} 被淘汰。"},
"all_lost_word_was": {"fa": "همه باختید! کلمه: {word}", "en": "All lost! Word: {word}", "ar": "خسر الجميع! الكلمة: {word}", "tr": "Herkes kaybetti! Kelime: {word}", "ru": "Все проиграли! Слово: {word}", "de": "Alle verloren! Wort: {word}", "zh": "全部失败！单词：{word}"},

# ═══════════════ 2048
"game_2048_title":   {"fa": "بازی 2048", "en": "2048 Game", "ar": "لعبة 2048", "tr": "2048 Oyunu", "ru": "Игра 2048", "de": "2048 Spiel", "zh": "2048 游戏"},
"you_won_2048":      {"fa": "تبریک! شما برنده شدید!", "en": "Congrats! You won!", "ar": "مبروك! لقد فزت!", "tr": "Tebrikler! Kazandın!", "ru": "Поздравляю! Вы победили!", "de": "Glückwunsch! Du hast gewonnen!", "zh": "恭喜！你赢了！"},
"you_lost_2048":     {"fa": "بازی تمام شد! باختید.", "en": "Game over! You lost.", "ar": "انتهت اللعبة! خسرت.", "tr": "Oyun bitti! Kaybettin.", "ru": "Игра окончена! Вы проиграли.", "de": "Spiel vorbei! Verloren.", "zh": "游戏结束！你输了。"},

# ═══════════════ SameGame
"samegame_title":  {"fa": "بازی جفت‌ها", "en": "Same Game", "ar": "لعبة الأزواج", "tr": "Aynı Oyun", "ru": "Одинаковые", "de": "Gleiche", "zh": "消消乐"},
"no_more_moves":   {"fa": "حرکت دیگری باقی نمانده! بازی تمام شد.", "en": "No more moves! Game over.", "ar": "لا حركات أخرى! انتهت اللعبة.", "tr": "Hamle kalmadı! Oyun bitti.", "ru": "Ходов больше нет! Игра окончена.", "de": "Keine Züge mehr! Spiel vorbei.", "zh": "没有可移动的！游戏结束。"},
"need_two_blocks": {"fa": "باید حداقل دو بلوک همرنگ کنار هم باشند!", "en": "Need at least 2 same-colored blocks together!", "ar": "تحتاج إلى بلوكين متطابقين على الأقل!", "tr": "En az 2 aynı renkli blok gerekli!", "ru": "Нужно минимум 2 одинаковых блока рядом!", "de": "Mindestens 2 gleichfarbige Blöcke!", "zh": "至少需要两个同色方块相邻！"},

# ═══════════════ Spuzzle
"spuzzle_title":      {"fa": "پازل کشویی", "en": "Sliding Puzzle", "ar": "لغز منزلق", "tr": "Kaydırmalı Bulmaca", "ru": "Пятнашки", "de": "Schiebepuzzle", "zh": "滑动拼图"},
"sort_numbers":       {"fa": "اعداد را مرتب کنید.", "en": "Sort the numbers.", "ar": "رتب الأرقام.", "tr": "Sayıları sırala.", "ru": "Расставьте числа.", "de": "Sortiere die Zahlen.", "zh": "请按顺序排列数字。"},
"puzzle_solved":      {"fa": "تبریک {name}! پازل حل شد!", "en": "Congrats {name}! Puzzle solved!", "ar": "مبروك {name}! تم حل اللغز!", "tr": "Tebrikler {name}! Bulmaca çözüldü!", "ru": "Поздравляю, {name}! Пазл решён!", "de": "Glückwunsch {name}! Puzzle gelöst!", "zh": "恭喜 {name}！拼图完成！"},
"solved_in_seconds":  {"fa": "زمان: {n} ثانیه", "en": "Time: {n} seconds", "ar": "الوقت: {n} ثانية", "tr": "Süre: {n} saniye", "ru": "Время: {n} секунд", "de": "Zeit: {n} Sekunden", "zh": "时间：{n} 秒"},

# ═══════════════ Doz4p
"doz4p_title":    {"fa": "دوز ۴ نفره", "en": "Tic-Tac-Toe 4P", "ar": "إكس أو ٤ لاعبين", "tr": "XOX 4K", "ru": "Крестики-нолики 4", "de": "Tic-Tac-Toe 4P", "zh": "井字棋四人"},
"doz4p_created":  {"fa": "بازی دوز ۴ نفره توسط {name} ساخته شد!", "en": "Tic-Tac-Toe 4P created by {name}!", "ar": "أنشأ {name} لعبة إكس أو ٤ لاعبين!", "tr": "{name} tarafından XOX 4K oluşturuldu!", "ru": "{name} создал игру 4 игрока!", "de": "Tic-Tac-Toe 4P von {name} erstellt!", "zh": "{name} 创建了四人井字棋！"},

# ═══════════════ Hokm
"hokm_title":          {"fa": "بازی حکم", "en": "Hokm Game", "ar": "لعبة حكم", "tr": "Hokm Oyunu", "ru": "Хокм", "de": "Hokm", "zh": "Hokm 游戏"},
"hokm_created":        {"fa": "بازی حکم {mode} نفره توسط {name} ساخته شد!", "en": "Hokm {mode}P created by {name}!", "ar": "أنشأ {name} حكم {mode} لاعبين!", "tr": "{name} tarafından Hokm {mode}K oluşturuldu!", "ru": "{name} создал Hokm {mode} игрока!", "de": "Hokm {mode}P von {name} erstellt!", "zh": "{name} 创建了 {mode} 人 Hokm！"},
"hokm_choose_suit":    {"fa": "حاکم عزیز، حکم را انتخاب کنید:", "en": "Dear Hakem, choose the trump suit:", "ar": "أيها الحاكم، اختر الحكم:", "tr": "Sevgili Hakem, kozu seç:", "ru": "Уважаемый хакем, выберите козырь:", "de": "Lieber Hakem, wähle die Trumpffarbe:", "zh": "亲爱的 Hakem，请选择王牌："},
"hokm_hakem":          {"fa": "حاکم", "en": "Hakem", "ar": "الحاكم", "tr": "Hakem", "ru": "Хакем", "de": "Hakem", "zh": "Hakem"},
"hokm_trump":          {"fa": "حکم", "en": "Trump", "ar": "الحكم", "tr": "Koz", "ru": "Козырь", "de": "Trumpf", "zh": "王牌"},
"hokm_show_hand":      {"fa": "نمایش دست من (خصوصی)", "en": "Show My Hand (private)", "ar": "اعرض يدي (خاص)", "tr": "Elimi Göster (özel)", "ru": "Показать руку (лично)", "de": "Meine Hand zeigen (privat)", "zh": "查看我的手牌（私密）"},
"hokm_your_hand":      {"fa": "دست شما:\n{hand}", "en": "Your hand:\n{hand}", "ar": "يدك:\n{hand}", "tr": "Elin:\n{hand}", "ru": "Ваша рука:\n{hand}", "de": "Deine Hand:\n{hand}", "zh": "你的手牌：\n{hand}"},
"hokm_no_cards":       {"fa": "شما کارتی در دست ندارید.", "en": "You have no cards.", "ar": "ليس لديك بطاقات.", "tr": "Kartınız yok.", "ru": "У вас нет карт.", "de": "Du hast keine Karten.", "zh": "你没有牌。"},
"hokm_must_follow":    {"fa": "شما باید از خال زمین ({suit}) بازی کنید!", "en": "You must follow suit ({suit})!", "ar": "يجب أن تلعب من نفس اللون ({suit})!", "tr": "Takım renginden oynamalısın ({suit})!", "ru": "Вы должны играть в масть ({suit})!", "de": "Du musst Farbe bedienen ({suit})!", "zh": "必须跟花色（{suit}）！"},
"hokm_invalid_card":   {"fa": "شماره کارت نامعتبر است.", "en": "Invalid card number.", "ar": "رقم بطاقة غير صالح.", "tr": "Geçersiz kart numarası.", "ru": "Неверный номер карты.", "de": "Ungültige Kartennummer.", "zh": "牌号无效。"},
"hokm_not_hakem":      {"fa": "شما حاکم نیستید!", "en": "You are not Hakem!", "ar": "أنت لست الحاكم!", "tr": "Sen Hakem değilsin!", "ru": "Вы не хакем!", "de": "Du bist nicht Hakem!", "zh": "你不是 Hakem！"},
"hokm_not_choosing":   {"fa": "الان زمان انتخاب حکم نیست!", "en": "Not the time to choose!", "ar": "ليس وقت الاختيار!", "tr": "Seçim zamanı değil!", "ru": "Не время выбирать!", "de": "Nicht die Zeit zu wählen!", "zh": "现在不是选择的时候！"},
"hokm_won_trick":      {"fa": "برنده این دست: {name}", "en": "Winner of trick: {name}", "ar": "الفائز بالدور: {name}", "tr": "Eli kazanan: {name}", "ru": "Победитель взятки: {name}", "de": "Stich gewonnen: {name}", "zh": "本轮赢家：{name}"},
"hokm_round_finished": {"fa": "این دست تمام شد! برنده: {name}\n\n-- دور جدید --\nحاکم جدید: {hakem}\nمنتظر انتخاب حکم...", "en": "Round finished! Winner: {name}\n\n-- New round --\nNew Hakem: {hakem}\nWaiting for trump...", "ar": "انتهى الدور! الفائز: {name}\n\n-- دور جديد --\nالحاكم الجديد: {hakem}\nفي انتظار الحكم...", "tr": "El bitti! Kazanan: {name}\n\n-- Yeni el --\nYeni Hakem: {hakem}\nKoz bekleniyor...", "ru": "Раунд окончен! Победитель: {name}\n\n-- Новый раунд --\nНовый хакем: {hakem}\nОжидание козыря...", "de": "Runde vorbei! Gewinner: {name}\n\n-- Neue Runde --\nNeuer Hakem: {hakem}\nWarte auf Trumpf...", "zh": "本轮结束！赢家：{name}\n\n-- 新一轮 --\n新 Hakem：{hakem}\n等待选择王牌..."},
"hokm_team_a":         {"fa": "تیم ۱", "en": "Team 1", "ar": "الفريق ١", "tr": "Takım 1", "ru": "Команда 1", "de": "Team 1", "zh": "第 1 队"},
"hokm_team_b":         {"fa": "تیم ۲", "en": "Team 2", "ar": "الفريق ٢", "tr": "Takım 2", "ru": "Команда 2", "de": "Team 2", "zh": "第 2 队"},
"hokm_played_card":    {"fa": "کارت بازی شده", "en": "Played card", "ar": "البطاقة الملعوبة", "tr": "Oynanan kart", "ru": "Сыгранная карта", "de": "Gespielte Karte", "zh": "已出的牌"},
"hokm_trick_score":    {"fa": "دست", "en": "Tricks", "ar": "الدورات", "tr": "Eller", "ru": "Взятки", "de": "Stiche", "zh": "墩数"},
"hokm_total_score":    {"fa": "امتیاز کل", "en": "Total score", "ar": "النقاط الكلية", "tr": "Toplam puan", "ru": "Общий счёт", "de": "Gesamtpunkte", "zh": "总分"},
"hokm_game_won":       {"fa": "بازی تمام شد! برنده نهایی: {name}", "en": "Game over! Final winner: {name}", "ar": "انتهت اللعبة! الفائز النهائي: {name}", "tr": "Oyun bitti! Son kazanan: {name}", "ru": "Игра окончена! Победитель: {name}", "de": "Spiel vorbei! Endsieger: {name}", "zh": "游戏结束！最终赢家：{name}"},
"hokm_wait":           {"fa": "صبر کنید...", "en": "Wait...", "ar": "انتظر...", "tr": "Bekle...", "ru": "Подождите...", "de": "Warte...", "zh": "请稍候..."},

# ═══════════════ Dooz (2P Tic-Tac-Toe)
"dooz_title":    {"fa": "دوز", "en": "Tic-Tac-Toe", "ar": "إكس أو", "tr": "XOX", "ru": "Крестики-нолики", "de": "Tic-Tac-Toe", "zh": "井字棋"},
"dooz_created":  {"fa": "بازی دوز توسط {name} ساخته شد!", "en": "Tic-Tac-Toe created by {name}!", "ar": "أنشأ {name} لعبة إكس أو!", "tr": "{name} tarafından XOX oluşturuldu!", "ru": "{name} создал крестики-нолики!", "de": "Tic-Tac-Toe von {name} erstellt!", "zh": "{name} 创建了井字棋！"},
"dooz_started":  {"fa": "بازی شروع شد!\n{name1} ⚔️ {name2}", "en": "Game started!\n{name1} ⚔️ {name2}", "ar": "بدأت اللعبة!\n{name1} ⚔️ {name2}", "tr": "Oyun başladı!\n{name1} ⚔️ {name2}", "ru": "Игра началась!\n{name1} ⚔️ {name2}", "de": "Spiel gestartet!\n{name1} ⚔️ {name2}", "zh": "游戏开始！\n{name1} ⚔️ {name2}"},
"dooz_your_turn": {"fa": "نوبت {name} ({symbol}) است.", "en": "Turn of {name} ({symbol}).", "ar": "دور {name} ({symbol}).", "tr": "Sıra {name} ({symbol}).", "ru": "Ход {name} ({symbol}).", "de": "Zug von {name} ({symbol}).", "zh": "轮到 {name}（{symbol}）。"},
"dooz_won":      {"fa": "بازی تمام شد! برنده: {name} 🏆", "en": "Game over! Winner: {name} 🏆", "ar": "انتهت اللعبة! الفائز: {name} 🏆", "tr": "Oyun bitti! Kazanan: {name} 🏆", "ru": "Игра окончена! Победитель: {name} 🏆", "de": "Spiel vorbei! Gewinner: {name} 🏆", "zh": "游戏结束！赢家：{name} 🏆"},

# ═══════════════ Connect4
"c4_title":     {"fa": "چهار در یک ردیف", "en": "Connect Four", "ar": "أربعة في صف", "tr": "Dörtlü Bağla", "ru": "Четыре в ряд", "de": "Vier gewinnt", "zh": "四子棋"},
"c4_created":   {"fa": "بازی چهار در یک ردیف توسط {name} ساخته شد!", "en": "Connect Four created by {name}!", "ar": "أنشأ {name} لعبة أربعة في صف!", "tr": "{name} tarafından Dörtlü Bağla oluşturuldu!", "ru": "{name} создал Четыре в ряд!", "de": "Vier gewinnt von {name} erstellt!", "zh": "{name} 创建了四子棋！"},
"c4_col_full":  {"fa": "این ستون پر است!", "en": "This column is full!", "ar": "هذا العمود ممتلئ!", "tr": "Bu sütun dolu!", "ru": "Этот столбец заполнен!", "de": "Diese Spalte ist voll!", "zh": "此列已满！"},

# ═══════════════ RPS
"rps_title":         {"fa": "سنگ، کاغذ، قیچی", "en": "Rock, Paper, Scissors", "ar": "حجر، ورقة، مقص", "tr": "Taş, Kağıt, Makas", "ru": "Камень, ножницы, бумага", "de": "Schere, Stein, Papier", "zh": "石头、剪刀、布"},
"rps_created":       {"fa": "بازی سنگ کاغذ قیچی توسط {name} ساخته شد!", "en": "RPS created by {name}!", "ar": "أنشأ {name} لعبة حجر ورقة مقص!", "tr": "{name} tarafından TKM oluşturuldu!", "ru": "{name} создал игру КНБ!", "de": "SSP von {name} erstellt!", "zh": "{name} 创建了石头剪刀布！"},
"rps_started":       {"fa": "بازی شروع شد!\n{name1} ⚔️ {name2}\n\nلطفاً انتخاب کنید:", "en": "Game started!\n{name1} ⚔️ {name2}\n\nChoose:", "ar": "بدأت اللعبة!\n{name1} ⚔️ {name2}\n\nاختر:", "tr": "Oyun başladı!\n{name1} ⚔️ {name2}\n\nSeç:", "ru": "Игра началась!\n{name1} ⚔️ {name2}\n\nВыберите:", "de": "Spiel gestartet!\n{name1} ⚔️ {name2}\n\nWähle:", "zh": "游戏开始！\n{name1} ⚔️ {name2}\n\n请选择："},
"rps_rock":          {"fa": "سنگ", "en": "Rock", "ar": "حجر", "tr": "Taş", "ru": "Камень", "de": "Stein", "zh": "石头"},
"rps_paper":         {"fa": "کاغذ", "en": "Paper", "ar": "ورقة", "tr": "Kağıt", "ru": "Бумага", "de": "Papier", "zh": "布"},
"rps_scissors":      {"fa": "قیچی", "en": "Scissors", "ar": "مقص", "tr": "Makas", "ru": "Ножницы", "de": "Schere", "zh": "剪刀"},
"rps_already_chosen":{"fa": "شما قبلاً انتخاب خود را ثبت کرده‌اید!", "en": "You already chose!", "ar": "اخترت بالفعل!", "tr": "Zaten seçtin!", "ru": "Вы уже выбрали!", "de": "Du hast bereits gewählt!", "zh": "你已经选择了！"},
"rps_chosen":        {"fa": "انتخاب شما ثبت شد.", "en": "Your choice registered.", "ar": "تم تسجيل اختيارك.", "tr": "Seçimin kaydedildi.", "ru": "Ваш выбор принят.", "de": "Wahl gespeichert.", "zh": "你的选择已记录。"},
"rps_waiting":       {"fa": "بازی در جریان است...\n{name1}: {s1}\n{name2}: {s2}\nمنتظر انتخاب حریف...", "en": "Game in progress...\n{name1}: {s1}\n{name2}: {s2}\nWaiting for opponent...", "ar": "اللعبة جارية...\n{name1}: {s1}\n{name2}: {s2}\nانتظار الخصم...", "tr": "Oyun sürüyor...\n{name1}: {s1}\n{name2}: {s2}\nRakip bekleniyor...", "ru": "Игра идёт...\n{name1}: {s1}\n{name2}: {s2}\nОжидание соперника...", "de": "Spiel läuft...\n{name1}: {s1}\n{name2}: {s2}\nWarte auf Gegner...", "zh": "游戏进行中...\n{name1}: {s1}\n{name2}: {s2}\n等待对手..."},
"rps_result":        {"fa": "نتایج بازی:\n{name1}: {c1}\n{name2}: {c2}", "en": "Results:\n{name1}: {c1}\n{name2}: {c2}", "ar": "النتائج:\n{name1}: {c1}\n{name2}: {c2}", "tr": "Sonuçlar:\n{name1}: {c1}\n{name2}: {c2}", "ru": "Результаты:\n{name1}: {c1}\n{name2}: {c2}", "de": "Ergebnisse:\n{name1}: {c1}\n{name2}: {c2}", "zh": "结果：\n{name1}: {c1}\n{name2}: {c2}"},
"rps_chosen_status": {"fa": "(انتخاب کرد)", "en": "(chose)", "ar": "(اختار)", "tr": "(seçti)", "ru": "(выбрал)", "de": "(gewählt)", "zh": "（已选择）"},
"rps_waiting_status":{"fa": "(منتظر...)", "en": "(waiting...)", "ar": "(ينتظر...)", "tr": "(bekliyor...)", "ru": "(ждёт...)", "de": "(wartet...)", "zh": "（等待中...）"},

# ═══════════════ Memory
"memory_title":        {"fa": "بازی حافظه", "en": "Memory Game", "ar": "لعبة الذاكرة", "tr": "Hafıza Oyunu", "ru": "Игра памяти", "de": "Memory-Spiel", "zh": "记忆游戏"},
"memory_created":      {"fa": "بازی حافظه ({size}) توسط {name} ساخته شد!", "en": "Memory ({size}) created by {name}!", "ar": "أنشأ {name} لعبة الذاكرة ({size})!", "tr": "{name} tarafından Hafıza ({size}) oluşturuldu!", "ru": "{name} создал игру памяти ({size})!", "de": "Memory ({size}) von {name} erstellt!", "zh": "{name} 创建了记忆游戏（{size}）！"},
"memory_already_flipped": {"fa": "این کارت قبلاً انتخاب شده!", "en": "Card already chosen!", "ar": "تم اختيار البطاقة!", "tr": "Bu kart zaten seçildi!", "ru": "Карта уже выбрана!", "de": "Karte bereits gewählt!", "zh": "卡片已选过！"},
"memory_matched":      {"fa": "✅ جفت پیدا شد!", "en": "✅ Match found!", "ar": "✅ تم العثور على زوج!", "tr": "✅ Eşleşme bulundu!", "ru": "✅ Пара найдена!", "de": "✅ Paar gefunden!", "zh": "✅ 配对成功！"},
"memory_no_match":     {"fa": "❌ جفت نشدند.", "en": "❌ No match.", "ar": "❌ لا يوجد تطابق.", "tr": "❌ Eşleşmedi.", "ru": "❌ Не совпадают.", "de": "❌ Kein Paar.", "zh": "❌ 未配对。"},
"memory_final_score":  {"fa": "امتیاز نهایی:\n{name1}: {s1}\n{name2}: {s2}", "en": "Final score:\n{name1}: {s1}\n{name2}: {s2}", "ar": "النتيجة النهائية:\n{name1}: {s1}\n{name2}: {s2}", "tr": "Son puan:\n{name1}: {s1}\n{name2}: {s2}", "ru": "Итоговый счёт:\n{name1}: {s1}\n{name2}: {s2}", "de": "Endstand:\n{name1}: {s1}\n{name2}: {s2}", "zh": "最终比分：\n{name1}: {s1}\n{name2}: {s2}"},
"memory_turn":         {"fa": "نوبت {name} است.", "en": "Turn of {name}.", "ar": "دور {name}.", "tr": "Sıra {name}.", "ru": "Ход {name}.", "de": "Zug von {name}.", "zh": "轮到 {name}。"},
"memory_level_easy":   {"fa": "آسان", "en": "Easy", "ar": "سهل", "tr": "Kolay", "ru": "Легко", "de": "Einfach", "zh": "简单"},
"memory_level_med":    {"fa": "متوسط", "en": "Medium", "ar": "متوسط", "tr": "Orta", "ru": "Средне", "de": "Mittel", "zh": "中等"},
"memory_level_hard":   {"fa": "سخت", "en": "Hard", "ar": "صعب", "tr": "Zor", "ru": "Сложно", "de": "Schwer", "zh": "困难"},
"memory_level_pro":    {"fa": "حرفه‌ای", "en": "Pro", "ar": "محترف", "tr": "Pro", "ru": "Про", "de": "Profi", "zh": "专业"},

# ═══════════════ Gardone
"gardone_title":         {"fa": "گردونه شانس", "en": "Lucky Wheel", "ar": "عجلة الحظ", "tr": "Çarkıfelek", "ru": "Колесо удачи", "de": "Glücksrad", "zh": "幸运轮盘"},
"gardone_active":        {"fa": "گردونه شانس فعال است!\n\nابتدا عضو کانال شوید سپس برای شرکت کلیک کنید.", "en": "Lucky Wheel is active!\n\nFirst join the channel then click to participate.", "ar": "عجلة الحظ نشطة!\n\nانضم للقناة ثم اضغط للمشاركة.", "tr": "Çarkıfelek aktif!\n\nÖnce kanala katıl sonra tıkla.", "ru": "Колесо удачи активно!\n\nСначала вступите в канал.", "de": "Glücksrad ist aktiv!\n\nTritt zuerst dem Kanal bei.", "zh": "幸运轮盘已开启！\n\n请先加入频道。"},
"gardone_join":          {"fa": "پیوستن به گردونه", "en": "Join Wheel", "ar": "انضم للعجلة", "tr": "Çarka Katıl", "ru": "Присоединиться", "de": "Beitreten", "zh": "加入轮盘"},
"gardone_spin":          {"fa": "چرخاندن گردونه", "en": "Spin Wheel", "ar": "أدر العجلة", "tr": "Çarkı Çevir", "ru": "Крутить", "de": "Drehen", "zh": "转动轮盘"},
"gardone_cancel":        {"fa": "لغو گردونه", "en": "Cancel Wheel", "ar": "إلغاء العجلة", "tr": "Çarkı İptal Et", "ru": "Отменить", "de": "Abbrechen", "zh": "取消轮盘"},
"gardone_joined":        {"fa": "شما با موفقیت پیوستید!", "en": "Successfully joined!", "ar": "انضممت بنجاح!", "tr": "Başarıyla katıldın!", "ru": "Вы успешно присоединились!", "de": "Erfolgreich beigetreten!", "zh": "成功加入！"},
"gardone_already_joined":{"fa": "شما قبلاً شرکت کرده‌اید!", "en": "Already participated!", "ar": "شاركت بالفعل!", "tr": "Zaten katıldın!", "ru": "Вы уже участвовали!", "de": "Schon teilgenommen!", "zh": "你已参加过！"},
"gardone_winner":        {"fa": "برنده مشخص شد!\n\nتبریک به {name} عزیز!", "en": "Winner found!\n\nCongrats {name}!", "ar": "الفائز!\n\nمبروك {name}!", "tr": "Kazanan belli!\n\nTebrikler {name}!", "ru": "Победитель!\n\nПоздравляем {name}!", "de": "Gewinner!\n\nGlückwunsch {name}!", "zh": "中奖者！\n\n恭喜 {name}！"},
"gardone_empty":         {"fa": "هنوز کسی شرکت نکرده است!", "en": "No one joined yet!", "ar": "لم ينضم أحد!", "tr": "Kimse katılmadı!", "ru": "Никто не присоединился!", "de": "Niemand beigetreten!", "zh": "还没有人参加！"},
"gardone_only_starter":  {"fa": "فقط ادمین سازنده می‌تواند!", "en": "Only the creator admin can!", "ar": "فقط المشرف المنشئ!", "tr": "Sadece oluşturan yönetici!", "ru": "Только создатель!", "de": "Nur der Ersteller!", "zh": "只有创建者可操作！"},
"gardone_spinning":      {"fa": "گردونه در حال چرخش است...", "en": "Wheel is spinning...", "ar": "العجلة تدور...", "tr": "Çark dönüyor...", "ru": "Колесо крутится...", "de": "Rad dreht...", "zh": "轮盘转动中..."},
"gardone_cancelled":     {"fa": "گردونه شانس توسط ادمین لغو شد.", "en": "Wheel cancelled by admin.", "ar": "تم إلغاء العجلة من المشرف.", "tr": "Çark yönetici tarafından iptal edildi.", "ru": "Колесо отменено.", "de": "Rad abgebrochen.", "zh": "管理员已取消轮盘。"},
"gardone_participants":  {"fa": "شرکت‌کنندگان ({n} نفر)", "en": "Participants ({n})", "ar": "المشاركون ({n})", "tr": "Katılımcılar ({n})", "ru": "Участники ({n})", "de": "Teilnehmer ({n})", "zh": "参与者（{n} 人）"},
"gardone_nobody":        {"fa": "هنوز کسی ثبت نام نکرده است.", "en": "No one registered yet.", "ar": "لم يسجل أحد بعد.", "tr": "Henüz kimse kayıt olmadı.", "ru": "Ещё никто не зарегистрирован.", "de": "Noch niemand registriert.", "zh": "还没有人注册。"},

# ═══════════════ Anonymous (Eteraf/Gharch)
"eteraf_default_text":  {"fa": "یک موضوع اعتراف جدید شروع شد.\nبرای ارسال اعتراف ناشناس، از دکمه زیر استفاده کنید.", "en": "A new confession topic started.\nUse the button below to send anonymously.", "ar": "بدأ موضوع اعتراف جديد.\nاستخدم الزر أدناه للإرسال المجهول.", "tr": "Yeni itiraf konusu başladı.\nAnonim göndermek için aşağıdaki butonu kullanın.", "ru": "Начата новая тема признаний.\nОтправьте анонимно через кнопку.", "de": "Neues Geständnis-Thema gestartet.\nNutze den Button für anonymes Senden.", "zh": "新的表白话题已开始。\n使用下方按钮匿名发送。"},
"eteraf_send_btn":      {"fa": "ارسال به صورت ناشناس", "en": "Send Anonymously", "ar": "أرسل مجهولاً", "tr": "Anonim Gönder", "ru": "Отправить анонимно", "de": "Anonym senden", "zh": "匿名发送"},
"eteraf_enter_text":    {"fa": "لطفاً متن دلخواه خود را برای شروع اعتراف ارسال کنید.\nبرای لغو /cancel را ارسال کنید.", "en": "Please send your custom text for the confession topic.\nSend /cancel to cancel.", "ar": "أرسل نصك المخصص لموضوع الاعتراف.\nأرسل /cancel للإلغاء.", "tr": "İtiraf konusu için özel metnini gönder.\nİptal için /cancel gönder.", "ru": "Отправьте свой текст для темы признаний.\nДля отмены /cancel.", "de": "Sende deinen Text für das Geständnis-Thema.\n/cancel zum Abbrechen.", "zh": "发送你的自定义文本。\n发送 /cancel 取消。"},
"eteraf_write":         {"fa": "اعتراف خود را بنویسید تا به صورت ناشناس در گروه ارسال شود...", "en": "Write your confession to send anonymously...", "ar": "اكتب اعترافك ليُرسل مجهولاً...", "tr": "Anonim gönderilecek itirafını yaz...", "ru": "Напишите ваше признание анонимно...", "de": "Schreibe dein Geständnis anonym...", "zh": "写下你的表白将匿名发送..."},
"eteraf_sent":          {"fa": "✅ اعتراف شما با موفقیت به صورت ناشناس ارسال شد.", "en": "✅ Confession sent anonymously.", "ar": "✅ تم إرسال اعترافك مجهولاً.", "tr": "✅ İtirafın anonim gönderildi.", "ru": "✅ Признание отправлено анонимно.", "de": "✅ Geständnis anonym gesendet.", "zh": "✅ 表白已匿名发送。"},
"eteraf_header":        {"fa": "#اعتراف_ناشناس 🤫", "en": "#Anonymous_Confession 🤫", "ar": "#اعتراف_مجهول 🤫", "tr": "#Anonim_İtiraf 🤫", "ru": "#Анонимное_Признание 🤫", "de": "#Anonymes_Geständnis 🤫", "zh": "#匿名表白 🤫"},
"gharch_send_btn":      {"fa": "ارسال پیام ناشناس", "en": "Send Anonymous Msg", "ar": "أرسل رسالة مجهولة", "tr": "Anonim Mesaj Gönder", "ru": "Отправить анонимно", "de": "Anonym senden", "zh": "发送匿名消息"},
"gharch_choose_god":    {"fa": "لطفاً یوزرنیم گاد بازی را ارسال کنید (مثال: @GodUsername).\nبرای لغو /cancel را ارسال کنید.", "en": "Please send the God's username (e.g.: @GodUsername).\nSend /cancel to cancel.", "ar": "أرسل اسم المستخدم للإله (مثال: @GodUsername).\nأرسل /cancel للإلغاء.", "tr": "God'un kullanıcı adını gönder (ör: @GodUsername).\nİptal için /cancel.", "ru": "Отправьте юзернейм Бога (@GodUsername).\n/cancel для отмены.", "de": "Sende den God-Benutzernamen (@GodUsername).\n/cancel zum Abbrechen.", "zh": "请发送上帝用户名（如 @GodUsername）。\n发送 /cancel 取消。"},
"gharch_confirm_god":   {"fa": "{god} عزیز،\nشما به عنوان گاد بازی انتخاب شدید. لطفاً تایید کنید.", "en": "Dear {god},\nYou've been chosen as God. Please confirm.", "ar": "{god} العزيز،\nتم اختيارك كإله. يرجى التأكيد.", "tr": "Sevgili {god},\nGod olarak seçildin. Lütfen onayla.", "ru": "{god}, вы выбраны Богом. Подтвердите.", "de": "{god}, du wurdest als Gott gewählt. Bestätige.", "zh": "{god}，你被选为上帝。请确认。"},
"gharch_confirm_btn":   {"fa": "تایید می‌کنم", "en": "I confirm", "ar": "أؤكد", "tr": "Onaylıyorum", "ru": "Подтверждаю", "de": "Bestätigen", "zh": "我确认"},
"gharch_you_are_god":   {"fa": "شما به عنوان گاد تایید شدید!", "en": "You are confirmed as God!", "ar": "تم تأكيدك كإله!", "tr": "God olarak onaylandın!", "ru": "Вы подтверждены как Бог!", "de": "Du bist als Gott bestätigt!", "zh": "你已被确认为上帝！"},
"gharch_not_god":       {"fa": "این درخواست برای شما نیست یا یوزرنیم شما تنظیم نشده.", "en": "Not for you or your username isn't set.", "ar": "ليس لك أو اسم المستخدم غير معد.", "tr": "Senin için değil veya kullanıcı adın ayarlı değil.", "ru": "Не для вас или юзернейм не задан.", "de": "Nicht für dich oder Username fehlt.", "zh": "不是给你的或用户名未设置。"},
"gharch_started":       {"fa": "بازی قارچ شروع شد!\n\nروی دکمه زیر کلیک کن و حرف دلت رو بنویس تا ناشناس در گروه ظاهر بشه!\n\nفقط گاد {god} هویت را می‌بیند.", "en": "Mushroom game started!\n\nClick the button below and write your message anonymously!\n\nOnly God {god} sees the sender.", "ar": "بدأت لعبة الفطر!\n\nاضغط الزر وأرسل رسالتك مجهولاً!\n\nفقط الإله {god} يرى المُرسل.", "tr": "Mantar oyunu başladı!\n\nButona tıkla ve anonim mesajını yaz!\n\nSadece God {god} görür.", "ru": "Грибная игра началась!\n\nНажмите кнопку и отправьте анонимно!\n\nТолько Бог {god} видит отправителя.", "de": "Pilz-Spiel gestartet!\n\nKlicke den Button und sende anonym!\n\nNur Gott {god} sieht den Absender.", "zh": "蘑菇游戏开始！\n\n点击下方按钮匿名发送！\n\n只有上帝 {god} 看到发送者。"},
"gharch_sent":          {"fa": "✅ پیام شما با موفقیت ناشناس ارسال شد.", "en": "✅ Message sent anonymously.", "ar": "✅ تم إرسال رسالتك مجهولاً.", "tr": "✅ Mesajın anonim gönderildi.", "ru": "✅ Сообщение отправлено анонимно.", "de": "✅ Nachricht anonym gesendet.", "zh": "✅ 消息已匿名发送。"},
"gharch_received":      {"fa": "#پیام_ناشناس 🍄", "en": "#Anonymous_Msg 🍄", "ar": "#رسالة_مجهولة 🍄", "tr": "#Anonim_Mesaj 🍄", "ru": "#Анонимное_Сообщение 🍄", "de": "#Anonyme_Nachricht 🍄", "zh": "#匿名消息 🍄"},
"gharch_god_report":    {"fa": "📝 گزارش پیام ناشناس جدید\n\n👤 ارسال کننده:\n- نام: {name}\n- یوزرنیم: @{uname}\n- آیدی: {uid}\n\n📜 متن:\n{msg}", "en": "📝 New anonymous message report\n\n👤 Sender:\n- Name: {name}\n- Username: @{uname}\n- ID: {uid}\n\n📜 Text:\n{msg}", "ar": "📝 تقرير رسالة مجهولة\n\n👤 المرسل:\n- الاسم: {name}\n- المعرف: @{uname}\n- الآيدي: {uid}\n\n📜 النص:\n{msg}", "tr": "📝 Yeni anonim mesaj raporu\n\n👤 Gönderen:\n- Ad: {name}\n- Kullanıcı: @{uname}\n- ID: {uid}\n\n📜 Metin:\n{msg}", "ru": "📝 Отчёт об анонимном сообщении\n\n👤 Отправитель:\n- Имя: {name}\n- Юзернейм: @{uname}\n- ID: {uid}\n\n📜 Текст:\n{msg}", "de": "📝 Neue anonyme Nachricht\n\n👤 Absender:\n- Name: {name}\n- Username: @{uname}\n- ID: {uid}\n\n📜 Text:\n{msg}", "zh": "📝 新的匿名消息报告\n\n👤 发送者：\n- 姓名：{name}\n- 用户名：@{uname}\n- ID：{uid}\n\n📜 文本：\n{msg}"},
"gharch_not_active":    {"fa": "این بازی قارچ دیگر فعال نیست.", "en": "This mushroom game is inactive.", "ar": "لعبة الفطر غير نشطة.", "tr": "Bu mantar oyunu aktif değil.", "ru": "Эта игра неактивна.", "de": "Dieses Pilz-Spiel ist inaktiv.", "zh": "此蘑菇游戏已失效。"},
"gharch_need_start":    {"fa": "لطفاً ابتدا از دکمه گروه شروع کنید.", "en": "Please start from the group button first.", "ar": "ابدأ من زر المجموعة أولاً.", "tr": "Önce gruptaki butondan başla.", "ru": "Начните с кнопки в группе.", "de": "Starte zuerst über den Gruppen-Button.", "zh": "请先从群组按钮开始。"},
"gharch_only_admin":    {"fa": "فقط ادمین‌های گروه می‌توانند این بازی را شروع کنند.", "en": "Only group admins can start this game.", "ar": "فقط مشرفو المجموعة يمكنهم البدء.", "tr": "Sadece grup yöneticileri başlatabilir.", "ru": "Только админы группы могут начать.", "de": "Nur Gruppen-Admins können starten.", "zh": "只有群组管理员可以开始。"},
"gharch_invalid_username": {"fa": "فرمت اشتباه. یوزرنیم را با @ ارسال کنید.", "en": "Wrong format. Send with @.", "ar": "تنسيق خاطئ. أرسل مع @.", "tr": "Yanlış format. @ ile gönder.", "ru": "Неверный формат. С @.", "de": "Falsches Format. Mit @.", "zh": "格式错误。带 @ 发送。"},

# ═══════════════ Stop
"only_admin":         {"fa": "این دستور فقط برای مدیران است.", "en": "Admins only.", "ar": "للمشرفين فقط.", "tr": "Sadece yöneticiler.", "ru": "Только для админов.", "de": "Nur für Admins.", "zh": "仅管理员可用。"},
"stopped_n_games":    {"fa": "✅ {n} بازی فعال لغو شد.", "en": "✅ {n} active games stopped.", "ar": "✅ تم إيقاف {n} لعبة.", "tr": "✅ {n} aktif oyun durduruldu.", "ru": "✅ Остановлено игр: {n}.", "de": "✅ {n} aktive Spiele gestoppt.", "zh": "✅ 已停止 {n} 个游戏。"},
"no_active_games":    {"fa": "هیچ بازی فعالی برای لغو وجود ندارد.", "en": "No active games to stop.", "ar": "لا ألعاب نشطة.", "tr": "Durdurulacak oyun yok.", "ru": "Нет активных игр.", "de": "Keine aktiven Spiele.", "zh": "没有活跃游戏。"},

# ═══════════════ خطاها
"banned":         {"fa": "🚫 حساب شما مسدود است.", "en": "🚫 Your account is banned.", "ar": "🚫 حسابك محظور.", "tr": "🚫 Hesabın yasaklandı.", "ru": "🚫 Ваш аккаунт заблокирован.", "de": "🚫 Dein Konto ist gesperrt.", "zh": "🚫 你的账户已被封禁。"},
"need_join":      {"fa": "❗️ برای استفاده ابتدا در کانال ما عضو شوید.", "en": "❗️ Please join our channel first.", "ar": "❗️ انضم إلى قناتنا أولاً.", "tr": "❗️ Lütfen önce kanalımıza katıl.", "ru": "❗️ Сначала подпишитесь на канал.", "de": "❗️ Tritt zuerst unserem Kanal bei.", "zh": "❗️ 请先加入我们的频道。"},
"need_active_sub":{"fa": "اشتراک شما منقضی شده.", "en": "Subscription expired.", "ar": "انتهى اشتراكك.", "tr": "Aboneliğin sona erdi.", "ru": "Подписка истекла.", "de": "Abo abgelaufen.", "zh": "订阅已过期。"},
"not_member":     {"fa": "هنوز عضو نشدی!", "en": "Not a member yet!", "ar": "لست عضواً بعد!", "tr": "Henüz üye değilsin!", "ru": "Вы не участник!", "de": "Noch kein Mitglied!", "zh": "还不是成员！"},
"error_occured":  {"fa": "خطایی رخ داد. لطفاً مجدداً امتحان کنید.", "en": "An error occurred. Try again.", "ar": "حدث خطأ. حاول مجدداً.", "tr": "Bir hata oluştu. Tekrar dene.", "ru": "Ошибка. Попробуйте снова.", "de": "Fehler aufgetreten. Erneut versuchen.", "zh": "发生错误。请重试。"},

# ═══════════════ پنل ادمین
"admin_panel":    {"fa": "پنل ادمین", "en": "Admin Panel", "ar": "لوحة المشرف", "tr": "Yönetici Paneli", "ru": "Панель админа", "de": "Admin-Panel", "zh": "管理面板"},
"admin_only":     {"fa": "دسترسی ندارید.", "en": "Access denied.", "ar": "لا وصول.", "tr": "Erişim yok.", "ru": "Доступ запрещён.", "de": "Kein Zugriff.", "zh": "无权限。"},
"admin_stats":    {"fa": "آمار ربات", "en": "Bot Stats", "ar": "إحصائيات البوت", "tr": "Bot İstatistikleri", "ru": "Статистика бота", "de": "Bot-Statistik", "zh": "机器人统计"},
"admin_users":    {"fa": "چک کاربر", "en": "Check User", "ar": "فحص مستخدم", "tr": "Kullanıcı Kontrol", "ru": "Проверить юзера", "de": "Nutzer prüfen", "zh": "检查用户"},
"admin_defpacks": {"fa": "پک‌های پیش‌فرض", "en": "Default Packs", "ar": "الباقات الافتراضية", "tr": "Varsayılan Paketler", "ru": "Пакеты по умолчанию", "de": "Standard-Pakete", "zh": "默认包"},
"admin_filters":  {"fa": "فیلترها", "en": "Filters", "ar": "الفلاتر", "tr": "Filtreler", "ru": "Фильтры", "de": "Filter", "zh": "过滤器"},
"admin_locks":    {"fa": "اسپانسری و قفل‌ها", "en": "Sponsorship & Locks", "ar": "الرعاية والأقفال", "tr": "Sponsorluk & Kilitler", "ru": "Спонсорство и блокировки", "de": "Sponsoring & Sperren", "zh": "赞助与锁定"},
"admin_bcast":    {"fa": "ارسال همگانی", "en": "Broadcast", "ar": "بث جماعي", "tr": "Yayın", "ru": "Рассылка", "de": "Rundsendung", "zh": "群发"},
"admin_refs":     {"fa": "مدیریت زیرمجموعه‌ها", "en": "Referrals Mgmt", "ar": "إدارة الإحالات", "tr": "Referans Yönetimi", "ru": "Управление рефералами", "de": "Empfehlungen", "zh": "推荐管理"},
"admin_settings": {"fa": "تنظیمات", "en": "Settings", "ar": "الإعدادات", "tr": "Ayarlar", "ru": "Настройки", "de": "Einstellungen", "zh": "设置"},
"admin_admins":   {"fa": "مدیریت ادمین‌ها", "en": "Manage Admins", "ar": "إدارة المشرفين", "tr": "Yöneticiler", "ru": "Управление админами", "de": "Admins verwalten", "zh": "管理员管理"},
"admin_backup":   {"fa": "بکاپ و ریستور", "en": "Backup & Restore", "ar": "نسخ احتياطي واستعادة", "tr": "Yedekle & Geri Yükle", "ru": "Бэкап и восстановление", "de": "Backup & Restore", "zh": "备份与恢复"},
}

# ═══════════════ کلیدهای جدید — افزودن به T
T.update({
    "pm_welcome_title": {
        "fa": "سلام {name} عزیز!\n\nبه راینوبازی خوش آمدید!",
        "en": "Hello {name}!\n\nWelcome to Rhino Games!",
        "ar": "مرحباً {name}!\n\nأهلاً بك في ألعاب رينو!",
        "tr": "Merhaba {name}!\n\nRhino Oyunları'na hoş geldiniz!",
        "ru": "Привет, {name}!\n\nДобро пожаловать в Rhino Games!",
        "de": "Hallo {name}!\n\nWillkommen bei Rhino Games!",
        "zh": "你好 {name}！\n\n欢迎来到 Rhino Games！",
    },
    "pm_welcome_body": {
        "fa": "برای شروع بازی‌ها، ربات را به گروه اضافه کنید.\nبازی‌ها فقط در گروه‌ها قابل اجرا هستند.",
        "en": "To start playing, add the bot to a group.\nGames only work in groups.",
        "ar": "للبدء في اللعب، أضف البوت إلى مجموعة.\nالألعاب تعمل فقط في المجموعات.",
        "tr": "Oynamak için botu bir gruba ekleyin.\nOyunlar yalnızca gruplarda çalışır.",
        "ru": "Чтобы начать играть, добавьте бота в группу.\nИгры работают только в группах.",
        "de": "Um zu spielen, füge den Bot einer Gruppe hinzu.\nSpiele funktionieren nur in Gruppen.",
        "zh": "要开始游戏，请将机器人添加到群组。\n游戏只在群组中可用。",
    },
    "btn_add_to_group": {
        "fa": "افزودن به گروه", "en": "Add to Group",
        "ar": "أضف إلى مجموعة", "tr": "Gruba Ekle",
        "ru": "Добавить в группу", "de": "Zur Gruppe hinzufügen",
        "zh": "添加到群组",
    },
    "btn_change_lang": {
        "fa": "تغییر زبان", "en": "Change Language",
        "ar": "تغيير اللغة", "tr": "Dili Değiştir",
        "ru": "Изменить язык", "de": "Sprache ändern",
        "zh": "更改语言",
    },
    "btn_donate": {
        "fa": "حمایت با استارز", "en": "Support with Stars",
        "ar": "ادعم بالنجوم", "tr": "Yıldızla Destekle",
        "ru": "Поддержать звёздами", "de": "Mit Sternen unterstützen",
        "zh": "用星星支持",
    },
    "donate_title": {
        "fa": "❤️ حمایت از راینوبازی\n\nبابت حمایت شما سپاسگزاریم! 🙏\n\nتعداد ستاره‌ای که می‌خواهید اهدا کنید را انتخاب کنید:\n\n💡 ستاره‌ها ایمن و سریع از طریق تلگرام پرداخت می‌شوند.",
        "en": "❤️ Support Rhino Games\n\nThank you for your support! 🙏\n\nChoose the amount of Stars you want to donate:\n\n💡 Stars are paid securely and quickly through Telegram.",
        "ar": "❤️ ادعم ألعاب رينو\n\nشكراً لدعمك! 🙏\n\nاختر عدد النجوم التي تريد التبرع بها:\n\n💡 تُدفع النجوم بأمان وسرعة عبر تلغرام.",
        "tr": "❤️ Rhino Oyunları'nı Destekle\n\nDesteğiniz için teşekkürler! 🙏\n\nBağışlamak istediğiniz Yıldız miktarını seçin:\n\n💡 Yıldızlar Telegram üzerinden güvenli ve hızlı ödenir.",
        "ru": "❤️ Поддержать Rhino Games\n\nСпасибо за поддержку! 🙏\n\nВыберите количество звёзд:\n\n💡 Звёзды оплачиваются безопасно через Telegram.",
        "de": "❤️ Rhino Games unterstützen\n\nDanke für deine Unterstützung! 🙏\n\nWähle die Anzahl der Sterne:\n\n💡 Sterne werden sicher über Telegram bezahlt.",
        "zh": "❤️ 支持 Rhino Games\n\n感谢您的支持！🙏\n\n选择您想捐赠的星星数量：\n\n💡 星星通过 Telegram 安全快速支付。",
    },
    "donate_custom": {
        "fa": "✏️ مقدار دلخواه", "en": "✏️ Custom Amount",
        "ar": "✏️ مقدار مخصص", "tr": "✏️ Özel Miktar",
        "ru": "✏️ Своя сумма", "de": "✏️ Eigener Betrag",
        "zh": "✏️ 自定义金额",
    },
    "donate_custom_prompt": {
        "fa": "تعداد ستاره (بین ۱ تا ۱۰۰۰۰) را بنویسید:\nبرای لغو /cancel را بزنید.",
        "en": "Enter the number of Stars (1 to 10000):\nSend /cancel to cancel.",
        "ar": "أدخل عدد النجوم (1 إلى 10000):\nأرسل /cancel للإلغاء.",
        "tr": "Yıldız sayısını girin (1-10000):\nİptal için /cancel gönderin.",
        "ru": "Введите количество звёзд (от 1 до 10000):\n/cancel для отмены.",
        "de": "Gib die Anzahl der Sterne ein (1 bis 10000):\n/cancel zum Abbrechen.",
        "zh": "输入星星数量（1 到 10000）：\n发送 /cancel 取消。",
    },
    "donate_invoice_title": {
        "fa": "حمایت از راینوبازی", "en": "Support Rhino Games",
        "ar": "ادعم ألعاب رينو", "tr": "Rhino Oyunları'nı Destekle",
        "ru": "Поддержать Rhino Games", "de": "Rhino Games unterstützen",
        "zh": "支持 Rhino Games",
    },
    "donate_invoice_desc": {
        "fa": "اهدا {n} ستاره", "en": "Donate {n} Stars",
        "ar": "تبرع بـ {n} نجمة", "tr": "{n} Yıldız bağışla",
        "ru": "Пожертвовать {n} звёзд", "de": "{n} Sterne spenden",
        "zh": "捐赠 {n} 星星",
    },
    "donate_thanks": {
        "fa": "🙏 از حمایت شما سپاسگزاریم!\n⭐ مقدار: {n} ستاره",
        "en": "🙏 Thank you for your support!\n⭐ Amount: {n} Stars",
        "ar": "🙏 شكراً لدعمك!\n⭐ المقدار: {n} نجمة",
        "tr": "🙏 Desteğiniz için teşekkürler!\n⭐ Miktar: {n} Yıldız",
        "ru": "🙏 Спасибо за поддержку!\n⭐ Сумма: {n} звёзд",
        "de": "🙏 Danke für deine Unterstützung!\n⭐ Betrag: {n} Sterne",
        "zh": "🙏 感谢您的支持！\n⭐ 数量：{n} 星星",
    },
    "force_join_msg": {
        "fa": "🔒 برای استفاده از ربات ابتدا در کانال‌های زیر عضو شوید:",
        "en": "🔒 Please join our channels first:",
        "ar": "🔒 يرجى الانضمام إلى قنواتنا أولاً:",
        "tr": "🔒 Lütfen önce kanallarımıza katılın:",
        "ru": "🔒 Сначала подпишитесь на наши каналы:",
        "de": "🔒 Bitte treten Sie zuerst unseren Kanälen bei:",
        "zh": "🔒 请先加入我们的频道：",
    },
    "force_join_btn": {
        "fa": "عضویت", "en": "Join", "ar": "انضم", "tr": "Katıl",
        "ru": "Подписаться", "de": "Beitreten", "zh": "加入",
    },
    "force_join_check": {
        "fa": "✅ عضو شدم", "en": "✅ I Joined",
        "ar": "✅ انضممت", "tr": "✅ Katıldım",
        "ru": "✅ Я подписался", "de": "✅ Ich bin beigetreten",
        "zh": "✅ 我已加入",
    },
    "force_join_alert": {
        "fa": "🔒 ابتدا در کانال‌ها عضو شوید",
        "en": "🔒 Join our channels first",
        "ar": "🔒 انضم إلى قنواتنا أولاً",
        "tr": "🔒 Önce kanallarımıza katıl",
        "ru": "🔒 Сначала подпишитесь",
        "de": "🔒 Tritt zuerst bei",
        "zh": "🔒 请先加入频道",
    },
    "panel_group_only": {
        "fa": "🔒 این پنل فقط در گروه‌ها کار می‌کند.\n\nربات را به گروه اضافه کنید و از آنجا بازی کنید.",
        "en": "🔒 This panel only works in groups.\n\nAdd the bot to a group to play.",
        "ar": "🔒 هذه اللوحة تعمل فقط في المجموعات.\n\nأضف البوت إلى مجموعة.",
        "tr": "🔒 Bu panel yalnızca gruplarda çalışır.\n\nBotu bir gruba ekleyin.",
        "ru": "🔒 Эта панель работает только в группах.\n\nДобавьте бота в группу.",
        "de": "🔒 Dieses Panel funktioniert nur in Gruppen.\n\nFüge den Bot einer Gruppe hinzu.",
        "zh": "🔒 此面板只在群组中可用。\n\n将机器人添加到群组。",
    },
    "inline_join_required": {
        "fa": "🔒 برای استفاده ابتدا در کانال‌ها عضو شوید",
        "en": "🔒 Please join our channels first",
        "ar": "🔒 انضم إلى قنواتنا أولاً",
        "tr": "🔒 Önce kanallarımıza katılın",
        "ru": "🔒 Сначала подпишитесь на каналы",
        "de": "🔒 Bitte zuerst beitreten",
        "zh": "🔒 请先加入频道",
    },
    "inline_open_bot": {
        "fa": "🎮 باز کردن ربات برای شروع",
        "en": "🎮 Open bot to start",
        "ar": "🎮 افتح البوت للبدء",
        "tr": "🎮 Başlamak için botu aç",
        "ru": "🎮 Открыть бота для старта",
        "de": "🎮 Bot öffnen zum Starten",
        "zh": "🎮 打开机器人开始",
    },
})

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
    """پر کردن کش از دیتابیس در هنگام استارت"""
    if lang and lang in LANGS:
        _user_lang_cache[user_id] = lang

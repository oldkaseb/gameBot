"""تایپ سرعتی — با ایموجی پریمیوم و ۷ زبان"""

import io
import random
from datetime import datetime
from aiogram import Router, F
from aiogram.types import CallbackQuery, Message, BufferedInputFile
from aiogram.enums import ParseMode
from PIL import Image, ImageDraw, ImageFont
import arabic_reshaper
from bidi.algorithm import get_display
import logging

from emojis import E
from langs import t, get_user_lang
from utils.premium import success, danger, kb
from . import state

router = Router(name="typing_game")
log = logging.getLogger("typing")

# ─────────── جملات (فارسی + انگلیسی)
SENTENCES = {
    "fa": [
        "آب از سرچشمه گل آلود است",
        "با یک گل بهار نمیشود",
        "باد آورده را باد میبرد",
        "جوجه را آخر پاییز میشمارند",
        "دوری و دوستی",
        "سکوت علامت رضاست",
        "عجله کار شیطان است",
        "هرکه بامش بیش برفش بیشتر",
        "یک دست صدا ندارد",
        "اول چاه را بکن بعد منارش را بدزد",
        "هر سخن جایی و هر نکته مکانی دارد",
        "توانا بود هر که دانا بود",
        "به پایان آمد این دفتر حکایت همچنان باقیست",
        "کوه به کوه نمیرسد آدم به آدم میرسد",
        "تا تنور داغ است باید نان را چسباند",
        "خدا گر ز حکمت ببندد دری ز رحمت گشاید در دیگری",
        "بهترین راه پیش بینی آینده ساختن آن است",
        "هرگز برای یادگیری دیر نیست",
        "برای پرواز کردن نیازی به بال نیست داشتن اراده کافیست",
        "یک سفر هزار کیلومتری با اولین قدم آغاز میشود",
    ],
    "en": [
        "The quick brown fox jumps over the lazy dog",
        "Actions speak louder than words",
        "Practice makes perfect",
        "Better late than never",
        "The pen is mightier than the sword",
        "Where there is a will there is a way",
        "A journey of a thousand miles begins with a single step",
        "The early bird catches the worm",
        "Honesty is the best policy",
        "Knowledge is power",
        "Time is money",
        "Every cloud has a silver lining",
        "Rome was not built in a day",
        "All that glitters is not gold",
        "The best way to predict the future is to create it",
    ],
    "ar": [
        "العلم نور والجهل ظلام",
        "الصبر مفتاح الفرج",
        "من جد وجد ومن زرع حصد",
        "خير الكلام ما قل ودل",
        "الوقت كالسيف إن لم تقطعه قطعك",
        "لا تؤجل عمل اليوم إلى الغد",
        "الكتاب خير جليس في الزمان",
        "الأمل يفتح أبواباً لا يفتحها اليأس",
    ],
    "tr": [
        "Bir elin nesi var iki elin sesi var",
        "Damlaya damlaya göl olur",
        "Bugünün işini yarına bırakma",
        "Sabreden derviş muradına ermiş",
        "Ağaç yaşken eğilir",
        "Az veren candan çok veren maldan",
    ],
    "ru": [
        "Терпение и труд всё перетрут",
        "Семь раз отмерь один раз отрежь",
        "Не откладывай на завтра то что можно сделать сегодня",
        "Ученье свет а неученье тьма",
        "Тише едешь дальше будешь",
        "Повторение мать учения",
    ],
    "de": [
        "Übung macht den Meister",
        "Aller Anfang ist schwer",
        "Morgenstund hat Gold im Mund",
        "Wer nicht wagt der nicht gewinnt",
        "Der frühe Vogel fängt den Wurm",
        "Reden ist Silber Schweigen ist Gold",
    ],
    "zh": [
        "千里之行始于足下",
        "熟能生巧",
        "有志者事竟成",
        "水滴石穿",
        "早起的鸟儿有虫吃",
        "活到老学到老",
    ],
}


def _pick_sentence(lang: str) -> str:
    pool = SENTENCES.get(lang) or SENTENCES["fa"]
    return random.choice(pool)


def _render_image(text: str, lang: str) -> io.BytesIO:
    """تصویر جملات فارسی/عربی را به درستی می‌چیند"""
    display = text
    if lang in ("fa", "ar"):
        reshaped = arabic_reshaper.reshape(text)
        display = get_display(reshaped)

    # فونت
    try:
        font = ImageFont.truetype("Vazir.ttf", 28)
    except IOError:
        log.warning("Vazir.ttf not found, using default")
        font = ImageFont.load_default()

    # اندازه
    dummy = Image.new("RGB", (1, 1))
    draw = ImageDraw.Draw(dummy)
    bbox = draw.textbbox((0, 0), display, font=font)
    w = bbox[2] - bbox[0] + 60
    h = bbox[3] - bbox[1] + 60

    img = Image.new("RGB", (max(w, 400), max(h, 120)), color=(30, 30, 46))
    draw = ImageDraw.Draw(img)
    draw.text((30, 30), display, fill=(255, 255, 255), font=font)

    buf = io.BytesIO()
    buf.name = "typing.jpeg"
    img.save(buf, "JPEG", quality=92)
    buf.seek(0)
    return buf


# ─────────── شروع
@router.callback_query(F.data.startswith("type_start_"))
async def start(cb: CallbackQuery):
    uid = cb.from_user.id
    lang = get_user_lang(uid)
    chat_id = cb.message.chat.id

    try:
        target = int(cb.data.rsplit("_", 1)[1])
    except (ValueError, IndexError):
        await cb.answer("❌", show_alert=True)
        return
    if uid != target:
        await cb.answer(t("not_your_panel", lang), show_alert=True)
        return

    if chat_id in state.active_games["typing"] and state.active_games["typing"][chat_id]:
        await cb.answer(t("game_already_running", lang), show_alert=True)
        return

    await cb.answer()
    sentence = _pick_sentence(lang)

    game = {
        "sentence": sentence,
        "start_time": datetime.now(),
        "lang": lang,
    }
    state.register("typing", chat_id, cb.message.message_id, game)

    await cb.message.edit_text(f"{E.HOURGLASS} 3… 2… 1…", parse_mode=ParseMode.HTML)

    image = _render_image(sentence, lang)
    await cb.bot.send_photo(
        chat_id,
        BufferedInputFile(image.read(), filename="typing.jpg"),
        caption=(
            f"{E.MIC}{E.SPARK} <b>{t('typing_games_title', lang)}</b>\n\n"
            f"{E.ZAP} {t('guess_one_letter', lang).replace('حرف', 'جمله').replace('letter', 'sentence')}"
        ),
        parse_mode=ParseMode.HTML,
    )


# ─────────── بررسی تایپ
@router.message(F.chat.type.in_({"group", "supergroup"}), F.text)
async def on_typing(message: Message):
    chat_id = message.chat.id
    games = state.active_games["typing"].get(chat_id, {})
    if not games:
        return

    game = next(iter(games.values()), None)
    if not game:
        return

    user_input = (message.text or "").strip()
    expected = game["sentence"].strip()

    # نرمال‌سازی: تبدیل ی/ك عربی، حذف فاصله‌های اضافی
    def norm(s: str) -> str:
        return s.replace("ي", "ی").replace("ك", "ک").strip()

    if norm(user_input) != norm(expected):
        return

    # ─── برنده
    duration = (datetime.now() - game["start_time"]).total_seconds()
    uid = message.from_user.id
    lang = get_user_lang(uid)

    await message.reply(
        f"{E.TROPHY}{E.PARTY} <b>{t('game_winner', lang, name=message.from_user.first_name)}</b>\n\n"
        f"{E.HOURGLASS} {t('solved_in_seconds', lang, n=f'{duration:.2f}')}",
        parse_mode=ParseMode.HTML,
    )

    # ذخیره در leaderboard
    try:
        from database import db
        await db.pool.execute(
            """INSERT INTO game_wins (user_id, game_type, wins, best_time)
               VALUES ($1, 'typing', 1, $2)
               ON CONFLICT (user_id, game_type) DO UPDATE
               SET wins = game_wins.wins + 1,
                   best_time = LEAST(COALESCE(game_wins.best_time, 999999), EXCLUDED.best_time)""",
            uid, duration,
        )
    except Exception as e:
        log.debug(f"leaderboard save failed: {e}")

    # پاک‌سازی
    gid = next(iter(games.keys()))
    state.unregister("typing", chat_id, gid)

# -*- coding: utf-8 -*-
"""games/demon_tower.py — موتور کامل ۷ زبانه برج شیاطین (Demon Tower) + دیتابیس + دستور «پنل برج» در پیوی"""

import json
import math
import os
import random
import string
import time
from aiogram import Router, F, Bot
from aiogram.types import Message, CallbackQuery, LabeledPrice
from aiogram.enums import ParseMode
from aiogram.filters import Command, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

from database import db
from emojis import E
from utils.premium import primary, success, danger, kb

router = Router(name="demon_tower")
OWNER_IDS = {7662192190, 6041119040}
OWNER_USERNAME = "oldkaseb"

STAR_PACKAGES = {
    "pack_1": {"stars": 50,  "coins": 2500,  "xp": 300,  "title": "Starter Hunter (2,500 Coins + 300 XP)"},
    "pack_2": {"stars": 150, "coins": 9000,  "xp": 1000, "title": "Blood Knight (9,000 Coins + 1,000 XP)"},
    "pack_3": {"stars": 400, "coins": 28000, "xp": 3000, "title": "Tower Lord (28,000 Coins + 3,000 XP)"},
    "pack_4": {"stars": 900, "coins": 75000, "xp": 8000, "title": "Demon Emperor (75,000 Coins + 8,000 XP)"},
}

DT_MESSAGES = {
    "fa": {
        "banned": "⛔ حساب شما در بازی برج شیاطین مسدود شده است.",
        "dev_mode": "🛠️ بازی برج شیاطین در حال توسعه است (فقط مالک دسترسی دارد).",
        "gender_locked": "کاراکتر شما قبلاً انتخاب شده و غیرقابل تغییر است!",
        "gender_saved": "✅ کاراکتر شما برای همیشه ثبت شد!",
        "item_not_found": "آیتم یافت نشد!",
        "equipped": "✅ آیتم «{name}» تجهیز شد!",
        "not_enough_coins": "سکه کافی ندارید! ({price} سکه نیاز است)",
        "bought_equipped": "✅ آیتم «{name}» خریداری و تجهیز شد!",
        "pick_gender_first": "ابتدا از بخش «کاراکتر» جنسیت خود را انتخاب کنید!",
        "sleeping": "😴 انسانیت شما صفر شده و کاراکتر در خواب ۲ روزه است ({hrs} ساعت باقی‌مانده).",
        "in_hospital": "🏥 شما در بیمارستان بستری هستید ({sec} ثانیه تا ترخیص).",
        "low_hp": "🩸 جان شما بسیار کم است! ابتدا به بیمارستان بروید.",
        "all_cleared": "🎉 شما تمام طبقات موجود برج را فتح کرده‌اید!",
        "floor_won": "🏆 طبقه {floor} ({boss}) فتح شد!\n🪙 +{coins} سکه | ⭐ +{xp} XP\n🎁 غنیمت: {drop}\n🩸 آسیب: {dmg} (انسانیت: {hum}%)",
        "sleep_triggered": "\n⚠️ انسانیت شما به صفر رسید و کاراکتر ۲ روز به خواب رفت!",
        "floor_lost": "💀 در برابر «{boss}» شکست خوردی و مجروح شدی! به بیمارستان مراجعه کن.",
        "already_hospital": "شما هم‌اکنون در حال درمان هستید!",
        "full_hp_hum": "جان و انسانیت شما کاملاً پر است!",
        "hospital_entered": "🏥 بستری شدید. زمان درمان بر اساس آسیب: {sec} ثانیه.",
        "empty_loot": "کیف غنیمت‌های شما خالی است!",
        "loot_sold": "💰 تمام غنیمت‌ها به مبلغ {val} سکه فروخته شد!",
        "invalid_amount": "مقدار سکه نامعتبر است!",
        "bank_deposited": "🏦 {amt} سکه در بانک ذخیره شد (سود ساعتی ۲٪ فعال است).",
        "bank_withdrawn": "🪙 {amt} سکه از بانک به کیف پول منتقل شد.",
        "min_transfer": "حداقل مبلغ انتقال ۱۰ سکه است!",
        "user_not_found": "کاربر مقصد در ربات یافت نشد!",
        "transfer_ok": "✅ {amt} سکه ارسال شد.\n📉 کسر ۳٪ مالیات ({tax} سکه) — دریافتی خالص: {net} سکه.",
        "invalid_gift": "❌ کد هدیه نامعتبر یا منقضی است!",
        "gift_used": "⚠️ شما قبلاً از این کد استفاده کرده‌اید!",
        "gift_full": "⚠️ ظرفیت این کد هدیه تمام شده است!",
        "gift_ok": "🎉 کد هدیه اعمال شد! +{coins} سکه و +{xp} XP دریافت کردید.",
        "min_voucher": "حداقل سکه پیشنهادی برای درخواست ووچر ۱۰۰ سکه است!",
        "voucher_sent": "⏳ درخواست ثبت شد و برای مالک ارسال گردید. در انتظار پاسخ مالک...",
    },
    "en": {
        "banned": "⛔ Your Demon Tower account is banned.",
        "dev_mode": "🛠️ Demon Tower is under maintenance (Owner only).",
        "gender_locked": "Character gender is already chosen and cannot be changed!",
        "gender_saved": "✅ Your character has been permanently registered!",
        "item_not_found": "Item not found!",
        "equipped": "✅ '{name}' equipped!",
        "not_enough_coins": "Not enough coins! ({price} required)",
        "bought_equipped": "✅ '{name}' purchased and equipped!",
        "pick_gender_first": "Please select your character gender in 'Character' menu first!",
        "sleeping": "😴 Humanity reached 0! Character is sleeping for 2 days ({hrs}h left).",
        "in_hospital": "🏥 You are recovering in the hospital ({sec}s left).",
        "low_hp": "🩸 Your HP is too low! Visit the hospital first.",
        "all_cleared": "🎉 You have conquered all available floors!",
        "floor_won": "🏆 Floor {floor} ({boss}) Cleared!\n🪙 +{coins} Coins | ⭐ +{xp} XP\n🎁 Loot: {drop}\n🩸 Damage taken: {dmg} (Humanity: {hum}%)",
        "sleep_triggered": "\n⚠️ Humanity hit 0! Your character fell asleep for 2 days!",
        "floor_lost": "💀 Defeated by '{boss}'! Go to the hospital to heal.",
        "already_hospital": "You are already being treated!",
        "full_hp_hum": "Your HP and Humanity are already full!",
        "hospital_entered": "🏥 Admitted to hospital. Recovery time: {sec}s.",
        "empty_loot": "Your loot bag is empty!",
        "loot_sold": "💰 All loot sold for {val} coins!",
        "invalid_amount": "Invalid coin amount!",
        "bank_deposited": "🏦 {amt} coins deposited in bank (2% hourly interest active).",
        "bank_withdrawn": "🪙 {amt} coins withdrawn to wallet.",
        "min_transfer": "Minimum transfer is 10 coins!",
        "user_not_found": "Target user not found in bot!",
        "transfer_ok": "✅ {amt} coins sent.\n📉 3% Tax ({tax} coins) — Net received: {net} coins.",
        "invalid_gift": "❌ Invalid or expired gift code!",
        "gift_used": "⚠️ You already used this gift code!",
        "gift_full": "⚠️ Gift code usage limit reached!",
        "gift_ok": "🎉 Gift redeemed! +{coins} Coins & +{xp} XP added.",
        "min_voucher": "Minimum offer for a voucher is 100 coins!",
        "voucher_sent": "⏳ Request sent to Owner. Waiting for owner response...",
    },
    "ar": {
        "banned": "⛔ حسابك محظور في برج الشياطين.",
        "dev_mode": "🛠️ اللعبة قيد التطوير حالياً (للمالك فقط).",
        "gender_locked": "تم اختيار الشخصية مسبقاً ولا يمكن تغييرها!",
        "gender_saved": "✅ تم تسجيل شخصيتك بنجاح!",
        "item_not_found": "العنصر غير موجود!",
        "equipped": "✅ تم تجهيز «{name}»!",
        "not_enough_coins": "عملاتك غير كافية! (مطلوب {price})",
        "bought_equipped": "✅ تم شراء وتجهيز «{name}»!",
        "pick_gender_first": "اختر جنس شخصيتك من قسم «الشخصية» أولاً!",
        "sleeping": "😴 وصلت الإنسانية إلى 0! الشخصية نائمة لمدة يومين ({hrs} ساعة متبقية).",
        "in_hospital": "🏥 أنت في المستشفى للعلاج ({sec} ثانية متبقية).",
        "low_hp": "🩸 صحتك منخفضة جداً! اذهب إلى المستشفى أولاً.",
        "all_cleared": "🎉 لقد فتحت جميع طوابق البرج!",
        "floor_won": "🏆 تم فتح الطابق {floor} ({boss})!\n🪙 +{coins} عملة | ⭐ +{xp} XP\n🎁 الغنيمة: {drop}\n🩸 الضرر: {dmg} (الإنسانية: {hum}%)",
        "sleep_triggered": "\n⚠️ وصلت الإنسانية إلى الصفر ونامت الشخصية ليومين!",
        "floor_lost": "💀 هُزمت أمام «{boss}»! اذهب للمستشفى للعلاج.",
        "already_hospital": "أنت قيد العلاج بالفعل!",
        "full_hp_hum": "صحتك وإنسانيتك كاملة!",
        "hospital_entered": "🏥 دخلت المستشفى. وقت العلاج: {sec} ثانية.",
        "empty_loot": "حقيبة الغنائم فارغة!",
        "loot_sold": "💰 تم بيع الغنائم مقابل {val} عملة!",
        "invalid_amount": "كمية غير صالحة!",
        "bank_deposited": "🏦 تم إيداع {amt} عملة في البنك (ربح 2% كل ساعة).",
        "bank_withdrawn": "🪙 تم سحب {amt} عملة إلى المحفظة.",
        "min_transfer": "الحد الأدنى للتحويل 10 عملات!",
        "user_not_found": "المستخدم غير موجود في البوت!",
        "transfer_ok": "✅ تم إرسال {amt} عملة.\n📉 ضريبة 3% ({tax}) — الصافي: {net} عملة.",
        "invalid_gift": "❌ كود الهدية غير صالح!",
        "gift_used": "⚠️ لقد استخدمت هذا الكود مسبقاً!",
        "gift_full": "⚠️ انتهت صلاحية استخدام هذا الكود!",
        "gift_ok": "🎉 تم تفعيل الكود! +{coins} عملة و +{xp} XP.",
        "min_voucher": "الحد الأدنى لطلب القسيمة 100 عملة!",
        "voucher_sent": "⏳ تم إرسال طلبك للمالك. بانتظار رد المالك...",
    },
    "tr": {
        "banned": "⛔ Şeytan Kulesi hesabınız yasaklandı.",
        "dev_mode": "🛠️ Oyun geliştirme aşamasında (Sadece kurucu girebilir).",
        "gender_locked": "Karakter zaten seçildi ve değiştirilemez!",
        "gender_saved": "✅ Karakteriniz kalıcı olarak kaydedildi!",
        "item_not_found": "Eşya bulunamadı!",
        "equipped": "✅ '{name}' kuşanıldı!",
        "not_enough_coins": "Yetersiz altın! ({price} gerekli)",
        "bought_equipped": "✅ '{name}' satın alındı ve kuşanıldı!",
        "pick_gender_first": "Önce 'Karakter' bölümünden cinsiyet seçin!",
        "sleeping": "😴 İnsanlık 0 oldu! Karakter 2 روز uykuda ({hrs} saat kaldı).",
        "in_hospital": "🏥 Hastanede tedavi görüyorsunuz ({sec} sn kaldı).",
        "low_hp": "🩸 Canınız çok az! Önce hastaneye gidin.",
        "all_cleared": "🎉 Tüm katları temizlediniz!",
        "floor_won": "🏆 Kat {floor} ({boss}) Geçildi!\n🪙 +{coins} Altın | ⭐ +{xp} XP\n🎁 Ganimet: {drop}\n🩸 Hasar: {dmg} (İnsanlık: {hum}%)",
        "sleep_triggered": "\n⚠️ İnsanlık 0 oldu, karakter 2 gün uykuya daldı!",
        "floor_lost": "💀 '{boss}' karşısında yenildin! Hastaneye git.",
        "already_hospital": "Zaten tedavi oluyorsunuz!",
        "full_hp_hum": "Can ve İnsanlık zaten dolu!",
        "hospital_entered": "🏥 Hastaneye yatıldı. Süre: {sec} sn.",
        "empty_loot": "Ganimet çantanız boş!",
        "loot_sold": "💰 Ganimetler {val} altına satıldı!",
        "invalid_amount": "Geçersiz miktar!",
        "bank_deposited": "🏦 {amt} altın bankaya yatırıldı (Saatlik %2 faiz).",
        "bank_withdrawn": "🪙 {amt} altın cüzdana çekildi.",
        "min_transfer": "Minimum transfer 10 altındır!",
        "user_not_found": "Kullanıcı bulunamadı!",
        "transfer_ok": "✅ {amt} altın gönderildi.\n📉 %3 Vergi ({tax}) — Net: {net} altın.",
        "invalid_gift": "❌ Geçersiz hediye kodu!",
        "gift_used": "⚠️ Bu kodu zaten kullandınız!",
        "gift_full": "⚠️ Kod kullanım limiti doldu!",
        "gift_ok": "🎉 Hediye alındı! +{coins} Altın & +{xp} XP.",
        "min_voucher": "Minimum teklif 100 altındır!",
        "voucher_sent": "⏳ Talep kurucuya iletildi. Yanıt bekleniyor...",
    },
    "ru": {
        "banned": "⛔ Ваш аккаунт в Башне Демонов заблокирован.",
        "dev_mode": "🛠️ Игра в разработке (доступ только для владельца).",
        "gender_locked": "Персонаж уже выбран и не может быть изменён!",
        "gender_saved": "✅ Персонаж сохранён навсегда!",
        "item_not_found": "Предмет не найден!",
        "equipped": "✅ «{name}» экипировано!",
        "not_enough_coins": "Недостаточно монет! (нужно {price})",
        "bought_equipped": "✅ «{name}» куплено и экипировано!",
        "pick_gender_first": "Сначала выберите пол в меню «Персонаж»!",
        "sleeping": "😴 Человечность на 0! Сон на 2 дня (осталось {hrs} ч.).",
        "in_hospital": "🏥 Вы на лечении в больнице (осталось {sec} сек).",
        "low_hp": "🩸 Мало здоровья! Сначала посетите больницу.",
        "all_cleared": "🎉 Вы прошли все этажи башни!",
        "floor_won": "🏆 Этаж {floor} ({boss}) пройден!\n🪙 +{coins} монет | ⭐ +{xp} XP\n🎁 Добыча: {drop}\n🩸 Урон: {dmg} (Человечность: {hum}%)",
        "sleep_triggered": "\n⚠️ Человечность 0! Персонаж уснул на 2 дня!",
        "floor_lost": "💀 Поражение от «{boss}»! Идите в больницу.",
        "already_hospital": "Вы уже лечитесь!",
        "full_hp_hum": "Здоровье и человечность полные!",
        "hospital_entered": "🏥 Госпитализация. Время лечения: {sec} сек.",
        "empty_loot": "Сумка добычи пуста!",
        "loot_sold": "💰 Добыча продана за {val} монет!",
        "invalid_amount": "Неверная сумма!",
        "bank_deposited": "🏦 {amt} монет положено в банк (+2% в час).",
        "bank_withdrawn": "🪙 {amt} монет снято со счёта.",
        "min_transfer": "Минимум для перевода — 10 монет!",
        "user_not_found": "Пользователь не найден!",
        "transfer_ok": "✅ Отправлено {amt} монет.\n📉 Налог 3% ({tax}) — Получено: {net}.",
        "invalid_gift": "❌ Неверный промокод!",
        "gift_used": "⚠️ Вы уже использовали этот код!",
        "gift_full": "⚠️ Лимит кода исчерпан!",
        "gift_ok": "🎉 Код активирован! +{coins} монет и +{xp} XP.",
        "min_voucher": "Минимум для ваучера — 100 монет!",
        "voucher_sent": "⏳ Запрос отправлен владельцу. Ожидайте ответа...",
    },
    "de": {
        "banned": "⛔ Dein Dämonenturm-Konto ist gesperrt.",
        "dev_mode": "🛠️ Dämonenturm ist im Wartungsmodus (Nur Owner).",
        "gender_locked": "Charakter wurde bereits gewählt!",
        "gender_saved": "✅ Charakter dauerhaft gespeichert!",
        "item_not_found": "Item nicht gefunden!",
        "equipped": "✅ '{name}' ausgerüstet!",
        "not_enough_coins": "Nicht genug Münzen! ({price} nötig)",
        "bought_equipped": "✅ '{name}' gekauft und ausgerüstet!",
        "pick_gender_first": "Wähle zuerst dein Geschlecht im 'Charakter' Menü!",
        "sleeping": "😴 Menschlichkeit 0! 2 Tage Schlaf ({hrs} Std übrig).",
        "in_hospital": "🏥 Du bist im Krankenhaus ({sec}s übrig).",
        "low_hp": "🩸 Zu wenig HP! Geh ins Krankenhaus.",
        "all_cleared": "🎉 Alle Etagen geschafft!",
        "floor_won": "🏆 Etage {floor} ({boss}) besiegt!\n🪙 +{coins} | ⭐ +{xp} XP\n🎁 Beute: {drop}\n🩸 Schaden: {dmg} (Menschlichkeit: {hum}%)",
        "sleep_triggered": "\n⚠️ Menschlichkeit 0! 2 Tage Schlaf!",
        "floor_lost": "💀 Gegen '{boss}' verloren! Geh ins Krankenhaus.",
        "already_hospital": "Du wirst bereits behandelt!",
        "full_hp_hum": "HP und Menschlichkeit sind voll!",
        "hospital_entered": "🏥 Behandlung gestartet: {sec}s.",
        "empty_loot": "Beutetasche ist leer!",
        "loot_sold": "💰 Beute für {val} Münzen verkauft!",
        "invalid_amount": "Ungültiger Betrag!",
        "bank_deposited": "🏦 {amt} Münzen eingezahlt (2% Zinsen/Std).",
        "bank_withdrawn": "🪙 {amt} Münzen abgehoben.",
        "min_transfer": "Mindestens 10 Münzen!",
        "user_not_found": "Nutzer nicht gefunden!",
        "transfer_ok": "✅ {amt} gesendet.\n📉 3% Steuer ({tax}) — Netto: {net}.",
        "invalid_gift": "❌ Ungültiger Gutscheincode!",
        "gift_used": "⚠️ Bereits eingelöst!",
        "gift_full": "⚠️ Limit erreicht!",
        "gift_ok": "🎉 Eingelöst! +{coins} Münzen & +{xp} XP.",
        "min_voucher": "Mindestens 100 Münzen erforderlich!",
        "voucher_sent": "⏳ Anfrage an Owner gesendet. Warte auf Antwort...",
    },
    "zh": {
        "banned": "⛔ 您的恶魔之塔账号已被封禁。",
        "dev_mode": "🛠️ 恶魔之塔正在维护开发中（仅限管理员进入）。",
        "gender_locked": "角色性别已选定，无法更改！",
        "gender_saved": "✅ 角色已永久保存！",
        "item_not_found": "未找到该物品！",
        "equipped": "✅ 已装备「{name}」！",
        "not_enough_coins": "金币不足！（需要 {price} 金币）",
        "bought_equipped": "✅ 已购买并装备「{name}」！",
        "pick_gender_first": "请先在「角色」菜单中选择性别！",
        "sleeping": "😴 人性值归零！角色沉睡2天（剩余 {hrs} 小时）。",
        "in_hospital": "🏥 正在医院治疗中（剩余 {sec} 秒）。",
        "low_hp": "🩸 生命值过低！请先前往医院治疗。",
        "all_cleared": "🎉 恭喜通关所有楼层！",
        "floor_won": "🏆 第 {floor} 层（{boss}）通关！\n🪙 +{coins} 金币 | ⭐ +{xp} XP\n🎁 战利品: {drop}\n🩸 受伤: {dmg} (人性: {hum}%)",
        "sleep_triggered": "\n⚠️ 人性值归零，角色进入2天沉睡！",
        "floor_lost": "💀 被「{boss}」击败！请前往医院治疗。",
        "already_hospital": "您已经在治疗中了！",
        "full_hp_hum": "生命值和人性值已满！",
        "hospital_entered": "🏥 已住院治疗，需耗时 {sec} 秒。",
        "empty_loot": "战利品背包为空！",
        "loot_sold": "💰 所有战利品已售出，获得 {val} 金币！",
        "invalid_amount": "金币数量无效！",
        "bank_deposited": "🏦 已存入 {amt} 金币（每小时 2% 利息）。",
        "bank_withdrawn": "🪙 已从银行取出 {amt} 金币。",
        "min_transfer": "最低转账金额为 10 金币！",
        "user_not_found": "未找到目标用户！",
        "transfer_ok": "✅ 已发送 {amt} 金币。\n📉 扣除 3% 税费 ({tax}) — 实际到账: {net} 金币。",
        "invalid_gift": "❌ 兑换码无效或已过期！",
        "gift_used": "⚠️ 您已使用过该兑换码！",
        "gift_full": "⚠️ 兑换码使用次数已达上限！",
        "gift_ok": "🎉 兑换成功！+{coins} 金币 & +{xp} XP。",
        "min_voucher": "申请代金券最低需提供 100 金币！",
        "voucher_sent": "⏳ 申请已发送给管理员，等待回复...",
    },
}


def _dt_msg(lang: str, key: str, **kwargs) -> str:
    d = DT_MESSAGES.get(lang, DT_MESSAGES["fa"])
    txt = d.get(key, DT_MESSAGES["fa"].get(key, key))
    return txt.format(**kwargs) if kwargs else txt


class TowerAdminStates(StatesGroup):
    set_male_img = State()
    set_female_img = State()
    add_floor = State()
    del_floor = State()
    add_weapon = State()
    del_weapon = State()
    add_armor = State()
    del_armor = State()
    add_gift = State()
    add_popup = State()
    check_user = State()
    charge_user = State()
    ban_user = State()
    voucher_note = State()


async def ensure_tower_tables():
    await db.ensure_pool()
    async with db.pool.acquire() as conn:
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS dt_config (
                key TEXT PRIMARY KEY,
                val TEXT
            );
            CREATE TABLE IF NOT EXISTS dt_players (
                user_id BIGINT PRIMARY KEY,
                gender TEXT DEFAULT NULL,
                level INT DEFAULT 1,
                xp BIGINT DEFAULT 0,
                coins BIGINT DEFAULT 200,
                bank_coins BIGINT DEFAULT 0,
                bank_last_ts DOUBLE PRECISION DEFAULT 0,
                current_floor INT DEFAULT 1,
                hp INT DEFAULT 120,
                max_hp INT DEFAULT 120,
                humanity INT DEFAULT 100,
                hospital_until DOUBLE PRECISION DEFAULT 0,
                sleep_until DOUBLE PRECISION DEFAULT 0,
                equipped_weapon INT DEFAULT 1,
                equipped_armor INT DEFAULT 0,
                owned_weapons TEXT DEFAULT '[1]',
                owned_armors TEXT DEFAULT '[]',
                inventory TEXT DEFAULT '[]',
                is_banned BOOLEAN DEFAULT FALSE
            );
            CREATE TABLE IF NOT EXISTS dt_floors (
                floor_num INT PRIMARY KEY,
                boss_name TEXT,
                photo TEXT,
                description TEXT,
                power_desc TEXT,
                weakness TEXT,
                hp INT,
                atk INT,
                def INT,
                reward_coins INT,
                reward_xp INT,
                drop_item TEXT,
                drop_price INT DEFAULT 50
            );
            CREATE TABLE IF NOT EXISTS dt_items (
                id SERIAL PRIMARY KEY,
                item_type TEXT,
                name TEXT,
                photo TEXT,
                price INT DEFAULT 0,
                hp_bonus INT DEFAULT 0,
                atk_bonus INT DEFAULT 0,
                def_bonus INT DEFAULT 0,
                spd_bonus INT DEFAULT 0
            );
            CREATE TABLE IF NOT EXISTS dt_gifts (
                code TEXT PRIMARY KEY,
                coins INT DEFAULT 0,
                xp INT DEFAULT 0,
                max_uses INT DEFAULT 1,
                used_by TEXT DEFAULT '[]'
            );
            CREATE TABLE IF NOT EXISTS dt_vouchers (
                id SERIAL PRIMARY KEY,
                user_id BIGINT,
                user_name TEXT,
                coins_offered BIGINT,
                voucher_type TEXT,
                status TEXT DEFAULT 'pending',
                owner_note TEXT DEFAULT '',
                voucher_code TEXT DEFAULT '',
                created_at DOUBLE PRECISION
            );
        """)

        w_count = await conn.fetchval("SELECT COUNT(*) FROM dt_items WHERE item_type='weapon'")
        if not w_count:
            await conn.execute("""
                INSERT INTO dt_items (item_type, name, photo, price, hp_bonus, atk_bonus, def_bonus, spd_bonus)
                VALUES
                ('weapon', 'شمشیر شکارچی (رایگان)', '', 0, 10, 18, 5, 0),
                ('weapon', 'تیغه خون‌آشام', '', 650, 35, 42, 12, 5),
                ('weapon', 'تبر دوزخی راینو', '', 1800, 80, 95, 25, -5),
                ('armor', 'زره چرمی سایه', '', 400, 50, 0, 22, 10),
                ('armor', 'زره پولادین امپراتور', '', 1400, 140, 10, 60, -5);
            """)

        f_count = await conn.fetchval("SELECT COUNT(*) FROM dt_floors")
        if not f_count:
            await conn.execute("""
                INSERT INTO dt_floors (floor_num, boss_name, photo, description, power_desc, weakness, hp, atk, def, reward_coins, reward_xp, drop_item, drop_price)
                VALUES
                (1, 'نگهبان دروازه خاکستر', '', 'اسکلت غول‌پیکر طبقه اول', 'زنجیر آتشین', 'ضربه سریع', 95, 16, 6, 120, 45, 'گوهر خاکستر', 40),
                (2, 'گرگینه خون‌خوار', '', 'شکارچی شب در طبقه دوم', 'پنجه زهرآلود', 'سپر نقره‌ای', 165, 26, 12, 240, 85, 'ناب گرگینه', 85),
                (3, 'ارباب سایه‌ها', '', 'جادوگر سقوط‌کرده طبقه سوم', 'جذب روح', 'تیغه خون‌آشام', 270, 40, 20, 450, 150, 'تاج سایه', 160),
                (4, 'اژدهای استخوانی', '', 'فرمانروای طبقه چهارم', 'طوفان شعله', 'زره پولادین', 460, 62, 35, 900, 320, 'قلب اژدها', 350);
            """)


async def get_dt_config(key: str, default: str = "") -> str:
    await ensure_tower_tables()
    val = await db.pool.fetchval("SELECT val FROM dt_config WHERE key=$1", key)
    return val if val is not None else default


async def set_dt_config(key: str, val: str):
    await ensure_tower_tables()
    await db.pool.execute(
        "INSERT INTO dt_config (key, val) VALUES ($1, $2) ON CONFLICT (key) DO UPDATE SET val=$2",
        key, val
    )


async def get_or_create_player(uid: int) -> dict:
    await ensure_tower_tables()
    now = time.time()
    row = await db.pool.fetchrow("SELECT * FROM dt_players WHERE user_id=$1", uid)
    if not row:
        first_w = await db.pool.fetchval("SELECT id FROM dt_items WHERE item_type='weapon' ORDER BY price ASC, id ASC LIMIT 1") or 1
        await db.pool.execute(
            """INSERT INTO dt_players (user_id, equipped_weapon, owned_weapons, bank_last_ts)
               VALUES ($1, $2, $3, $4) ON CONFLICT DO NOTHING""",
            uid, first_w, json.dumps([first_w]), now
        )
        row = await db.pool.fetchrow("SELECT * FROM dt_players WHERE user_id=$1", uid)

    p = dict(row)

    # سود ساعتی بانک (۲٪ در هر ساعت)
    if p["bank_coins"] > 0 and p["bank_last_ts"] > 0:
        hours_passed = int((now - p["bank_last_ts"]) // 3600)
        if hours_passed >= 1:
            profit = int(p["bank_coins"] * 0.02 * min(hours_passed, 72))
            if profit > 0:
                p["bank_coins"] += profit
                p["bank_last_ts"] = now
                await db.pool.execute(
                    "UPDATE dt_players SET bank_coins=$1, bank_last_ts=$2 WHERE user_id=$3",
                    p["bank_coins"], now, uid
                )
    else:
        await db.pool.execute("UPDATE dt_players SET bank_last_ts=$1 WHERE user_id=$2", now, uid)

    if p["hospital_until"] > 0 and now >= p["hospital_until"]:
        p["hospital_until"] = 0
        p["hp"] = p["max_hp"]
        p["humanity"] = 100
        await db.pool.execute(
            "UPDATE dt_players SET hospital_until=0, hp=max_hp, humanity=100 WHERE user_id=$1", uid
        )

    if p["sleep_until"] > 0 and now >= p["sleep_until"]:
        p["sleep_until"] = 0
        p["humanity"] = 100
        p["hp"] = p["max_hp"]
        await db.pool.execute(
            "UPDATE dt_players SET sleep_until=0, humanity=100, hp=max_hp WHERE user_id=$1", uid
        )

    items_rows = await db.pool.fetch("SELECT * FROM dt_items ORDER BY price ASC, id ASC")
    items_map = {r["id"]: dict(r) for r in items_rows}

    w_obj = items_map.get(p["equipped_weapon"], {"hp_bonus": 0, "atk_bonus": 15, "def_bonus": 5, "spd_bonus": 0, "name": "شمشیر پایه"})
    a_obj = items_map.get(p["equipped_armor"], {"hp_bonus": 0, "atk_bonus": 0, "def_bonus": 0, "spd_bonus": 0, "name": "بدون زره"})

    lvl = max(1, int(p["xp"] // 100) + 1)
    calc_max_hp = 100 + (lvl * 20) + w_obj["hp_bonus"] + a_obj["hp_bonus"]
    calc_atk = 15 + (lvl * 6) + w_obj["atk_bonus"] + a_obj["atk_bonus"]
    calc_def = 8 + (lvl * 4) + w_obj["def_bonus"] + a_obj["def_bonus"]
    calc_spd = 10 + (lvl * 2) + w_obj["spd_bonus"] + a_obj["spd_bonus"]

    if lvl != p["level"] or calc_max_hp != p["max_hp"]:
        p["level"] = lvl
        p["max_hp"] = calc_max_hp
        p["hp"] = min(p["hp"], calc_max_hp)
        await db.pool.execute(
            "UPDATE dt_players SET level=$1, max_hp=$2, hp=$3 WHERE user_id=$4",
            lvl, calc_max_hp, p["hp"], uid
        )

    floors = [dict(r) for r in await db.pool.fetch("SELECT * FROM dt_floors ORDER BY floor_num ASC")]
    cur_floor_obj = next((f for f in floors if f["floor_num"] == p["current_floor"]), None)
    if not cur_floor_obj and floors:
        cur_floor_obj = floors[-1]

    vouchers = [
        dict(r) for r in await db.pool.fetch(
            "SELECT * FROM dt_vouchers WHERE user_id=$1 ORDER BY id DESC LIMIT 5", uid
        )
    ]

    dev_mode = (await get_dt_config("dev_mode", "0")) == "1"
    male_img = await get_dt_config("male_img", "")
    female_img = await get_dt_config("female_img", "")

    popup_raw = await get_dt_config("active_popup", "")
    popup_data = None
    if popup_raw:
        try:
            pd = json.loads(popup_raw)
            if pd.get("expires_at", 0) > now:
                popup_data = pd
        except Exception:
            pass

    return {
        "dev_mode": dev_mode,
        "is_owner": int(uid) in OWNER_IDS,
        "male_img": male_img,
        "female_img": female_img,
        "popup": popup_data,
        "player": {
            "user_id": p["user_id"],
            "gender": p["gender"],
            "level": p["level"],
            "xp": p["xp"],
            "coins": p["coins"],
            "bank_coins": p["bank_coins"],
            "current_floor": p["current_floor"],
            "hp": p["hp"],
            "max_hp": p["max_hp"],
            "atk": calc_atk,
            "def": calc_def,
            "spd": calc_spd,
            "humanity": p["humanity"],
            "hospital_rem": max(0, int(p["hospital_until"] - now)),
            "sleep_rem": max(0, int(p["sleep_until"] - now)),
            "equipped_weapon": p["equipped_weapon"],
            "equipped_armor": p["equipped_armor"],
            "weapon_name": w_obj["name"],
            "armor_name": a_obj["name"],
            "owned_weapons": json.loads(p["owned_weapons"] or "[1]"),
            "owned_armors": json.loads(p["owned_armors"] or "[]"),
            "inventory": json.loads(p["inventory"] or "[]"),
            "is_banned": p["is_banned"],
        },
        "current_boss": cur_floor_obj,
        "items": list(items_map.values()),
        "vouchers": vouchers,
        "star_packages": [{"id": k, **v} for k, v in STAR_PACKAGES.items()],
    }


async def handle_tower_api_action(payload: dict) -> dict:
    uid = int(payload.get("uid") or 0)
    name = payload.get("name") or "Player"
    lang = payload.get("lang") or "fa"
    action = payload.get("action") or "state"
    now = time.time()

    full_state = await get_or_create_player(uid)
    p = full_state["player"]

    if p["is_banned"]:
        return {"ok": False, "error": _dt_msg(lang, "banned"), "state": full_state}

    if full_state["dev_mode"] and not full_state["is_owner"]:
        return {"ok": False, "error": _dt_msg(lang, "dev_mode"), "state": full_state}

    if action == "choose_gender":
        if p["gender"]:
            return {"ok": False, "error": _dt_msg(lang, "gender_locked"), "state": full_state}
        g = payload.get("gender")
        if g not in ("male", "female"):
            return {"ok": False, "error": "Invalid", "state": full_state}
        await db.pool.execute("UPDATE dt_players SET gender=$1 WHERE user_id=$2", g, uid)
        return {"ok": True, "msg": _dt_msg(lang, "gender_saved"), "state": await get_or_create_player(uid)}

    if action == "buy_or_equip_item":
        item_id = int(payload.get("item_id") or 0)
        item_row = await db.pool.fetchrow("SELECT * FROM dt_items WHERE id=$1", item_id)
        if not item_row:
            return {"ok": False, "error": _dt_msg(lang, "item_not_found"), "state": full_state}

        itype = item_row["item_type"]
        price = item_row["price"]
        owned_w = p["owned_weapons"]
        owned_a = p["owned_armors"]

        if itype == "weapon":
            if item_id in owned_w:
                await db.pool.execute("UPDATE dt_players SET equipped_weapon=$1 WHERE user_id=$2", item_id, uid)
                return {"ok": True, "msg": _dt_msg(lang, "equipped", name=item_row["name"]), "state": await get_or_create_player(uid)}
            if p["coins"] < price:
                return {"ok": False, "error": _dt_msg(lang, "not_enough_coins", price=price), "state": full_state}
            owned_w.append(item_id)
            await db.pool.execute(
                "UPDATE dt_players SET coins=coins-$1, owned_weapons=$2, equipped_weapon=$3 WHERE user_id=$4",
                price, json.dumps(owned_w), item_id, uid
            )
            return {"ok": True, "msg": _dt_msg(lang, "bought_equipped", name=item_row["name"]), "state": await get_or_create_player(uid)}
        else:
            if item_id in owned_a:
                await db.pool.execute("UPDATE dt_players SET equipped_armor=$1 WHERE user_id=$2", item_id, uid)
                return {"ok": True, "msg": _dt_msg(lang, "equipped", name=item_row["name"]), "state": await get_or_create_player(uid)}
            if p["coins"] < price:
                return {"ok": False, "error": _dt_msg(lang, "not_enough_coins", price=price), "state": full_state}
            owned_a.append(item_id)
            await db.pool.execute(
                "UPDATE dt_players SET coins=coins-$1, owned_armors=$2, equipped_armor=$3 WHERE user_id=$4",
                price, json.dumps(owned_a), item_id, uid
            )
            return {"ok": True, "msg": _dt_msg(lang, "bought_equipped", name=item_row["name"]), "state": await get_or_create_player(uid)}

    if action == "battle_floor":
        if not p["gender"]:
            return {"ok": False, "error": _dt_msg(lang, "pick_gender_first"), "state": full_state}
        if p["sleep_rem"] > 0:
            hrs = round(p["sleep_rem"] / 3600, 1)
            return {"ok": False, "error": _dt_msg(lang, "sleeping", hrs=hrs), "state": full_state}
        if p["hospital_rem"] > 0:
            return {"ok": False, "error": _dt_msg(lang, "in_hospital", sec=p["hospital_rem"]), "state": full_state}
        if p["hp"] <= 10:
            return {"ok": False, "error": _dt_msg(lang, "low_hp"), "state": full_state}

        chosen_w = int(payload.get("weapon_id") or p["equipped_weapon"])
        if chosen_w in p["owned_weapons"] and chosen_w != p["equipped_weapon"]:
            await db.pool.execute("UPDATE dt_players SET equipped_weapon=$1 WHERE user_id=$2", chosen_w, uid)
            full_state = await get_or_create_player(uid)
            p = full_state["player"]

        boss = full_state["current_boss"]
        if not boss:
            return {"ok": False, "error": _dt_msg(lang, "all_cleared"), "state": full_state}

        player_dmg = max(8, p["atk"] + int(p["spd"] * 0.4) - int(boss["def"] * 0.5))
        boss_dmg = max(6, boss["atk"] - int(p["def"] * 0.55))
        rounds_to_kill = math.ceil(boss["hp"] / player_dmg)
        total_damage_taken = max(8, min(p["hp"], rounds_to_kill * boss_dmg + random.randint(-5, 10)))

        new_hp = max(0, p["hp"] - total_damage_taken)
        new_humanity = max(0, p["humanity"] - random.randint(12, 20))
        sleep_until = (now + 2 * 86400) if new_humanity == 0 else 0

        if new_hp > 0:
            inv = p["inventory"]
            if boss.get("drop_item"):
                inv.append({"name": boss["drop_item"], "price": boss.get("drop_price", 50)})

            await db.pool.execute(
                """UPDATE dt_players
                   SET hp=$1, humanity=$2, sleep_until=$3,
                       coins=coins+$4, xp=xp+$5, current_floor=current_floor+1, inventory=$6
                   WHERE user_id=$7""",
                new_hp, new_humanity, sleep_until,
                boss["reward_coins"], boss["reward_xp"], json.dumps(inv), uid
            )
            msg = _dt_msg(
                lang, "floor_won",
                floor=boss["floor_num"], boss=boss["boss_name"],
                coins=boss["reward_coins"], xp=boss["reward_xp"],
                drop=boss.get("drop_item") or "—", dmg=total_damage_taken, hum=new_humanity
            )
            if sleep_until > 0:
                msg += _dt_msg(lang, "sleep_triggered")
            return {"ok": True, "msg": msg, "state": await get_or_create_player(uid)}
        else:
            await db.pool.execute(
                "UPDATE dt_players SET hp=5, humanity=$1, sleep_until=$2 WHERE user_id=$3",
                new_humanity, sleep_until, uid
            )
            return {
                "ok": False,
                "error": _dt_msg(lang, "floor_lost", boss=boss["boss_name"]),
                "state": await get_or_create_player(uid),
            }

    if action == "enter_hospital":
        if p["hospital_rem"] > 0:
            return {"ok": False, "error": _dt_msg(lang, "already_hospital"), "state": full_state}
        missing_hp = max(0, p["max_hp"] - p["hp"])
        missing_hum = max(0, 100 - p["humanity"])
        if missing_hp == 0 and missing_hum == 0:
            return {"ok": False, "error": _dt_msg(lang, "full_hp_hum"), "state": full_state}

        wait_seconds = max(15, missing_hp * 2 + missing_hum * 2)
        until_ts = now + wait_seconds
        await db.pool.execute("UPDATE dt_players SET hospital_until=$1 WHERE user_id=$2", until_ts, uid)
        return {
            "ok": True,
            "msg": _dt_msg(lang, "hospital_entered", sec=wait_seconds),
            "state": await get_or_create_player(uid),
        }

    if action == "sell_loot":
        inv = p["inventory"]
        if not inv:
            return {"ok": False, "error": _dt_msg(lang, "empty_loot"), "state": full_state}
        total_val = sum(int(x.get("price", 50)) for x in inv)
        await db.pool.execute(
            "UPDATE dt_players SET coins=coins+$1, inventory='[]' WHERE user_id=$2", total_val, uid
        )
        return {
            "ok": True,
            "msg": _dt_msg(lang, "loot_sold", val=total_val),
            "state": await get_or_create_player(uid),
        }

    if action == "bank_deposit":
        amt = int(payload.get("amount") or 0)
        if amt <= 0 or amt > p["coins"]:
            return {"ok": False, "error": _dt_msg(lang, "invalid_amount"), "state": full_state}
        await db.pool.execute(
            "UPDATE dt_players SET coins=coins-$1, bank_coins=bank_coins+$1, bank_last_ts=$2 WHERE user_id=$3",
            amt, now, uid
        )
        return {"ok": True, "msg": _dt_msg(lang, "bank_deposited", amt=amt), "state": await get_or_create_player(uid)}

    if action == "bank_withdraw":
        amt = int(payload.get("amount") or 0)
        if amt <= 0 or amt > p["bank_coins"]:
            return {"ok": False, "error": _dt_msg(lang, "invalid_amount"), "state": full_state}
        await db.pool.execute(
            "UPDATE dt_players SET bank_coins=bank_coins-$1, coins=coins+$1 WHERE user_id=$2",
            amt, uid
        )
        return {"ok": True, "msg": _dt_msg(lang, "bank_withdrawn", amt=amt), "state": await get_or_create_player(uid)}

    if action == "transfer_coins":
        target_str = str(payload.get("target") or "").strip()
        amt = int(payload.get("amount") or 0)
        if amt < 10:
            return {"ok": False, "error": _dt_msg(lang, "min_transfer"), "state": full_state}
        if amt > p["coins"]:
            return {"ok": False, "error": _dt_msg(lang, "not_enough_coins", price=amt), "state": full_state}

        target_uid = None
        if target_str.isdigit():
            target_uid = int(target_str)
        else:
            uname = target_str.lstrip("@").lower()
            row = await db.pool.fetchrow("SELECT user_id FROM users WHERE LOWER(username)=$1", uname)
            if row:
                target_uid = row["user_id"]

        if not target_uid or target_uid == uid:
            return {"ok": False, "error": _dt_msg(lang, "user_not_found"), "state": full_state}

        await get_or_create_player(target_uid)
        tax = max(1, round(amt * 0.03))
        net_amount = amt - tax

        await db.pool.execute("UPDATE dt_players SET coins=coins-$1 WHERE user_id=$2", amt, uid)
        await db.pool.execute("UPDATE dt_players SET coins=coins+$1 WHERE user_id=$2", net_amount, target_uid)
        return {
            "ok": True,
            "msg": _dt_msg(lang, "transfer_ok", amt=amt, tax=tax, net=net_amount),
            "state": await get_or_create_player(uid),
        }

    if action == "create_star_invoice":
        pack_id = payload.get("pack_id")
        pack = STAR_PACKAGES.get(pack_id)
        if not pack:
            return {"ok": False, "error": "Invalid Pack", "state": full_state}

        bot_token = os.environ.get("BOT_TOKEN", "")
        temp_bot = Bot(token=bot_token)
        try:
            invoice_link = await temp_bot.create_invoice_link(
                title=pack["title"],
                description=f"+{pack['coins']:,} Coins & +{pack['xp']:,} XP in Demon Tower",
                payload=f"dtpack_{pack_id}_{uid}",
                provider_token="",
                currency="XTR",
                prices=[LabeledPrice(label="Stars", amount=pack["stars"])],
            )
            return {"ok": True, "invoice_link": invoice_link, "state": full_state}
        except Exception as e:
            return {"ok": False, "error": str(e), "state": full_state}
        finally:
            await temp_bot.session.close()

    if action == "redeem_gift":
        code = str(payload.get("code") or "").strip()
        row = await db.pool.fetchrow("SELECT * FROM dt_gifts WHERE code=$1", code)
        if not row:
            return {"ok": False, "error": _dt_msg(lang, "invalid_gift"), "state": full_state}

        used_list = json.loads(row["used_by"] or "[]")
        if uid in used_list:
            return {"ok": False, "error": _dt_msg(lang, "gift_used"), "state": full_state}
        if len(used_list) >= row["max_uses"]:
            return {"ok": False, "error": _dt_msg(lang, "gift_full"), "state": full_state}

        used_list.append(uid)
        await db.pool.execute("UPDATE dt_gifts SET used_by=$1 WHERE code=$2", json.dumps(used_list), code)
        await db.pool.execute(
            "UPDATE dt_players SET coins=coins+$1, xp=xp+$2 WHERE user_id=$3",
            row["coins"], row["xp"], uid
        )
        return {
            "ok": True,
            "msg": _dt_msg(lang, "gift_ok", coins=row["coins"], xp=row["xp"]),
            "state": await get_or_create_player(uid),
        }

    if action == "request_voucher":
        coins_offered = int(payload.get("coins") or 0)
        v_type = str(payload.get("voucher_type") or "ووچر استارز")
        if coins_offered < 100:
            return {"ok": False, "error": _dt_msg(lang, "min_voucher"), "state": full_state}
        if coins_offered > p["coins"]:
            return {"ok": False, "error": _dt_msg(lang, "not_enough_coins", price=coins_offered), "state": full_state}

        await db.pool.execute("UPDATE dt_players SET coins=coins-$1 WHERE user_id=$2", coins_offered, uid)
        vid = await db.pool.fetchval(
            """INSERT INTO dt_vouchers (user_id, user_name, coins_offered, voucher_type, status, created_at)
               VALUES ($1, $2, $3, $4, 'pending', $5) RETURNING id""",
            uid, name, coins_offered, v_type, now
        )

        bot_token = os.environ.get("BOT_TOKEN", "")
        if bot_token:
            temp_bot = Bot(token=bot_token)
            try:
                for oid in OWNER_IDS:
                    try:
                        await temp_bot.send_message(
                            chat_id=oid,
                            text=(
                                f"🎟️ <b>درخواست ووچر جدید (برج شیاطین #{vid})</b>\n\n"
                                f"👤 کاربر: <b>{name}</b> (<code>{uid}</code>)\n"
                                f"🎁 نوع ووچر: <b>{v_type}</b>\n"
                                f"🪙 سکه پیشنهادی: <b>{coins_offered:,} سکه</b>\n\n"
                                f"وضعیت را انتخاب کنید:"
                            ),
                            reply_markup=kb([
                                [
                                    success("✅ تایید و صدور کد ووچر", f"dtv_app_{vid}"),
                                    danger("❌ رد درخواست (عودت سکه)", f"dtv_rej_{vid}"),
                                ]
                            ]),
                            parse_mode=ParseMode.HTML,
                        )
                    except Exception:
                        pass
            finally:
                await temp_bot.session.close()

        return {
            "ok": True,
            "msg": _dt_msg(lang, "voucher_sent"),
            "state": await get_or_create_player(uid),
        }

    return {"ok": True, "state": full_state}


@router.callback_query(F.data.startswith("dtv_app_") | F.data.startswith("dtv_rej_"))
async def cb_owner_voucher_decision(cb: CallbackQuery, state: FSMContext):
    if cb.from_user.id not in OWNER_IDS:
        await cb.answer("فقط مالک!", show_alert=True)
        return

    parts = cb.data.split("_")
    decision = "approved" if parts[1] == "app" else "rejected"
    vid = int(parts[2])

    await state.set_state(TowerAdminStates.voucher_note)
    await state.update_data(vid=vid, decision=decision)
    await cb.answer()
    await cb.message.reply(
        f"📝 لطفاً یادداشت خود را برای درخواست ووچر #{vid} ({'تایید' if decision=='approved' else 'رد'}) بنویسید:\n"
        f"(اگر یادداشتی ندارید کلمه <code>بدون یادداشت</code> را بفرستید)",
        parse_mode=ParseMode.HTML,
    )


@router.message(StateFilter(TowerAdminStates.voucher_note), F.text)
async def msg_owner_voucher_note(msg: Message, state: FSMContext):
    data = await state.get_data()
    vid = data.get("vid")
    decision = data.get("decision")
    note = msg.text.strip()
    if note == "بدون یادداشت":
        note = ""
    await state.clear()

    await ensure_tower_tables()
    vrow = await db.pool.fetchrow("SELECT * FROM dt_vouchers WHERE id=$1", vid)
    if not vrow:
        await msg.reply("❌ درخواست یافت نشد.")
        return

    target_uid = vrow["user_id"]
    if decision == "approved":
        rand_part = "".join(random.choices(string.ascii_uppercase + string.digits, k=8))
        v_code = f"RHINO-VCH-{vid}-{rand_part}"
        await db.pool.execute(
            "UPDATE dt_vouchers SET status='approved', owner_note=$1, voucher_code=$2 WHERE id=$3",
            note, v_code, vid
        )
        try:
            voucher_card = (
                f"🎟️ <b>برگه رسمی ووچر برج شیاطین راینو</b>\n\n"
                f"🔹 کد یکتای ووچر: <code>{v_code}</code>\n"
                f"🎁 نوع ووچر: <b>{vrow['voucher_type']}</b>\n"
                f"🪙 سکه پرداخت‌شده: <b>{vrow['coins_offered']:,}</b>\n"
                f"👤 شناسه کاربری: <code>{target_uid}</code>\n"
                + (f"📌 یادداشت مالک: <b>{note}</b>\n" if note else "")
            )
            await msg.bot.send_message(target_uid, voucher_card, parse_mode=ParseMode.HTML)
            await msg.bot.send_message(
                target_uid,
                f"✅ درخواست ووچر شما تایید شد!\n"
                f"👈 <b>برای دریافت هدیه، پیام بالا (حاوی کد ووچر) را برای مالک فوروارد کنید:</b>\n"
                f"🆔 @{OWNER_USERNAME}",
                parse_mode=ParseMode.HTML,
            )
        except Exception:
            pass
        await msg.reply(f"✅ درخواست #{vid} تایید شد و کد ووچر ({v_code}) برای کاربر ارسال گردید.")
    else:
        await db.pool.execute(
            "UPDATE dt_vouchers SET status='rejected', owner_note=$1 WHERE id=$2",
            note, vid
        )
        await db.pool.execute(
            "UPDATE dt_players SET coins=coins+$1 WHERE user_id=$2",
            vrow["coins_offered"], target_uid
        )
        try:
            await msg.bot.send_message(
                target_uid,
                f"❌ <b>درخواست ووچر #{vid} شما رد شد</b> و مقدار {vrow['coins_offered']:,} سکه به حساب شما بازگشت.\n"
                + (f"📌 یادداشت مالک: <b>{note}</b>" if note else ""),
                parse_mode=ParseMode.HTML,
            )
        except Exception:
            pass
        await msg.reply(f"❌ درخواست #{vid} رد شد و سکه کاربر عودت داده شد.")


async def _tower_admin_kb():
    dev_on = (await get_dt_config("dev_mode", "0")) == "1"
    dev_lbl = "🛠️ وضعیت: در حال توسعه (فقط مالک)" if dev_on else "🟢 وضعیت: باز برای همه کاربران"
    return kb([
        [primary("👹 افزودن/ویرایش غول و طبقه", "dtadm:add_floor"),
         danger("🗑️ حذف طبقه", "dtadm:del_floor")],
        [primary("⚔️ افزودن سلاح جدید", "dtadm:add_weapon"),
         danger("🗑️ حذف سلاح", "dtadm:del_weapon")],
        [primary("🛡️ افزودن زره جدید", "dtadm:add_armor"),
         danger("🗑️ حذف زره", "dtadm:del_armor")],
        [primary("🚹 تنظیم عکس کاراکتر مرد", "dtadm:male_img"),
         primary("🚺 تنظیم عکس کاراکتر زن", "dtadm:female_img")],
        [success("🎁 ساخت کد هدیه (سکه/XP)", "dtadm:add_gift"),
         primary("📢 ساخت پاپ‌آپ تبلیغاتی شناور", "dtadm:add_popup")],
        [primary("🔍 بررسی کاربر", "dtadm:check_user"),
         success("⚡ شارژ سکه و XP کاربر", "dtadm:charge_user")],
        [danger("🚫 محروم / آزاد کردن کاربر از برج", "dtadm:ban_user")],
        [success(dev_lbl, "dtadm:toggle_dev")],
    ])


@router.message(Command("tower_panel"))
@router.message(F.text.in_({"پنل برج", "پنل برج شیاطین", "/tower"}))
async def cmd_tower_panel(msg: Message, state: FSMContext):
    if msg.from_user.id not in OWNER_IDS:
        return
    await state.clear()
    await ensure_tower_tables()
    floors_cnt = await db.pool.fetchval("SELECT COUNT(*) FROM dt_floors") or 0
    items_cnt = await db.pool.fetchval("SELECT COUNT(*) FROM dt_items") or 0
    players_cnt = await db.pool.fetchval("SELECT COUNT(*) FROM dt_players") or 0

    await msg.answer(
        f"👹 <b>پنل فرماندهی برج شیاطین (Demon Tower)</b>\n\n"
        f"📊 بازیکنان برج: <b>{players_cnt} نفر</b>\n"
        f"🏰 طبقات ثبت‌شده: <b>{floors_cnt} طبقه</b>\n"
        f"⚔️ سلاح‌ها و زره‌ها: <b>{items_cnt} مورد</b>\n\n"
        f"بخش مورد نظر را انتخاب کنید:",
        reply_markup=await _tower_admin_kb(),
        parse_mode=ParseMode.HTML,
    )


@router.callback_query(F.data == "dtadm:toggle_dev")
async def cb_toggle_dev(cb: CallbackQuery):
    if cb.from_user.id not in OWNER_IDS:
        return
    cur = await get_dt_config("dev_mode", "0")
    new_val = "0" if cur == "1" else "1"
    await set_dt_config("dev_mode", new_val)
    await cb.answer("وضعیت بازی تغییر کرد!")
    await cb.message.edit_reply_markup(reply_markup=await _tower_admin_kb())


@router.callback_query(F.data.startswith("dtadm:"))
async def cb_tower_admin_actions(cb: CallbackQuery, state: FSMContext):
    if cb.from_user.id not in OWNER_IDS:
        return
    act = cb.data.split(":")[1]
    await state.clear()
    await cb.answer()

    if act == "male_img":
        await state.set_state(TowerAdminStates.set_male_img)
        await cb.message.reply("🚹 لینک مستقیم تصویر کاراکتر **مرد** را ارسال کنید:")
    elif act == "female_img":
        await state.set_state(TowerAdminStates.set_female_img)
        await cb.message.reply("🚺 لینک مستقیم تصویر کاراکتر **زن** را ارسال کنید:")
    elif act == "add_floor":
        await state.set_state(TowerAdminStates.add_floor)
        await cb.message.reply(
            "👹 اطلاعات طبقه و غول را با جداکننده <code>|</code> بفرستید:\n\n"
            "<code>شماره_طبقه | نام_غول | لینک_عکس | توضیح | قدرت_غول | نقطه_ضعف | جان_HP | حمله_ATK | دفاع_DEF | پاداش_سکه | پاداش_XP | نام_غنیمت | قیمت_فروش_غنیمت</code>\n\n"
            "مثال:\n"
            "<code>5 | غول آتشین | - | نگهبان طبقه پنجم | شمشیر گدازه | سپر یخی | 650 | 85 | 40 | 1500 | 500 | یاقوت مذاب | 450</code>",
            parse_mode=ParseMode.HTML,
        )
    elif act == "del_floor":
        await state.set_state(TowerAdminStates.del_floor)
        await cb.message.reply("🗑️ شماره طبقه‌ای که می‌خواهید حذف شود را بفرستید:")
    elif act == "add_weapon":
        await state.set_state(TowerAdminStates.add_weapon)
        await cb.message.reply(
            "⚔️ مشخصات سلاح جدید را با جداکننده <code>|</code> بفرستید:\n"
            "<code>نام_سلاح | لینک_عکس | قیمت_سکه | افزایش_جان | افزایش_حمله | افزایش_دفاع | افزایش_سرعت</code>\n\n"
            "مثال:\n"
            "<code>شمشیر اژدها | - | 3000 | 120 | 140 | 30 | 10</code>",
            parse_mode=ParseMode.HTML,
        )
    elif act == "del_weapon":
        rows = await db.pool.fetch("SELECT id, name, price FROM dt_items WHERE item_type='weapon' ORDER BY id")
        txt = "\n".join(f"کد <code>{r['id']}</code>: {r['name']} ({r['price']} سکه)" for r in rows)
        await state.set_state(TowerAdminStates.del_weapon)
        await cb.message.reply(f"🗑️ کد سلاح را برای حذف بفرستید:\n\n{txt}", parse_mode=ParseMode.HTML)
    elif act == "add_armor":
        await state.set_state(TowerAdminStates.add_armor)
        await cb.message.reply(
            "🛡️ مشخصات زره جدید را با جداکننده <code>|</code> بفرستید:\n"
            "<code>نام_زره | لینک_عکس | قیمت_سکه | افزایش_جان | افزایش_دفاع | تغییر_سرعت</code>\n\n"
            "مثال:\n"
            "<code>زره الماس | - | 2500 | 200 | 90 | 15</code>",
            parse_mode=ParseMode.HTML,
        )
    elif act == "del_armor":
        rows = await db.pool.fetch("SELECT id, name, price FROM dt_items WHERE item_type='armor' ORDER BY id")
        txt = "\n".join(f"کد <code>{r['id']}</code>: {r['name']} ({r['price']} سکه)" for r in rows)
        await state.set_state(TowerAdminStates.del_armor)
        await cb.message.reply(f"🗑️ کد زره را برای حذف بفرستید:\n\n{txt}", parse_mode=ParseMode.HTML)
    elif act == "add_gift":
        await state.set_state(TowerAdminStates.add_gift)
        await cb.message.reply(
            "🎁 اطلاعات کد هدیه را با <code>|</code> بفرستید:\n"
            "<code>کد_هدیه | مقدار_سکه | مقدار_XP | تعداد_دفعات_مجاز</code>\n\n"
            "مثال:\n<code>RHINO2026 | 5000 | 500 | 50</code>",
            parse_mode=ParseMode.HTML,
        )
    elif act == "add_popup":
        await state.set_state(TowerAdminStates.add_popup)
        await cb.message.reply(
            "📢 مشخصات پاپ‌آپ تبلیغاتی شناور را با <code>|</code> بفرستید:\n"
            "<code>متن_پاپ‌آپ | لینک_عکس_(یا -) | متن_دکمه_(یا -) | لینک_دکمه_(یا -) | مدت_ساعت_نمایش</code>\n\n"
            "(برای حذف پاپ‌آپ فعلی کلمه <code>حذف</code> را بفرستید)",
            parse_mode=ParseMode.HTML,
        )
    elif act == "check_user":
        await state.set_state(TowerAdminStates.check_user)
        await cb.message.reply("🔍 آیدی عددی کاربر را بفرستید:")
    elif act == "charge_user":
        await state.set_state(TowerAdminStates.charge_user)
        await cb.message.reply(
            "⚡ آیدی عددی، سکه و XP را با <code>|</code> بفرستید:\n"
            "<code>آیدی_کاربر | مقدار_سکه_اضافی | مقدار_XP_اضافی</code>",
            parse_mode=ParseMode.HTML,
        )
    elif act == "ban_user":
        await state.set_state(TowerAdminStates.ban_user)
        await cb.message.reply("🚫 آیدی عددی کاربر را بفرستید تا وضعیت مسدودیتش در برج تغییر کند:")


@router.message(StateFilter(TowerAdminStates.set_male_img), F.text)
async def st_male_img(msg: Message, state: FSMContext):
    await set_dt_config("male_img", msg.text.strip())
    await state.clear()
    await msg.reply("✅ تصویر کاراکتر مرد ذخیره شد.")


@router.message(StateFilter(TowerAdminStates.set_female_img), F.text)
async def st_female_img(msg: Message, state: FSMContext):
    await set_dt_config("female_img", msg.text.strip())
    await state.clear()
    await msg.reply("✅ تصویر کاراکتر زن ذخیره شد.")


@router.message(StateFilter(TowerAdminStates.add_floor), F.text)
async def st_add_floor(msg: Message, state: FSMContext):
    parts = [x.strip() for x in msg.text.split("|")]
    if len(parts) < 12:
        await msg.reply("❌ تعداد بخش‌ها کامل نیست!")
        return
    fnum = int(parts[0])
    bname, photo, desc, pdesc, weak = parts[1], parts[2], parts[3], parts[4], parts[5]
    hp, atk, df, rcoins, rxp = int(parts[6]), int(parts[7]), int(parts[8]), int(parts[9]), int(parts[10])
    drop_item = parts[11]
    drop_price = int(parts[12]) if len(parts) > 12 and parts[12].isdigit() else 50
    if photo == "-":
        photo = ""

    await db.pool.execute(
        """INSERT INTO dt_floors (floor_num, boss_name, photo, description, power_desc, weakness, hp, atk, def, reward_coins, reward_xp, drop_item, drop_price)
           VALUES ($1,$2,$3,$4,$5,$6,$7,$8,$9,$10,$11,$12,$13)
           ON CONFLICT (floor_num) DO UPDATE SET
           boss_name=$2, photo=$3, description=$4, power_desc=$5, weakness=$6, hp=$7, atk=$8, def=$9, reward_coins=$10, reward_xp=$11, drop_item=$12, drop_price=$13""",
        fnum, bname, photo, desc, pdesc, weak, hp, atk, df, rcoins, rxp, drop_item, drop_price
    )
    await state.clear()
    await msg.reply(f"✅ طبقه {fnum} ({bname}) ثبت/بروزرسانی شد!")


@router.message(StateFilter(TowerAdminStates.del_floor), F.text)
async def st_del_floor(msg: Message, state: FSMContext):
    if msg.text.strip().isdigit():
        await db.pool.execute("DELETE FROM dt_floors WHERE floor_num=$1", int(msg.text.strip()))
        await state.clear()
        await msg.reply("🗑️ طبقه حذف شد.")


@router.message(StateFilter(TowerAdminStates.add_weapon), F.text)
async def st_add_weapon(msg: Message, state: FSMContext):
    p = [x.strip() for x in msg.text.split("|")]
    if len(p) < 7:
        await msg.reply("❌ فرمت نادرست است.")
        return
    photo = "" if p[1] == "-" else p[1]
    await db.pool.execute(
        """INSERT INTO dt_items (item_type, name, photo, price, hp_bonus, atk_bonus, def_bonus, spd_bonus)
           VALUES ('weapon', $1, $2, $3, $4, $5, $6, $7)""",
        p[0], photo, int(p[2]), int(p[3]), int(p[4]), int(p[5]), int(p[6])
    )
    await state.clear()
    await msg.reply(f"⚔️ سلاح «{p[0]}» اضافه شد!")


@router.message(StateFilter(TowerAdminStates.del_weapon), F.text)
@router.message(StateFilter(TowerAdminStates.del_armor), F.text)
async def st_del_item(msg: Message, state: FSMContext):
    if msg.text.strip().isdigit():
        await db.pool.execute("DELETE FROM dt_items WHERE id=$1", int(msg.text.strip()))
        await state.clear()
        await msg.reply("🗑️ آیتم حذف شد.")


@router.message(StateFilter(TowerAdminStates.add_armor), F.text)
async def st_add_armor(msg: Message, state: FSMContext):
    p = [x.strip() for x in msg.text.split("|")]
    if len(p) < 6:
        await msg.reply("❌ فرمت نادرست است.")
        return
    photo = "" if p[1] == "-" else p[1]
    await db.pool.execute(
        """INSERT INTO dt_items (item_type, name, photo, price, hp_bonus, atk_bonus, def_bonus, spd_bonus)
           VALUES ('armor', $1, $2, $3, $4, 0, $5, $6)""",
        p[0], photo, int(p[2]), int(p[3]), int(p[4]), int(p[5])
    )
    await state.clear()
    await msg.reply(f"🛡️ زره «{p[0]}» اضافه شد!")


@router.message(StateFilter(TowerAdminStates.add_gift), F.text)
async def st_add_gift(msg: Message, state: FSMContext):
    p = [x.strip() for x in msg.text.split("|")]
    if len(p) < 4:
        await msg.reply("❌ فرمت نادرست است.")
        return
    await db.pool.execute(
        """INSERT INTO dt_gifts (code, coins, xp, max_uses, used_by)
           VALUES ($1, $2, $3, $4, '[]')
           ON CONFLICT (code) DO UPDATE SET coins=$2, xp=$3, max_uses=$4""",
        p[0], int(p[1]), int(p[2]), int(p[3])
    )
    await state.clear()
    await msg.reply(f"🎁 کد هدیه <code>{p[0]}</code> ساخته شد!", parse_mode=ParseMode.HTML)


@router.message(StateFilter(TowerAdminStates.add_popup), F.text)
async def st_add_popup(msg: Message, state: FSMContext):
    if msg.text.strip() == "حذف":
        await set_dt_config("active_popup", "")
        await state.clear()
        await msg.reply("🗑️ پاپ‌آپ تبلیغاتی حذف شد.")
        return
    p = [x.strip() for x in msg.text.split("|")]
    if len(p) < 5:
        await msg.reply("❌ فرمت نادرست است.")
        return
    hours = float(p[4])
    popup_obj = {
        "text": p[0],
        "photo": "" if p[1] == "-" else p[1],
        "btn_text": "" if p[2] == "-" else p[2],
        "btn_url": "" if p[3] == "-" else p[3],
        "expires_at": time.time() + (hours * 3600),
    }
    await set_dt_config("active_popup", json.dumps(popup_obj))
    await state.clear()
    await msg.reply(f"📢 پاپ‌آپ تبلیغاتی برای مدت {hours} ساعت فعال شد!")


@router.message(StateFilter(TowerAdminStates.check_user), F.text)
async def st_check_user(msg: Message, state: FSMContext):
    if not msg.text.strip().isdigit():
        return
    uid = int(msg.text.strip())
    st = await get_or_create_player(uid)
    p = st["player"]
    await state.clear()
    await msg.reply(
        f"👤 <b>پرونده بازیکن برج شیاطین</b> (<code>{uid}</code>)\n\n"
        f"🔹 جنسیت: {p['gender'] or 'انتخاب نشده'}\n"
        f"⭐ لول: {p['level']} (XP: {p['xp']})\n"
        f"🪙 سکه کیف پول: {p['coins']:,} | 🏦 بانک: {p['bank_coins']:,}\n"
        f"🏰 طبقه فعلی: {p['current_floor']}\n"
        f"❤️ جان: {p['hp']}/{p['max_hp']} | 🧠 انسانیت: {p['humanity']}%\n"
        f"⚔️ سلاح: {p['weapon_name']} | 🛡️ زره: {p['armor_name']}\n"
        f"🚫 مسدود: {'بله' if p['is_banned'] else 'خیر'}",
        parse_mode=ParseMode.HTML,
    )


@router.message(StateFilter(TowerAdminStates.charge_user), F.text)
async def st_charge_user(msg: Message, state: FSMContext):
    p = [x.strip() for x in msg.text.split("|")]
    if len(p) < 3:
        return
    uid, add_c, add_xp = int(p[0]), int(p[1]), int(p[2])
    await get_or_create_player(uid)
    await db.pool.execute(
        "UPDATE dt_players SET coins=coins+$1, xp=xp+$2 WHERE user_id=$3",
        add_c, add_xp, uid
    )
    await state.clear()
    await msg.reply(f"⚡ کاربر <code>{uid}</code> به میزان +{add_c} سکه و +{add_xp} XP شارژ شد!", parse_mode=ParseMode.HTML)


@router.message(StateFilter(TowerAdminStates.ban_user), F.text)
async def st_ban_user(msg: Message, state: FSMContext):
    if not msg.text.strip().isdigit():
        return
    uid = int(msg.text.strip())
    await get_or_create_player(uid)
    cur = await db.pool.fetchval("SELECT is_banned FROM dt_players WHERE user_id=$1", uid)
    new_b = not bool(cur)
    await db.pool.execute("UPDATE dt_players SET is_banned=$1 WHERE user_id=$2", new_b, uid)
    await state.clear()
    await msg.reply(f"وضعیت مسدودیت کاربر {uid} در برج شیاطین به «{'مسدود' if new_b else 'آزاد'}» تغییر یافت.")

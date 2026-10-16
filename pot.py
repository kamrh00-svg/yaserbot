import os
import re
import html
import random
import asyncio
import logging
import sqlite3
import threading
from contextlib import contextmanager
from datetime import datetime, timedelta, timezone

from pyrogram import Client, filters, enums
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton, Message, CallbackQuery, ChatPermissions

# ========================= Configuration =========================
API_ID = int(os.getenv("API_ID", "0"))
API_HASH = os.getenv("API_HASH", "")
BOT_TOKEN = os.getenv("BOT_TOKEN", "")
PRIMARY_DEVELOPER_ID = int(os.getenv("PRIMARY_DEVELOPER_ID", "7548185368"))
DEVELOPER_USERNAME = os.getenv("DEVELOPER_USERNAME", "was_yaser").lstrip("@")
DEVELOPER_URL = f"https://t.me/{DEVELOPER_USERNAME}"
BOT_NAME = "سورس الكردي"
DB_PATH = os.getenv("DB_PATH", "kurdi_supreme.db")

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
log = logging.getLogger("kurdi-supreme")

if not API_ID or not API_HASH or not BOT_TOKEN:
    log.warning("Set API_ID, API_HASH, and BOT_TOKEN environment variables before running the bot.")

app = Client(
    "kurdi_supreme_session",
    api_id=API_ID,
    api_hash=API_HASH,
    bot_token=BOT_TOKEN,
    parse_mode=enums.ParseMode.HTML,
)

RANKS = {
    "source_dev": {"name": "مطور السورس", "level": 110, "label": "مطور السورس"},
    "base_dev": {"name": "المطور الأساسي", "level": 100, "label": "المطور الأساسي"},
    "al_moheeb": {"name": "المهيب", "level": 90, "label": "المهيب"},
    "queen": {"name": "الملكة", "level": 85, "label": "الملكة"},
    "king": {"name": "الملك", "level": 85, "label": "الملك"},
    "secondary_dev": {"name": "المطور الثانوي", "level": 80, "label": "المطور الثانوي"},
    "developer": {"name": "المطور", "level": 70, "label": "المطور"},
    "base_creator": {"name": "المنشئ الأساسي", "level": 60, "label": "المنشئ الأساسي"},
    "creator": {"name": "المنشئ", "level": 50, "label": "المنشئ"},
    "manager": {"name": "المدير", "level": 40, "label": "المدير"},
    "admin": {"name": "الأدمن", "level": 30, "label": "الأدمن"},
    "member": {"name": "عضو", "level": 0, "label": "عضو"},
}

RANK_ALIASES = {
    "أدمن": "admin", "ادمن": "admin", "الأدمن": "admin", "الادمن": "admin",
    "مدير": "manager", "المدير": "manager",
    "منشئ": "creator", "المنشئ": "creator",
    "منشئ أساسي": "base_creator", "منشئ اساسي": "base_creator",
    "مطور": "developer", "المطور": "developer",
    "مطور ثانوي": "secondary_dev", "المطور الثانوي": "secondary_dev",
    "ملك": "king", "الملك": "king", "ملكة": "queen", "الملكة": "queen",
    "مهيب": "al_moheeb", "المهيب": "al_moheeb",
    "مطور أساسي": "base_dev", "مطور اساسي": "base_dev", "المطور الأساسي": "base_dev",
    "مطور السورس": "source_dev", "مطور سورس": "source_dev",
}

DUAS = [
    "اللهم إني أسألك العفو والعافية في الدنيا والآخرة.",
    "رب اشرح لي صدري ويسّر لي أمري.",
    "اللهم اقسم لنا من خشيتك ما تحول به بيننا وبين معاصيك.",
    "اللهم إني أعوذ بك من زوال نعمتك وتحول عافيتك.",
]

# قوائم البصمات الصوتية الجديدة (أدعية وأغاني بصيغة رسائل صوتية وهمية أو محاكاة بصمات)
VOICE_DUAS = [
    "https://t.example.com/voice_dua_1.ogg",  # بصوت عذب دعاء مستجاب
    "https://t.example.com/voice_dua_2.ogg",  # بصوت خاشع أدعية الليل
]

VOICE_SONGS = [
    "https://t.example.com/voice_song_1.ogg", # مقطع صوتي طربي هادئ
    "https://t.example.com/voice_song_2.ogg", # بصمة أغنية عراقية أصيلة
]

QUOTES = [
    "كن كالنخيل عن الأحقاد مرتفعاً، يُرمى بالحجر فيلقي أطيب الثمر.",
    "النجاح ليس ألّا تخطئ، بل أن تتعلم من الخطأ ولا تكرره.",
]
WOULD_YOU_RATHER = [
    "لو خيّروك تعيش وحدك بجزيرة لو تعيش ويا شخص مزعج؟",
    "تسامح شخص خان ثقتك لو تنهي علاقتك بيه؟",
]
TRUTH_QUESTIONS = [
    "شنو أكثر صفة تحبها بنفسك؟",
    "شنو قرار تتمنى لو أخذته بوقت أبكر؟",
]

TRIVIA_QUESTIONS = [
    {"q": "ما هي عاصمة اليابان؟", "a": "طوكيو"},
    {"q": "كم عدد سور القرآن الكريم؟", "a": "114"},
    {"q": "ما هو الكوكب الأحمر في المجموعة الشمسية؟", "a": "المريخ"},
]

WORD_UNSCRAMBLE = [
    {"scrambled": "ك ر د ي", "answer": "كردي"},
    {"scrambled": "ت ي ل ي ج ر ا م", "answer": "تيليجرام"},
    {"scrambled": "س و ر س", "answer": "سورس"},
]

TITLES = ["الأسطورة", "الشيخ", "الزعيم", "المحارب", "الفيلسوف", "الهادئ", "المشاكس"]

active_games = {}
marriage_proposals = {}
user_spam_tracker = {}
user_add_cmd_state = {}
_salary_cooldowns = {}
_gift_cooldowns = {}

# ========================= Database =========================
_db_lock = threading.RLock()
conn = sqlite3.connect(DB_PATH, check_same_thread=False, timeout=30)
conn.row_factory = sqlite3.Row
with _db_lock:
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")


def init_db():
    with _db_lock:
        conn.executescript("""
        CREATE TABLE IF NOT EXISTS settings (
            chat_id INTEGER PRIMARY KEY,
            enabled INTEGER NOT NULL DEFAULT 1,
            lock_links INTEGER NOT NULL DEFAULT 1,
            lock_forward INTEGER NOT NULL DEFAULT 0,
            lock_bots INTEGER NOT NULL DEFAULT 1,
            lock_media INTEGER NOT NULL DEFAULT 0,
            lock_stickers INTEGER NOT NULL DEFAULT 0,
            lock_spam INTEGER NOT NULL DEFAULT 0,
            lock_tag INTEGER NOT NULL DEFAULT 0,
            auto_clean INTEGER NOT NULL DEFAULT 0,
            clean_count INTEGER NOT NULL DEFAULT 25,
            clean_minutes INTEGER NOT NULL DEFAULT 1
        );
        CREATE TABLE IF NOT EXISTS aliases (
            chat_id INTEGER NOT NULL,
            alias_name TEXT NOT NULL,
            original_cmd TEXT NOT NULL,
            PRIMARY KEY(chat_id, alias_name)
        );
        CREATE TABLE IF NOT EXISTS ranks (
            user_id INTEGER NOT NULL,
            chat_id INTEGER NOT NULL,
            rank_key TEXT NOT NULL,
            assigned_by INTEGER,
            assigned_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            PRIMARY KEY(user_id, chat_id)
        );
        CREATE TABLE IF NOT EXISTS global_ranks (
            user_id INTEGER PRIMARY KEY,
            rank_key TEXT NOT NULL,
            assigned_by INTEGER,
            assigned_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
        );
        CREATE TABLE IF NOT EXISTS points (
            chat_id INTEGER NOT NULL,
            user_id INTEGER NOT NULL,
            score INTEGER NOT NULL DEFAULT 0,
            PRIMARY KEY(chat_id, user_id)
        );
        CREATE TABLE IF NOT EXISTS marriages (
            chat_id INTEGER NOT NULL,
            user1_id INTEGER NOT NULL,
            user2_id INTEGER NOT NULL,
            married_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            PRIMARY KEY(chat_id, user1_id)
        );
        CREATE TABLE IF NOT EXISTS jail (
            chat_id INTEGER NOT NULL,
            user_id INTEGER NOT NULL,
            jailed_by INTEGER NOT NULL,
            PRIMARY KEY(chat_id, user_id)
        );
        CREATE TABLE IF NOT EXISTS message_counts (
            chat_id INTEGER NOT NULL,
            user_id INTEGER NOT NULL,
            count INTEGER NOT NULL DEFAULT 0,
            PRIMARY KEY(chat_id, user_id)
        );
        CREATE TABLE IF NOT EXISTS warnings (
            chat_id INTEGER NOT NULL,
            user_id INTEGER NOT NULL,
            count INTEGER NOT NULL DEFAULT 0,
            PRIMARY KEY(chat_id, user_id)
        );
        CREATE TABLE IF NOT EXISTS audit_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT, chat_id INTEGER NOT NULL, actor_id INTEGER NOT NULL,
            target_id INTEGER, action TEXT NOT NULL, details TEXT, created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
        );
        """)
        conn.commit()


@contextmanager
def db_cursor():
    with _db_lock:
        cur = conn.cursor()
        try:
            yield cur
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            cur.close()


init_db()


def ensure_settings(chat_id: int):
    with db_cursor() as cur:
        cur.execute("INSERT OR IGNORE INTO settings (chat_id) VALUES (?)", (chat_id,))


def get_settings(chat_id: int):
    with db_cursor() as cur:
        cur.execute("SELECT * FROM settings WHERE chat_id = ?", (chat_id,))
        row = cur.fetchone()
    return dict(row) if row else None


def get_alias_cmd(chat_id: int, text: str) -> str:
    with db_cursor() as cur:
        cur.execute("SELECT original_cmd FROM aliases WHERE chat_id = ? AND alias_name = ?", (chat_id, text))
        row = cur.fetchone()
        if row:
            return row["original_cmd"]
    return text


def get_rank_key(user_id: int, chat_id: int | None = None) -> str:
    if user_id == PRIMARY_DEVELOPER_ID:
        return "source_dev"
    with db_cursor() as cur:
        cur.execute("SELECT rank_key FROM global_ranks WHERE user_id = ?", (user_id,))
        row = cur.fetchone()
        if row and row["rank_key"] in RANKS:
            return row["rank_key"]
        if chat_id is not None:
            cur.execute("SELECT rank_key FROM ranks WHERE user_id = ? AND chat_id = ?", (user_id, chat_id))
            row = cur.fetchone()
            if row and row["rank_key"] in RANKS:
                return row["rank_key"]
    return "member"


def get_rank(user_id: int, chat_id: int | None = None) -> str:
    return RANKS[get_rank_key(user_id, chat_id)]["name"]


def rank_level(user_id: int, chat_id: int | None = None) -> int:
    return RANKS[get_rank_key(user_id, chat_id)]["level"]


def is_owner(user_id: int) -> bool:
    return user_id == PRIMARY_DEVELOPER_ID


def is_jailed(chat_id: int, user_id: int) -> bool:
    with db_cursor() as cur:
        cur.execute("SELECT 1 FROM jail WHERE chat_id = ? AND user_id = ?", (chat_id, user_id))
        return bool(cur.fetchone())


def audit(chat_id: int, actor_id: int, action: str, target_id: int | None = None, details: str = ""):
    with db_cursor() as cur:
        cur.execute("INSERT INTO audit_log (chat_id, actor_id, target_id, action, details) VALUES (?, ?, ?, ?, ?)",
                    (chat_id, actor_id, target_id, action, details[:500]))


def esc(value) -> str:
    return html.escape(str(value or ""), quote=True)


async def is_telegram_admin(client: Client, chat_id: int, user_id: int) -> bool:
    try:
        member = await client.get_chat_member(chat_id, user_id)
        return member.status in (enums.ChatMemberStatus.OWNER, enums.ChatMemberStatus.ADMINISTRATOR)
    except Exception:
        return False


async def bot_has_right(client: Client, chat_id: int, right: str) -> bool:
    try:
        me = await client.get_chat_member(chat_id, "me")
        if me.status == enums.ChatMemberStatus.OWNER:
            return True
        if me.status != enums.ChatMemberStatus.ADMINISTRATOR:
            return False
        return bool(getattr(me.privileges, right, False))
    except Exception:
        return False


async def can_manage(client: Client, message: Message, action: str = "manage") -> bool:
    user = message.from_user
    if not user:
        return False
    if await is_telegram_admin(client, message.chat.id, user.id):
        return True
    if action in ("rank", "settings"):
        return rank_level(user.id, message.chat.id) >= RANKS["manager"]["level"]
    return False


def settings_keyboard(settings: dict) -> InlineKeyboardMarkup:
    def state(key):
        return "مفعل" if settings.get(key) else "معطل"
    return InlineKeyboardMarkup([
        [InlineKeyboardButton(f"قفل الروابط: {state('lock_links')}", callback_data="toggle:lock_links")],
        [InlineKeyboardButton(f"قفل التوجيه: {state('lock_forward')}", callback_data="toggle:lock_forward")],
        [InlineKeyboardButton(f"منع البوتات: {state('lock_bots')}", callback_data="toggle:lock_bots")],
        [InlineKeyboardButton(f"قفل الوسائط: {state('lock_media')}", callback_data="toggle:lock_media")],
        [InlineKeyboardButton(f"قفل الملصقات: {state('lock_stickers')}", callback_data="toggle:lock_stickers")],
        [InlineKeyboardButton(f"قفل التكرار: {state('lock_spam')}", callback_data="toggle:lock_spam")],
        [InlineKeyboardButton(f"قفل التاج والتاق: {state('lock_tag')}", callback_data="toggle:lock_tag")],
        [InlineKeyboardButton(f"المسح التلقائي: {state('auto_clean')}", callback_data="toggle:auto_clean")],
        [InlineKeyboardButton("عدد الرسائل -", callback_data="clean:dec"), InlineKeyboardButton(f"{settings.get('clean_count', 25)} رسالة", callback_data="noop"), InlineKeyboardButton("عدد الرسائل +", callback_data="clean:inc")],
        [InlineKeyboardButton("تحديث اللوحة", callback_data="refresh_settings")],
    ])


def commands_keyboard() -> InlineKeyboardMarkup:
    buttons = [
        [
            InlineKeyboardButton("الحماية", callback_data="cmd_tab:1"),
            InlineKeyboardButton("الإدارة", callback_data="cmd_tab:2")
        ],
        [
            InlineKeyboardButton("البنك والألعاب", callback_data="cmd_tab:3"),
            InlineKeyboardButton("الترفيه والبصمات", callback_data="cmd_tab:4")
        ],
        [
            InlineKeyboardButton("إغلاق القائمة", callback_data="close_cmds")
        ]
    ]
    return InlineKeyboardMarkup(buttons)


def get_command_text(tab: int = 1) -> str:
    if tab == 1:
        return (
            "أوامر الحماية والأمان:\n\n"
            "• تفعيل / تعطيل - لتفعيل أو تعطيل البوت.\n"
            "• قفل الروابط / فتح الروابط\n"
            "• قفل التوجيه / فتح التوجيه\n"
            "• قفل الوسائط / فتح الوسائط\n"
            "• قفل الملصقات / فتح الملصقات\n"
            "• قفل التكرار / فتح التكرار\n"
            "• قفل التاج / فتح التاج\n"
            "• اعدادات - فتح لوحة التحكم بالزرار."
        )
    elif tab == 2:
        return (
            "أوامر الإدارة والرفع:\n\n"
            "• رفع أدمن / رفع مدير / رفع منشئ (بالرد)\n"
            "• تنزيل - لتنزيل رتبة العضو (بالرد)\n"
            "• حظر / كتم / تقييد / تحذير (بالرد)\n"
            "• كتم [المدقائق] - كتم العضو لمؤقت زمني.\n"
            "• فك الحظر / فك الكتم (بالرد)\n"
            "• مسح التحذيرات / تصفير النقاط / تصفير الرسائل\n"
            "• اضف امر - نظام إنشاء اختصارات الأوامر.\n"
            "• قائمة الرتب / المطورين / سجل الادارة / احصائيات"
        )
    elif tab == 3:
        return (
            "أوامر البنك والألعاب:\n\n"
            "• بنك / فلوسي - لمعرفة رصيدك.\n"
            "• راتب - الحصول على راتبك اليومي.\n"
            "• هدية - صندوق الجوائز اليومية.\n"
            "• تحويل [المبلغ] - تحويل نقاط بالرد.\n"
            "• روليت [المبلغ] - لعبة الرهان بالنقاط.\n"
            "• تخمين - لعبة حزر الرقم السرّي.\n"
            "• سؤال سريع / تفكيك - ألعاب الحصول على نقاط.\n"
            "• توب - قائمة الأوائل بالنقاط."
        )
    else:
        return (
            "أوامر الترفيه والبصمات الصوتية:\n\n"
            "• بصمة دعاء - جلب دعاء عشوائي بصمة صوتية.\n"
            "• بصمة أغنية - جلب مقطع طربي عشوائي بصمة صوتية.\n"
            "• حجر / ورقة / مقص - لعبة ضد البوت.\n"
            "• زواج (بالرد) / موافق / طلاق / زوجتي\n"
            "• سجن / فك سجن / السجناء - نظام السجن.\n"
            "• عجلة الحظ - عجلة المكافآت العشوائية.\n"
            "• نسبة الحب / نسبة الذكاء / نسبة الغباء\n"
            "• حظك اليوم / لقبي - لمعرفة حظك ولقبك.\n"
            "• دعاء / اقتباس / لو خيروك / صراحة"
        )


async def send_settings(message: Message):
    settings = get_settings(message.chat.id)
    if not settings:
        ensure_settings(message.chat.id)
        settings = get_settings(message.chat.id)
    await message.reply_text(
        f"لوحة {BOT_NAME}\nالمالك: @{esc(DEVELOPER_USERNAME)}\n\nاختر الإعداد الذي تريد تغييره:",
        reply_markup=settings_keyboard(settings),
    )


# ========================= Welcoming =========================
@app.on_message(filters.group & filters.new_chat_members)
async def welcome_new_members(client: Client, message: Message):
    for member in message.new_chat_members:
        if member.is_bot:
            continue
        await message.reply_text(
            f"أهلاً بك يا {esc(member.first_name)} في المجموعة!\n"
            f"آيديك: {member.id}\n"
            f"نتمنى لك وقتاً ممتعاً معنا!"
        )


# ========================= Private interface (واجهة الخاص المطابقة للصورة) =========================
@app.on_message(filters.private & filters.text & ~filters.bot)
async def private_handler(client: Client, message: Message):
    text = (message.text or "").strip()
    user = message.from_user
    if not user:
        return
    if text.lower() in ("/start", "start", "بدء"):
        # تصميم الأزرار مطابق تماماً للصورة المطلوبة:
        # 1. زر المالك في الأعلى
        # 2. زرين في المنتصف (اضفني، المطور)
        # 3. زر أسفل عريض (لشراء بوت مشابه)
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton(f"- {esc(DEVELOPER_USERNAME)}", url=DEVELOPER_URL)],
            [
                InlineKeyboardButton("اضفني", callback_data="none"),
                InlineKeyboardButton("المطور", url=DEVELOPER_URL)
            ],
            [InlineKeyboardButton("لشراء بوت مشابه", url=DEVELOPER_URL)]
        ])
        
        # صورة جديدة جميلة تعبر عن سورس الكردي
        photo_url = "https://images.unsplash.com/photo-1618005182384-a83a8bd57fbe?q=80&w=1000&auto=format&fit=crop"
        
        caption_text = (
            f"- أهلاً بك في بوت الحماية الخاص بـ {esc(BOT_NAME)}.\n"
            f"- وظيفتي حماية المجموعات من التفليش والتخريب.\n"
            f"- لتفعيل البوت أرسل كلمة: تفعيل\n\n"
            f"المعرف الأساسي: @{esc(DEVELOPER_USERNAME)}"
        )
        
        try:
            await message.reply_photo(photo=photo_url, caption=caption_text, reply_markup=keyboard)
        except Exception:
            await message.reply_text(caption_text, reply_markup=keyboard)


# ========================= Group commands =========================
@app.on_message(filters.group & filters.text & ~filters.bot)
async def group_handler(client: Client, message: Message):
    raw_text = (message.text or "").strip()
    chat_id = message.chat.id
    user = message.from_user
    if not user:
        return
    user_id = user.id

    state_key = (chat_id, user_id)
    if state_key in user_add_cmd_state:
        step = user_add_cmd_state[state_key]["step"]
        if step == 1:
            user_add_cmd_state[state_key]["orig"] = raw_text
            user_add_cmd_state[state_key]["step"] = 2
            return await message.reply_text("قم الان بأرسال الامر الجديد .")
        elif step == 2:
            orig_cmd = user_add_cmd_state[state_key]["orig"]
            new_alias = raw_text
            del user_add_cmd_state[state_key]
            with db_cursor() as cur:
                cur.execute("INSERT OR REPLACE INTO aliases (chat_id, alias_name, original_cmd) VALUES (?, ?, ?)", (chat_id, new_alias, orig_cmd))
            return await message.reply_text("تم حفظ الامر بنجاح")

    if raw_text in ("اضف امر", "أضف أمر"):
        if not await can_manage(client, message, "rank"):
            return await message.reply_text("هذا الأمر متاح للمشرفين والمديرين فقط.")
        user_add_cmd_state[state_key] = {"step": 1, "orig": ""}
        return await message.reply_text("قم الان بأرسال الامر القديم")

    text = get_alias_cmd(chat_id, raw_text)
    settings = get_settings(chat_id)

    if text == "الاختصارات":
        with db_cursor() as cur:
            cur.execute("SELECT alias_name, original_cmd FROM aliases WHERE chat_id = ?", (chat_id,))
            rows = cur.fetchall()
        if not rows:
            return await message.reply_text("لا توجد اختصارات مضافة في هذه المجموعة بعد.")
        lines = ["قائمة الاختصارات المضافة:"]
        lines.extend(f"• {row['alias_name']} ➔ {row['original_cmd']}" for row in rows)
        return await message.reply_text("\n".join(lines))

    if is_jailed(chat_id, user_id) and text not in ("فك سجن", "كفالة"):
        if random.random() < 0.3:
            return await message.reply_text(f"أنت في السجن يا {esc(user.first_name)}! لا يمكنك المشاركة بالألعاب أو الأوامر.")

    if text in ("السلام عليكم", "سلام عليكم", "السلام عليكم ورحمة الله"):
        return await message.reply_text(f"وعليكم السلام ورحمة الله وبركاته، أهلاً بك يا {esc(user.first_name)}")

    if text in ("هلو", "هلا", "مرحبا"):
        return await message.reply_text(f"أهلاً وسهلاً بك يا {esc(user.first_name)}")

    if text in ("الاوامر", "أوامر", "الاوامر بالازرار"):
        return await message.reply_text(
            get_command_text(1),
            reply_markup=commands_keyboard()
        )

    # الأقسام الجديدة تماماً: بصمات صوتية عشوائية للأدعية والأغاني ضمن الترفيه
    if text in ("بصمة دعاء", "دعاء صوتي"):
        # محاكاة إرسال بصمة صوتية (Voice Message) للأدعية
        chosen_dua = random.choice(DUAS)
        return await message.reply_voice(voice=random.choice(VOICE_DUAS), caption=f"دعاء بصوت عذب:\n{chosen_dua}")

    if text in ("بصمة أغنية", "اغنية صوتية", "طرب"):
        # محاكاة إرسال بصمة صوتية للأغاني
        return await message.reply_voice(voice=random.choice(VOICE_SONGS), caption="مقطع صوتي طربي حصري عبر سورس الكردي.")

    if text in ("هدية", "الهدية"):
        now = datetime.now(timezone.utc)
        last = _gift_cooldowns.get((chat_id, user_id))
        if last and now - last < timedelta(hours=12):
            return await message.reply_text("لقد استلمت هديتك مؤخراً! عد بعد عدة ساعات.")
        _gift_cooldowns[(chat_id, user_id)] = now
        gift_pts = random.randint(15, 60)
        with db_cursor() as cur:
            cur.execute("INSERT INTO points (chat_id, user_id, score) VALUES (?, ?, ?) ON CONFLICT(chat_id, user_id) DO UPDATE SET score = score + ?", (chat_id, user_id, gift_pts, gift_pts))
        return await message.reply_text(f"مبروك! فتحت صندوق الهدايا وحصلت على {gift_pts} نقطة!")

    if text in ("المطورين", "المطورين والمشرفين"):
        return await message.reply_text(f"مطور السورس الأساسي: @{esc(DEVELOPER_USERNAME)}\nالآيدي: {PRIMARY_DEVELOPER_ID}")

    if text in ("تخمين", "حزر الرقم"):
        num = random.randint(1, 10)
        active_games[chat_id] = {"type": "تخمين الرقم", "answer": str(num), "prize": 5}
        return await message.reply_text("اخترت رقماً سرية بين 1 و 10! أول شخص يحزر الرقم يربح 5 نقاط.")

    if chat_id in active_games and text == active_games[chat_id]["answer"]:
        prize = active_games[chat_id]["prize"]
        game_name = active_games[chat_id]["type"]
        del active_games[chat_id]
        with db_cursor() as cur:
            cur.execute("INSERT INTO points (chat_id, user_id, score) VALUES (?, ?, ?) ON CONFLICT(chat_id, user_id) DO UPDATE SET score = score + ?", (chat_id, user_id, prize, prize))
            cur.execute("SELECT score FROM points WHERE chat_id = ? AND user_id = ?", (chat_id, user_id))
            score = cur.fetchone()["score"]
        return await message.reply_text(f"إجابتك صحيحة في لعبة ({game_name}) وربحت {prize} نقاط.\nمجموعك الحالي: {score}")

    if text == "سجن":
        if not await can_manage(client, message, "rank"):
            return await message.reply_text("السجن متاح للمشرفين والمديرين فقط.")
        if not message.reply_to_message or not message.reply_to_message.from_user:
            return await message.reply_text("رد على رسالة العضو المطلوب سجنه.")
        target = message.reply_to_message.from_user
        if target.id == PRIMARY_DEVELOPER_ID or target.id == user_id:
            return await message.reply_text("لا يمكنك سجن نفسك أو المطور الأساسي!")
        with db_cursor() as cur:
            cur.execute("INSERT OR REPLACE INTO jail (chat_id, user_id, jailed_by) VALUES (?, ?, ?)", (chat_id, target.id, user_id))
        return await message.reply_text(f"تم إدخال {esc(target.first_name)} إلى سجن المجموعة!")

    if text in ("فك سجن", "إفراج"):
        if not await can_manage(client, message, "rank"):
            return await message.reply_text("هذا الأمر متاح للمشرفين والمديرين فقط.")
        if not message.reply_to_message or not message.reply_to_message.from_user:
            return await message.reply_text("رد على رسالة العضو المسجون.")
        target = message.reply_to_message.from_user
        with db_cursor() as cur:
            cur.execute("DELETE FROM jail WHERE chat_id = ? AND user_id = ?", (chat_id, target.id))
        return await message.reply_text(f"تم الإفراج عن {esc(target.first_name)} وبإمكانه المشاركة الآن!")

    if text == "السجناء":
        with db_cursor() as cur:
            cur.execute("SELECT user_id FROM jail WHERE chat_id = ?", (chat_id,))
            rows = cur.fetchall()
        if not rows:
            return await message.reply_text("لا يوجد سجناء في الوقت الحالي!")
        lines = ["قائمة السجناء بالمجموعة:"]
        lines.extend(f"• {r['user_id']}" for r in rows)
        return await message.reply_text("\n".join(lines))

    if text in ("عجلة الحظ", "يا نصيب"):
        prize = random.choice([0, 5, 10, 20, 50, 100])
        with db_cursor() as cur:
            cur.execute("INSERT INTO points (chat_id, user_id, score) VALUES (?, ?, ?) ON CONFLICT(chat_id, user_id) DO UPDATE SET score = score + ?", (chat_id, user_id, prize, prize))
        return await message.reply_text(f"درت عجلة الحظ وفزت بـ {prize} نقطة!")

    if text in ("تفعيل", "/enable"):
        if not (await is_telegram_admin(client, chat_id, user_id) or is_owner(user_id)):
            return await message.reply_text("تفعيل البوت متاح لمشرفي المجموعة فقط.")
        ensure_settings(chat_id)
        return await message.reply_text(f"تم تفعيل {BOT_NAME}.")

    if text in ("تعطيل", "/disable"):
        if not await is_telegram_admin(client, chat_id, user_id):
            return await message.reply_text("هذا الأمر للمشرفين فقط.")
        with db_cursor() as cur:
            cur.execute("UPDATE settings SET enabled = 0 WHERE chat_id = ?", (chat_id,))
        return await message.reply_text("تم تعطيل أوامر الحماية في هذه المجموعة.")

    if text in ("ايدي", "id", "/id"):
        target = message.reply_to_message.from_user if message.reply_to_message and message.reply_to_message.from_user else user
        return await message.reply_text(
            f"معلومات العضو\nالاسم: {esc(target.first_name)}\nالآيدي: {target.id}\n"
            f"الرتبة: {get_rank(target.id, chat_id)}\nآيدي المجموعة: {chat_id}")

    if text in ("اعدادات المسح", "اعدادات", "لوحة التحكم"):
        if not await can_manage(client, message, "settings"):
            return await message.reply_text("تحتاج صلاحية مشرف أو رتبة مدير فأعلى.")
        return await send_settings(message)

    if text.startswith("روليت"):
        parts = text.split()
        if len(parts) < 2 or not parts[1].isdigit():
            return await message.reply_text("اكتب المبلغ للرهان عليه، مثال: روليت 10")
        bet = int(parts[1])
        if bet <= 0:
            return await message.reply_text("يجب أن يكون الرهان بأكثر من 0 نقطة.")
        
        with db_cursor() as cur:
            cur.execute("SELECT score FROM points WHERE chat_id = ? AND user_id = ?", (chat_id, user_id))
            row = cur.fetchone()
            score = row["score"] if row else 0
            if score < bet:
                return await message.reply_text("رصيدك لا يكفي للمراهنة بهذا المبلغ!")
            
            won = random.choice([True, False])
            if won:
                cur.execute("UPDATE points SET score = score + ? WHERE chat_id = ? AND user_id = ?", (bet, chat_id, user_id))
                return await message.reply_text(f"مبروك! ضربت معك الروليت وفزت بـ {bet} نقطة إضافية!")
            else:
                cur.execute("UPDATE points SET score = score - ? WHERE chat_id = ? AND user_id = ?", (bet, chat_id, user_id))
                return await message.reply_text(f"للأسف! خسرت الرهان وضاعت منك {bet} نقطة.")

    if text in ("حجر", "ورقة", "مقص"):
        bot_choice = random.choice(["حجر", "ورقة", "مقص"])
        user_choice = text
        if user_choice == bot_choice:
            res = "تعادل"
        elif (user_choice == "حجر" and bot_choice == "مقص") or (user_choice == "ورقة" and bot_choice == "حجر") or (user_choice == "مقص" and bot_choice == "ورقة"):
            res = "فزت عليّ يا بطل!"
            with db_cursor() as cur:
                cur.execute("INSERT INTO points (chat_id, user_id, score) VALUES (?, ?, 2) ON CONFLICT(chat_id, user_id) DO UPDATE SET score = score + 2", (chat_id, user_id))
        else:
            res = "خسرت، أنا الفائز!"
        return await message.reply_text(f"اختيارك: {user_choice} | اختياري: {bot_choice}\nالنتيجة: {res}")

    if text in ("لقبي", "لقب"):
        return await message.reply_text(f"لقبك اليوم في المجموعة هو: {random.choice(TITLES)}")

    if text == "تصفير النقاط":
        if not await can_manage(client, message, "rank"):
            return await message.reply_text("هذا الأمر متاح للمشرفين والمديرين فقط.")
        with db_cursor() as cur:
            cur.execute("DELETE FROM points WHERE chat_id = ?", (chat_id,))
        return await message.reply_text("تم تصفير نقاط جميع الأعضاء في المجموعة وإعادة القائمة من جديد.")

    if text in ("تصفير الرسائل", "تصفير العداد"):
        if not await can_manage(client, message, "rank"):
            return await message.reply_text("هذا الأمر متاح للمشرفين والمديرين فقط.")
        with db_cursor() as cur:
            cur.execute("DELETE FROM message_counts WHERE chat_id = ?", (chat_id,))
        return await message.reply_text("تم تصفير عداد الرسائل والإحصائيات الخاصة بالمجموعة بنجاح.")

    if text in ("بنك", "فلوسي", "رصيدي"):
        with db_cursor() as cur:
            cur.execute("SELECT score FROM points WHERE chat_id = ? AND user_id = ?", (chat_id, user_id))
            row = cur.fetchone()
            score = row["score"] if row else 0
        return await message.reply_text(f"رصيدك في بنك المجموعة:\nالنقاط: {score} نقطة.")

    if text in ("راتب", "راتبي"):
        now = datetime.now(timezone.utc)
        last = _salary_cooldowns.get((chat_id, user_id))
        if last and now - last < timedelta(hours=24):
            remaining = timedelta(hours=24) - (now - last)
            hours, remainder = divmod(remaining.seconds, 3600)
            minutes, _ = divmod(remainder, 60)
            return await message.reply_text(f"يمكنك استلام راتبك بعد {hours} ساعة و {minutes} دقيقة.")
        _salary_cooldowns[(chat_id, user_id)] = now
        salary = random.randint(10, 50)
        with db_cursor() as cur:
            cur.execute("INSERT INTO points (chat_id, user_id, score) VALUES (?, ?, ?) ON CONFLICT(chat_id, user_id) DO UPDATE SET score = score + ?", (chat_id, user_id, salary, salary))
        return await message.reply_text(f"تم إيداع راتبك اليومي بقيمة {salary} نقطة بنجاح!")

    if text.startswith("تحويل"):
        if not message.reply_to_message or not message.reply_to_message.from_user:
            return await message.reply_text("للتحويل، رد على رسالة العضو واكتب: تحويل 10")
        target = message.reply_to_message.from_user
        if target.id == user_id:
            return await message.reply_text("لا يمكنك تحويل النقاط لنفسك.")
        parts = text.split()
        if len(parts) < 2 or not parts[1].isdigit():
            return await message.reply_text("يرجى كتابة المبلغ بالأرقام، مثال: تحويل 10")
        amount = int(parts[1])
        if amount <= 0:
            return await message.reply_text("يجب أن يكون المبلغ أكثر من 0.")
        
        with db_cursor() as cur:
            cur.execute("SELECT score FROM points WHERE chat_id = ? AND user_id = ?", (chat_id, user_id))
            row = cur.fetchone()
            my_score = row["score"] if row else 0
            if my_score < amount:
                return await message.reply_text("رصيدك لا يكفي لإتمام عملية التحويل.")
            cur.execute("UPDATE points SET score = score - ? WHERE chat_id = ? AND user_id = ?", (amount, chat_id, user_id))
            cur.execute("INSERT INTO points (chat_id, user_id, score) VALUES (?, ?, ?) ON CONFLICT(chat_id, user_id) DO UPDATE SET score = score + ?", (chat_id, target.id, amount, amount))
        return await message.reply_text(f"تم تحويل {amount} نقطة بنجاح إلى {esc(target.first_name)}.")

    if text in ("تفكيك", "خمن"):
        item = random.choice(WORD_UNSCRAMBLE)
        active_games[chat_id] = {"type": "تفكيك الكلمة", "answer": item["answer"], "prize": 4}
        return await message.reply_text(f"لعبة تفكيك الكلمة!\n\nجمع الحروف: {item['scrambled']}\nالجائزة: 4 نقاط!")

    if text in ("سؤال سريع", "اختبار", "تحدي ذكاء"):
        item = random.choice(TRIVIA_QUESTIONS)
        active_games[chat_id] = {"type": "سؤال سريع", "answer": item["a"], "prize": 3}
        return await message.reply_text(f"تحدي السرعة والمعلومات!\n\nالسؤال: {item['q']}\nأسرع واحد يجاوب يربح 3 نقاط!")

    if text in ("نسبة الحب", "حب"):
        target = message.reply_to_message.from_user if message.reply_to_message and message.reply_to_message.from_user else user
        return await message.reply_text(f"نسبة الحب بينك وبين {esc(target.first_name)} هي: {random.randint(1, 100)}%")

    if text in ("نسبة الذكاء", "ذكائي"):
        return await message.reply_text(f"نسبة ذكاء {esc(user.first_name)} هي: {random.randint(20, 100)}%")

    if text in ("نسبة الغباء", "غبائي"):
        return await message.reply_text(f"نسبة غباء {esc(user.first_name)} هي: {random.randint(1, 80)}%")

    if text == "زواج":
        if not message.reply_to_message or not message.reply_to_message.from_user:
            return await message.reply_text("بالرد على العضو للزواج منه.")
        target = message.reply_to_message.from_user
        if target.id == user_id:
            return await message.reply_text("لا يمكنك الزواج من نفسك!")
        
        with db_cursor() as cur:
            cur.execute("SELECT user2_id FROM marriages WHERE chat_id = ? AND user1_id = ?", (chat_id, user_id))
            if cur.fetchone():
                return await message.reply_text("أنت متزوج بالفعل!")
            cur.execute("SELECT user1_id FROM marriages WHERE chat_id = ? AND user2_id = ?", (chat_id, target.id))
            if cur.fetchone():
                return await message.reply_text(f"{esc(target.first_name)} متزوج بالفعل.")

        if chat_id not in marriage_proposals:
            marriage_proposals[chat_id] = {}
        marriage_proposals[chat_id][target.id] = user_id
        return await message.reply_text(f"يا {esc(target.first_name)}، يطلب {esc(user.first_name)} الزواج منك!\nاكتب موافق أو رفض.")

    if text in ("موافق", "اقبل") and chat_id in marriage_proposals and user_id in marriage_proposals[chat_id]:
        requester_id = marriage_proposals[chat_id][user_id]
        del marriage_proposals[chat_id][user_id]
        with db_cursor() as cur:
            cur.execute("INSERT INTO marriages (chat_id, user1_id, user2_id) VALUES (?, ?, ?)", (chat_id, requester_id, user_id))
            cur.execute("INSERT INTO marriages (chat_id, user1_id, user2_id) VALUES (?, ?, ?)", (chat_id, user_id, requester_id))
        return await message.reply_text("ألف مبروك! تم عقد الزواج بنجاح")

    if text in ("زوجتي", "زوجي"):
        with db_cursor() as cur:
            cur.execute("SELECT user2_id FROM marriages WHERE chat_id = ? AND user1_id = ?", (chat_id, user_id))
            row = cur.fetchone()
            if not row:
                return await message.reply_text("أنت غير متزوج حالياً.")
            partner_id = row["user2_id"]
        return await message.reply_text(f"شريك حياتك المسجل في المجموعة هو العضو صاحب الآيدي: {partner_id}")

    if text in ("رفض", "أرفض") and chat_id in marriage_proposals and user_id in marriage_proposals[chat_id]:
        del marriage_proposals[chat_id][user_id]
        return await message.reply_text("تم رفض طلب الزواج!")

    if text in ("طلاق", "إنهاء الزواج", "خلع"):
        with db_cursor() as cur:
            cur.execute("SELECT user2_id FROM marriages WHERE chat_id = ? AND user1_id = ?", (chat_id, user_id))
            row = cur.fetchone()
            if not row:
                return await message.reply_text("أنت لست متزوجاً أساساً!")
            partner_id = row["user2_id"]
            cur.execute("DELETE FROM marriages WHERE chat_id = ? AND (user1_id = ? OR user1_id = ?)", (chat_id, user_id, partner_id))
        return await message.reply_text("تم الانفصال وإتمام الطلاق بنجاح.")

    if text.startswith("رفع "):
        if not await can_manage(client, message, "rank"):
            return await message.reply_text("ما عندك صلاحية رفع الرتب.")
        if not message.reply_to_message or not message.reply_to_message.from_user:
            return await message.reply_text("رد على رسالة العضو واكتب: رفع أدمن")
        target = message.reply_to_message.from_user
        label = text[4:].strip()
        new_key = RANK_ALIASES.get(label)
        if not new_key or new_key in ("member", "source_dev"):
            return await message.reply_text("رتبة غير معروفة أو لا يمكن منحها بهذا الأمر.")
        if new_key == "base_dev" and not is_owner(user_id):
            return await message.reply_text("تعيين المطور الأساسي حصري لمطور السورس.")
        actor_is_tg_admin = await is_telegram_admin(client, chat_id, user_id)
        actor_level = max(rank_level(user_id, chat_id), RANKS["admin"]["level"] if actor_is_tg_admin else 0)
        target_level = rank_level(target.id, chat_id)
        new_level = RANKS[new_key]["level"]
        if not is_owner(user_id):
            if new_level >= actor_level:
                return await message.reply_text("ما تگدر تمنح رتبة مساوية أو أعلى من رتبتك.")
            if target.id == PRIMARY_DEVELOPER_ID or target_level >= actor_level:
                return await message.reply_text("ما تگدر تغيّر رتبة شخص مساوي أو أعلى منك.")
        with db_cursor() as cur:
            cur.execute("INSERT OR REPLACE INTO ranks (user_id, chat_id, rank_key, assigned_by, assigned_at) VALUES (?, ?, ?, ?, ?)",
                        (target.id, chat_id, new_key, user_id, datetime.now(timezone.utc).isoformat()))
        audit(chat_id, user_id, "rank_promote", target.id, new_key)
        return await message.reply_text(f"تم منح {esc(target.first_name)} رتبة {RANKS[new_key]['name']}.")

    if text in ("تنزيل", "تنزيل رتبة"):
        if not await can_manage(client, message, "rank"):
            return await message.reply_text("ما عندك صلاحية تنزيل الرتب.")
        if not message.reply_to_message or not message.reply_to_message.from_user:
            return await message.reply_text("رد على رسالة العضو واكتب: تنزيل")
        target = message.reply_to_message.from_user
        if target.id == PRIMARY_DEVELOPER_ID:
            return await message.reply_text("رتبة المطور الأساسي محمية.")
        if not is_owner(user_id) and rank_level(target.id, chat_id) >= rank_level(user_id, chat_id):
            return await message.reply_text("ما تگدر تنزّل رتبة شخص مساوي أو أعلى منك.")
        with db_cursor() as cur:
            cur.execute("DELETE FROM ranks WHERE user_id = ? AND chat_id = ?", (target.id, chat_id))
        audit(chat_id, user_id, "rank_demote", target.id, "member")
        return await message.reply_text(f"تم إرجاع {esc(target.first_name)} إلى رتبة عضو.")

    if text in ("رتبتي", "رتب"):
        if is_owner(user_id):
            return await message.reply_text("رتبتك الخاصة: مطور السورس\nهذه الرتبة لا يمكن منحها أو سحبها من داخل البوت.")
        return await message.reply_text(f"رتبتك الحالية: {get_rank(user_id, chat_id)}")

    if text == "قائمة الرتب":
        with db_cursor() as cur:
            cur.execute("SELECT user_id, rank_key FROM ranks WHERE chat_id = ? ORDER BY user_id", (chat_id,))
            rows = cur.fetchall()
        if not rows:
            return await message.reply_text("ماكو رتب مخصصة بالمجموعة حالياً.")
        lines = ["رتب المجموعة"]
        for row in rows[:80]:
            lines.append(f"• {row['user_id']} — {RANKS.get(row['rank_key'], RANKS['member'])['name']}")
        return await message.reply_text("\n".join(lines))

    if text == "سجل الادارة":
        if not (is_owner(user_id) or rank_level(user_id, chat_id) >= RANKS["manager"]["level"] or await is_telegram_admin(client, chat_id, user_id)):
            return await message.reply_text("هذا الأمر للمشرفين والمديرين فقط.")
        with db_cursor() as cur:
            cur.execute("SELECT actor_id, target_id, action, details, created_at FROM audit_log WHERE chat_id = ? ORDER BY id DESC LIMIT 10", (chat_id,))
            logs = cur.fetchall()
        if not logs:
            return await message.reply_text("سجل الإدارة فارغ حالياً.")
        lines = ["آخر عمليات الإدارة"]
        lines.extend(f"• {esc(row['action'])} | المنفذ {row['actor_id']} | الهدف {row['target_id'] or '-'} | {esc(row['created_at'])}" for row in logs)
        return await message.reply_text("\n".join(lines))

    if text in ("حظك اليوم", "حظي"):
        return await message.reply_text(f"نسبة حظك اليوم يا {esc(user.first_name)} هي: {random.randint(15, 100)}%")

    if text in ("معلومات البوت", "معلومات السورس"):
        return await message.reply_text(f"{esc(BOT_NAME)}\nالإصدار: Supreme Edition 2026\nرتبتك: {esc(get_rank(user_id, chat_id))}")

    if text in ("دعاء", "دع"):
        return await message.reply_text(random.choice(DUAS))
    if text in ("اقتباس", "ق"):
        return await message.reply_text(random.choice(QUOTES))
    if text in ("كت", "لو خيروك", "خيروك"):
        return await message.reply_text(random.choice(WOULD_YOU_RATHER))
    if text in ("صراحة", "سؤال", "اسألني"):
        return await message.reply_text(random.choice(TRUTH_QUESTIONS))
    if text in ("نقاطي", "نقاط"):
        with db_cursor() as cur:
            cur.execute("SELECT score FROM points WHERE chat_id = ? AND user_id = ?", (chat_id, user_id))
            row = cur.fetchone()
        return await message.reply_text(f"نقاطك: {row['score'] if row else 0}")
    if text == "توب":
        with db_cursor() as cur:
            cur.execute("SELECT user_id, score FROM points WHERE chat_id = ? ORDER BY score DESC LIMIT 10", (chat_id,))
            rows = cur.fetchall()
        if not rows:
            return await message.reply_text("ماكو نقاط بعد!")
        lines = ["أفضل 10 أعضاء بالنقاط"]
        lines.extend(f"{i}. {row['user_id']} — {row['score']}" for i, row in enumerate(rows, 1))
        return await message.reply_text("\n".join(lines))

    target_msg = message.reply_to_message
    target_user = target_msg.from_user if target_msg else None
    if text.startswith("كتم ") and target_msg and target_user:
        parts = text.split()
        if len(parts) >= 2 and parts[1].isdigit():
            mins = int(parts[1])
            if await bot_has_right(client, chat_id, "can_restrict_members"):
                await client.restrict_chat_member(
                    chat_id, target_user.id,
                    ChatPermissions(),
                    until_date=datetime.now(timezone.utc) + timedelta(minutes=mins)
                )
                return await message.reply_text(f"تم كتم {esc(target_user.first_name)} لمدة {mins} دقيقة.")

    if text in ("حظر", "الغاء الحظر", "فك الحظر", "كتم", "الغاء الكتم", "تقييد", "الغاء التقييد", "تحذير", "مسح"):
        if not target_msg:
            return await message.reply_text("استخدم الأمر بالرد على رسالة العضو.")
        actor_is_admin = await is_telegram_admin(client, chat_id, user_id)
        if not (actor_is_admin or is_owner(user_id) or rank_level(user_id, chat_id) >= RANKS["admin"]["level"]):
            return await message.reply_text("تحتاج رتبة أدمن على الأقل أو صلاحية مشرف في تيليجرام.")
        if text == "مسح":
            if not await bot_has_right(client, chat_id, "can_delete_messages"):
                return await message.reply_text("ارفع البوت مشرفاً مع صلاحية حذف الرسائل.")
            try:
                await target_msg.delete()
                await message.delete()
                return
            except Exception:
                return await message.reply_text("ما كدرت أحذف الرسالة.")
        if not target_user:
            return await message.reply_text("ما كدرت أحدد حساب العضو.")
        if target_user.id == PRIMARY_DEVELOPER_ID or target_user.id == user_id:
            return await message.reply_text("ما يصير تنفّذ هذا الإجراء على نفسك أو المطور الأساسي.")
        if not is_owner(user_id) and rank_level(target_user.id, chat_id) >= rank_level(user_id, chat_id):
            return await message.reply_text("ما تگدر تعاقب شخص رتبته مساوية أو أعلى منك.")
        try:
            if text == "حظر":
                await client.ban_chat_member(chat_id, target_user.id)
                audit(chat_id, user_id, "ban", target_user.id)
                return await message.reply_text(f"تم حظر {esc(target_user.first_name)}.")
            if text in ("الغاء الحظر", "فك الحظر"):
                await client.unban_chat_member(chat_id, target_user.id, only_if_banned=True)
                return await message.reply_text(f"تم فك حظر {esc(target_user.first_name)}.")
            if text in ("كتم", "تقييد"):
                await client.restrict_chat_member(chat_id, target_user.id, ChatPermissions())
                audit(chat_id, user_id, "mute", target_user.id)
                return await message.reply_text(f"تم تقييد {esc(target_user.first_name)}.")
            if text in ("الغاء الكتم", "فك الكتم", "الغاء التقييد"):
                await client.restrict_chat_member(chat_id, target_user.id, ChatPermissions(can_send_messages=True))
                return await message.reply_text(f"تم إلغاء تقييد {esc(target_user.first_name)}.")
            if text == "تحذير":
                with db_cursor() as cur:
                    cur.execute("INSERT INTO warnings (chat_id, user_id, count) VALUES (?, ?, 1) ON CONFLICT(chat_id, user_id) DO UPDATE SET count = count + 1", (chat_id, target_user.id))
                    cur.execute("SELECT count FROM warnings WHERE chat_id = ? AND user_id = ?", (chat_id, target_user.id))
                    count = cur.fetchone()["count"]
                if count >= 3 and await bot_has_right(client, chat_id, "can_restrict_members"):
                    await client.ban_chat_member(chat_id, target_user.id)
                    with db_cursor() as cur:
                        cur.execute("DELETE FROM warnings WHERE chat_id = ? AND user_id = ?", (chat_id, target_user.id))
                    return await message.reply_text(f"{esc(target_user.first_name)} وصل 3 تحذيرات وتم حظره.")
                return await message.reply_text(f"تحذير {count}/3 لـ {esc(target_user.first_name)}.")
        except Exception:
            return await message.reply_text("فشل تنفيذ الأمر.")

    if settings and settings.get("enabled", 1):
        is_admin = await is_telegram_admin(client, chat_id, user_id)
        if not is_admin:
            if settings.get("lock_tag") and ("@" in raw_text or "#" in raw_text):
                if await bot_has_right(client, chat_id, "can_delete_messages"):
                    try:
                        await message.delete()
                    except Exception:
                        pass
                return

            if settings.get("lock_spam"):
                tracker_key = (chat_id, user_id)
                last_track = user_spam_tracker.get(tracker_key, {"text": "", "count": 0})
                if last_track["text"] == raw_text and len(raw_text) > 2:
                    last_track["count"] += 1
                else:
                    last_track = {"text": raw_text, "count": 1}
                user_spam_tracker[tracker_key] = last_track
                
                if last_track["count"] >= 4:
                    try:
                        await message.delete()
                        if last_track["count"] == 4:
                            warn = await message.reply_text(f"يا {esc(user.first_name)}، يمنع التكرار والإزعاج داخل المجموعة!")
                            await asyncio.sleep(4)
                            await warn.delete()
                        return
                    except Exception:
                        pass

            if settings.get("lock_links") and re.search(r"(https?://|t\.me/|telegram\.me/|www\.)", raw_text, re.I):
                if await bot_has_right(client, chat_id, "can_delete_messages"):
                    try:
                        await message.delete()
                    except Exception:
                        pass
                return


# ================= Callback Query Handler =================
@app.on_callback_query()
async def callback_handler(client: Client, callback: CallbackQuery):
    data = callback.data
    chat = callback.message.chat
    
    if data == "noop":
        return await callback.answer()
        
    if data == "close_cmds":
        return await callback.message.delete()

    if data.startswith("cmd_tab:"):
        tab = int(data.split(":")[1])
        try:
            await callback.message.edit_text(
                get_command_text(tab),
                reply_markup=commands_keyboard()
            )
        except Exception:
            pass
        return await callback.answer()

    if data == "refresh_settings":
        settings = get_settings(chat.id)
        if settings:
            try:
                await callback.message.edit_reply_markup(reply_markup=settings_keyboard(settings))
                return await callback.answer("تم تحديث اللوحة.")
            except Exception:
                pass
        return await callback.answer()

    if data.startswith("toggle:"):
        if not await can_manage(client, callback.message, "settings"):
            return await callback.answer("تحتاج صلاحية مدير لتغيير الإعدادات.", show_alert=True)
        key = data.split(":", 1)[1]
        settings = get_settings(chat.id)
        if not settings:
            ensure_settings(chat.id)
            settings = get_settings(chat.id)
        current_val = settings.get(key, 0)
        new_val = 0 if current_val else 1
        with db_cursor() as cur:
            cur.execute(f"UPDATE settings SET {key} = ? WHERE chat_id = ?", (new_val, chat.id))
        updated_settings = get_settings(chat.id)
        try:
            await callback.message.edit_reply_markup(reply_markup=settings_keyboard(updated_settings))
            await callback.answer(f"تم تغيير إعداد {key}")
        except Exception:
            await callback.answer()

# ========================= Run Bot =========================
if __name__ == "__main__":
    log.info("Starting %s...", BOT_NAME)
    app.run()


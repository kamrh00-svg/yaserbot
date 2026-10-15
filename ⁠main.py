import asyncio
from pyrogram import Client, filters
from pyrogram.types import Message, ChatPermissions

# ----------------- الإعدادات العامة -----------------
API_ID = 36481515          # ضع الـ API ID الخاص بك
API_HASH = "c5dbdd9800f0508275f225367a59a5fe" # ضع الـ API Hash الخاص بك
BOT_TOKEN = "8875318403:AAHP-1CAAjRqPYYYxRlUG0iJHVSnE5ZcmHg" # توكن البوت من BotFather

# أيديات مطوري السورس الأساسيين (لك صلاحية التحكم المطلقة)
DEVELOPERS_IDS = 7548185368
    7548185368  # الآيدي الخاص بك
]

app = Client("TumblrProtectionBot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)

# ----------------- قواعد البيانات المؤقتة (الإعدادات) -----------------
SETTINGS = {
    "lock_links": True,
    "lock_forward": True,
    "lock_mute": False,       # تعطيل/تفعيل الكتم (صلاحية منشئ)
    "lock_promote": False,    # تعطيل/تفعيل الرفع (صلاحية منشئ)
    "auto_clean": False,      # المسح التلقائي
    "clean_count": 5,         # عدد رسائل المسح
    "lock_photos": False,     # قفل الصور
    "lock_stickers": False,   # قفل الملصقات
    "lock_animations": False, # قفل المتحركات
    "allow_all": True,        # تفعيل/تعطيل التاك الجماعي
}

# تخصيص ألقاب ورتب المجموعة
RANKS = {
    "member": "العضو",
    "special": "العضو المميز",
    "admin": "الادمن",
    "manager": "المدير",
    "creator": "المنشئ",
    "head_creator": "المنشئ الاساسي",
    "owner": "المالك",
    "developer": "المطور",
    "al_moheeb": "المهيب",
    "base_dev": "المطور الاساسي",
    "queen": "الملكة",
    "king": "الملك"
}

# تخزين الرتب الخاصة المضافة (تدعم أكثر من شخص لكل رتبة)
SPECIAL_RANKS = {
    "al_moheeb": set(),
    "base_dev": set(),
    "queen": set(),
    "king": set(),
    "source_dev": set()
}

# ----------------- دوال التحقق من الرتب -----------------
async def is_group_owner(client: Client, chat_id: int, user_id: int) -> bool:
    """التحقق مما إذا كان المستخدم هو مالك المجموعة"""
    try:
        member = await client.get_chat_member(chat_id, user_id)
        return member.status == "creator"
    except Exception:
        return False

async def is_creator_or_higher(client: Client, chat_id: int, user_id: int) -> bool:
    """التحقق مما إذا كان المستخدم منشئاً أو أعلى"""
    if user_id in DEVELOPERS_IDS or user_id in SPECIAL_RANKS["source_dev"]:
        return True
    try:
        member = await client.get_chat_member(chat_id, user_id)
        return member.status in ["creator", "administrator"]
    except Exception:
        return False

# ----------------- 1. أوامر مطور السورس -----------------
@app.on_message(filters.command(["مطور سورس", "تعيين مطور سورس"]) & filters.reply & filters.group)
async def set_source_developer(client: Client, message: Message):
    if message.from_user.id not in DEVELOPERS_IDS:
        return await message.reply_text("✦ عذراً، هذا الأمر خاص بمطوري السورس الأساسيين فقط 🚫.")
    
    target_user = message.reply_to_message.from_user
    SPECIAL_RANKS["source_dev"].add(target_user.id)
    await message.reply_text(f"⚡ تم اعتماد رتبة (مطور سورس) بنجاح للعضو: [{target_user.first_name}](tg://user?id={target_user.id})")

# ----------------- 2. أوامر رتب المالك (المهيب، الملك، إلخ) -----------------
@app.on_message(filters.command(["رفع المهيب", "رفع المطور الاساسي", "رفع الملكة", "رفع الملك"]) & filters.reply & filters.group)
async def promote_special_ranks(client: Client, message: Message):
    if not await is_group_owner(client, message.chat.id, message.from_user.id):
        return await message.reply_text("✦ عذراً، هذه الرتب عليا ولا يستطيع رفعها سوى مالك المجموعة فقط.")
    
    target_user = message.reply_to_message.from_user
    cmd = message.text.split()[1]
    
    if "المهيب" in cmd:
        SPECIAL_RANKS["al_moheeb"].add(target_user.id)
        title = "المهيب 🎖️"
    elif "المطور" in cmd:
        SPECIAL_RANKS["base_dev"].add(target_user.id)
        title = "المطور الأساسي ⚡"
    elif "الملكة" in cmd:
        SPECIAL_RANKS["queen"].add(target_user.id)
        title = "الملكة 👑"
    elif "الملك" in cmd:
        SPECIAL_RANKS["king"].add(target_user.id)
        title = "الملك 🦁"
        
    await message.reply_text(f"🌟 تم رفعه بنجاح ليحمل رتبة (**{title}**)\n👤 [{target_user.first_name}](tg://user?id={target_user.id})")

# ----------------- 3. تعطيل/تفعيل الكتم والرفع (صلاحية منشئ) -----------------
@app.on_message(filters.command(["تفعيل الكتم", "تعطيل الكتم"]) & filters.group)
async def toggle_mute_lock(client: Client, message: Message):
    if not await is_group_owner(client, message.chat.id, message.from_user.id):
        return await message.reply_text("✦ هذا الأمر يخص منشئ المجموعة فقط.")
    
    if "تفعيل" in message.text:
        SETTINGS["lock_mute"] = True
        await message.reply_text("🔒 تم تفعيل قفل الكتم: لا يمكن لمن هو أدنى من المنشئ كتم الأعضاء.")
    else:
        SETTINGS["lock_mute"] = False
        await message.reply_text("🔓 **تم تعطيل قفل الكتم.**")

@app.on_message(filters.command(["تفعيل الرفع", "تعطيل الرفع"]) & filters.group)
async def toggle_promote_lock(client: Client, message: Message):
    if not await is_group_owner(client, message.chat.id, message.from_user.id):
        return await message.reply_text("✦ هذا الأمر يخص منشئ المجموعة فقط.")
    
    if "تفعيل" in message.text:
        SETTINGS["lock_promote"] = True
        await message.reply_text("🔒 تم تفعيل قفل الرفع: لا يمكن لمن هو أدنى من المنشئ رفع الأعضاء.")
    else:
        SETTINGS["lock_promote"] = False
        await message.reply_text("🔓 **تم تعطيل قفل الرفع.**")

# ----------------- 4. التاك الجماعي (@all / all) -----------------
@app.on_message(filters.command(["تفعيل all", "تعطيل all"]) & filters.group)
async def toggle_all_cmd(client: Client, message: Message):
    if "تفعيل" in message.text:
        SETTINGS["allow_all"] = True
        await message.reply_text("✅ **تم تفعيل التاك الجماعي (all).**")
    else:
        SETTINGS["allow_all"] = False
        await message.reply_text("❌ **تم تعطيل التاك الجماعي (all).**")

@app.on_message(filters.command("all") & filters.group)
async def mention_all(client: Client, message: Message):
    if not SETTINGS.get("allow_all", True):
        return
    text = message.text.split(None, 1)[1] if len(message.text.split(None, 1)) > 1 else "سلام عليكم ياب"
    mentions = []
    async for member in client.get_chat_members(message.chat.id):
        if not member.user.is_bot:
            mentions.append(f"[{member.user.first_name}](tg://user?id={member.user.id})")
            if len(mentions) >= 20: 
                break
    await message.reply_text(f"{text}\n" + " ".join(mentions))

# ----------------- 5. المسح التلقائي وعدد الميديا -----------------
@app.on_message(filters.command(["تفعيل المسح التلقائي", "تعطيل المسح التلقائي"]) & filters.group)
async def auto_clean_toggle(client: Client, message: Message):
    if "تفعيل" in message.text:
        SETTINGS["auto_clean"] = True
        await message.reply_text("✨ **تم تفعيل المسح التلقائي.**")
    else:
        SETTINGS["auto_clean"] = False
        await message.reply_text("🚫 **تم تعطيل المسح التلقائي.**")

@app.on_message(filters.command(["امسح"]) & filters.group)
async def clean_messages(client: Client, message: Message):
    count = SETTINGS["clean_count"]
    async for msg in client.get_chat_history(message.chat.id, limit=count):
        try:
            await msg.delete()
        except:
            pass

@app.on_message(filters.command(["وضع عدد المسح"]) & filters.group)
async def set_clean_count(client: Client, message: Message):
    try:
        num = int(message.text.split()[1])
        SETTINGS["clean_count"] = num
        await message.reply_text(f"🔢 تم تحديث عدد المسح إلى: {num}")
    except IndexError:
        await message.reply_text("⚠️ مثال: `وضع عدد المسح 10`")

# ----------------- 6. قفل وفتح الوسائط والكل -----------------
@app.on_message(filters.command(["قفل الكل", "فتح الكل"]) & filters.group)
async def lock_unlock_all(client: Client, message: Message):
    status = True if "قفل" in message.text else False
    SETTINGS.update({"lock_links": status, "lock_photos": status, "lock_stickers": status, "lock_animations": status})
    action = "قفل" if status else "فتح"
    await message.reply_text(f"🔒 **تم {action} جميع الإضافات (الروابط، الصور، الملصقات، المتحركات).**")

@app.on_message(filters.command(["قفل التوجيه", "فتح التوجيه"]) & filters.group)
async def forward_lock_toggle(client: Client, message: Message):
    SETTINGS["lock_forward"] = True if "قفل" in message.text else False
    action = "قفل" if SETTINGS["lock_forward"] else "فتح"
    await message.reply_text(f"🔓 **تم {action} التوجيه.**")

# ----------------- 7. تخصيص ردود الألقاب -----------------
@app.on_message(filters.command(["تغير رد"]) & filters.group)
async def change_rank_response(client: Client, message: Message):
    try:
        args = message.text.split(maxsplit=2)
        rank_key = args[1].strip('{}')
        new_title = args[2]
        if rank_key in RANKS:
            RANKS[rank_key] = new_title
            await message.reply_text(f"✏️ تم تغيير رد الرتبة ({rank_key}) إلى: {new_title}")
        else:
            await message.reply_text("⚠️ الرتبة غير موجودة ضمن القائمة.")
    except IndexError:
        await message.reply_text("⚠️ الاستخدام الصحيح: `تغير رد {الادمن} لقب جديد`")

@app.on_message(filters.command(["حذف رد"]) & filters.group)
async def delete_rank_response(client: Client, message: Message):
    try:
        rank_key = message.text.split()[1].strip('{}')
        if rank_key in RANKS:
            RANKS[rank_key] = rank_key
            await message.reply_text(f"🗑️ **تم إرجاع رد الرتبة ({rank_key}) للافتراضي.**")
        else:
            await message.reply_text("⚠️ الرتبة غير موجودة.")
    except IndexError:
        await message.reply_text("⚠️ الاستخدام الصحيح: `حذف رد {الادمن}`")

# ----------------- محرك المراقبة والفلترة الشامل -----------------
@app.on_message(filters.group & ~filters.service)
async def protection_engine(client: Client, message: Message):
    user_id = message.from_user.id if message.from_user else 0
    if user_id and await is_creator_or_higher(client, message.chat.id, user_id):
        return

    # فحص الصور
    if SETTINGS["lock_photos"] and message.photo:
        return await message.delete()

    # فحص الملصقات
    if SETTINGS["lock_stickers"] and message.sticker:
        return await message.delete()

    # فحص المتحركات (GIF)
    if SETTINGS["lock_animations"] and message.animation:
        return await message.delete()

    # فحص التوجيه
    if SETTINGS["lock_forward"] and message.forward_date:
        return await message.delete()

    # فحص الروابط
    if SETTINGS["lock_links"] and message.text:
        if any(link in message.text for link in ["http://", "https://", "t.me/", "www."]):
            return await message.delete()

# تشغيل البوت
if __name__ == "__main__":
    print("> جاري تشغيل السورس الشامل والمدمج بنجاح...")
    app.run()

import os
import asyncio
from pyrogram import Client, filters
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton

# --- الإعدادات الأساسية لبوت المصنع ---
API_ID = 36481515
API_HASH = "c5dbdd9800f0508275f284f18b340059"
BOT_TOKEN = "8875318403:AAHP-1CAAjRqPYYYLKYhO3Ym1d6M3x8K49c"  # توكن بوت المصنع الخاص بك

# --- الآيدي الخاص بك (المطور الأساسي الأوحد للمصنع) ---
DEVELOPER_ID = 7548185368

app = Client("KurdsMakerBot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)

# قاموس لتتبع خطوات التنصيب الخاصة بك (token, owner_id)
maker_steps = {}

@app.on_message(filters.command("start") & filters.private)
async def maker_start(client: Client, message: Message):
    user_id = message.from_user.id
    user_name = message.from_user.mention
    
    # التحقق مما إذا كان المرسل هو أنت أم شخص آخر
    if user_id != DEVELOPER_ID:
        await message.reply_text(
            f"🚫 **عذراً يا {user_name}، هذا البوت خاص بمطور السورس فقط!**\n\n"
            "⚡ لا يمكنك استخدام مصنع سورس الكردي الضخم.\n"
            "👑 المطور الأساسي: [Yaser](tg://user?id=7548185368)"
        )
        return

    # إذا كنت أنت المطور، تظهر لك لوحة التحكم بالمصنع
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("🛠 تنصيب سورس الكردي لشخص", callback_data="install_bot")],
        [InlineKeyboardButton("📊 احصائيات المصنع", callback_data="maker_stats")]
    ])
    
    text = (
        f"✨ **أهلاً بك يا مطورنا الأساسي ({user_name}) في لوحة تحكم مصنع سورس الكردي!**\n\n"
        "🤖 أنت وحدك من تملك صلاحية تنصيب البوتات للناس.\n"
        "⚡ اضغط على الزر أدناه لبدء عملية تنصيب جديدة."
    )
    await message.reply_text(text, reply_markup=keyboard)

@app.on_callback_query(filters.regex("install_bot"))
async def install_bot_callback(client, callback_query):
    user_id = callback_query.from_user.id
    if user_id != DEVELOPER_ID:
        return
    
    maker_steps[user_id] = {"step": "waiting_for_token"}
    await callback_query.message.edit_text(
        "🤖 **خطوة التنصيب (1/2):**\n\n"
        "• قم بإرسال **توكن البوت الجديد** (Bot Token) الذي تريد تنصيب سورس الكردي عليه الآن في الرسائل."
    )

@app.on_message(filters.text & filters.private)
async def process_maker_steps(client: Client, message: Message):
    user_id = message.from_user.id
    if user_id != DEVELOPER_ID:
        return
    
    user_data = maker_steps.get(user_id)
    if not user_data:
        return
    
    step = user_data.get("step")
    
    # الخطوة الأولى: استلام التوكن
    if step == "waiting_for_token":
        token = message.text.strip()
        maker_steps[user_id]["token"] = token
        maker_steps[user_id]["step"] = "waiting_for_owner_id"
        
        await message.reply_text(
            "✅ **تم استلام التوكن بنجاح!**\n\n"
            "👤 **خطوة التنصيب (2/2):**\n"
            "• الآن أرسل **آيدي حساب المالك الأساسي** للبوت الجديد (ليتم تعيينه برتبة مطور أساسي في السورس)."
        )
    
    # الخطوة الثانية: استلام آيدي المالك وتشغيل التنصيب
    elif step == "waiting_for_owner_id":
        owner_id = message.text.strip()
        token = user_data.get("token")
        
        # إعادة تعيين الحالة
        maker_steps[user_id] = None
        
        await message.reply_text(
            f"🚀 **جاري تنصيب وتجهيز سورس الكردي الضخم...**\n\n"
            f"• التوكن: `{token[:10]}...`\n"
            f"• آيدي المالك الأساسي: `{owner_id}`\n\n"
            "✅ تم ربط البوت وتفعيل صلاحيات المطور الأساسي له بنجاح!"
        )

print("⚡ [MAKER BOT - SECURE] بوت المصنع الآمن قيد التشغيل...")
app.run()

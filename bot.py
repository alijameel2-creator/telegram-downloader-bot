import os
import asyncio
import sqlite3
from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from pyrogram.errors import UserNotParticipant
import yt_dlp

API_ID = 21685261
API_HASH = "b9f1c28529edd2b5c7590e3ed27baffa"
BOT_TOKEN = "8410578423:AAHNjWAfrXe_kLIho9wUaCv5bzSUjtiRAlE"
ADMIN_USERNAME = "ccf4t"

app = Client("downloader_bot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)

# إعداد قاعدة البيانات لحفظ قنوات الاشتراك الإجباري والإعدادات
db = sqlite3.connect("bot_database.db", check_same_thread=False)
cursor = db.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS settings (
    key TEXT PRIMARY KEY,
    value TEXT
)
""")
db.commit()

def get_setting(key, default=""):
    cursor.execute("SELECT value FROM settings WHERE key = ?", (key,))
    row = cursor.fetchone()
    return row[0] if row else default

def set_setting(key, value):
    cursor.execute("INSERT OR REPLACE INTO settings (key, value) VALUES (?, ?)", (key, value))
    db.commit()

user_links = {}

async def check_subscription(client, user_id, chat_username):
    if not chat_username:
        return True
    try:
        member = await client.get_chat_member(chat_username, user_id)
        if member.status in ["creator", "administrator", "member"]:
            return True
    except UserNotParticipant:
        return False
    except Exception:
        return True
    return False

@app.on_message(filters.command("start"))
async def start_command(client, message):
    user_id = message.from_user.id
    username = message.from_user.username
    
    forced_channel = get_setting("forced_channel", "")
    if forced_channel and not await check_subscription(client, user_id, forced_channel):
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("📢 اشترك في القناة أولاً", url=f"https://t.me/{forced_channel.replace('@', '')}")],
            [InlineKeyboardButton("🔄 تحقق من الاشتراك", callback_data="check_sub")]
        ])
        await message.reply_text(
            "⚠️ **عذراً عزيزي المستخدم!**\n\n"
            "استخدام هذا البوت يتطلب الاشتراك في القناة الرسمية أولاً. يرجى الاشتراك ثم اضغط تحقق 👇",
            reply_markup=keyboard
        )
        return

    welcome_text = (
        "✨ **مرحباً بك في بوت التحميل الشامل والمتطور!** 🎬🔥\n\n"
        "📥 أرسل لي أي رابط (يوتيوب، تيك توك، إنستغرام، فيسبوك...)\n"
        "وسأقوم بتحميله لك فوراً وبدون علامات مائية وبأعلى جودة!\n\n"
        "🛠 **ملاحظة:** تم برمجة وتطوير هذا البوت بصيانة شخصية بواسطة المطور.\n"
        "📢 للتواصل مع المطور أو الإعلان استخدم الأزرار أدناه 👇"
    )
    
    keyboard_buttons = [
        [
            InlineKeyboardButton("⚙️ إعدادات البوت", callback_data="bot_settings"),
            InlineKeyboardButton("👨‍💻 مطور البوت", url=f"https://t.me/{ADMIN_USERNAME}")
        ]
    ]
    
    if username == ADMIN_USERNAME:
        keyboard_buttons.append([InlineKeyboardButton("🛠 لوحة تحكم المشرف", callback_data="admin_panel")])

    await message.reply_text(welcome_text, reply_markup=InlineKeyboardMarkup(keyboard_buttons))

@app.on_callback_query(filters.regex("check_sub"))
async def check_sub_callback(client, callback_query: CallbackQuery):
    user_id = callback_query.from_user.id
    forced_channel = get_setting("forced_channel", "")
    if await check_subscription(client, user_id, forced_channel):
        await callback_query.message.edit_text("✅ **شكراً لاشتراكك!**\nالآن يمكنك إرسال أي رابط وسأقوم بتحميله لك فوراً 🚀")
    else:
        await callback_query.answer("❌ لم تقم بالاشتراك في القناة بعد!", show_alert=True)

@app.on_callback_query(filters.regex("bot_settings"))
async def settings_callback(client, callback_query: CallbackQuery):
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("🔙 عودة للقائمة الرئيسية", callback_data="back_home")]
    ])
    await callback_query.message.edit_text(
        "⚙️ **لوحة إعدادات البوت العامة:**\n\n"
        "• حالة السيرفر: يعمل بكفاءة تامة 24/7 ✅\n"
        "• جودة التحميل: فائقة وبدون علامات مائية 🎬\n"
        f"• المطور والصيانة: @{ADMIN_USERNAME}",
        reply_markup=keyboard
    )

@app.on_callback_query(filters.regex("admin_panel"))
async def admin_panel_callback(client, callback_query: CallbackQuery):
    if callback_query.from_user.username != ADMIN_USERNAME:
        await callback_query.answer("⚠️ هذه اللوحة مخصصة لمطور البوت فقط!", show_alert=True)
        return

    current_channel = get_setting("forced_channel", "غير متوفرة")
    audio_mode = get_setting("audio_mode", "audio")
    mode_text = "رسالة صوتية (Voice) 🎤" if audio_mode == "voice" else "ملف صوتي عادي 🎵"

    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton(f"📢 قناة الاشتراك: {current_channel}", callback_data="none")],
        [InlineKeyboardButton(f"🎵 وضع الصوت: {mode_text}", callback_data="toggle_audio_mode")],
        [InlineKeyboardButton("➕ تعيين قناة اشتراك إجباري جديدة", callback_data="set_channel_prompt")],
        [InlineKeyboardButton("🔙 عودة للرئيسية", callback_data="back_home")]
    ])
    await callback_query.message.edit_text(
        "🛠 **لوحة تحكم المشرف الخاصة:**\n\n"
        "من هنا يمكنك التحكم بإعدادات البوت، القنوات، وخصائص التحميل مباشرة.",
        reply_markup=keyboard
    )

@app.on_callback_query(filters.regex("toggle_audio_mode"))
async def toggle_audio_mode(client, callback_query: CallbackQuery):
    if callback_query.from_user.username != ADMIN_USERNAME:
        return
    current_mode = get_setting("audio_mode", "audio")
    new_mode = "voice" if current_mode == "audio" else "audio"
    set_setting("audio_mode", new_mode)
    
    await callback_query.answer(f"تم تغيير وضع إرسال الصوت إلى: {new_mode}", show_alert=True)
    await admin_panel_callback(client, callback_query)

@app.on_callback_query(filters.regex("set_channel_prompt"))
async def set_channel_prompt(client, callback_query: CallbackQuery):
    if callback_query.from_user.username != ADMIN_USERNAME:
        return
    await callback_query.message.edit_text(
        "✍️ **تعيين قناة اشتراك إجباري:**\n\n"
        "أرسل الآن معرف القناة بالشكل التالي كمثل:\n"
        "`/setchannel @YourChannelName`\n\n"
        "أو أرسل `/setchannel none` لإلغاء الاشتراك الإجباري تماماً.",
        reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 عودة لوحة التحكم", callback_data="admin_panel")]])
    )

@app.on_message(filters.command("setchannel") & filters.text)
async def set_channel_command(client, message):
    if message.from_user.username != ADMIN_USERNAME:
        await message.reply_text("⚠️ هذا الأمر مخصص للمطور فقط!")
        return
    
    parts = message.text.split(maxsplit=1)
    if len(parts) < 2:
        await message.reply_text("❌ يرجى كتابة المعرف مع الأمر، مثال:\n`/setchannel @ChannelName`")
        return
    
    new_channel = parts[1].strip()
    if new_channel.lower() == "none":
        set_setting("forced_channel", "")
        await message.reply_text("✅ تم إلغاء الاشتراك الإجباري بنجاح!")
    else:
        set_setting("forced_channel", new_channel)
        await message.reply_text(f"✅ تم تعيين قناة الاشتراك الإجباري بنجاح إلى: `{new_channel}`")

@app.on_callback_query(filters.regex("back_home"))
async def home_callback(client, callback_query: CallbackQuery):
    user_id = callback_query.from_user.id
    username = callback_query.from_user.username
    
    keyboard_buttons = [
        [
            InlineKeyboardButton("⚙️ إعدادات البوت", callback_data="bot_settings"),
            InlineKeyboardButton("👨‍💻 مطور البوت", url=f"https://t.me/{ADMIN_USERNAME}")
        ]
    ]
    if username == ADMIN_USERNAME:
        keyboard_buttons.append([InlineKeyboardButton("🛠 لوحة تحكم المشرف", callback_data="admin_panel")])

    await callback_query.message.edit_text(
        "✨ **مرحباً بك مجدداً في القائمة الرئيسية!**\n\n"
        "أرسل لي رابط الفيديو الذي ترغب بتحميله الآن 🚀",
        reply_markup=InlineKeyboardMarkup(keyboard_buttons)
    )

@app.on_message(filters.text & ~filters.command(["start", "setchannel"]))
async def get_link(client, message):
    user_id = message.from_user.id
    
    forced_channel = get_setting("forced_channel", "")
    if forced_channel and not await check_subscription(client, user_id, forced_channel):
        await message.reply_text("⚠️ يرجى الاشتراك في قناة البوت أولاً لاستخدام هذه الميزة!")
        return

    url = message.text.strip()
    if not url.startswith("http"):
        await message.reply_text("❌ يرجى إرسال رابط صالح يبدأ بـ http أو https")
        return

    user_links[user_id] = url

    keyboard = InlineKeyboardMarkup([
        [
            InlineKeyboardButton("📥 تحميل فيديو", callback_data="download_video"),
            InlineKeyboardButton("🎵 تحميل صوت", callback_data="download_audio")
        ],
        [
            InlineKeyboardButton("📝 جلب العنوان والوصف", callback_data="get_caption")
        ]
    ])

    await message.reply_text(
        "🎯 **تم استلام الرابط بنجاح!**\nاختر ما ترغب باستخراجه من الرابط أدناه:",
        reply_markup=keyboard
    )

@app.on_callback_query()
async def handle_buttons(client, callback_query: CallbackQuery):
    user_id = callback_query.from_user.id
    action = callback_query.data
    
    if action in ["check_sub", "bot_settings", "admin_panel", "toggle_audio_mode", "set_channel_prompt", "back_home", "none"]:
        return

    if user_id not in user_links:
        await callback_query.answer("⚠️ انتهت صلاحية الرابط، يرجى إرساله مرة أخرى.", show_alert=True)
        return

    url = user_links[user_id]
    await callback_query.answer()

    if action == "get_caption":
        status_msg = await callback_query.message.edit_text("⏳ جاري استخراج العنوان والوصف...")
        try:
            def fetch_info():
                with yt_dlp.YoutubeDL({'extract_flat': True}) as ydl:
                    return ydl.extract_info(url, download=False)
            
            info = await asyncio.to_thread(fetch_info)
            title = info.get('title', 'غير متوفر')
            description = info.get('description', 'لا يوجد وصف')
            
            text_result = f"📌 **العنوان:**\n`{title}`\n\n📝 **الوصف:**\n{description[:1000]}"
            await callback_query.message.edit_text(text_result)
        except Exception as e:
            await callback_query.message.edit_text(f"❌ حدث خطأ أثناء استخراج المعلومات:\n`{str(e)}`")
        return

    status_msg = await callback_query.message.edit_text("⏳ جاري المعالجة والتحميل، يرجى الانتظار قليلاً...")

    os.makedirs("downloads", exist_ok=True)

    if action == "download_video":
        ydl_opts = {
            'format': 'best',
            'outtmpl': 'downloads/%(id)s.%(ext)s',
            'restrictfilenames': True,
        }
    elif action == "download_audio":
        ydl_opts = {
            'format': 'bestaudio/best',
            'outtmpl': 'downloads/%(id)s.%(ext)s',
            'restrictfilenames': True,
        }

    try:
        def download():
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=True)
                return ydl.prepare_filename(info)

        file_path = await asyncio.to_thread(download)

        if action == "download_video":
            await status_msg.edit_text("📤 جاري إرسال الفيديو إليك...")
            await client.send_video(chat_id=user_id, video=file_path, caption=f"✨ تم التحميل بواسطة مطور البوت: @{ADMIN_USERNAME}")
        elif action == "download_audio":
            audio_mode = get_setting("audio_mode", "audio")
            if audio_mode == "voice":
                await status_msg.edit_text("📤 جاري إرسال الرسالة الصوتية إليك...")
                await client.send_voice(chat_id=user_id, voice=file_path, caption=f"🎵 تم إرسال الصوت بواسطة المطور: @{ADMIN_USERNAME}")
            else:
                await status_msg.edit_text("📤 جاري إرسال الملف الصوتي إليك...")
                await client.send_audio(chat_id=user_id, audio=file_path, caption=f"🎵 تم إرسال الصوت بواسطة المطور: @{ADMIN_USERNAME}")

        if os.path.exists(file_path):
            os.remove(file_path)
            
        await status_msg.delete()

    except Exception as e:
        await status_msg.edit_text(f"❌ حدث خطأ أثناء التحميل:\n`{str(e)}`")

print("🤖 Bot is running smoothly without ffmpeg dependency...")
app.run()

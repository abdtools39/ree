import openai
import telebot
from datetime import datetime, timedelta
from instagrapi import Client
from scheduler import Scheduler
from instagram_manager import InstagramManager

openai.api_key = "YOUR_OPENAI_API_KEY"  # استبدله بمفتاحك من OpenAI

# إعدادات البوت
TOKEN = "YOUR_BOT_TOKEN"
bot = telebot.TeleBot(TOKEN)

user_states = {}
temp_data = {}

# إضافة حسابات انستقرام
class InstagramSessionManager:
    @staticmethod
    def get_saved_accounts():
        return ["account1", "account2"]  # هنا تقدر تضيف الحسابات المحفوظة

    @staticmethod
    def load_session(username):
        # تحميل الجلسة باستخدام instagrapi
        manager = InstagramManager()
        manager.load_session()
        return manager.get_client()

# الردود على الأوامر الأساسية
@bot.message_handler(commands=['start'])
def start(message):
    chat_id = message.chat.id
    bot.send_message(chat_id, "مرحبا! أنا البوت المسؤول عن نشر الميمز.")
    markup = telebot.types.InlineKeyboardMarkup()
    markup.add(telebot.types.InlineKeyboardButton("⏰ جدولة نشر", callback_data='schedule_post'))
    bot.send_message(chat_id, "اختر أحد الخيارات:", reply_markup=markup)

# التعامل مع جدولة النشر
@bot.callback_query_handler(func=lambda call: True)
def callback_query(call):
    chat_id = call.message.chat.id
    if call.data == 'schedule_post':
        temp_data[chat_id] = {'schedule': True}
        markup = telebot.types.InlineKeyboardMarkup()
        markup.add(
            telebot.types.InlineKeyboardButton("📸 بوست", callback_data='s_post'),
            telebot.types.InlineKeyboardButton("📖 ستوري", callback_data='s_story'),
            telebot.types.InlineKeyboardButton("🎥 ريلز", callback_data='s_reel')
        )
        bot.send_message(chat_id, "اختر نوع المحتوى المجدول:", reply_markup=markup)

    elif call.data.startswith('s_'):
        kind = call.data[2:]
        temp_data[chat_id] = {'type': kind, 'schedule': True}
        accounts = InstagramSessionManager.get_saved_accounts()
        markup = telebot.types.InlineKeyboardMarkup()
        for acc in accounts:
            markup.add(telebot.types.InlineKeyboardButton(acc, callback_data=f'sched_account:{acc}'))
        bot.send_message(chat_id, "اختار الحساب اللي تريد تنشر منه:", reply_markup=markup)

    elif call.data.startswith("sched_account:"):
        username = call.data.split(":")[1]
        temp_data[chat_id]['account'] = username
        bot.send_message(chat_id, "زين، أرسللي الصورة أو الفيديو:")
        user_states[chat_id] = 'waiting_for_sched_media'

# التعامل مع الميديا والكابشن
@bot.message_handler(content_types=['photo', 'video'])
def handle_media(msg):
    chat_id = msg.chat.id
    if user_states.get(chat_id) != 'waiting_for_sched_media':
        return

    file_info = bot.get_file(msg.photo[-1].file_id if msg.photo else msg.video.file_id)
    downloaded_file = bot.download_file(file_info.file_path)
    file_path = f"media/{chat_id}_{file_info.file_unique_id}.jpg" if msg.photo else f"media/{chat_id}_{file_info.file_unique_id}.mp4"
    
    with open(file_path, 'wb') as f:
        f.write(downloaded_file)

    temp_data[chat_id]['file_path'] = file_path
    user_states[chat_id] = 'waiting_for_sched_caption'

    # توليد الكابشن باستخدام GPT
    generated_caption = Scheduler.generate_caption("post", "Funny meme video")  # يمكن تغيير "Funny meme video" إلى وصف الميديا
    temp_data[chat_id]['caption'] = generated_caption

    bot.send_message(chat_id, f"تم توليد الكابشن تلقائيًا: \n{generated_caption}\nإذا حبيت تعدل، اكتب الكابشن الجديد أو اكتب - لتجاهل.")
    bot.send_message(chat_id, "متى تريد تنشره؟\nاكتب الوقت بهالشكل: `YYYY-MM-DD HH:MM`\nمثال: `2025-04-15 18:30`", parse_mode="Markdown")

    user_states[chat_id] = 'waiting_for_sched_time'

# التعامل مع وقت الجدولة
@bot.message_handler(func=lambda msg: user_states.get(msg.chat.id) == 'waiting_for_sched_time')
def handle_sched_time(msg):
    chat_id = msg.chat.id
    try:
        dt = datetime.strptime(msg.text.strip(), '%Y-%m-%d %H:%M')
        temp_data[chat_id]['timestamp'] = dt.timestamp()

        data = temp_data[chat_id]
        Scheduler.add_post({
            "chat_id": chat_id,
            "username": data['account'],
            "file_path": data['file_path'],
            "caption": data['caption'],
            "timestamp": data['timestamp'],
            "type": data['type']
        })
        bot.send_message(chat_id, f"✅ تم جدولة النشر ليوم {dt.strftime('%Y-%m-%d %H:%M')}")
    except ValueError:
        bot.send_message(chat_id, "❌ تنسيق التاريخ غلط، جرب من جديد.")

    user_states.pop(chat_id, None)
    temp_data.pop(chat_id, None)

# تشغيل البوت
Scheduler.set_bot(bot)
Scheduler.load()
Scheduler.start(InstagramSessionManager.load_session)
bot.polling(non_stop=True)

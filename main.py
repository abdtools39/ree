import os
import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
from instagram_manager import InstagramSessionManager

API_TOKEN = 'YOUR_BOT_TOKEN_HERE'  # حط التوكن هنا
bot = telebot.TeleBot(API_TOKEN)

user_states = {}
temp_data = {}

@bot.message_handler(commands=['start'])
def start_handler(message):
    markup = InlineKeyboardMarkup()
    markup.add(InlineKeyboardButton("➕ إضافة حساب إنستقرام", callback_data='add_account'))
    markup.add(InlineKeyboardButton("📂 حساباتي", callback_data='show_accounts'))
    bot.send_message(message.chat.id, "أهلًا بيك في بوت إدارة الإنستقرام 👋\nاختر أحد الخيارات:", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: True)
def callback_handler(call):
    chat_id = call.message.chat.id
    if call.data == 'add_account':
        bot.send_message(chat_id, "أرسل الآن اسم المستخدم (username) لحسابك على إنستقرام:")
        user_states[chat_id] = 'waiting_for_username'
    elif call.data == 'show_accounts':
        accounts = InstagramSessionManager.get_saved_accounts()
        if accounts:
            accounts_text = "\n".join(f"• {acc}" for acc in accounts)
            bot.send_message(chat_id, f"الحسابات المحفوظة:\n{accounts_text}")
        else:
            bot.send_message(chat_id, "لا يوجد حسابات محفوظة بعد.")

@bot.message_handler(func=lambda msg: user_states.get(msg.chat.id) == 'waiting_for_username')
def get_username(msg):
    temp_data[msg.chat.id] = {'username': msg.text}
    user_states[msg.chat.id] = 'waiting_for_password'
    bot.send_message(msg.chat.id, "تمام، الحين أرسل كلمة المرور الخاصة بالحساب:")

@bot.message_handler(func=lambda msg: user_states.get(msg.chat.id) == 'waiting_for_password')
def get_password(msg):
    username = temp_data[msg.chat.id]['username']
    password = msg.text
    bot.send_message(msg.chat.id, f"جاري تسجيل الدخول لحساب {username}...")

    success = InstagramSessionManager.login_and_store_session(username, password)
    if success:
        bot.send_message(msg.chat.id, f"✅ تم تسجيل الدخول وتخزين الجلسة بنجاح لحساب {username}!")
    else:
        bot.send_message(msg.chat.id, "❌ فشل تسجيل الدخول. تأكد من المعلومات.")

    # Reset state
    user_states.pop(msg.chat.id, None)
    temp_data.pop(msg.chat.id, None)

bot.infinity_polling()

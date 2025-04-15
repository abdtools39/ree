import openai
import json
import threading
import time
import os
from datetime import datetime
from instagrapi.exceptions import LoginRequired

openai.api_key = "YOUR_OPENAI_API_KEY"  # استبدله بمفتاحك من OpenAI

class Scheduler:
    FILE = 'data/schedule.json'
    scheduled_posts = []
    bot = None

    @classmethod
    def set_bot(cls, bot_instance):
        cls.bot = bot_instance

    @classmethod
    def load(cls):
        if os.path.exists(cls.FILE):
            with open(cls.FILE, 'r') as f:
                cls.scheduled_posts = json.load(f)

    @classmethod
    def save(cls):
        with open(cls.FILE, 'w') as f:
            json.dump(cls.scheduled_posts, f, indent=2)

    @classmethod
    def add_post(cls, data):
        cls.scheduled_posts.append(data)
        cls.save()

    @classmethod
    def generate_caption(cls, media_type, description):
        try:
            prompt = f"Generate a catchy {media_type} caption for this: {description}"
            response = openai.Completion.create(
                engine="text-davinci-003",  # يمكنك استخدام أي موديل من OpenAI
                prompt=prompt,
                max_tokens=100
            )
            caption = response.choices[0].text.strip()
            return caption
        except Exception as e:
            print(f"Error generating caption: {e}")
            return "No caption generated."

    @classmethod
    def start(cls, instagrapi_loader):
        def worker():
            while True:
                now = datetime.now().timestamp()
                for post in cls.scheduled_posts[:]:
                    if post["timestamp"] <= now:
                        try:
                            cl = instagrapi_loader(post['username'])
                            if not cl:
                                continue
                            if post['type'] == 'post':
                                cl.photo_upload(post['file_path'], post['caption'] or "")
                            elif post['type'] == 'story':
                                cl.photo_upload_to_story(post['file_path'])
                            elif post['type'] == 'reel':
                                cl.video_upload(post['file_path'], post['caption'] or "")
                            if cls.bot:
                                cls.bot.send_message(post['chat_id'], f"✅ تم نشر {post['type']} تلقائيًا على @{post['username']}")
                        except LoginRequired:
                            cls.bot.send_message(post['chat_id'], f"⚠️ جلسة @{post['username']} غير صالحة. يرجى تسجيل الدخول من جديد.")
                        except Exception as e:
                            cls.bot.send_message(post['chat_id'], f"❌ فشل نشر المنشور المجدول: {e}")
                        cls.scheduled_posts.remove(post)
                        cls.save()
                time.sleep(10)
        threading.Thread(target=worker, daemon=True).start()

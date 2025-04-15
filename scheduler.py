import json
import threading
import time
import os
from datetime import datetime
from instagrapi.exceptions import LoginRequired

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

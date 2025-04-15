from instagrapi import Client
import json
import os

class InstagramManager:
    def __init__(self):
        self.client = None
        self.session_file = "insta_sessions.json"

    def login(self, username, password):
        self.client = Client()
        self.client.login(username, password)
        self.save_session()

    def save_session(self):
        if self.client is None:
            raise Exception("لا يمكن حفظ الجلسة لأنك لم تقم بتسجيل الدخول.")
        session_data = self.client.get_settings()
        with open(self.session_file, "w") as f:
            json.dump(session_data, f)

    def load_session(self):
        if os.path.exists(self.session_file):
            with open(self.session_file, "r") as f:
                session_data = json.load(f)
            self.client = Client()
            self.client.load_settings(session_data)
        else:
            raise Exception("لم يتم العثور على ملف الجلسة.")

    def get_client(self):
        if self.client is None:
            raise Exception("لم يتم تسجيل الدخول بعد.")
        return self.client

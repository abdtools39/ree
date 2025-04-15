import os
from instagrapi import Client

SESSION_DIR = "sessions"
os.makedirs(SESSION_DIR, exist_ok=True)

class InstagramSessionManager:

    @staticmethod
    def get_session_path(username):
        return os.path.join(SESSION_DIR, f"{username}.session")

    @staticmethod
    def login_and_store_session(username, password):
        try:
            cl = Client()
            cl.login(username, password)
            cl.dump_settings(InstagramSessionManager.get_session_path(username))
            return True
        except Exception as e:
            print(f"[Login Error] {e}")
            return False

    @staticmethod
    def load_session(username):
        cl = Client()
        session_path = InstagramSessionManager.get_session_path(username)
        if os.path.exists(session_path):
            cl.load_settings(session_path)
            cl.get_timeline_feed()  # Trigger session validation
            return cl
        return None

    @staticmethod
    def get_saved_accounts():
        return [f.split(".")[0] for f in os.listdir(SESSION_DIR) if f.endswith(".session")]

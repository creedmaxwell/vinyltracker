import base64, os
import sqlite3
from threading import Lock
import json
from datetime import datetime

DB_PATH = "sessions.db"

class SessionStore:
    def __init__(self):
        self._init_db()
        self.lock = Lock()
    
    def _init_db(self):
        """Initialize the database schema"""
        with sqlite3.connect(DB_PATH) as conn:
            conn.execute('''
                CREATE TABLE IF NOT EXISTS sessions (
                    session_id TEXT PRIMARY KEY,
                    data TEXT NOT NULL
                )
            ''')
            conn.commit()
    
    def _get_connection(self):
        """Create a new connection for each operation"""
        return sqlite3.connect(DB_PATH)
    
    def generate_session_id(self):
        rnum = os.urandom(32)
        return base64.b64encode(rnum).decode('utf-8')
    
    def create_session(self):
        session_id = self.generate_session_id()
        empty_data = json.dumps({"history": []})
        with self.lock:
            with self._get_connection() as conn:
                conn.execute(
                    'INSERT INTO sessions (session_id, data) VALUES (?, ?)',
                    (session_id, empty_data)
                )
                conn.commit()
        return session_id
    
    def get_session_data(self, session_id):
        """Return parsed session data (dict) or None."""
        with self.lock:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('SELECT data FROM sessions WHERE session_id = ?', (session_id,))
                result = cursor.fetchone()
                if not result:
                    return None
                try:
                    return json.loads(result[0])
                except Exception:
                    return None
    
    def save_session_data(self, session_id, data):
        """Replace session data (data should be JSON-serializable)."""
        json_data = json.dumps(data)
        with self.lock:
            with self._get_connection() as conn:
                conn.execute(
                    'INSERT OR REPLACE INTO sessions (session_id, data) VALUES (?, ?)',
                    (session_id, json_data)
                )
                conn.commit()

    # Convenience helpers for conversation history:
    def append_message(self, session_id, role, content):
        """
        role: "user" or "assistant" or "system"
        content: string
        """
        now = datetime.utcnow().isoformat() + "Z"
        session = self.get_session_data(session_id)
        if session is None:
            # create a session if missing
            session = {"history": []}
        history = session.get("history", [])
        history.append({"role": role, "content": content, "timestamp": now})
        # optional: keep history capped here (e.g., last 20 messages)
        MAX = 40
        if len(history) > MAX:
            history = history[-MAX:]
        session["history"] = history
        self.save_session_data(session_id, session)
        return session
    
    def get_history(self, session_id, limit: int = 20):
        """Return the last `limit` history entries as a list of dicts (ordered oldest -> newest)."""
        session = self.get_session_data(session_id)
        if not session:
            return []
        history = session.get("history", [])
        return history[-limit:]
    
    def clear_history(self, session_id):
        session = self.get_session_data(session_id) or {}
        session["history"] = []
        self.save_session_data(session_id, session)
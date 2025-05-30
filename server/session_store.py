import base64, os
import sqlite3
from threading import Lock
import json

class SessionStore:
    def __init__(self):
        self._init_db()
        self.lock = Lock()
    
    def _init_db(self):
        """Initialize the database schema"""
        with sqlite3.connect('sessions.db') as conn:
            conn.execute('''
                CREATE TABLE IF NOT EXISTS sessions (
                    session_id TEXT PRIMARY KEY,
                    data TEXT NOT NULL
                )
            ''')
            conn.commit()
    
    def _get_connection(self):
        """Create a new connection for each operation"""
        return sqlite3.connect('sessions.db')
    
    def generate_session_id(self):
        rnum = os.urandom(32)
        return base64.b64encode(rnum).decode('utf-8')
    
    def create_session(self):
        session_id = self.generate_session_id()
        with self.lock:
            with self._get_connection() as conn:
                conn.execute(
                    'INSERT INTO sessions (session_id, data) VALUES (?, ?)',
                    (session_id, '{}')
                )
                conn.commit()
        return session_id
    
    def get_session_data(self, session_id):
        with self.lock:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('SELECT data FROM sessions WHERE session_id = ?', (session_id,))
                result = cursor.fetchone()
                return eval(result[0]) if result else None
    
    def save_session_data(self, session_id, data):
        with self.lock:
            with self._get_connection() as conn:
                conn.execute(
                    'INSERT OR REPLACE INTO sessions (session_id, data) VALUES (?, ?)',
                    (session_id, str(data))
                )
                conn.commit()
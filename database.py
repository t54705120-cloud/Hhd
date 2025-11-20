import sqlite3
from datetime import datetime, timedelta


class Database:
    def __init__(self):
        self.conn = sqlite3.connect("bot.db", check_same_thread=False)
        self.cursor = self.conn.cursor()
        self.create_tables()

    def create_tables(self):
        self.cursor.execute(
            """CREATE TABLE IF NOT EXISTS banned (
                chat_id INTEGER,
                user_id INTEGER
            )"""
        )

        self.cursor.execute(
            """CREATE TABLE IF NOT EXISTS muted (
                chat_id INTEGER,
                user_id INTEGER,
                until TEXT
            )"""
        )

        self.cursor.execute(
            """CREATE TABLE IF NOT EXISTS restricted (
                chat_id INTEGER,
                user_id INTEGER
            )"""
        )

        self.cursor.execute(
            """CREATE TABLE IF NOT EXISTS owners (
                chat_id INTEGER,
                user_id INTEGER
            )"""
        )

        self.cursor.execute(
            """CREATE TABLE IF NOT EXISTS admins (
                chat_id INTEGER,
                user_id INTEGER
            )"""
        )

        self.cursor.execute(
            """CREATE TABLE IF NOT EXISTS vip (
                chat_id INTEGER,
                user_id INTEGER
            )"""
        )

        self.cursor.execute(
            """CREATE TABLE IF NOT EXISTS messages (
                chat_id INTEGER,
                user_id INTEGER,
                count INTEGER DEFAULT 0
            )"""
        )

        self.cursor.execute(
            """CREATE TABLE IF NOT EXISTS warnings (
                chat_id INTEGER,
                user_id INTEGER,
                count INTEGER DEFAULT 0
            )"""
        )

        self.cursor.execute(
            """CREATE TABLE IF NOT EXISTS custom_replies (
                chat_id INTEGER,
                keyword TEXT,
                type TEXT,
                content TEXT,
                file_id TEXT,
                caption TEXT
            )"""
        )

        self.cursor.execute(
            """CREATE TABLE IF NOT EXISTS global_replies (
                keyword TEXT,
                type TEXT,
                content TEXT,
                file_id TEXT,
                caption TEXT
            )"""
        )

        self.cursor.execute(
            """CREATE TABLE IF NOT EXISTS welcome_status (
                chat_id INTEGER,
                enabled INTEGER DEFAULT 0
            )"""
        )

        self.cursor.execute(
            """CREATE TABLE IF NOT EXISTS group_lock (
                chat_id INTEGER,
                locked INTEGER DEFAULT 0
            )"""
        )

        self.cursor.execute(
            """CREATE TABLE IF NOT EXISTS bot_status (
                chat_id INTEGER,
                enabled INTEGER DEFAULT 1
            )"""
        )

        self.cursor.execute(
            """CREATE TABLE IF NOT EXISTS spam_history (
                chat_id INTEGER,
                user_id INTEGER,
                message_text TEXT,
                timestamp TEXT
            )"""
        )

        self.cursor.execute(
            """CREATE TABLE IF NOT EXISTS stats (
                key TEXT PRIMARY KEY,
                value INTEGER DEFAULT 0
            )"""
        )

        self.conn.commit()

    # ------------------------
    # Basic Check Functions
    # ------------------------

    def is_owner(self, chat_id, user_id):
        return self._exists("owners", chat_id, user_id)

    def is_admin(self, chat_id, user_id):
        return self._exists("admins", chat_id, user_id)

    def is_vip(self, chat_id, user_id):
        return self._exists("vip", chat_id, user_id)

    # ------------------------
    # Ban / Mute / Restrict
    # ------------------------

    def add_banned(self, chat_id, user_id):
        self._insert_unique("banned", chat_id, user_id)

    def remove_banned(self, chat_id, user_id):
        self._remove("banned", chat_id, user_id)

    def add_muted(self, chat_id, user_id, until=None):
        self.cursor.execute(
            "DELETE FROM muted WHERE chat_id=? AND user_id=?", (chat_id, user_id)
        )
        self.cursor.execute(
            "INSERT INTO muted (chat_id, user_id, until) VALUES (?, ?, ?)",
            (chat_id, user_id, until),
        )
        self.conn.commit()

    def remove_muted(self, chat_id, user_id):
        self._remove("muted", chat_id, user_id)

    def add_restricted(self, chat_id, user_id):
        self._insert_unique("restricted", chat_id, user_id)

    def remove_restricted(self, chat_id, user_id):
        self._remove("restricted", chat_id, user_id)

    # ------------------------
    # Ranks
    # ------------------------

    def add_owner(self, chat_id, user_id):
        self._insert_unique("owners", chat_id, user_id)

    def add_admin(self, chat_id, user_id):
        self._insert_unique("admins", chat_id, user_id)

    def add_vip(self, chat_id, user_id):
        self._insert_unique("vip", chat_id, user_id)

    def remove_all_ranks(self, chat_id, user_id):
        for table in ("owners", "admins", "vip"):
            self.cursor.execute(
                f"DELETE FROM {table} WHERE chat_id=? AND user_id=?", (chat_id, user_id)
            )
        self.conn.commit()

    # ------------------------
    # Messages Counter
    # ------------------------

    def increment_message_count(self, chat_id, user_id):
        if not self._exists("messages", chat_id, user_id):
            self.cursor.execute(
                "INSERT INTO messages (chat_id, user_id, count) VALUES (?, ?, 1)",
                (chat_id, user_id),
            )
        else:
            self.cursor.execute(
                "UPDATE messages SET count = count + 1 WHERE chat_id=? AND user_id=?",
                (chat_id, user_id),
            )
        self.conn.commit()

    def get_message_count(self, chat_id, user_id):
        self.cursor.execute(
            "SELECT count FROM messages WHERE chat_id=? AND user_id=?",
            (chat_id, user_id),
        )
        row = self.cursor.fetchone()
        return row[0] if row else 0

    def get_top_users(self, chat_id, limit=20):
        self.cursor.execute(
            "SELECT user_id, count FROM messages WHERE chat_id=? ORDER BY count DESC LIMIT ?",
            (chat_id, limit),
        )
        return self.cursor.fetchall()

    # ------------------------
    # Warnings
    # ------------------------

    def add_warning(self, chat_id, user_id):
        if not self._exists("warnings", chat_id, user_id):
            self.cursor.execute(
                "INSERT INTO warnings (chat_id, user_id, count) VALUES (?, ?, 1)",
                (chat_id, user_id),
            )
        else:
            self.cursor.execute(
                "UPDATE warnings SET count = count + 1 WHERE chat_id=? AND user_id=?",
                (chat_id, user_id),
            )
        self.conn.commit()

        return self.get_warnings(chat_id, user_id)

    def get_warnings(self, chat_id, user_id):
        self.cursor.execute(
            "SELECT count FROM warnings WHERE chat_id=? AND user_id=?",
            (chat_id, user_id),
        )
        row = self.cursor.fetchone()
        return row[0] if row else 0

    def reset_warnings(self, chat_id, user_id):
        self.cursor.execute(
            "UPDATE warnings SET count = 0 WHERE chat_id=? AND user_id=?",
            (chat_id, user_id),
        )
        self.conn.commit()

    # ------------------------
    # Custom Replies
    # ------------------------

    def add_custom_reply(self, chat_id, keyword, data):
        self.cursor.execute(
            "DELETE FROM custom_replies WHERE chat_id=? AND keyword=?",
            (chat_id, keyword),
        )
        self.cursor.execute(
            """INSERT INTO custom_replies
               (chat_id, keyword, type, content, file_id, caption)
               VALUES (?, ?, ?, ?, ?, ?)""",
            (
                chat_id,
                keyword,
                data.get("type"),
                data.get("content"),
                data.get("file_id"),
                data.get("caption"),
            ),
        )
        self.conn.commit()

    def get_custom_reply(self, chat_id, keyword):
        self.cursor.execute(
            "SELECT type, content, file_id, caption FROM custom_replies WHERE chat_id=? AND keyword=?",
            (chat_id, keyword),
        )
        row = self.cursor.fetchone()
        if not row:
            return None

        return {
            "type": row[0],
            "content": row[1],
            "file_id": row[2],
            "caption": row[3],
        }

    # ------------------------
    # Global Replies
    # ------------------------

    def add_global_reply(self, keyword, data):
        self.cursor.execute("DELETE FROM global_replies WHERE keyword=?", (keyword,))
        self.cursor.execute(
            """INSERT INTO global_replies
                (keyword, type, content, file_id, caption)
                VALUES (?, ?, ?, ?, ?)""",
            (
                keyword,
                data.get("type"),
                data.get("content"),
                data.get("file_id"),
                data.get("caption"),
            ),
        )
        self.conn.commit()

    def get_global_reply(self, keyword):
        self.cursor.execute(
            "SELECT type, content, file_id, caption FROM global_replies WHERE keyword=?",
            (keyword,),
        )
        row = self.cursor.fetchone()
        if not row:
            return None

        return {
            "type": row[0],
            "content": row[1],
            "file_id": row[2],
            "caption": row[3],
        }

    # ------------------------
    # Welcome System
    # ------------------------

    def set_welcome_status(self, chat_id, enabled):
        self.cursor.execute(
            "DELETE FROM welcome_status WHERE chat_id=?", (chat_id,)
        )
        self.cursor.execute(
            "INSERT INTO welcome_status(chat_id, enabled) VALUES (?, ?)",
            (chat_id, 1 if enabled else 0),
        )
        self.conn.commit()

    def is_welcome_enabled(self, chat_id):
        self.cursor.execute(
            "SELECT enabled FROM welcome_status WHERE chat_id=?", (chat_id,)
        )
        row = self.cursor.fetchone()
        return row and row[0] == 1

    # ------------------------
    # Group Lock
    # ------------------------

    def set_group_lock(self, chat_id, locked):
        self.cursor.execute(
            "DELETE FROM group_lock WHERE chat_id=?", (chat_id,)
        )
        self.cursor.execute(
            "INSERT INTO group_lock(chat_id, locked) VALUES (?, ?)",
            (chat_id, 1 if locked else 0),
        )
        self.conn.commit()

    def is_group_locked(self, chat_id):
        self.cursor.execute(
            "SELECT locked FROM group_lock WHERE chat_id=?", (chat_id,)
        )
        row = self.cursor.fetchone()
        return row and row[0] == 1

    # ------------------------
    # Bot Status
    # ------------------------

    def set_bot_status(self, chat_id, enabled):
        self.cursor.execute("DELETE FROM bot_status WHERE chat_id=?", (chat_id,))
        self.cursor.execute(
            "INSERT INTO bot_status(chat_id, enabled) VALUES (?, ?)",
            (chat_id, 1 if enabled else 0),
        )
        self.conn.commit()

    def is_bot_enabled(self, chat_id):
        self.cursor.execute(
            "SELECT enabled FROM bot_status WHERE chat_id=?", (chat_id,)
        )
        row = self.cursor.fetchone()
        return row and row[0] == 1

    # ------------------------
    # Spam System
    # ------------------------

    def add_message_to_history(self, chat_id, user_id, message_text):
        timestamp = datetime.utcnow().isoformat()
        self.cursor.execute(
            """INSERT INTO spam_history (chat_id, user_id, message_text, timestamp)
               VALUES (?, ?, ?, ?)""",
            (chat_id, user_id, message_text, timestamp),
        )
        self.conn.commit()

    def get_recent_messages(self, chat_id, user_id, minutes=1):
        cutoff = datetime.utcnow() - timedelta(minutes=minutes)
        self.cursor.execute(
            """SELECT message_text, timestamp FROM spam_history
               WHERE chat_id=? AND user_id=? AND timestamp>=?""",
            (chat_id, user_id, cutoff.isoformat()),
        )
        rows = self.cursor.fetchall()
        return [{"message_text": r[0], "timestamp": r[1]} for r in rows]

    # ------------------------
    # Stats System
    # ------------------------

    def get_stat(self, key):
        self.cursor.execute("SELECT value FROM stats WHERE key=?", (key,))
        row = self.cursor.fetchone()
        return row[0] if row else 0

    def increment_stat(self, key):
        if self.get_stat(key) == 0:
            self.cursor.execute(
                "INSERT OR REPLACE INTO stats (key, value) VALUES (?, ?)",
                (key, 1),
            )
        else:
            self.cursor.execute(
                "UPDATE stats SET value = value + 1 WHERE key=?", (key,)
            )
        self.conn.commit()

    # ------------------------
    # Utilities
    # ------------------------

    def clear_all_data(self, chat_id):
        for table in (
            "banned",
            "muted",
            "restricted",
            "messages",
            "warnings",
            "custom_replies",
        ):
            self.cursor.execute(f"DELETE FROM {table} WHERE chat_id=?", (chat_id,))
        self.conn.commit()

    def clear_banned(self, chat_id):
        self._clear("banned", chat_id)

    def clear_muted(self, chat_id):
        self._clear("muted", chat_id)

    def _exists(self, table, chat_id, user_id):
        self.cursor.execute(
            f"SELECT 1 FROM {table} WHERE chat_id=? AND user_id=?",
            (chat_id, user_id),
        )
        return self.cursor.fetchone() is not None

    def _insert_unique(self, table, chat_id, user_id):
        if not self._exists(table, chat_id, user_id):
            self.cursor.execute(
                f"INSERT INTO {table} (chat_id, user_id) VALUES (?, ?)",
                (chat_id, user_id),
            )
            self.conn.commit()

    def _remove(self, table, chat_id, user_id):
        self.cursor.execute(
            f"DELETE FROM {table} WHERE chat_id=? AND user_id=?",
            (chat_id, user_id),
        )
        self.conn.commit()

    def _clear(self, table, chat_id):
        self.cursor.execute(
            f"DELETE FROM {table} WHERE chat_id=?", (chat_id,)
        )
        self.conn.commit()

    # ------------------------
    # Extra Info
    # ------------------------

    def get_total_users(self):
        self.cursor.execute("SELECT COUNT(DISTINCT user_id) FROM messages")
        row = self.cursor.fetchone()
        return row[0] if row else 0

    def get_total_groups(self):
        self.cursor.execute("SELECT COUNT(DISTINCT chat_id) FROM messages")
        row = self.cursor.fetchone()
        return row[0] if row else 0

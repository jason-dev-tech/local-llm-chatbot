import sqlite3
from config import DB_PATH


def get_connection():
    return sqlite3.connect(DB_PATH)


def init_db():
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id TEXT NOT NULL,
            role TEXT NOT NULL,
            content TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS sessions (
            session_id TEXT PRIMARY KEY,
            title TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    conn.commit()
    conn.close()


def save_message(session_id, role, content):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO messages (session_id, role, content)
        VALUES (?, ?, ?)
    """, (session_id, role, content))

    conn.commit()
    conn.close()


def get_recent_messages(session_id, limit=10):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT role, content
        FROM messages
        WHERE session_id = ?
        ORDER BY id DESC
        LIMIT ?
    """, (session_id, limit))

    rows = cursor.fetchall()
    conn.close()

    rows.reverse()

    return [{"role": role, "content": content} for role, content in rows]


def create_session(session_id, title=None):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        INSERT OR IGNORE INTO sessions (session_id, title)
        VALUES (?, ?)
    """, (session_id, title))

    conn.commit()
    conn.close()


def update_session_title(session_id, title):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        UPDATE sessions
        SET title = ?
        WHERE session_id = ?
    """, (title, session_id))

    conn.commit()
    conn.close()


def get_all_sessions():
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT DISTINCT session_id
        FROM messages
        ORDER BY session_id
    """)

    rows = cursor.fetchall()
    conn.close()

    return [row[0] for row in rows]


def get_all_sessions_with_titles():
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT session_id, title
        FROM sessions
        ORDER BY created_at
    """)

    rows = cursor.fetchall()
    conn.close()

    return rows


def session_exists(session_id):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT 1
        FROM sessions
        WHERE session_id = ?
        LIMIT 1
    """, (session_id,))

    row = cursor.fetchone()
    conn.close()

    return row is not None


def delete_session(session_id):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        DELETE FROM messages
        WHERE session_id = ?
    """, (session_id,))

    cursor.execute("""
        DELETE FROM sessions
        WHERE session_id = ?
    """, (session_id,))

    conn.commit()
    conn.close()


def get_session_title(session_id):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT title
        FROM sessions
        WHERE session_id = ?
    """, (session_id,))

    row = cursor.fetchone()
    conn.close()

    return row[0] if row else None
import sqlite3
from config import DB_PATH


def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS sessions (
            session_id TEXT PRIMARY KEY,
            title TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id TEXT NOT NULL,
            role TEXT NOT NULL,
            content TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (session_id) REFERENCES sessions(session_id)
        )
    """)

    conn.commit()
    conn.close()

    ensure_updated_at_column()


def ensure_updated_at_column():
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("PRAGMA table_info(sessions)")
    columns = [row["name"] for row in cursor.fetchall()]

    if "updated_at" not in columns:
        cursor.execute("""
            ALTER TABLE sessions
            ADD COLUMN updated_at TIMESTAMP
        """)

        cursor.execute("""
            UPDATE sessions
            SET updated_at = created_at
            WHERE updated_at IS NULL
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

    cursor.execute("""
        UPDATE sessions
        SET updated_at = CURRENT_TIMESTAMP
        WHERE session_id = ?
    """, (session_id,))

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

    rows = list(rows)
    rows.reverse()

    return [
        {
            "role": row["role"],
            "content": row["content"],
        }
        for row in rows
    ]


def get_session_messages(session_id):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT id, role, content, created_at
        FROM messages
        WHERE session_id = ?
        ORDER BY id ASC
    """, (session_id,))

    rows = cursor.fetchall()
    conn.close()

    return [
        {
            "id": row["id"],
            "role": row["role"],
            "content": row["content"],
            "created_at": row["created_at"],
        }
        for row in rows
    ]


def create_session(session_id, title=None):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        INSERT OR IGNORE INTO sessions (session_id, title)
        VALUES (?, ?)
    """, (session_id, title))

    cursor.execute("""
        UPDATE sessions
        SET updated_at = CURRENT_TIMESTAMP
        WHERE session_id = ?
    """, (session_id,))

    conn.commit()
    conn.close()


def update_session_title(session_id, title):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        UPDATE sessions
        SET title = ?, updated_at = CURRENT_TIMESTAMP
        WHERE session_id = ?
    """, (title, session_id))

    conn.commit()
    conn.close()


def get_all_sessions():
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT session_id
        FROM sessions
        ORDER BY updated_at DESC, created_at DESC
    """)

    rows = cursor.fetchall()
    conn.close()

    return [row["session_id"] for row in rows]


def get_all_sessions_with_titles():
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT session_id, title, created_at, updated_at
        FROM sessions
        ORDER BY updated_at DESC, created_at DESC
    """)

    rows = cursor.fetchall()
    conn.close()

    return [
        (row["session_id"], row["title"])
        for row in rows
    ]


def get_session(session_id):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT session_id, title, created_at, updated_at
        FROM sessions
        WHERE session_id = ?
        LIMIT 1
    """, (session_id,))

    row = cursor.fetchone()
    conn.close()

    if not row:
        return None

    return {
        "session_id": row["session_id"],
        "title": row["title"],
        "created_at": row["created_at"],
        "updated_at": row["updated_at"],
    }


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

    return row["title"] if row else None
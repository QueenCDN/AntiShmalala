import sqlite3

DATABASE_NAME = 'shma_bot.db'

def init_db():
    conn = sqlite3.connect(DATABASE_NAME)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS muted_users (
            user_id INTEGER PRIMARY KEY
        )
    ''')
    conn.commit()
    conn.close()

def is_user_muted(user_id: int) -> bool:
    conn = sqlite3.connect(DATABASE_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT 1 FROM muted_users WHERE user_id = ?", (user_id,))
    result = cursor.fetchone()
    conn.close()
    return result is not None

def mute_user(user_id: int):
    if not is_user_muted(user_id):
        conn = sqlite3.connect(DATABASE_NAME)
        cursor = conn.cursor()
        cursor.execute("INSERT INTO muted_users (user_id) VALUES (?)", (user_id,))
        conn.commit()
        conn.close()
        return True
    return False


def unmute_user(user_id: int):
    if is_user_muted(user_id):
        conn = sqlite3.connect(DATABASE_NAME)
        cursor = conn.cursor()
        cursor.execute("DELETE FROM muted_users WHERE user_id = ?", (user_id,))
        conn.commit()
        conn.close()
        return True
    return False

init_db()
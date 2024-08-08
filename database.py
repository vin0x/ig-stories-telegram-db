import sqlite3

def init_db():
    conn = sqlite3.connect('stories.db')
    cursor = conn.cursor()
    cursor.execute('''CREATE TABLE IF NOT EXISTS stories (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        telegram_user_id INTEGER,
                        instagram_user TEXT,
                        file_path TEXT,
                        time_posted TEXT,
                        country TEXT
                      )''')
    conn.commit()
    conn.close()


def save_story(telegram_user_id, instagram_user, file_path, time_posted, country):
    conn = sqlite3.connect('stories.db')
    cursor = conn.cursor()
    cursor.execute('INSERT INTO stories (telegram_user_id, instagram_user, file_path, time_posted, country) VALUES (?, ?, ?, ?, ?)',
                   (telegram_user_id, instagram_user, file_path, time_posted, country))
    conn.commit()
    conn.close()

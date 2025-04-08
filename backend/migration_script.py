# migration_script.py
import sqlite3

with sqlite3.connect("user_data.db") as conn:
    cursor = conn.cursor()
    print(" Running migration script...")

    # ✅ Create tables if missing
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            username TEXT PRIMARY KEY,
            password TEXT,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        );
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS results (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT,
            level INTEGER,
            correct INTEGER,
            answer TEXT,
            timestamp TEXT
        );
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS vocab_log (
            username TEXT,
            vocab TEXT,
            translation TEXT
        );
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS lesson_content (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            lesson_id INTEGER NOT NULL,
            title TEXT,
            content TEXT,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        );
    ''')

    # ✅ Add missing 'target_user' column
    cursor.execute("PRAGMA table_info(lesson_content);")
    columns = [col[1] for col in cursor.fetchall()]
    if "target_user" not in columns:
        cursor.execute("ALTER TABLE lesson_content ADD COLUMN target_user TEXT;")
        print("✅ 'target_user' column added.")
    else:
        print("ℹ️ 'target_user' column already exists.")

    # ✅ Add missing 'password' and 'created_at' columns to users table
    cursor.execute("PRAGMA table_info(users);")
    user_columns = [col[1] for col in cursor.fetchall()]

    if "password" not in user_columns:
        cursor.execute("ALTER TABLE users ADD COLUMN password TEXT;")
        print("✅ 'password' column added to users table.")
    else:
        print("ℹ️ 'password' column already exists.")

    if "created_at" not in user_columns:
        cursor.execute("ALTER TABLE users ADD COLUMN created_at DATETIME DEFAULT CURRENT_TIMESTAMP;")
        print("✅ 'created_at' column added to users table.")
    else:
        print("ℹ️ 'created_at' column already exists.")

    conn.commit()
    print("✅ Migration completed.")

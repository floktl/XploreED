# utils/setup/migration_script.py

import os
from pathlib import Path
from dotenv import load_dotenv

# Load .env file early!
env_path = Path(__file__).resolve().parent.parent.parent / "secrets" / ".env"
load_dotenv(dotenv_path=env_path)

# NOW import anything using DB_FILE
import sys
sys.path.append(str(Path(__file__).resolve().parents[2]))

from utils.db_utils import get_connection

with get_connection() as conn:
    cursor = conn.cursor()
    print("🔄 Running migration script...")

    # ✅ Create users table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            username TEXT PRIMARY KEY,
            password TEXT,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        );
    ''')

    # ✅ Create results table
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

    # ✅ Create vocab_log table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS vocab_log (
            username TEXT,
            vocab TEXT,
            translation TEXT
        );
    ''')

    # ✅ Create lesson_content table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS lesson_content (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            lesson_id INTEGER NOT NULL,
            title TEXT,
            content TEXT,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        );
    ''')

    # ✅ Add target_user column if missing
    cursor.execute("PRAGMA table_info(lesson_content);")
    columns = [col[1] for col in cursor.fetchall()]
    if "target_user" not in columns:
        cursor.execute("ALTER TABLE lesson_content ADD COLUMN target_user TEXT;")
        print("✅ 'target_user' column added.")
    else:
        print("ℹ️ 'target_user' column already exists.")

    # ✅ Add published column if missing
    if "published" not in columns:
        cursor.execute("ALTER TABLE lesson_content ADD COLUMN published INTEGER DEFAULT 0;")
        print("✅ 'published' column added.")
    else:
        print("ℹ️ 'published' column already exists.")

    # ✅ Add missing user columns
    cursor.execute("PRAGMA table_info(users);")
    user_columns = [col[1] for col in cursor.fetchall()]
    if "password" not in user_columns:
        cursor.execute("ALTER TABLE users ADD COLUMN password TEXT;")
        print("✅ 'password' column added.")
    else:
        print("ℹ️ 'password' column already exists.")

    if "created_at" not in user_columns:
        cursor.execute("ALTER TABLE users ADD COLUMN created_at DATETIME DEFAULT CURRENT_TIMESTAMP;")
        print("✅ 'created_at' column added.")
    else:
        print("ℹ️ 'created_at' column already exists.")

    # ✅ Create lesson_progress table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS lesson_progress (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id TEXT NOT NULL,
            lesson_id INTEGER NOT NULL,
            block_id TEXT NOT NULL,
            completed INTEGER NOT NULL DEFAULT 0,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(user_id, lesson_id, block_id),
            FOREIGN KEY (lesson_id) REFERENCES lesson_content(lesson_id)
        );
    ''')
    print("✅ 'lesson_progress' table created (if not exists).")

    # ✅ Create lesson_blocks table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS lesson_blocks (
            lesson_id INTEGER NOT NULL,
            block_id TEXT NOT NULL,
            PRIMARY KEY (lesson_id, block_id)
        );
    ''')
    print("✅ 'lesson_blocks' table created (if not exists).")

# ✅ Add num_blocks column if missing
cursor.execute("PRAGMA table_info(lesson_content);")
columns = [col[1] for col in cursor.fetchall()]
if "num_blocks" not in columns:
    cursor.execute("ALTER TABLE lesson_content ADD COLUMN num_blocks INTEGER DEFAULT 0;")
    print("✅ 'num_blocks' column added.")
else:
    print("ℹ️ 'num_blocks' column already exists.")

# ✅ Add ai_enabled column if missing
cursor.execute("PRAGMA table_info(lesson_content);")
columns = [col[1] for col in cursor.fetchall()]
if "ai_enabled" not in columns:
    cursor.execute("ALTER TABLE lesson_content ADD COLUMN ai_enabled INTEGER DEFAULT 0;")
    print("✅ 'ai_enabled' column added.")
else:
    print("ℹ️ 'ai_enabled' column already exists.")


conn.commit()
print("✅ Migration completed.")

# app/migration_script.py
"""Database migration script executed on container startup."""

import os
from pathlib import Path

try:
    from dotenv import load_dotenv  # type: ignore
except Exception:
    def load_dotenv(dotenv_path=None, **_):  # type: ignore
        if dotenv_path and os.path.exists(dotenv_path):
            with open(dotenv_path) as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith('#') and '=' in line:
                        key, value = line.split('=', 1)
                        os.environ.setdefault(key, value)


# Load .env file early!
env_path = Path(__file__).resolve().parent.parent.parent / "secrets" / ".env"
load_dotenv(dotenv_path=env_path)


# NOW import anything using DB_FILE
import sys

sys.path.append(str(Path(__file__).resolve().parents[2]))

try:
    from src.core.database.connection import get_connection
except ImportError:
    # Try alternative import path
    sys.path.append(str(Path(__file__).resolve().parents[2] / "src"))
    from core.database.connection import get_connection


with get_connection() as conn:
    cursor = conn.cursor()
    print("🔄 Running migration script...")

    # ✅ Create users table
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS users (
            username TEXT PRIMARY KEY,
            password TEXT,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        );
    """
    )

    # ✅ Create results table
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS results (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT,
            level INTEGER,
            correct INTEGER,
            answer TEXT,
            timestamp TEXT
        );
    """
    )

    # ✅ Create vocab_log table
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS vocab_log (
            username TEXT,
            vocab TEXT,
            translation TEXT,
            word_type TEXT,
            article TEXT,
            details TEXT,
            repetitions INTEGER DEFAULT 0,
            interval_days INTEGER DEFAULT 1,
            ef REAL DEFAULT 2.5,
            next_review DATETIME DEFAULT CURRENT_TIMESTAMP,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            context TEXT,
            exercise TEXT,
            quality INTEGER DEFAULT 0,
            last_review DATETIME
        );
    """
    )

    # ✅ Add spaced repetition columns if missing
    cursor.execute("PRAGMA table_info(vocab_log);")
    vocab_cols = [col[1] for col in cursor.fetchall()]
    if "repetitions" not in vocab_cols:
        cursor.execute(
            "ALTER TABLE vocab_log ADD COLUMN repetitions INTEGER DEFAULT 0;"
        )
        print("✅ 'repetitions' column added.")
    else:
        print("ℹ️ 'repetitions' column already exists.")

    if "interval_days" not in vocab_cols:
        cursor.execute(
            "ALTER TABLE vocab_log ADD COLUMN interval_days INTEGER DEFAULT 1;"
        )
        print("✅ 'interval_days' column added.")
    else:
        print("ℹ️ 'interval_days' column already exists.")

    if "ef" not in vocab_cols:
        cursor.execute("ALTER TABLE vocab_log ADD COLUMN ef REAL DEFAULT 2.5;")
        print("✅ 'ef' column added.")
    else:
        print("ℹ️ 'ef' column already exists.")

    if "next_review" not in vocab_cols:
        cursor.execute("ALTER TABLE vocab_log ADD COLUMN next_review DATETIME;")
        cursor.execute(
            "UPDATE vocab_log SET next_review = CURRENT_TIMESTAMP WHERE next_review IS NULL;"
        )
        print("✅ 'next_review' column added.")
    else:
        print("ℹ️ 'next_review' column already exists.")

    # ✅ Add new metadata columns
    if "created_at" not in vocab_cols:
        cursor.execute("ALTER TABLE vocab_log ADD COLUMN created_at DATETIME;")
        cursor.execute(
            "UPDATE vocab_log SET created_at = CURRENT_TIMESTAMP WHERE created_at IS NULL;"
        )
        print("✅ 'created_at' column added.")
    else:
        print("ℹ️ 'created_at' column already exists.")

    if "context" not in vocab_cols:
        cursor.execute("ALTER TABLE vocab_log ADD COLUMN context TEXT;")
        print("✅ 'context' column added.")
    else:
        print("ℹ️ 'context' column already exists.")

    if "exercise" not in vocab_cols:
        cursor.execute("ALTER TABLE vocab_log ADD COLUMN exercise TEXT;")
        print("✅ 'exercise' column added.")
    else:
        print("ℹ️ 'exercise' column already exists.")

    if "word_type" not in vocab_cols:
        cursor.execute("ALTER TABLE vocab_log ADD COLUMN word_type TEXT;")
        print("✅ 'word_type' column added.")
    else:
        print("ℹ️ 'word_type' column already exists.")

    if "article" not in vocab_cols:
        cursor.execute("ALTER TABLE vocab_log ADD COLUMN article TEXT;")
        print("✅ 'article' column added.")
    else:
        print("ℹ️ 'article' column already exists.")

    if "details" not in vocab_cols:
        cursor.execute("ALTER TABLE vocab_log ADD COLUMN details TEXT;")
        print("✅ 'details' column added.")
    else:
        print("ℹ️ 'details' column already exists.")

    if "last_review" not in vocab_cols:
        cursor.execute("ALTER TABLE vocab_log ADD COLUMN last_review DATETIME;")
        cursor.execute(
            "UPDATE vocab_log SET last_review = created_at WHERE last_review IS NULL;"
        )
        print("✅ 'last_review' column added.")
    else:
        print("ℹ️ 'last_review' column already exists.")

    if "quality" not in vocab_cols:
        cursor.execute("ALTER TABLE vocab_log ADD COLUMN quality INTEGER DEFAULT 0;")
        print("✅ 'quality' column added.")
    else:
        print("ℹ️ 'quality' column already exists.")

    # ✅ Remove duplicate vocab entries before enforcing uniqueness
    cursor.execute(
        "DELETE FROM vocab_log WHERE rowid NOT IN (SELECT MIN(rowid) FROM vocab_log GROUP BY username, vocab);"
    )
    print("✅ Duplicate vocab entries removed from 'vocab_log'.")

    # ✅ Ensure unique constraint on (username, vocab)
    cursor.execute(
        "CREATE UNIQUE INDEX IF NOT EXISTS idx_vocab_unique ON vocab_log(username, vocab);"
    )
    print("✅ Unique index created on 'vocab_log'(username, vocab).")

    # ✅ Create lesson_content table
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS lesson_content (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            lesson_id INTEGER NOT NULL,
            title TEXT,
            content TEXT,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        );
    """
    )

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
        cursor.execute(
            "ALTER TABLE lesson_content ADD COLUMN published INTEGER DEFAULT 0;"
        )
        print("✅ 'published' column added.")
    else:
        print("ℹ️ 'published' column already exists.")

    # ✅ Add skill_level column if missing
    if "skill_level" not in columns:
        cursor.execute("ALTER TABLE lesson_content ADD COLUMN skill_level TEXT;")
        print("✅ 'skill_level' column added to lesson_content.")
    else:
        print("ℹ️ 'skill_level' column already exists in lesson_content.")

    # ✅ Add num_blocks column if missing
    if "num_blocks" not in columns:
        cursor.execute("ALTER TABLE lesson_content ADD COLUMN num_blocks INTEGER DEFAULT 0;")
        print("✅ 'num_blocks' column added to lesson_content.")
    else:
        print("ℹ️ 'num_blocks' column already exists in lesson_content.")

    # ✅ Add ai_enabled column if missing
    if "ai_enabled" not in columns:
        cursor.execute("ALTER TABLE lesson_content ADD COLUMN ai_enabled INTEGER DEFAULT 0;")
        print("✅ 'ai_enabled' column added to lesson_content.")
    else:
        print("ℹ️ 'ai_enabled' column already exists in lesson_content.")

    # ✅ Add updated_at column if missing
    if "updated_at" not in columns:
        cursor.execute("ALTER TABLE lesson_content ADD COLUMN updated_at DATETIME DEFAULT CURRENT_TIMESTAMP;")
        print("✅ 'updated_at' column added to lesson_content.")
    else:
        print("ℹ️ 'updated_at' column already exists in lesson_content.")

    # ✅ Add missing user columns
    cursor.execute("PRAGMA table_info(users);")
    user_columns = [col[1] for col in cursor.fetchall()]
    if "password" not in user_columns:
        cursor.execute("ALTER TABLE users ADD COLUMN password TEXT;")
        print("✅ 'password' column added.")
    else:
        print("ℹ️ 'password' column already exists.")

    if "created_at" not in user_columns:
        cursor.execute("ALTER TABLE users ADD COLUMN created_at DATETIME;")
        cursor.execute(
            "UPDATE users SET created_at = CURRENT_TIMESTAMP WHERE created_at IS NULL;"
        )
        print("✅ 'created_at' column added.")
    else:
        print("ℹ️ 'created_at' column already exists.")

    if "skill_level" not in user_columns:
        cursor.execute("ALTER TABLE users ADD COLUMN skill_level INTEGER DEFAULT 0;")
        print("✅ 'skill_level' column added.")
    else:
        print("ℹ️ 'skill_level' column already exists.")

    # ✅ Create lesson_progress table
    cursor.execute(
        """
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
    """
    )
    print("✅ 'lesson_progress' table created (if not exists).")

    # ✅ Create lesson_blocks table
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS lesson_blocks (
            lesson_id INTEGER NOT NULL,
            block_id TEXT NOT NULL,
            PRIMARY KEY (lesson_id, block_id)
        );
    """
    )
    print("✅ 'lesson_blocks' table created (if not exists).")

    # ✅ Create support_feedback table
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS support_feedback (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            message TEXT NOT NULL,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        );
        """
    )
    print("✅ 'support_feedback' table created (if not exists).")

    # ✅ Create support_requests table
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS support_requests (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL,
            subject TEXT NOT NULL,
            description TEXT NOT NULL,
            urgency TEXT DEFAULT 'medium',
            contact_method TEXT DEFAULT 'email',
            status TEXT DEFAULT 'pending',
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            attachments TEXT,
            admin_notes TEXT
        );
        """
    )
    print("✅ 'support_requests' table created (if not exists).")

    # ✅ Create exercise_submissions table
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS exercise_submissions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL,
            block_id TEXT NOT NULL,
            answers TEXT NOT NULL,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        );
        """
    )
    print("✅ 'exercise_submissions' table created (if not exists).")

    # ✅ Create ai_user_data table
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS ai_user_data (
            username TEXT PRIMARY KEY,
            exercises TEXT,
            next_exercises TEXT,
            exercises_updated_at DATETIME,
            weakness_lesson TEXT,
            weakness_topic TEXT,
            lesson_updated_at DATETIME
        );
        """
    )
    print("✅ 'ai_user_data' table created (if not exists).")

    # ✅ Add next_exercises column if missing
    cursor.execute("PRAGMA table_info(ai_user_data);")
    ai_cols = [col[1] for col in cursor.fetchall()]
    if "next_exercises" not in ai_cols:
        cursor.execute("ALTER TABLE ai_user_data ADD COLUMN next_exercises TEXT;")
        print("✅ 'next_exercises' column added to 'ai_user_data'.")
    else:
        print("ℹ️ 'next_exercises' column already exists in 'ai_user_data'.")

    # ✅ Add exercise_history column if missing
    if "exercise_history" not in ai_cols:
        cursor.execute("ALTER TABLE ai_user_data ADD COLUMN exercise_history TEXT;")
        print("✅ 'exercise_history' column added to 'ai_user_data'.")
    else:
        print("ℹ️ 'exercise_history' column already exists in 'ai_user_data'.")

    # ✅ Create topic_memory table
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS topic_memory (
            username TEXT NOT NULL,
            grammar TEXT,
            topic TEXT,
            skill_type TEXT,
            context TEXT,
            lesson_content_id TEXT,
            ease_factor REAL,
            interval INTEGER,
            next_repeat DATETIME,
            repetitions INTEGER,
            last_review DATETIME,
            correct INTEGER DEFAULT 0,
            quality INTEGER DEFAULT 0
        );
        """
    )
    print("✅ 'topic_memory' table created (if not exists).")

    # ✅ Ensure required topic_memory columns exist for older DBs
    cursor.execute("PRAGMA table_info(topic_memory);")
    tm_cols = [col[1] for col in cursor.fetchall()]
    topic_memory_columns = [
        ("skill_type", "TEXT"),
        ("context", "TEXT"),
        ("lesson_content_id", "TEXT"),
        ("ease_factor", "REAL"),
        ("interval", "INTEGER"),
        ("next_repeat", "DATETIME"),
        ("repetitions", "INTEGER"),
        ("last_review", "DATETIME"),
        ("correct", "INTEGER DEFAULT 0"),
        ("quality", "INTEGER DEFAULT 0"),
    ]
    for col_name, col_def in topic_memory_columns:
        if col_name not in tm_cols:
            cursor.execute(f"ALTER TABLE topic_memory ADD COLUMN {col_name} {col_def};")
            print(f"✅ '{col_name}' column added to 'topic_memory'.")


# ✅ Rename 'topic' column to 'grammar'
cursor.execute("PRAGMA table_info(topic_memory);")
topic_cols = [col[1] for col in cursor.fetchall()]
if "grammar" not in topic_cols and "topic" in topic_cols:
    try:
        cursor.execute("ALTER TABLE topic_memory RENAME COLUMN topic TO grammar;")
        print("✅ 'topic' column renamed to 'grammar'.")
    except Exception:
        print("⚠️ Failed to rename column 'topic' to 'grammar'.")


# ✅ Add new 'topic' column if missing
cursor.execute("PRAGMA table_info(topic_memory);")
topic_cols = [col[1] for col in cursor.fetchall()]
if "topic" not in topic_cols:
    cursor.execute("ALTER TABLE topic_memory ADD COLUMN topic TEXT;")
    print("✅ 'topic' column added to 'topic_memory'.")
else:
    print("ℹ️ 'topic' column already exists in 'topic_memory'.")


# ✅ Add correct column if missing
cursor.execute("PRAGMA table_info(topic_memory);")
topic_cols = [col[1] for col in cursor.fetchall()]
if "correct" not in topic_cols:
    cursor.execute(
        "ALTER TABLE topic_memory ADD COLUMN correct INTEGER DEFAULT 0;"
    )
    print("✅ 'correct' column added to 'topic_memory'.")
# no-op else
# ✅ Add context column if missing
cursor.execute("PRAGMA table_info(topic_memory);")
topic_cols = [col[1] for col in cursor.fetchall()]
if "context" not in topic_cols:
    cursor.execute("ALTER TABLE topic_memory ADD COLUMN context TEXT;")
    print("✅ 'context' column added to 'topic_memory'.")


# ✅ Add quality column if missing
cursor.execute("PRAGMA table_info(topic_memory);")
topic_cols = [col[1] for col in cursor.fetchall()]
if "quality" not in topic_cols:
    cursor.execute("ALTER TABLE topic_memory ADD COLUMN quality INTEGER DEFAULT 0;")
    print("✅ 'quality' column added to 'topic_memory'.")

# ✅ Add id column if missing (for existing tables that might not have it)
cursor.execute("PRAGMA table_info(topic_memory);")
topic_cols = [col[1] for col in cursor.fetchall()]
if "id" not in topic_cols:
    try:
        # SQLite doesn't support adding PRIMARY KEY columns, so we need to recreate the table
        print("⚠️ 'id' column missing from topic_memory table. Attempting to add it...")

        # Get existing data
        existing_data = cursor.execute("SELECT * FROM topic_memory").fetchall()

        # Drop the table
        cursor.execute("DROP TABLE topic_memory")

        # Recreate with proper schema
        cursor.execute(
            """
            CREATE TABLE topic_memory (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT NOT NULL,
                grammar TEXT,
                topic TEXT,
                skill_type TEXT,
                context TEXT,
                lesson_content_id TEXT,
                ease_factor REAL,
                interval INTEGER,
                next_repeat DATETIME,
                repetitions INTEGER,
                last_review DATETIME,
                correct INTEGER DEFAULT 0,
                quality INTEGER DEFAULT 0
            );
            """
        )

        # Restore data if any existed
        if existing_data:
            for row in existing_data:
                cursor.execute(
                    """
                    INSERT INTO topic_memory (
                        username, grammar, topic, skill_type, context,
                        lesson_content_id, ease_factor, interval, next_repeat,
                        repetitions, last_review, correct, quality
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    row
                )

        print("✅ 'id' column added to 'topic_memory' table.")
    except Exception as e:
        print(f"⚠️ Failed to add 'id' column to topic_memory table: {e}")
        # If we can't add the id column, at least ensure the table exists with basic structure
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS topic_memory (
                username TEXT NOT NULL,
                grammar TEXT,
                topic TEXT,
                skill_type TEXT,
                context TEXT,
                lesson_content_id TEXT,
                ease_factor REAL,
                interval INTEGER,
                next_repeat DATETIME,
                repetitions INTEGER,
                last_review DATETIME,
                correct INTEGER DEFAULT 0,
                quality INTEGER DEFAULT 0
            );
            """
        )
else:
    print("ℹ️ 'id' column already exists in 'topic_memory'.")


# ✅ Add num_blocks column if missing
cursor.execute("PRAGMA table_info(lesson_content);")
columns = [col[1] for col in cursor.fetchall()]
if "num_blocks" not in columns:
    cursor.execute(
        "ALTER TABLE lesson_content ADD COLUMN num_blocks INTEGER DEFAULT 0;"
    )
    print("✅ 'num_blocks' column added.")


# ✅ Add ai_enabled column if missing
cursor.execute("PRAGMA table_info(lesson_content);")
columns = [col[1] for col in cursor.fetchall()]
if "ai_enabled" not in columns:
    cursor.execute(
        "ALTER TABLE lesson_content ADD COLUMN ai_enabled INTEGER DEFAULT 0;"
    )
    print("✅ 'ai_enabled' column added.")

# ✅ Create mistral_chat_history table
cursor.execute(
    """
    CREATE TABLE IF NOT EXISTS mistral_chat_history (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT NOT NULL,
        question TEXT NOT NULL,
        answer TEXT NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """
)
print("✅ 'mistral_chat_history' table created (if not exists).")

# ✅ Create ai_exercise_results table used by results endpoint
cursor.execute(
    """
    CREATE TABLE IF NOT EXISTS ai_exercise_results (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        block_id TEXT NOT NULL,
        username TEXT NOT NULL,
        results TEXT,
        summary TEXT,
        ai_feedback TEXT,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP
    );
    """
)
print("✅ 'ai_exercise_results' table created (if not exists).")

conn.commit()
print("✅ Migration completed.")

# scripts/migration_script.py
"""Database migration script executed on container startup."""

import os
import sqlite3
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


# Load .env file early! (with fallback paths)
env_paths = [
    Path(__file__).resolve().parent.parent / "secrets" / ".env",
    Path(__file__).resolve().parent.parent.parent / "secrets" / ".env",
    Path("/app/secrets/.env"),
    Path("/app/backend/secrets/.env"),
]

for env_path in env_paths:
    if env_path.exists():
        load_dotenv(dotenv_path=env_path)
        break

# Get database path from environment with fallbacks
db_path = os.getenv("DB_FILE", "database/user_data.db")
db_path = Path(db_path)

# Handle relative paths in Docker environment
if not db_path.is_absolute():
    # If we're in a Docker container, make it absolute
    if os.path.exists("/app"):
        db_path = Path("/app") / db_path
    else:
        # Local development
        db_path = Path(__file__).resolve().parent.parent / db_path

# Ensure database directory exists
db_path.parent.mkdir(parents=True, exist_ok=True)

print(f"🔄 Running migration script...")
print(f"   Database path: {db_path}")
print(f"   Database directory: {db_path.parent}")

try:
    # Connect to database
    conn = sqlite3.connect(str(db_path))
    cursor = conn.cursor()
    print("✅ Database connection established")

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
            exercise TEXT
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

    # ✅ Create topic_memory table
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS topic_memory (
            username TEXT,
            grammar TEXT,
            topic TEXT,
            skill_type TEXT,
            context TEXT,
            ease_factor REAL DEFAULT 2.5,
            repetitions INTEGER DEFAULT 0,
            interval INTEGER DEFAULT 1,
            next_repeat DATETIME DEFAULT CURRENT_TIMESTAMP,
            last_review DATETIME DEFAULT CURRENT_TIMESTAMP,
            correct BOOLEAN DEFAULT 0,
            quality INTEGER DEFAULT 0,
            PRIMARY KEY (username, grammar, topic, skill_type)
        );
    """
    )

    # ✅ Create sessions table
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS sessions (
            session_id TEXT PRIMARY KEY,
            username TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
    """
    )

    # ✅ Create user_progress table
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS user_progress (
            username TEXT PRIMARY KEY,
            level INTEGER DEFAULT 1,
            total_exercises INTEGER DEFAULT 0,
            correct_exercises INTEGER DEFAULT 0,
            last_activity DATETIME DEFAULT CURRENT_TIMESTAMP,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        );
    """
    )

    # ✅ Create user_settings table
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS user_settings (
            username TEXT PRIMARY KEY,
            language TEXT DEFAULT 'en',
            difficulty TEXT DEFAULT 'medium',
            notifications BOOLEAN DEFAULT 1,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
        );
    """
    )

    # Commit changes and close connection
    conn.commit()
    conn.close()

    print("✅ Database migration completed successfully!")

except Exception as e:
    print(f"⚠️ Migration script encountered an error: {str(e)}")
    print("   This is normal during Docker build if database is not accessible.")
    print("   Migration will run again during container startup if needed.")
    # Don't exit with error code to allow Docker build to continue

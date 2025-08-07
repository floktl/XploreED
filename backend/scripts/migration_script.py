"""
XplorED - Database Migration Script

This script handles database schema creation and updates for the XplorED platform.
It creates all necessary tables and ensures the database is properly initialized.

Features:
- Database Schema Creation: Create all required tables
- Environment Detection: Handle Docker and local environments
- Error Handling: Graceful error handling for Docker and local environments
- Logging: Proper logging configuration

For detailed architecture information, see: docs/backend_structure.md
"""

import sqlite3
import os
import sys
from pathlib import Path
from typing import Optional

# Add src to path for imports
# In Docker: /app/scripts/migration_script.py -> /app/src/
# In local: backend/scripts/migration_script.py -> backend/src/
if os.path.exists("/app"):
    # Docker container environment
    sys.path.insert(0, "/app/src")
else:
    # Local development environment
    sys.path.insert(0, str(Path(__file__).parent / "src"))

# Import logging configuration
from config.logging_config import setup_logging
import logging

# Setup logging
setup_logging(log_level="INFO")
logger = logging.getLogger(__name__)


def load_environment_variables() -> None:
    """Load environment variables from .env files with fallback paths."""
    try:
        from dotenv import load_dotenv  # type: ignore
    except ImportError:
        logger.warning("python-dotenv not available, using fallback loader")
        load_dotenv = _fallback_dotenv_loader

    # Define possible .env file locations
    env_paths = [
        Path(__file__).resolve().parent.parent / "secrets" / ".env",
        Path(__file__).resolve().parent.parent.parent / "secrets" / ".env",
        Path("/app/secrets/.env"),
        Path("/app/backend/secrets/.env"),
    ]

    # Try to load from each location
    for env_path in env_paths:
        if env_path.exists():
            load_dotenv(dotenv_path=str(env_path))
            logger.info(f"Loaded environment from: {env_path}")
            break
    else:
        logger.warning("No .env file found in any expected location")


def _fallback_dotenv_loader(dotenv_path: Optional[str] = None, **kwargs) -> None:
    """Fallback .env loader when python-dotenv is not available."""
    if not dotenv_path or not os.path.exists(dotenv_path):
        return

    with open(dotenv_path) as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith('#') and '=' in line:
                key, value = line.split('=', 1)
                os.environ.setdefault(key, value)


def resolve_database_path() -> Path:
    """Resolve the database file path with proper fallbacks."""
    db_path = os.getenv("DB_FILE", "database/user_data.db")
    db_path = Path(db_path)

    # Handle relative paths in Docker environment
    if not db_path.is_absolute():
        if os.path.exists("/app"):
            # Docker container environment - use the exact path from DB_FILE
            db_path = Path("/app") / db_path
        else:
            # Local development environment
            db_path = Path(__file__).resolve().parent.parent / db_path

    # Ensure database directory exists
    db_path.parent.mkdir(parents=True, exist_ok=True)

    logger.info(f"Database path resolved to: {db_path}")
    return db_path


def create_users_table(cursor: sqlite3.Cursor) -> None:
    """Create and update the users table with all required columns."""
    # Create base table
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS users (
            username TEXT PRIMARY KEY,
            password TEXT,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        );
        """
    )

    # Check existing columns and add missing ones
    cursor.execute("PRAGMA table_info(users);")
    user_columns = [col[1] for col in cursor.fetchall()]

    column_updates = [
        ("email", "TEXT"),
        ("skill_level", "INTEGER DEFAULT 1"),
        ("is_admin", "INTEGER DEFAULT 0"),
    ]

    for column_name, column_definition in column_updates:
        if column_name not in user_columns:
            cursor.execute(f"ALTER TABLE users ADD COLUMN {column_name} {column_definition};")
            logger.info(f"Added '{column_name}' column to users table")
        else:
            logger.debug(f"'{column_name}' column already exists in users table")


def create_results_table(cursor: sqlite3.Cursor) -> None:
    """Create the results table for storing exercise results."""
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
    logger.info("Results table created/verified")


def create_vocab_log_table(cursor: sqlite3.Cursor) -> None:
    """Create and update the vocab_log table with spaced repetition columns."""
    # Create base table
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

    # Check existing columns and add missing ones
    cursor.execute("PRAGMA table_info(vocab_log);")
    vocab_cols = [col[1] for col in cursor.fetchall()]

    column_updates = [
        ("repetitions", "INTEGER DEFAULT 0"),
        ("interval_days", "INTEGER DEFAULT 1"),
        ("ef", "REAL DEFAULT 2.5"),
        ("next_review", "DATETIME"),
        ("created_at", "DATETIME"),
        ("context", "TEXT"),
        ("exercise", "TEXT"),
    ]

    for column_name, column_definition in column_updates:
        if column_name not in vocab_cols:
            cursor.execute(f"ALTER TABLE vocab_log ADD COLUMN {column_name} {column_definition};")

            # Set default values for datetime columns
            if column_name in ["next_review", "created_at"]:
                cursor.execute(f"UPDATE vocab_log SET {column_name} = CURRENT_TIMESTAMP WHERE {column_name} IS NULL;")

            logger.info(f"Added '{column_name}' column to vocab_log table")
        else:
            logger.debug(f"'{column_name}' column already exists in vocab_log table")

    # Add missing columns that were causing errors
    missing_columns = [
        ("last_reviewed", "DATETIME"),
        ("quality", "INTEGER DEFAULT 0"),
        ("last_review", "DATETIME"),
    ]

    for column_name, column_definition in missing_columns:
        if column_name not in vocab_cols:
            cursor.execute(f"ALTER TABLE vocab_log ADD COLUMN {column_name} {column_definition};")
            logger.info(f"Added '{column_name}' column to vocab_log table")
        else:
            logger.debug(f"'{column_name}' column already exists in vocab_log table")


def create_topic_memory_table(cursor: sqlite3.Cursor) -> None:
    """Create the topic_memory table for spaced repetition of grammar topics."""
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS topic_memory (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
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
            quality INTEGER DEFAULT 0
        );
        """
    )

    # Check existing columns and add missing ones
    cursor.execute("PRAGMA table_info(topic_memory);")
    topic_cols = [col[1] for col in cursor.fetchall()]

    # Add missing columns
    missing_columns = [
        ("last_reviewed", "DATETIME"),
        ("strength", "REAL DEFAULT 1.0"),
    ]

    for column_name, column_definition in missing_columns:
        if column_name not in topic_cols:
            cursor.execute(f"ALTER TABLE topic_memory ADD COLUMN {column_name} {column_definition};")
            logger.info(f"Added '{column_name}' column to topic_memory table")
        else:
            logger.debug(f"'{column_name}' column already exists in topic_memory table")

    logger.info("Topic memory table created/verified")


def create_sessions_table(cursor: sqlite3.Cursor) -> None:
    """Create the sessions table for user session management."""
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS sessions (
            session_id TEXT PRIMARY KEY,
            username TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        """
    )
    logger.info("Sessions table created/verified")


def create_user_progress_table(cursor: sqlite3.Cursor) -> None:
    """Create the user_progress table for tracking user learning progress."""
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
    logger.info("User progress table created/verified")


def create_user_settings_table(cursor: sqlite3.Cursor) -> None:
    """Create the user_settings table for user preferences."""
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
    logger.info("User settings table created/verified")


def create_support_requests_table(cursor: sqlite3.Cursor) -> None:
    """Create the support_requests table for support ticket management."""
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
    logger.info("Support requests table created/verified")


def create_ai_user_data_table(cursor: sqlite3.Cursor) -> None:
    """Create the ai_user_data table for storing AI exercise data."""
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

    # Check existing columns and add missing ones
    cursor.execute("PRAGMA table_info(ai_user_data);")
    ai_cols = [col[1] for col in cursor.fetchall()]

    # Add next_exercises column if missing
    if "next_exercises" not in ai_cols:
        cursor.execute("ALTER TABLE ai_user_data ADD COLUMN next_exercises TEXT;")
        logger.info("Added 'next_exercises' column to ai_user_data table")
    else:
        logger.debug("'next_exercises' column already exists in ai_user_data table")

    # Add exercise_history column if missing
    if "exercise_history" not in ai_cols:
        cursor.execute("ALTER TABLE ai_user_data ADD COLUMN exercise_history TEXT;")
        logger.info("Added 'exercise_history' column to ai_user_data table")
    else:
        logger.debug("'exercise_history' column already exists in ai_user_data table")

    logger.info("AI user data table created/verified")


def create_exercise_history_table(cursor: sqlite3.Cursor) -> None:
    """Create the exercise_history table for tracking exercise questions."""
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS exercise_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL,
            question TEXT NOT NULL,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        );
        """
    )
    logger.info("Exercise history table created/verified")


def create_ai_exercise_results_table(cursor: sqlite3.Cursor) -> None:
    """Create the ai_exercise_results table for storing AI exercise evaluation results."""
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS ai_exercise_results (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            block_id TEXT NOT NULL,
            username TEXT NOT NULL,
            results TEXT NOT NULL,
            summary TEXT NOT NULL,
            ai_feedback TEXT,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        );
        """
    )
    logger.info("AI exercise results table created/verified")


def create_topic_memory_status_table(cursor: sqlite3.Cursor) -> None:
    """Create the topic_memory_status table for tracking topic memory processing status."""
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS topic_memory_status (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            block_id TEXT NOT NULL,
            username TEXT NOT NULL,
            status TEXT DEFAULT 'pending',
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(block_id, username)
        );
        """
    )
    logger.info("Topic memory status table created/verified")


def create_ai_exercise_blocks_table(cursor: sqlite3.Cursor) -> None:
    """Create the ai_exercise_blocks table for storing AI-generated exercise blocks."""
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS ai_exercise_blocks (
            id TEXT PRIMARY KEY,
            username TEXT NOT NULL,
            lessonId TEXT,
            title TEXT,
            level INTEGER,
            topic TEXT,
            exercises TEXT,
            feedbackPrompt TEXT,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        );
        """
    )
    logger.info("AI exercise blocks table created/verified")


def run_migration() -> None:
    """Execute the complete database migration process."""
    logger.info("🔄 Starting database migration...")

    # Load environment variables
    load_environment_variables()

    # Resolve database path
    db_path = resolve_database_path()
    logger.info(f"Database path: {db_path}")
    logger.info(f"Database directory: {db_path.parent}")

    try:
        # Connect to database
        conn = sqlite3.connect(str(db_path))
        cursor = conn.cursor()
        logger.info("✅ Database connection established")

        # Create/update all tables
        create_users_table(cursor)
        create_results_table(cursor)
        create_vocab_log_table(cursor)
        create_topic_memory_table(cursor)
        create_sessions_table(cursor)
        create_user_progress_table(cursor)
        create_user_settings_table(cursor)
        create_support_requests_table(cursor)
        create_ai_user_data_table(cursor)
        create_exercise_history_table(cursor)
        create_ai_exercise_results_table(cursor)
        create_topic_memory_status_table(cursor)
        create_ai_exercise_blocks_table(cursor)

        # Commit changes and close connection
        conn.commit()
        conn.close()

        logger.info("✅ Database migration completed successfully!")

    except Exception as e:
        logger.error(f"❌ Migration script encountered an error: {str(e)}")
        logger.info("   This is normal during Docker build if database is not accessible.")
        logger.info("   Migration will run again during container startup if needed.")
        # Don't exit with error code to allow Docker build to continue


if __name__ == "__main__":
    run_migration()

# utils/setup/analytics_migration.py

import os
from pathlib import Path
from dotenv import load_dotenv
import datetime

# Load .env file early!
env_path = Path(__file__).resolve().parent.parent.parent / "secrets" / ".env"
load_dotenv(dotenv_path=env_path)

# NOW import anything using DB_FILE
from utils.db_utils import get_connection

with get_connection() as conn:
    cursor = conn.cursor()
    print("🔄 Running analytics migration script...")

    # Create user_analytics table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS user_analytics (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL,
            activity_type TEXT NOT NULL,
            activity_date DATE NOT NULL,
            correct_count INTEGER DEFAULT 0,
            attempt_count INTEGER DEFAULT 0,
            time_spent_seconds INTEGER DEFAULT 0,
            UNIQUE(username, activity_type, activity_date)
        );
    ''')
    print("✅ 'user_analytics' table created (if not exists).")

    # Create user_streaks table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS user_streaks (
            username TEXT PRIMARY KEY,
            current_streak INTEGER DEFAULT 0,
            longest_streak INTEGER DEFAULT 0,
            last_activity_date DATE,
            streak_start_date DATE
        );
    ''')
    print("✅ 'user_streaks' table created (if not exists).")

    # Create user_achievements table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS user_achievements (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL,
            achievement_id TEXT NOT NULL,
            earned_date DATETIME DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(username, achievement_id)
        );
    ''')
    print("✅ 'user_achievements' table created (if not exists).")

    # Create achievements table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS achievements (
            achievement_id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            description TEXT NOT NULL,
            icon TEXT NOT NULL,
            requirement_type TEXT NOT NULL,
            requirement_value INTEGER NOT NULL
        );
    ''')
    print("✅ 'achievements' table created (if not exists).")

    # Insert default achievements
    achievements = [
        ('first_translation', 'First Steps', 'Complete your first translation', '🎯', 'translations', 1),
        ('translation_10', 'Translation Novice', 'Complete 10 translations', '📝', 'translations', 10),
        ('translation_50', 'Translation Expert', 'Complete 50 translations', '📚', 'translations', 50),
        ('perfect_5', 'Accuracy Beginner', 'Get 5 perfect translations in a row', '🎯', 'perfect_streak', 5),
        ('perfect_10', 'Accuracy Pro', 'Get 10 perfect translations in a row', '🎯', 'perfect_streak', 10),
        ('streak_3', 'Consistent Learner', 'Maintain a 3-day learning streak', '🔥', 'streak', 3),
        ('streak_7', 'Weekly Warrior', 'Maintain a 7-day learning streak', '🔥', 'streak', 7),
        ('streak_30', 'Monthly Master', 'Maintain a 30-day learning streak', '🔥', 'streak', 30),
        ('lesson_complete_1', 'Lesson Starter', 'Complete your first lesson', '📘', 'lessons', 1),
        ('lesson_complete_5', 'Lesson Enthusiast', 'Complete 5 lessons', '📚', 'lessons', 5),
        ('pronunciation_5', 'Voice Beginner', 'Practice pronunciation 5 times', '🎤', 'pronunciation', 5),
        ('pronunciation_20', 'Voice Master', 'Practice pronunciation 20 times', '🎙️', 'pronunciation', 20),
    ]

    # Check if achievements already exist
    cursor.execute("SELECT COUNT(*) FROM achievements")
    count = cursor.fetchone()[0]

    if count == 0:
        cursor.executemany(
            "INSERT INTO achievements (achievement_id, name, description, icon, requirement_type, requirement_value) VALUES (?, ?, ?, ?, ?, ?)",
            achievements
        )
        print("✅ Default achievements inserted.")
    else:
        print("ℹ️ Achievements already exist, skipping insertion.")

    # Create activity_log table for detailed tracking
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS activity_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL,
            activity_type TEXT NOT NULL,
            details TEXT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        );
    ''')
    print("✅ 'activity_log' table created (if not exists).")

    # Migrate existing data from results table to user_analytics
    cursor.execute("SELECT COUNT(*) FROM user_analytics")
    analytics_count = cursor.fetchone()[0]

    if analytics_count == 0:
        print("ℹ️ Migrating existing results to analytics...")

        # Check if results table exists
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='results'")
        if not cursor.fetchone():
            print("ℹ️ Results table doesn't exist yet, skipping migration.")
            conn.commit()
            print("✅ Analytics migration completed.")
            exit(0)

        # Get all results
        cursor.execute('''
            SELECT username, level, correct, timestamp
            FROM results
            ORDER BY username, timestamp
        ''')
        results = cursor.fetchall()

        # Group by username and date
        analytics_data = {}
        for username, level, correct, timestamp in results:
            try:
                date = datetime.datetime.fromisoformat(timestamp).date().isoformat()
            except (ValueError, TypeError):
                # If timestamp is not in ISO format, use today's date
                date = datetime.date.today().isoformat()

            key = (username, 'translation', date)
            if key not in analytics_data:
                analytics_data[key] = {'correct': 0, 'attempts': 0}

            analytics_data[key]['attempts'] += 1
            if correct:
                analytics_data[key]['correct'] += 1

        # Insert into user_analytics
        for (username, activity_type, date), counts in analytics_data.items():
            cursor.execute('''
                INSERT INTO user_analytics
                (username, activity_type, activity_date, correct_count, attempt_count)
                VALUES (?, ?, ?, ?, ?)
            ''', (username, activity_type, date, counts['correct'], counts['attempts']))

        print(f"✅ Migrated {len(analytics_data)} analytics records from {len(results)} results.")
    else:
        print("ℹ️ Analytics data already exists, skipping migration.")

    conn.commit()
    print("✅ Analytics migration completed.")

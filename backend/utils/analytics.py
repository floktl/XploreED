# utils/analytics.py

import datetime
from .db_utils import get_connection, execute_query, fetch_custom

def log_activity(username, activity_type, details=None):
    """
    Log a user activity for analytics purposes
    
    Args:
        username (str): The username
        activity_type (str): Type of activity (translation, pronunciation, lesson, etc.)
        details (dict, optional): Additional details about the activity
    """
    if not username:
        return False
        
    details_json = str(details) if details else None
    
    return execute_query(
        "INSERT INTO activity_log (username, activity_type, details) VALUES (?, ?, ?)",
        (username, activity_type, details_json)
    )

def update_analytics(username, activity_type, correct=False, time_spent=0):
    """
    Update user analytics for the current day
    
    Args:
        username (str): The username
        activity_type (str): Type of activity (translation, pronunciation, lesson, etc.)
        correct (bool): Whether the activity was completed correctly
        time_spent (int): Time spent on the activity in seconds
    """
    if not username:
        return False
        
    today = datetime.date.today().isoformat()
    
    with get_connection() as conn:
        # Check if there's an entry for today
        cursor = conn.execute(
            "SELECT id FROM user_analytics WHERE username = ? AND activity_type = ? AND activity_date = ?",
            (username, activity_type, today)
        )
        row = cursor.fetchone()
        
        if row:
            # Update existing entry
            conn.execute(
                """
                UPDATE user_analytics 
                SET attempt_count = attempt_count + 1,
                    correct_count = correct_count + ?,
                    time_spent_seconds = time_spent_seconds + ?
                WHERE username = ? AND activity_type = ? AND activity_date = ?
                """,
                (1 if correct else 0, time_spent, username, activity_type, today)
            )
        else:
            # Create new entry
            conn.execute(
                """
                INSERT INTO user_analytics 
                (username, activity_type, activity_date, correct_count, attempt_count, time_spent_seconds)
                VALUES (?, ?, ?, ?, 1, ?)
                """,
                (username, activity_type, today, 1 if correct else 0, time_spent)
            )
        
        # Update streak
        update_streak(conn, username)
        
        # Check for achievements
        check_achievements(conn, username)
        
        conn.commit()
        return True

def update_streak(conn, username):
    """
    Update the user's streak based on activity
    
    Args:
        conn: Database connection
        username (str): The username
    """
    today = datetime.date.today()
    yesterday = (today - datetime.timedelta(days=1)).isoformat()
    today = today.isoformat()
    
    # Check if user has a streak record
    cursor = conn.execute(
        "SELECT current_streak, longest_streak, last_activity_date, streak_start_date FROM user_streaks WHERE username = ?",
        (username,)
    )
    row = cursor.fetchone()
    
    if row:
        current_streak, longest_streak, last_activity_date, streak_start_date = row
        
        # If last activity was today, no need to update
        if last_activity_date == today:
            return
            
        # If last activity was yesterday, increment streak
        if last_activity_date == yesterday:
            current_streak += 1
            longest_streak = max(current_streak, longest_streak)
            
            conn.execute(
                """
                UPDATE user_streaks 
                SET current_streak = ?, longest_streak = ?, last_activity_date = ?
                WHERE username = ?
                """,
                (current_streak, longest_streak, today, username)
            )
        # If last activity was before yesterday, reset streak
        elif last_activity_date < yesterday:
            conn.execute(
                """
                UPDATE user_streaks 
                SET current_streak = 1, last_activity_date = ?, streak_start_date = ?
                WHERE username = ?
                """,
                (today, today, username)
            )
    else:
        # Create new streak record
        conn.execute(
            """
            INSERT INTO user_streaks 
            (username, current_streak, longest_streak, last_activity_date, streak_start_date)
            VALUES (?, 1, 1, ?, ?)
            """,
            (username, today, today)
        )

def check_achievements(conn, username):
    """
    Check if user has earned any new achievements
    
    Args:
        conn: Database connection
        username (str): The username
    """
    # Get all achievements
    cursor = conn.execute("SELECT * FROM achievements")
    achievements = cursor.fetchall()
    
    # Get user's current achievements
    cursor = conn.execute(
        "SELECT achievement_id FROM user_achievements WHERE username = ?",
        (username,)
    )
    earned_achievements = [row[0] for row in cursor.fetchall()]
    
    for achievement in achievements:
        achievement_id = achievement[0]
        
        # Skip if already earned
        if achievement_id in earned_achievements:
            continue
            
        requirement_type = achievement[4]
        requirement_value = achievement[5]
        
        # Check if user meets the requirement
        if requirement_type == 'translations':
            # Count total translations
            cursor = conn.execute(
                """
                SELECT SUM(attempt_count) FROM user_analytics 
                WHERE username = ? AND activity_type = 'translation'
                """,
                (username,)
            )
            count = cursor.fetchone()[0] or 0
            if count >= requirement_value:
                award_achievement(conn, username, achievement_id)
                
        elif requirement_type == 'perfect_streak':
            # Check for consecutive correct translations
            cursor = conn.execute(
                """
                SELECT correct FROM results 
                WHERE username = ? 
                ORDER BY timestamp DESC 
                LIMIT ?
                """,
                (username, requirement_value)
            )
            results = cursor.fetchall()
            if len(results) >= requirement_value and all(row[0] for row in results):
                award_achievement(conn, username, achievement_id)
                
        elif requirement_type == 'streak':
            # Check current streak
            cursor = conn.execute(
                "SELECT current_streak FROM user_streaks WHERE username = ?",
                (username,)
            )
            row = cursor.fetchone()
            if row and row[0] >= requirement_value:
                award_achievement(conn, username, achievement_id)
                
        elif requirement_type == 'lessons':
            # Count completed lessons
            cursor = conn.execute(
                """
                SELECT COUNT(DISTINCT level) FROM results 
                WHERE username = ? AND correct = 1 AND level > 0
                """,
                (username,)
            )
            count = cursor.fetchone()[0] or 0
            if count >= requirement_value:
                award_achievement(conn, username, achievement_id)
                
        elif requirement_type == 'pronunciation':
            # Count pronunciation practice sessions
            cursor = conn.execute(
                """
                SELECT SUM(attempt_count) FROM user_analytics 
                WHERE username = ? AND activity_type = 'pronunciation'
                """,
                (username,)
            )
            count = cursor.fetchone()[0] or 0
            if count >= requirement_value:
                award_achievement(conn, username, achievement_id)

def award_achievement(conn, username, achievement_id):
    """
    Award an achievement to a user
    
    Args:
        conn: Database connection
        username (str): The username
        achievement_id (str): The achievement ID
    """
    try:
        conn.execute(
            "INSERT INTO user_achievements (username, achievement_id) VALUES (?, ?)",
            (username, achievement_id)
        )
        return True
    except:
        return False

def get_user_analytics(username, days=30):
    """
    Get analytics data for a user
    
    Args:
        username (str): The username
        days (int): Number of days to include
        
    Returns:
        dict: Analytics data
    """
    if not username:
        return {}
        
    # Calculate date range
    end_date = datetime.date.today()
    start_date = end_date - datetime.timedelta(days=days-1)
    
    # Generate all dates in range
    date_range = []
    current_date = start_date
    while current_date <= end_date:
        date_range.append(current_date.isoformat())
        current_date += datetime.timedelta(days=1)
    
    # Get analytics data
    rows = fetch_custom(
        """
        SELECT activity_date, activity_type, correct_count, attempt_count, time_spent_seconds
        FROM user_analytics
        WHERE username = ? AND activity_date >= ? AND activity_date <= ?
        ORDER BY activity_date
        """,
        (username, start_date.isoformat(), end_date.isoformat())
    )
    
    # Initialize data structure
    analytics = {
        'dates': date_range,
        'activities': {},
        'totals': {
            'correct': 0,
            'attempts': 0,
            'time_spent': 0
        },
        'accuracy': 0
    }
    
    # Process data
    for row in rows:
        date = row['activity_date']
        activity_type = row['activity_type']
        correct = row['correct_count']
        attempts = row['attempt_count']
        time_spent = row['time_spent_seconds']
        
        # Initialize activity type if not exists
        if activity_type not in analytics['activities']:
            analytics['activities'][activity_type] = {
                'daily': {d: {'correct': 0, 'attempts': 0, 'time': 0} for d in date_range},
                'total_correct': 0,
                'total_attempts': 0,
                'total_time': 0
            }
            
        # Update daily data
        analytics['activities'][activity_type]['daily'][date] = {
            'correct': correct,
            'attempts': attempts,
            'time': time_spent
        }
        
        # Update activity totals
        analytics['activities'][activity_type]['total_correct'] += correct
        analytics['activities'][activity_type]['total_attempts'] += attempts
        analytics['activities'][activity_type]['total_time'] += time_spent
        
        # Update overall totals
        analytics['totals']['correct'] += correct
        analytics['totals']['attempts'] += attempts
        analytics['totals']['time_spent'] += time_spent
    
    # Calculate accuracy
    if analytics['totals']['attempts'] > 0:
        analytics['accuracy'] = round(
            (analytics['totals']['correct'] / analytics['totals']['attempts']) * 100
        )
    
    # Get streak data
    streak_row = fetch_custom(
        "SELECT current_streak, longest_streak, streak_start_date FROM user_streaks WHERE username = ?",
        (username,)
    )
    
    if streak_row:
        analytics['streak'] = {
            'current': streak_row[0]['current_streak'],
            'longest': streak_row[0]['longest_streak'],
            'start_date': streak_row[0]['streak_start_date']
        }
    else:
        analytics['streak'] = {
            'current': 0,
            'longest': 0,
            'start_date': None
        }
    
    # Get achievements
    achievement_rows = fetch_custom(
        """
        SELECT a.achievement_id, a.name, a.description, a.icon, ua.earned_date
        FROM user_achievements ua
        JOIN achievements a ON ua.achievement_id = a.achievement_id
        WHERE ua.username = ?
        ORDER BY ua.earned_date DESC
        """,
        (username,)
    )
    
    analytics['achievements'] = [
        {
            'id': row['achievement_id'],
            'name': row['name'],
            'description': row['description'],
            'icon': row['icon'],
            'earned_date': row['earned_date']
        }
        for row in achievement_rows
    ]
    
    # Get available achievements
    available_rows = fetch_custom(
        """
        SELECT achievement_id, name, description, icon, requirement_type, requirement_value
        FROM achievements
        WHERE achievement_id NOT IN (
            SELECT achievement_id FROM user_achievements WHERE username = ?
        )
        """,
        (username,)
    )
    
    analytics['available_achievements'] = [
        {
            'id': row['achievement_id'],
            'name': row['name'],
            'description': row['description'],
            'icon': row['icon'],
            'requirement_type': row['requirement_type'],
            'requirement_value': row['requirement_value']
        }
        for row in available_rows
    ]
    
    return analytics

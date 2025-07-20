"""Account settings endpoints."""

from app.imports.imports import *
from flask import current_app

@settings_bp.route('/password', methods=['POST'])
def update_password_route():
    """Change the logged in user's password."""
    user = get_current_user()
    if not user:
        return jsonify({'error': 'Unauthorized'}), 401
    data = request.get_json() or {}
    current_pw = data.get('current_password', '')
    new_pw = data.get('new_password', '')
    if not current_pw or not new_pw:
        return jsonify({'error': 'Missing fields'}), 400

    row = fetch_one('users', 'WHERE username = ?', (user,))
    if not row or not check_password_hash(row['password'], current_pw):
        return jsonify({'error': 'Incorrect password'}), 400

    hashed = generate_password_hash(new_pw)
    update_row('users', {'password': hashed}, 'username = ?', (user,))
    return jsonify({'msg': 'password updated'})


@settings_bp.route('/deactivate', methods=['POST'])
def deactivate_account_route():
    """Delete all data for the current user."""
    user = get_current_user()
    if not user:
        return jsonify({'error': 'Unauthorized'}), 401

    try:
        user_row = fetch_one('users', 'WHERE username = ?', (user,))
        if not user_row:
            return jsonify({'error': 'User not found'}), 404

        # current_app.logger.info(f"User {user} requesting account deactivation")

        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM ai_user_data WHERE username = ?", (user,))
            ai_deleted = cursor.rowcount
            # current_app.logger.info(f"Deleted {ai_deleted} records from ai_user_data for user {user}")

            cursor.execute("DELETE FROM vocab_log WHERE username = ?", (user,))
            vocab_deleted = cursor.rowcount
            # current_app.logger.info(f"Deleted {vocab_deleted} records from vocab_log for user {user}")

            cursor.execute("DELETE FROM topic_memory WHERE username = ?", (user,))
            topic_deleted = cursor.rowcount
            # current_app.logger.info(f"Deleted {topic_deleted} records from topic_memory for user {user}")

            cursor.execute("DELETE FROM results WHERE username = ?", (user,))
            results_deleted = cursor.rowcount
            # current_app.logger.info(f"Deleted {results_deleted} records from results for user {user}")

            cursor.execute("DELETE FROM exercise_submissions WHERE username = ?", (user,))
            submissions_deleted = cursor.rowcount
            # current_app.logger.info(f"Deleted {submissions_deleted} records from exercise_submissions for user {user}")

            cursor.execute("DELETE FROM lesson_progress WHERE user_id = ?", (user,))
            lesson_progress_deleted = cursor.rowcount
            # current_app.logger.info(f"Deleted {lesson_progress_deleted} records from lesson_progress for user {user}")

            cursor.execute("DELETE FROM users WHERE username = ?", (user,))
            user_deleted = cursor.rowcount
            # current_app.logger.info(f"Deleted {user_deleted} records from users for user {user}")

            conn.commit()

        session_manager.destroy_user_sessions(user)
        # current_app.logger.info(f"Destroyed all sessions for user {user}")
        # current_app.logger.info(f"Account deactivation completed for user {user}. Deleted: AI data={ai_deleted}, vocab={vocab_deleted}, topic_memory={topic_deleted}, results={results_deleted}, exercise_submissions={submissions_deleted}, lesson_progress={lesson_progress_deleted}, user={user_deleted}")

        resp = make_response(jsonify({'message': 'Account deactivated successfully'}))
        resp.set_cookie('session_id', '', max_age=0)
        return resp

    except Exception as e:
        current_app.logger.error(f"Error deactivating account for user {user}: {str(e)}")
        return jsonify({'error': 'Failed to deactivate account'}), 500

# routes/analytics.py

from flask import Blueprint, request, jsonify
from utils.session.session_manager import session_manager
from utils.analytics import get_user_analytics, log_activity, update_analytics
from utils.db_utils import fetch_custom

analytics_bp = Blueprint("analytics", __name__)

@analytics_bp.route("/analytics", methods=["GET"])
def get_analytics():
    """Get analytics data for the current user"""
    session_id = request.cookies.get("session_id")
    username = session_manager.get_user(session_id)
    
    if not username:
        return jsonify({"error": "Unauthorized"}), 401
    
    days = request.args.get("days", 30, type=int)
    analytics = get_user_analytics(username, days)
    
    return jsonify(analytics)

@analytics_bp.route("/analytics/log", methods=["POST"])
def log_user_activity():
    """Log a user activity for analytics"""
    session_id = request.cookies.get("session_id")
    username = session_manager.get_user(session_id)
    
    if not username:
        return jsonify({"error": "Unauthorized"}), 401
    
    data = request.get_json()
    activity_type = data.get("activity_type")
    details = data.get("details")
    
    if not activity_type:
        return jsonify({"error": "Missing activity_type"}), 400
    
    success = log_activity(username, activity_type, details)
    
    if not success:
        return jsonify({"error": "Failed to log activity"}), 500
    
    return jsonify({"status": "success"})

@analytics_bp.route("/analytics/update", methods=["POST"])
def update_user_analytics():
    """Update user analytics for an activity"""
    session_id = request.cookies.get("session_id")
    username = session_manager.get_user(session_id)
    
    if not username:
        return jsonify({"error": "Unauthorized"}), 401
    
    data = request.get_json()
    activity_type = data.get("activity_type")
    correct = data.get("correct", False)
    time_spent = data.get("time_spent", 0)
    
    if not activity_type:
        return jsonify({"error": "Missing activity_type"}), 400
    
    success = update_analytics(username, activity_type, correct, time_spent)
    
    if not success:
        return jsonify({"error": "Failed to update analytics"}), 500
    
    return jsonify({"status": "success"})

@analytics_bp.route("/analytics/achievements", methods=["GET"])
def get_user_achievements():
    """Get achievements for the current user"""
    session_id = request.cookies.get("session_id")
    username = session_manager.get_user(session_id)
    
    if not username:
        return jsonify({"error": "Unauthorized"}), 401
    
    # Get earned achievements
    earned = fetch_custom(
        """
        SELECT a.achievement_id, a.name, a.description, a.icon, ua.earned_date
        FROM user_achievements ua
        JOIN achievements a ON ua.achievement_id = a.achievement_id
        WHERE ua.username = ?
        ORDER BY ua.earned_date DESC
        """,
        (username,)
    )
    
    # Get available achievements
    available = fetch_custom(
        """
        SELECT achievement_id, name, description, icon, requirement_type, requirement_value
        FROM achievements
        WHERE achievement_id NOT IN (
            SELECT achievement_id FROM user_achievements WHERE username = ?
        )
        """,
        (username,)
    )
    
    return jsonify({
        "earned": [
            {
                "id": row["achievement_id"],
                "name": row["name"],
                "description": row["description"],
                "icon": row["icon"],
                "earned_date": row["earned_date"]
            }
            for row in earned
        ],
        "available": [
            {
                "id": row["achievement_id"],
                "name": row["name"],
                "description": row["description"],
                "icon": row["icon"],
                "requirement_type": row["requirement_type"],
                "requirement_value": row["requirement_value"]
            }
            for row in available
        ]
    })

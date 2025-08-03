"""
XplorED - Feedback Management Module

This module provides feedback management functions for the XplorED platform,
following clean architecture principles as outlined in the documentation.

Feedback Management Components:
- Feedback Submission: Submit and store user feedback
- Feedback Retrieval: Get feedback lists and individual feedback
- Feedback Statistics: Calculate feedback statistics and analytics
- Feedback Search: Search through feedback messages

For detailed architecture information, see: docs/backend_structure.md
"""

import logging
from typing import List, Optional, Tuple

from core.database.connection import select_one, select_rows, insert_row, update_row, delete_rows, fetch_one, fetch_all, fetch_custom, execute_query, get_connection
from datetime import datetime, timedelta
from shared.exceptions import DatabaseError, ValidationError
from shared.types import FeedbackData, FeedbackList, ValidationResult

logger = logging.getLogger(__name__)


def submit_feedback(message: str, username: Optional[str] = None) -> Tuple[bool, Optional[str]]:
    """
    Store a feedback message from a user.

    Args:
        message: The feedback message content
        username: Optional username if user is authenticated

    Returns:
        Tuple of (success, error_message)

    Raises:
        ValueError: If message is invalid
    """
    try:
        if not message or not message.strip():
            raise ValueError("Message is required and cannot be empty")

        message = message.strip()
        if len(message) > 1000:
            raise ValueError("Message is too long (maximum 1000 characters)")

        logger.info(f"Submitting feedback from user {username or 'anonymous'}")

        feedback_data = {
            'message': message,
            'created_at': datetime.utcnow().isoformat()
        }

        # Add username if provided
        if username:
            feedback_data['username'] = username

        success = insert_row('support_feedback', feedback_data)

        if success:
            logger.info(f"Successfully submitted feedback from user {username or 'anonymous'}")
            return True, None
        else:
            logger.error(f"Failed to submit feedback from user {username or 'anonymous'}")
            return False, "Failed to save feedback"

    except ValueError as e:
        logger.error(f"Validation error submitting feedback: {e}")
        return False, str(e)
    except DatabaseError:
        raise
    except Exception as e:
        logger.error(f"Error submitting feedback: {e}")
        raise DatabaseError(f"Error submitting feedback: {str(e)}")


def get_feedback_list(
    limit: int = 50,
    offset: int = 0,
    category: Optional[str] = None,
    priority: Optional[str] = None,
    status: Optional[str] = None,
    search: Optional[str] = None
) -> FeedbackData:
    """
    Get a list of feedback messages with pagination and filtering.

    Args:
        limit: Maximum number of feedback messages to return
        offset: Number of messages to skip for pagination
        category: Filter by feedback category
        priority: Filter by priority level
        status: Filter by feedback status
        search: Search in feedback messages

    Returns:
        Dictionary containing feedback list and total count

    Raises:
        ValueError: If pagination parameters are invalid
    """
    try:
        if limit <= 0 or limit > 100:
            limit = 50

        if offset < 0:
            offset = 0

        logger.info(f"Getting feedback list with limit {limit}, offset {offset}")

        # Build WHERE clause for filtering
        where_conditions = []
        params = []

        if category:
            where_conditions.append("category = ?")
            params.append(category)

        if priority:
            where_conditions.append("priority = ?")
            params.append(priority)

        if status:
            where_conditions.append("status = ?")
            params.append(status)

        if search:
            where_conditions.append("message LIKE ?")
            params.append(f"%{search}%")

        where_clause = " AND ".join(where_conditions) if where_conditions else None

        # Get total count
        count_result = select_one(
            "support_feedback",
            columns=["COUNT(*) as total"],
            where=where_clause,
            params=tuple(params) if params else None
        )
        total = count_result.get("total", 0) if count_result else 0

        # Get filtered rows
        rows = select_rows(
            "support_feedback",
            columns=["id", "message", "category", "priority", "status", "user_email", "created_at", "username"],
            where=where_clause,
            params=tuple(params) if params else None,
            order_by="id DESC",
            limit=limit,
            offset=offset
        )

        feedback_list = []
        for row in rows:
            feedback_list.append({
                "id": row.get("id"),
                "message": row.get("message"),
                "category": row.get("category"),
                "priority": row.get("priority"),
                "status": row.get("status"),
                "user_email": row.get("user_email"),
                "created_at": row.get("created_at"),
                "user": row.get("username")
            })

        logger.info(f"Retrieved {len(feedback_list)} feedback messages out of {total} total")
        return {
            "feedback": feedback_list,
            "total": total
        }

    except ValueError as e:
        logger.error(f"Validation error getting feedback list: {e}")
        raise
    except DatabaseError:
        raise
    except Exception as e:
        logger.error(f"Error getting feedback list: {e}")
        raise DatabaseError(f"Error getting feedback list: {str(e)}")


def get_feedback_by_id(feedback_id: int) -> Optional[FeedbackData]:
    """
    Get a specific feedback message by ID.

    Args:
        feedback_id: The feedback message ID

    Returns:
        Feedback message details or None if not found

    Raises:
        ValueError: If feedback_id is invalid
    """
    try:
        if not feedback_id or feedback_id <= 0:
            raise ValueError("Valid feedback ID is required")

        logger.info(f"Getting feedback by ID {feedback_id}")

        row = select_one(
            "support_feedback",
            columns=["id", "message", "username", "created_at"],
            where="id = ?",
            params=(feedback_id,)
        )

        if row:
            feedback = {
                "id": row.get("id"),
                "message": row.get("message"),
                "username": row.get("username"),
                "created_at": row.get("created_at")
            }
            logger.info(f"Retrieved feedback {feedback_id}")
            return feedback
        else:
            logger.warning(f"Feedback {feedback_id} not found")
            return None

    except ValueError as e:
        logger.error(f"Validation error getting feedback by ID: {e}")
        raise
    except DatabaseError:
        raise
    except Exception as e:
        logger.error(f"Error getting feedback by ID {feedback_id}: {e}")
        raise DatabaseError(f"Error getting feedback by ID {feedback_id}: {str(e)}")


def delete_feedback(feedback_id: int) -> Tuple[bool, Optional[str]]:
    """
    Delete a feedback message.

    Args:
        feedback_id: The feedback message ID to delete

    Returns:
        Tuple of (success, error_message)

    Raises:
        ValueError: If feedback_id is invalid
    """
    try:
        if not feedback_id or feedback_id <= 0:
            raise ValueError("Valid feedback ID is required")

        logger.info(f"Deleting feedback {feedback_id}")

        # Check if feedback exists
        existing = get_feedback_by_id(feedback_id)
        if not existing:
            return False, "Feedback not found"

        # Delete the feedback
        success = delete_rows("support_feedback", "WHERE id = ?", (feedback_id,))

        if success:
            logger.info(f"Successfully deleted feedback {feedback_id}")
            return True, None
        else:
            logger.error(f"Failed to delete feedback {feedback_id}")
            return False, "Failed to delete feedback"

    except ValueError as e:
        logger.error(f"Validation error deleting feedback: {e}")
        return False, str(e)
    except DatabaseError:
        raise
    except Exception as e:
        logger.error(f"Error deleting feedback {feedback_id}: {e}")
        raise DatabaseError(f"Error deleting feedback {feedback_id}: {str(e)}")


def get_feedback_statistics() -> FeedbackData:
    """
    Get feedback statistics and analytics.

    Returns:
        Dictionary containing feedback statistics

    Raises:
        Exception: If database error occurs
    """
    try:
        logger.info("Getting feedback statistics")

        # Get total feedback count
        total_feedback = fetch_one("SELECT COUNT(*) as count FROM support_feedback")
        total_count = total_feedback.get("count", 0) if total_feedback else 0

        # Get feedback from last 30 days
        thirty_days_ago = (datetime.utcnow() - timedelta(days=30)).isoformat()
        recent_feedback = fetch_one(
            "SELECT COUNT(*) as count FROM support_feedback WHERE created_at >= ?",
            (thirty_days_ago,)
        )
        recent_count = recent_feedback.get("count", 0) if recent_feedback else 0

        # Get feedback from last 7 days
        seven_days_ago = (datetime.utcnow() - timedelta(days=7)).isoformat()
        weekly_feedback = fetch_one(
            "SELECT COUNT(*) as count FROM support_feedback WHERE created_at >= ?",
            (seven_days_ago,)
        )
        weekly_count = weekly_feedback.get("count", 0) if weekly_feedback else 0

        # Get feedback from today
        today = datetime.utcnow().strftime("%Y-%m-%d")
        today_feedback = fetch_one(
            "SELECT COUNT(*) as count FROM support_feedback WHERE DATE(created_at) = ?",
            (today,)
        )
        today_count = today_feedback.get("count", 0) if today_feedback else 0

        # Get feedback with usernames vs anonymous
        authenticated_feedback = fetch_one(
            "SELECT COUNT(*) as count FROM support_feedback WHERE username IS NOT NULL"
        )
        authenticated_count = authenticated_feedback.get("count", 0) if authenticated_feedback else 0
        anonymous_count = total_count - authenticated_count

        # Calculate average feedback per day (last 30 days)
        avg_per_day = recent_count / 30 if recent_count > 0 else 0

        statistics = {
            "total_feedback": total_count,
            "recent_feedback_30_days": recent_count,
            "recent_feedback_7_days": weekly_count,
            "today_feedback": today_count,
            "authenticated_feedback": authenticated_count,
            "anonymous_feedback": anonymous_count,
            "average_per_day": round(avg_per_day, 2),
            "generated_at": datetime.utcnow().isoformat()
        }

        logger.info(f"Generated feedback statistics: {total_count} total, {recent_count} recent")
        return statistics

    except Exception as e:
        logger.error(f"Error getting feedback statistics: {e}")
        raise DatabaseError(f"Error getting feedback statistics: {str(e)}")


def search_feedback(query: str, limit: int = 20) -> FeedbackList:
    """
    Search through feedback messages.

    Args:
        query: Search query string
        limit: Maximum number of results to return

    Returns:
        List of matching feedback messages

    Raises:
        ValueError: If query is invalid
    """
    try:
        if not query or not query.strip():
            raise ValueError("Search query is required")

        query = query.strip()
        if len(query) < 2:
            raise ValueError("Search query must be at least 2 characters")

        if limit <= 0 or limit > 100:
            limit = 20

        logger.info(f"Searching feedback with query '{query}', limit {limit}")

        # Search in message content
        rows = select_rows(
            "support_feedback",
            columns=["id", "message", "username", "created_at"],
            where="message LIKE ?",
            params=(f"%{query}%",),
            order_by="id DESC",
            limit=limit
        )

        results = []
        for row in rows:
            results.append({
                "id": row.get("id"),
                "message": row.get("message"),
                "username": row.get("username"),
                "created_at": row.get("created_at"),
                "match_type": "message_content"
            })

        logger.info(f"Found {len(results)} feedback messages matching query '{query}'")
        return results

    except ValueError as e:
        logger.error(f"Validation error searching feedback: {e}")
        raise
    except Exception as e:
        logger.error(f"Error searching feedback: {e}")
        raise DatabaseError(f"Error searching feedback: {str(e)}")


def get_user_feedback(username: str, limit: int = 20) -> FeedbackList:
    """
    Get feedback messages from a specific user.

    Args:
        username: The username to get feedback for
        limit: Maximum number of feedback messages to return

    Returns:
        List of feedback messages from the user

    Raises:
        ValueError: If username is invalid
    """
    try:
        if not username:
            raise ValueError("Username is required")

        if limit <= 0 or limit > 100:
            limit = 20

        logger.info(f"Getting feedback for user {username}, limit {limit}")

        rows = select_rows(
            "support_feedback",
            columns=["id", "message", "username", "created_at"],
            where="username = ?",
            params=(username,),
            order_by="id DESC",
            limit=limit
        )

        user_feedback = []
        for row in rows:
            user_feedback.append({
                "id": row.get("id"),
                "message": row.get("message"),
                "username": row.get("username"),
                "created_at": row.get("created_at")
            })

        logger.info(f"Retrieved {len(user_feedback)} feedback messages for user {username}")
        return user_feedback

    except ValueError as e:
        logger.error(f"Validation error getting user feedback: {e}")
        raise
    except Exception as e:
        logger.error(f"Error getting user feedback for {username}: {e}")
        raise DatabaseError(f"Error getting user feedback for {username}: {str(e)}")

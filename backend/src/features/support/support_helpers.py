"""
Support Helper Functions

This module contains helper functions for support and feedback operations that are used
by the support routes but should not be in the route files themselves.

Author: German Class Tool Team
Date: 2025
"""

import logging
from typing import Dict, Any, List, Optional, Tuple

from core.services.import_service import *


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
            'created_at': datetime.datetime.utcnow().isoformat()
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
    except Exception as e:
        logger.error(f"Error submitting feedback: {e}")
        return False, "Database error"


def get_feedback_list(limit: int = 50, offset: int = 0) -> List[Dict[str, Any]]:
    """
    Get a list of feedback messages with pagination.

    Args:
        limit: Maximum number of feedback messages to return
        offset: Number of messages to skip for pagination

    Returns:
        List of feedback messages with details

    Raises:
        ValueError: If pagination parameters are invalid
    """
    try:
        if limit <= 0 or limit > 100:
            limit = 50

        if offset < 0:
            offset = 0

        logger.info(f"Getting feedback list with limit {limit}, offset {offset}")

        rows = select_rows(
            "support_feedback",
            columns=["id", "message", "username", "created_at"],
            order_by="id DESC",
            limit=limit,
            offset=offset
        )

        feedback_list = []
        for row in rows or []:
            feedback_list.append({
                "id": row["id"],
                "message": row["message"],
                "username": row.get("username", "anonymous"),
                "created_at": row["created_at"]
            })

        logger.info(f"Retrieved {len(feedback_list)} feedback messages")
        return feedback_list

    except ValueError as e:
        logger.error(f"Validation error getting feedback list: {e}")
        raise
    except Exception as e:
        logger.error(f"Error getting feedback list: {e}")
        raise


def get_feedback_by_id(feedback_id: int) -> Optional[Dict[str, Any]]:
    """
    Get a specific feedback message by ID.

    Args:
        feedback_id: The feedback message ID to retrieve

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

        if not row:
            logger.warning(f"Feedback with ID {feedback_id} not found")
            return None

        feedback = {
            "id": row["id"],
            "message": row["message"],
            "username": row.get("username", "anonymous"),
            "created_at": row["created_at"]
        }

        logger.info(f"Retrieved feedback with ID {feedback_id}")
        return feedback

    except ValueError as e:
        logger.error(f"Validation error getting feedback by ID: {e}")
        raise
    except Exception as e:
        logger.error(f"Error getting feedback by ID {feedback_id}: {e}")
        raise


def delete_feedback(feedback_id: int) -> Tuple[bool, Optional[str]]:
    """
    Delete a feedback message by ID.

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

        logger.info(f"Deleting feedback with ID {feedback_id}")

        # Check if feedback exists
        existing = select_one(
            "support_feedback",
            columns="1",
            where="id = ?",
            params=(feedback_id,)
        )

        if not existing:
            logger.warning(f"Feedback with ID {feedback_id} not found for deletion")
            return False, "Feedback not found"

        success = delete_rows(
            "support_feedback",
            "WHERE id = ?",
            (feedback_id,)
        )

        if success:
            logger.info(f"Successfully deleted feedback with ID {feedback_id}")
            return True, None
        else:
            logger.error(f"Failed to delete feedback with ID {feedback_id}")
            return False, "Failed to delete feedback"

    except ValueError as e:
        logger.error(f"Validation error deleting feedback: {e}")
        return False, str(e)
    except Exception as e:
        logger.error(f"Error deleting feedback with ID {feedback_id}: {e}")
        return False, "Database error"


def get_feedback_statistics() -> Dict[str, Any]:
    """
    Get statistics about feedback messages.

    Returns:
        Dictionary containing feedback statistics

    Raises:
        Exception: If database error occurs
    """
    try:
        logger.info("Getting feedback statistics")

        # Get total feedback count
        total_row = select_one(
            "support_feedback",
            columns="COUNT(*) as count"
        )
        total_feedback = total_row.get("count", 0) if total_row else 0

        # Get feedback count by user type
        anonymous_row = select_one(
            "support_feedback",
            columns="COUNT(*) as count",
            where="username IS NULL OR username = ''"
        )
        anonymous_feedback = anonymous_row.get("count", 0) if anonymous_row else 0

        registered_feedback = total_feedback - anonymous_feedback

        # Get recent feedback count (last 7 days)
        from datetime import datetime, timedelta
        week_ago = datetime.now() - timedelta(days=7)

        recent_row = select_one(
            "support_feedback",
            columns="COUNT(*) as count",
            where="created_at >= ?",
            params=(week_ago.isoformat(),)
        )
        recent_feedback = recent_row.get("count", 0) if recent_row else 0

        # Get average message length
        avg_length_row = select_one(
            "support_feedback",
            columns="AVG(LENGTH(message)) as avg_length"
        )
        avg_length = round(avg_length_row.get("avg_length", 0), 1) if avg_length_row else 0

        statistics = {
            "total_feedback": total_feedback,
            "anonymous_feedback": anonymous_feedback,
            "registered_feedback": registered_feedback,
            "recent_feedback": recent_feedback,
            "average_message_length": avg_length
        }

        logger.info(f"Retrieved feedback statistics: {statistics}")
        return statistics

    except Exception as e:
        logger.error(f"Error getting feedback statistics: {e}")
        raise


def search_feedback(query: str, limit: int = 20) -> List[Dict[str, Any]]:
    """
    Search feedback messages by content.

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
            raise ValueError("Search query must be at least 2 characters long")

        if limit <= 0 or limit > 50:
            limit = 20

        logger.info(f"Searching feedback with query: '{query}'")

        # Use LIKE for case-insensitive search
        search_pattern = f"%{query}%"

        rows = select_rows(
            "support_feedback",
            columns=["id", "message", "username", "created_at"],
            where="message LIKE ?",
            params=(search_pattern,),
            order_by="id DESC",
            limit=limit
        )

        results = []
        for row in rows or []:
            results.append({
                "id": row["id"],
                "message": row["message"],
                "username": row.get("username", "anonymous"),
                "created_at": row["created_at"]
            })

        logger.info(f"Found {len(results)} feedback messages matching query '{query}'")
        return results

    except ValueError as e:
        logger.error(f"Validation error searching feedback: {e}")
        raise
    except Exception as e:
        logger.error(f"Error searching feedback with query '{query}': {e}")
        raise


def get_user_feedback(username: str, limit: int = 20) -> List[Dict[str, Any]]:
    """
    Get feedback messages submitted by a specific user.

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

        if limit <= 0 or limit > 50:
            limit = 20

        logger.info(f"Getting feedback for user {username}")

        rows = select_rows(
            "support_feedback",
            columns=["id", "message", "created_at"],
            where="username = ?",
            params=(username,),
            order_by="id DESC",
            limit=limit
        )

        feedback_list = []
        for row in rows or []:
            feedback_list.append({
                "id": row["id"],
                "message": row["message"],
                "created_at": row["created_at"]
            })

        logger.info(f"Retrieved {len(feedback_list)} feedback messages for user {username}")
        return feedback_list

    except ValueError as e:
        logger.error(f"Validation error getting user feedback: {e}")
        raise
    except Exception as e:
        logger.error(f"Error getting feedback for user {username}: {e}")
        raise


def create_support_ticket(username: str, subject: str, message: str, priority: str = "normal") -> Tuple[bool, Optional[str], Optional[int]]:
    """
    Create a support ticket for a user.

    Args:
        username: The username creating the ticket
        subject: Ticket subject line
        message: Detailed ticket message
        priority: Ticket priority (low, normal, high, urgent)

    Returns:
        Tuple of (success, error_message, ticket_id)

    Raises:
        ValueError: If required parameters are invalid
    """
    try:
        if not username:
            raise ValueError("Username is required")

        if not subject or not subject.strip():
            raise ValueError("Subject is required")

        if not message or not message.strip():
            raise ValueError("Message is required")

        subject = subject.strip()
        message = message.strip()

        if len(subject) > 200:
            raise ValueError("Subject is too long (maximum 200 characters)")

        if len(message) > 2000:
            raise ValueError("Message is too long (maximum 2000 characters)")

        valid_priorities = ["low", "normal", "high", "urgent"]
        if priority not in valid_priorities:
            priority = "normal"

        logger.info(f"Creating support ticket for user {username} with priority {priority}")

        ticket_data = {
            'username': username,
            'subject': subject,
            'message': message,
            'priority': priority,
            'status': 'open',
            'created_at': datetime.datetime.utcnow().isoformat()
        }

        success = insert_row('support_tickets', ticket_data)

        if success:
            # Get the ticket ID
            ticket_row = select_one(
                "support_tickets",
                columns="id",
                where="username = ? AND subject = ? AND created_at = ?",
                params=(username, subject, ticket_data['created_at'])
            )

            ticket_id = ticket_row.get("id") if ticket_row else None

            logger.info(f"Successfully created support ticket {ticket_id} for user {username}")
            return True, None, ticket_id
        else:
            logger.error(f"Failed to create support ticket for user {username}")
            return False, "Failed to create ticket", None

    except ValueError as e:
        logger.error(f"Validation error creating support ticket: {e}")
        return False, str(e), None
    except Exception as e:
        logger.error(f"Error creating support ticket for user {username}: {e}")
        return False, "Database error", None

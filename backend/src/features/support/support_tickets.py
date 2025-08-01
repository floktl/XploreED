"""
XplorED - Support Tickets Module

This module provides support ticket and request management functions for the XplorED platform,
following clean architecture principles as outlined in the documentation.

Support Tickets Components:
- Ticket Creation: Create support tickets and requests
- Ticket Management: Manage ticket lifecycle and status
- Request Processing: Process support requests and track progress
- Attachment Handling: Handle file attachments for support requests

For detailed architecture information, see: docs/backend_structure.md
"""

import logging
import uuid
from typing import Dict, Any, List, Optional, Tuple

from core.database.connection import select_one, select_rows, insert_row, update_row, delete_rows, fetch_one, fetch_all, fetch_custom, execute_query, get_connection
from datetime import datetime

logger = logging.getLogger(__name__)


def create_support_ticket(username: str, subject: str, message: str, priority: str = "normal", attachments: Optional[List[Any]] = None) -> Tuple[bool, Optional[str], Optional[int]]:
    """
    Create a new support ticket.

    Args:
        username: The username creating the ticket
        subject: The ticket subject
        message: The ticket message
        priority: Ticket priority (low, normal, high, urgent)
        attachments: Optional list of file attachments

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

        # Validate priority
        valid_priorities = ["low", "normal", "high", "urgent"]
        if priority not in valid_priorities:
            priority = "normal"

        logger.info(f"Creating support ticket for user {username} with priority {priority}")

        # Generate unique ticket ID
        ticket_id = str(uuid.uuid4())

        # Create ticket data
        ticket_data = {
            "ticket_id": ticket_id,
            "username": username,
            "subject": subject,
            "message": message,
            "priority": priority,
            "status": "open",
            "created_at": datetime.utcnow().isoformat(),
            "updated_at": datetime.utcnow().isoformat()
        }

        # Add attachments if provided
        if attachments:
            ticket_data["attachments"] = str(attachments)  # Convert to string for storage

        # Insert ticket into database
        success = insert_row("support_tickets", ticket_data)

        if success:
            logger.info(f"Successfully created support ticket {ticket_id} for user {username}")
            return True, None, ticket_id
        else:
            logger.error(f"Failed to create support ticket for user {username}")
            return False, "Failed to create ticket", None

    except ValueError as e:
        logger.error(f"Validation error creating support ticket: {e}")
        return False, str(e), None
    except Exception as e:
        logger.error(f"Error creating support ticket: {e}")
        return False, "Database error", None


def create_support_request(username: str, subject: str, description: str, urgency: str = "medium", contact_method: str = "email", attachments: Optional[List[Any]] = None) -> int:
    """
    Create a new support request.

    Args:
        username: The username creating the request
        subject: The request subject
        description: The request description
        urgency: Request urgency (low, medium, high, critical)
        contact_method: Preferred contact method (email, phone, chat)
        attachments: Optional list of file attachments

    Returns:
        Request ID if successful, -1 otherwise

    Raises:
        ValueError: If required parameters are invalid
    """
    try:
        if not username:
            raise ValueError("Username is required")

        if not subject or not subject.strip():
            raise ValueError("Subject is required")

        if not description or not description.strip():
            raise ValueError("Description is required")

        subject = subject.strip()
        description = description.strip()

        if len(subject) > 200:
            raise ValueError("Subject is too long (maximum 200 characters)")

        if len(description) > 5000:
            raise ValueError("Description is too long (maximum 5000 characters)")

        # Validate urgency
        valid_urgency_levels = ["low", "medium", "high", "critical"]
        if urgency not in valid_urgency_levels:
            urgency = "medium"

        # Validate contact method
        valid_contact_methods = ["email", "phone", "chat"]
        if contact_method not in valid_contact_methods:
            contact_method = "email"

        logger.info(f"Creating support request for user {username} with urgency {urgency}")

        # Create request data
        request_data = {
            "username": username,
            "subject": subject,
            "description": description,
            "urgency": urgency,
            "contact_method": contact_method,
            "status": "pending",
            "created_at": datetime.utcnow().isoformat(),
            "updated_at": datetime.utcnow().isoformat()
        }

        # Add attachments if provided
        if attachments:
            request_data["attachments"] = str(attachments)  # Convert to string for storage

        # Insert request into database
        success = insert_row("support_requests", request_data)

        if success:
            # Get the inserted request ID
            request = select_one(
                "support_requests",
                columns=["id"],
                where="username = ? AND subject = ? AND created_at = ?",
                params=(username, subject, request_data["created_at"])
            )

            request_id = request.get("id") if request else -1

            if request_id != -1:
                logger.info(f"Successfully created support request {request_id} for user {username}")
            else:
                logger.warning(f"Created support request but could not retrieve ID for user {username}")

            return request_id
        else:
            logger.error(f"Failed to create support request for user {username}")
            return -1

    except ValueError as e:
        logger.error(f"Validation error creating support request: {e}")
        raise
    except Exception as e:
        logger.error(f"Error creating support request: {e}")
        return -1


def get_support_request(request_id: int) -> Optional[Dict[str, Any]]:
    """
    Get a support request by ID.

    Args:
        request_id: The support request ID

    Returns:
        Support request details or None if not found

    Raises:
        ValueError: If request_id is invalid
    """
    try:
        if not request_id or request_id <= 0:
            raise ValueError("Valid request ID is required")

        logger.info(f"Getting support request {request_id}")

        row = select_one(
            "support_requests",
            columns=["id", "username", "subject", "description", "urgency", "contact_method", "status", "created_at", "updated_at", "attachments"],
            where="id = ?",
            params=(request_id,)
        )

        if row:
            request = {
                "id": row.get("id"),
                "username": row.get("username"),
                "subject": row.get("subject"),
                "description": row.get("description"),
                "urgency": row.get("urgency"),
                "contact_method": row.get("contact_method"),
                "status": row.get("status"),
                "created_at": row.get("created_at"),
                "updated_at": row.get("updated_at"),
                "attachments": row.get("attachments")
            }
            logger.info(f"Retrieved support request {request_id}")
            return request
        else:
            logger.warning(f"Support request {request_id} not found")
            return None

    except ValueError as e:
        logger.error(f"Validation error getting support request: {e}")
        raise
    except Exception as e:
        logger.error(f"Error getting support request {request_id}: {e}")
        return None


def update_support_request_status(request_id: int, status: str, admin_notes: Optional[str] = None) -> bool:
    """
    Update the status of a support request.

    Args:
        request_id: The support request ID
        status: New status (pending, in_progress, resolved, closed)
        admin_notes: Optional admin notes

    Returns:
        True if update was successful, False otherwise

    Raises:
        ValueError: If parameters are invalid
    """
    try:
        if not request_id or request_id <= 0:
            raise ValueError("Valid request ID is required")

        if not status:
            raise ValueError("Status is required")

        # Validate status
        valid_statuses = ["pending", "in_progress", "resolved", "closed"]
        if status not in valid_statuses:
            raise ValueError(f"Invalid status. Must be one of: {', '.join(valid_statuses)}")

        logger.info(f"Updating support request {request_id} status to {status}")

        # Prepare update data
        update_data = {
            "status": status,
            "updated_at": datetime.utcnow().isoformat()
        }

        if admin_notes:
            update_data["admin_notes"] = admin_notes

        # Update the request
        success = update_row(
            "support_requests",
            update_data,
            "WHERE id = ?",
            (request_id,)
        )

        if success:
            logger.info(f"Successfully updated support request {request_id} status to {status}")
            return True
        else:
            logger.error(f"Failed to update support request {request_id} status")
            return False

    except ValueError as e:
        logger.error(f"Validation error updating support request status: {e}")
        raise
    except Exception as e:
        logger.error(f"Error updating support request {request_id} status: {e}")
        return False


def get_user_support_requests(username: str, limit: int = 20) -> List[Dict[str, Any]]:
    """
    Get support requests for a specific user.

    Args:
        username: The username to get requests for
        limit: Maximum number of requests to return

    Returns:
        List of support requests for the user

    Raises:
        ValueError: If username is invalid
    """
    try:
        if not username:
            raise ValueError("Username is required")

        if limit <= 0 or limit > 100:
            limit = 20

        logger.info(f"Getting support requests for user {username}, limit {limit}")

        rows = select_rows(
            "support_requests",
            columns=["id", "subject", "urgency", "status", "created_at", "updated_at"],
            where="username = ?",
            params=(username,),
            order_by="created_at DESC",
            limit=limit
        )

        user_requests = []
        for row in rows:
            user_requests.append({
                "id": row.get("id"),
                "subject": row.get("subject"),
                "urgency": row.get("urgency"),
                "status": row.get("status"),
                "created_at": row.get("created_at"),
                "updated_at": row.get("updated_at")
            })

        logger.info(f"Retrieved {len(user_requests)} support requests for user {username}")
        return user_requests

    except ValueError as e:
        logger.error(f"Validation error getting user support requests: {e}")
        raise
    except Exception as e:
        logger.error(f"Error getting user support requests for {username}: {e}")
        return []


def get_pending_support_requests(limit: int = 50) -> List[Dict[str, Any]]:
    """
    Get pending support requests for admin review.

    Args:
        limit: Maximum number of requests to return

    Returns:
        List of pending support requests

    Raises:
        ValueError: If limit is invalid
    """
    try:
        if limit <= 0 or limit > 200:
            limit = 50

        logger.info(f"Getting pending support requests, limit {limit}")

        rows = select_rows(
            "support_requests",
            columns=["id", "username", "subject", "urgency", "contact_method", "created_at"],
            where="status = 'pending'",
            order_by="urgency DESC, created_at ASC",
            limit=limit
        )

        pending_requests = []
        for row in rows:
            pending_requests.append({
                "id": row.get("id"),
                "username": row.get("username"),
                "subject": row.get("subject"),
                "urgency": row.get("urgency"),
                "contact_method": row.get("contact_method"),
                "created_at": row.get("created_at")
            })

        logger.info(f"Retrieved {len(pending_requests)} pending support requests")
        return pending_requests

    except ValueError as e:
        logger.error(f"Validation error getting pending support requests: {e}")
        raise
    except Exception as e:
        logger.error(f"Error getting pending support requests: {e}")
        return []

"""
XplorED - Support and Feedback API Routes

This module contains API routes for user support, feedback submission,
and help system functionality, following clean architecture principles
as outlined in the documentation.

Route Categories:
- Feedback Submission: User feedback and bug reports
- Support Requests: Help and support ticket management
- System Status: Application health and status information
- Help Documentation: User guidance and documentation access

Support Features:
- Anonymous feedback submission
- User-specific support requests
- System health monitoring
- Help content delivery

Business Logic:
All support logic has been moved to appropriate helper modules to maintain
separation of concerns and follow clean architecture principles.

For detailed architecture information, see: docs/backend_structure.md
"""

import logging
from typing import Dict, Any, Optional
from datetime import datetime

from flask import request, jsonify # type: ignore
from pydantic import ValidationError
from infrastructure.imports import Imports
from api.middleware.auth import get_current_user, is_admin, require_user
from core.database.connection import select_rows, select_one
from features.support import (
    submit_feedback,
    get_feedback_list,
    get_feedback_by_id,
    delete_feedback,
    get_feedback_statistics,
    search_feedback,
    get_user_feedback,
    create_support_ticket,
    create_support_request,
    get_system_status,
    get_help_content,
    get_help_topics,
    search_help_content,
    get_support_request,
    update_support_request_status,
    get_user_support_requests,
    get_pending_support_requests,
)
from config.blueprint import support_bp
from api.schemas import SupportRequestSchema


# === Logging Configuration ===
logger = logging.getLogger(__name__)


# === Feedback Submission Routes ===

@support_bp.route("/feedback", methods=["POST"])
def submit_feedback_route():
    """
    Submit user feedback or bug report.

    This endpoint allows users to submit feedback, bug reports, or
    feature requests. Feedback can be submitted anonymously or with
    user identification for follow-up.

    Request Body:
        - message (str, required): Feedback message content
        - category (str, optional): Feedback category (bug, feature, general)
        - priority (str, optional): Priority level (low, medium, high, critical)
        - user_email (str, optional): User email for follow-up
        - user_context (str, optional): Additional context information

    Valid Categories:
        - bug: Bug reports and issues
        - feature: Feature requests
        - general: General feedback
        - improvement: Improvement suggestions
        - question: Questions and inquiries

    Valid Priorities:
        - low: Low priority issues
        - medium: Medium priority issues (default)
        - high: High priority issues
        - critical: Critical issues requiring immediate attention

    JSON Response Structure:
        {
            "message": str,                      # Success message
            "feedback_id": int,                  # Feedback identifier
            "submitted_at": str,                 # Submission timestamp
            "status": str                        # Feedback status
        }

    Status Codes:
        - 200: Success
        - 400: Invalid data or validation error
        - 500: Internal server error
    """
    try:
        data = request.get_json()

        if not data:
            return jsonify({"error": "No data provided"}), 400

        message = data.get("message", "").strip()
        category = data.get("category", "general")
        priority = data.get("priority", "medium")
        user_email = data.get("user_email", "").strip()
        user_context = data.get("user_context", "")

        if not message:
            return jsonify({"error": "Feedback message is required"}), 400

        # Validate category
        valid_categories = ["bug", "feature", "general", "improvement", "question"]
        if category not in valid_categories:
            return jsonify({"error": f"Invalid category: {category}"}), 400

        # Validate priority
        valid_priorities = ["low", "medium", "high", "critical"]
        if priority not in valid_priorities:
            return jsonify({"error": f"Invalid priority: {priority}"}), 400

        # Get current user if available
        user = get_current_user()

        # Submit feedback
        success, error_message = submit_feedback(message, user)

        if success:
            return jsonify({
                "message": "Feedback submitted successfully",
                "submitted_at": datetime.now().isoformat(),
                "status": "pending"
            })
        else:
            return jsonify({"error": error_message or "Failed to submit feedback"}), 500

    except Exception as e:
        logger.error(f"Error submitting feedback: {e}")
        return jsonify({"error": "Failed to submit feedback"}), 500


@support_bp.route("/feedback", methods=["GET"])
def get_feedback_route():
    """
    Get feedback list with filtering and pagination.

    This endpoint retrieves feedback submissions with optional filtering
    by category, priority, status, and date range. Admin access required.

    Query Parameters:
        - category (str, optional): Filter by feedback category
        - priority (str, optional): Filter by priority level
        - status (str, optional): Filter by feedback status
        - limit (int, optional): Maximum number of feedback items (default: 20)
        - offset (int, optional): Pagination offset (default: 0)
        - search (str, optional): Search in feedback messages

    JSON Response Structure:
        {
            "feedback": [                        # Array of feedback items
                {
                    "id": int,                   # Feedback identifier
                    "message": str,              # Feedback message
                    "category": str,             # Feedback category
                    "priority": str,             # Priority level
                    "status": str,               # Feedback status
                    "user_email": str,           # User email (if provided)
                    "submitted_at": str,         # Submission timestamp
                    "user": str                  # User identifier (if authenticated)
                }
            ],
            "total": int,                        # Total number of feedback items
            "limit": int,                        # Requested limit
            "offset": int                        # Requested offset
        }

    Status Codes:
        - 200: Success
        - 401: Unauthorized
        - 403: Admin access required
        - 500: Internal server error
    """
    try:
        if not is_admin():
            return jsonify({"error": "Admin access required"}), 403

        # Get query parameters
        category = request.args.get("category")
        priority = request.args.get("priority")
        status = request.args.get("status")
        limit = int(request.args.get("limit", 20))
        offset = int(request.args.get("offset", 0))
        search = request.args.get("search", "").strip()

        # Get feedback list
        feedback_list = get_feedback_list(
            category=category,
            priority=priority,
            status=status,
            limit=limit,
            offset=offset,
            search=search
        )

        return jsonify({
            "feedback": feedback_list.get("feedback", []),
            "total": feedback_list.get("total", 0),
            "limit": limit,
            "offset": offset
        })

    except Exception as e:
        logger.error(f"Error getting feedback: {e}")
        return jsonify({"error": "Failed to retrieve feedback"}), 500


@support_bp.route("/support-request", methods=["POST"])
def create_support_request_route():
    """
    Create a new support request.

    This endpoint allows users to create support requests for
    technical assistance, account issues, or general help.

    Request Body:
        - subject (str, required): Support request subject
        - message (str, required): Detailed description of the issue
        - category (str, optional): Support category (technical, account, billing)
        - priority (str, optional): Priority level (low, medium, high, urgent)
        - attachments (array, optional): File attachments (not implemented)

    Valid Categories:
        - technical: Technical issues and bugs
        - account: Account-related issues
        - billing: Billing and payment issues
        - general: General support requests

    JSON Response Structure:
        {
            "message": str,                      # Success message
            "request_id": int,                   # Support request identifier
            "created_at": str,                   # Creation timestamp
            "status": str                        # Request status
        }

    Status Codes:
        - 200: Success
        - 400: Invalid data
        - 401: Unauthorized
        - 500: Internal server error
    """
    try:
        user = require_user()
        data = request.get_json()

        if not data:
            return jsonify({"error": "No data provided"}), 400

        subject = data.get("subject", "").strip()
        message = data.get("message", "").strip()
        category = data.get("category", "general")
        priority = data.get("priority", "medium")

        if not subject:
            return jsonify({"error": "Subject is required"}), 400

        if not message:
            return jsonify({"error": "Message is required"}), 400

        # Validate category
        valid_categories = ["technical", "account", "billing", "general"]
        if category not in valid_categories:
            return jsonify({"error": f"Invalid category: {category}"}), 400

        # Validate priority
        valid_priorities = ["low", "medium", "high", "urgent"]
        if priority not in valid_priorities:
            return jsonify({"error": f"Invalid priority: {priority}"}), 400

        # Create support request
        request_id = create_support_request(
            username=user,
            subject=subject,
            description=message,
            urgency=priority
        )

        if request_id:
            return jsonify({
                "message": "Support request created successfully",
                "request_id": request_id,
                "created_at": datetime.now().isoformat(),
                "status": "open"
            })
        else:
            return jsonify({"error": "Failed to create support request"}), 500

    except Exception as e:
        logger.error(f"Error creating support request: {e}")
        return jsonify({"error": "Failed to create support request"}), 500


@support_bp.route("/support-request/<int:request_id>", methods=["GET"])
def get_support_request_route(request_id: int):
    """
    Get details of a specific support request.

    This endpoint retrieves detailed information about a support request,
    including messages, status updates, and resolution details.

    Path Parameters:
        - request_id (int, required): Support request identifier

    JSON Response Structure:
        {
            "request": {
                "id": int,                       # Request identifier
                "subject": str,                  # Request subject
                "message": str,                  # Request message
                "category": str,                 # Support category
                "priority": str,                 # Priority level
                "status": str,                   # Request status
                "user": str,                     # User identifier
                "created_at": str,               # Creation timestamp
                "updated_at": str,               # Last update timestamp
                "resolved_at": str               # Resolution timestamp (if resolved)
            },
            "messages": [                        # Support conversation
                {
                    "id": int,                   # Message identifier
                    "message": str,              # Message content
                    "sender": str,               # Sender (user or support)
                    "timestamp": str,            # Message timestamp
                    "is_internal": bool          # Internal note flag
                }
            ]
        }

    Status Codes:
        - 200: Success
        - 401: Unauthorized
        - 403: Access denied
        - 404: Support request not found
        - 500: Internal server error
    """
    try:
        user = require_user()

        # Get support request details
        support_request = get_support_request(request_id)

        if not support_request:
            return jsonify({"error": "Support request not found"}), 404

        return jsonify(support_request)

    except Exception as e:
        logger.error(f"Error getting support request {request_id}: {e}")
        return jsonify({"error": "Failed to retrieve support request"}), 500


@support_bp.route("/status", methods=["GET"])
def get_system_status_route():
    """
    Get system status and health information.

    This endpoint provides information about the system's current
    status, including service availability and performance metrics.

    JSON Response Structure:
        {
            "status": str,                       # Overall system status
            "timestamp": str,                    # Status check timestamp
            "services": {                        # Service status
                "database": str,                 # Database status
                "ai_services": str,              # AI services status
                "translation": str,              # Translation service status
                "tts": str                       # Text-to-speech status
            },
            "performance": {                     # Performance metrics
                "response_time": float,          # Average response time
                "uptime": float,                 # System uptime percentage
                "active_users": int,             # Current active users
                "requests_per_minute": float     # Request rate
            },
            "maintenance": {                     # Maintenance information
                "scheduled_maintenance": bool,   # Scheduled maintenance flag
                "maintenance_window": str,       # Maintenance window
                "notifications": [str]           # System notifications
            }
        }

    Status Codes:
        - 200: Success
        - 500: Internal server error
    """
    try:
        # Get system status
        system_status = get_system_status()

        return jsonify(system_status)

    except Exception as e:
        logger.error(f"Error getting system status: {e}")
        return jsonify({"error": "Failed to retrieve system status"}), 500


@support_bp.route("/help", methods=["GET"])
def get_help_content_route():
    """
    Get help content and documentation.

    This endpoint retrieves help content, tutorials, and documentation
    for users to learn about the platform features.

    Query Parameters:
        - topic (str, optional): Specific help topic
        - search (str, optional): Search in help content
        - category (str, optional): Help content category

    JSON Response Structure:
        {
            "content": [                         # Help content items
                {
                    "id": str,                   # Content identifier
                    "title": str,                # Content title
                    "content": str,              # Content body
                    "category": str,             # Content category
                    "tags": [str],               # Content tags
                    "last_updated": str          # Last update timestamp
                }
            ],
            "categories": [str],                 # Available categories
            "search_results": bool               # Whether results are from search
        }

    Status Codes:
        - 200: Success
        - 500: Internal server error
    """
    try:
        # Get query parameters
        topic = request.args.get("topic")
        search = request.args.get("search", "").strip()
        category = request.args.get("category")

        # Get help content
        if search:
            # Use search function if search parameter is provided
            help_content = search_help_content(search, language="en", limit=10)
        elif topic:
            # Use topic function if topic parameter is provided
            help_content = get_help_content(topic, language="en", format_type="json")
        else:
            # Get all help topics
            help_content = get_help_topics("en")

        return jsonify(help_content)

    except Exception as e:
        logger.error(f"Error getting help content: {e}")
        return jsonify({"error": "Failed to retrieve help content"}), 500


@support_bp.route("/help/topics", methods=["GET"])
def get_help_topics_route():
    """
    Get available help topics and categories.

    This endpoint provides a list of available help topics and categories
    to help users navigate the help system.

    JSON Response Structure:
        {
            "topics": [                          # Available topics
                {
                    "id": str,                   # Topic identifier
                    "title": str,                # Topic title
                    "description": str,          # Topic description
                    "category": str,             # Topic category
                    "article_count": int         # Number of articles
                }
            ],
            "categories": [                      # Available categories
                {
                    "name": str,                 # Category name
                    "description": str,          # Category description
                    "topic_count": int           # Number of topics
                }
            ]
        }

    Status Codes:
        - 200: Success
        - 500: Internal server error
    """
    try:
        # Get help topics
        help_topics = get_help_topics()

        return jsonify(help_topics)

    except Exception as e:
        logger.error(f"Error getting help topics: {e}")
        return jsonify({"error": "Failed to retrieve help topics"}), 500

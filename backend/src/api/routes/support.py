"""
German Class Tool - Support and Feedback API Routes

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
from core.services.import_service import *
from core.utils.helpers import get_current_user, is_admin, require_user
from core.database.connection import select_rows, select_one
from features.support.support_helpers import (
    submit_feedback,
    create_support_request,
    get_system_status,
    get_help_content
)
from api.middleware.session import session_manager
from config.blueprint import support_bp


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
        - message: Feedback message content (required)
        - category: Feedback category (bug, feature, general)
        - priority: Priority level (low, medium, high, critical)
        - user_email: User email for follow-up (optional)
        - user_context: Additional context information (optional)

    Returns:
        JSON response with submission status or error details
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

        # Get current user if authenticated
        user = get_current_user()

        # Submit feedback
        success, error = submit_feedback(
            message=message,
            username=user
        )

        if not success:
            return jsonify({"error": error or "Failed to submit feedback"}), 500

        feedback_id = "feedback_" + str(datetime.now().timestamp())

        return jsonify({
            "message": "Feedback submitted successfully",
            "feedback_id": feedback_id,
            "status": "received"
        })

    except Exception as e:
        logger.error(f"Error submitting feedback: {e}")
        return jsonify({"error": "Failed to submit feedback"}), 500


@support_bp.route("/feedback", methods=["GET"])
def get_feedback_route():
    """
    Retrieve feedback submissions (admin only).

    This endpoint allows administrators to view submitted feedback
    and support requests for review and response.

    Query Parameters:
        - category: Filter by feedback category
        - priority: Filter by priority level
        - status: Filter by processing status
        - limit: Maximum number of results
        - offset: Pagination offset

    Returns:
        JSON response with feedback list or unauthorized error
    """
    try:
        # Check admin privileges
        if not is_admin():
            return jsonify({"error": "Unauthorized"}), 401

        # Get query parameters
        category = request.args.get("category")
        priority = request.args.get("priority")
        status = request.args.get("status", "pending")
        limit = int(request.args.get("limit", 50))
        offset = int(request.args.get("offset", 0))

        # Build query conditions
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

        where_clause = " AND ".join(where_conditions) if where_conditions else "1=1"

        # Fetch feedback
        feedback_list = select_rows(
            "support_feedback",
            columns="id, message, category, priority, status, created_at, user_email, username",
            where=where_clause,
            params=tuple(params),
            order_by="created_at DESC",
            limit=limit
        )

        return jsonify({
            "feedback": feedback_list,
            "total": len(feedback_list),
            "limit": limit,
            "offset": offset
        })

    except Exception as e:
        logger.error(f"Error retrieving feedback: {e}")
        return jsonify({"error": "Failed to retrieve feedback"}), 500


# === Support Request Routes ===
@support_bp.route("/support-request", methods=["POST"])
def create_support_request_route():
    """
    Create a new support request.

    This endpoint allows users to create formal support requests
    for technical issues or account problems.

    Request Body:
        - subject: Support request subject (required)
        - description: Detailed description of the issue (required)
        - urgency: Urgency level (low, medium, high, urgent)
        - contact_method: Preferred contact method (email, phone)
        - attachments: List of file attachments (optional)

    Returns:
        JSON response with request ID and status
    """
    try:
        user = require_user()
        data = request.get_json()

        if not data:
            return jsonify({"error": "No data provided"}), 400

        subject = data.get("subject", "").strip()
        description = data.get("description", "").strip()
        urgency = data.get("urgency", "medium")
        contact_method = data.get("contact_method", "email")
        attachments = data.get("attachments", [])

        if not subject:
            return jsonify({"error": "Subject is required"}), 400

        if not description:
            return jsonify({"error": "Description is required"}), 400

        # Validate urgency
        valid_urgency_levels = ["low", "medium", "high", "urgent"]
        if urgency not in valid_urgency_levels:
            return jsonify({"error": f"Invalid urgency level: {urgency}"}), 400

        # Validate contact method
        valid_contact_methods = ["email", "phone", "chat"]
        if contact_method not in valid_contact_methods:
            return jsonify({"error": f"Invalid contact method: {contact_method}"}), 400

        # Create support request
        request_id = create_support_request(
            username=user,
            subject=subject,
            description=description,
            urgency=urgency,
            contact_method=contact_method,
            attachments=attachments
        )

        return jsonify({
            "message": "Support request created successfully",
            "request_id": request_id,
            "status": "open"
        })

    except Exception as e:
        logger.error(f"Error creating support request: {e}")
        return jsonify({"error": "Failed to create support request"}), 500


@support_bp.route("/support-request/<int:request_id>", methods=["GET"])
def get_support_request_route(request_id: int):
    """
    Retrieve a specific support request.

    This endpoint allows users to view the details of their support
    requests and any responses from the support team.

    Args:
        request_id: Unique identifier of the support request

    Returns:
        JSON response with request details or not found error
    """
    try:
        user = require_user()

        # Fetch support request
        request_data = select_one(
            "support_requests",
            columns="*",
            where="id = ? AND username = ?",
            params=(request_id, user)
        )

        if not request_data:
            return jsonify({"error": "Support request not found"}), 404

        # Fetch responses for this request
        responses = select_rows(
            "support_responses",
            columns="*",
            where="request_id = ?",
            params=(request_id,),
            order_by="created_at ASC"
        )

        return jsonify({
            "request": request_data,
            "responses": responses,
            "total_responses": len(responses)
        })

    except Exception as e:
        logger.error(f"Error retrieving support request {request_id}: {e}")
        return jsonify({"error": "Failed to retrieve support request"}), 500


# === System Status Routes ===
@support_bp.route("/status", methods=["GET"])
def get_system_status_route():
    """
    Get system status and health information.

    This endpoint provides information about the application's
    current status, including database connectivity, external
    service status, and overall system health.

    Returns:
        JSON response with system status information
    """
    try:
        # Get system status
        status_info = get_system_status()

        return jsonify({
            "status": "healthy",
            "timestamp": datetime.now().isoformat(),
            "services": status_info.get("services", {}),
            "database": status_info.get("database", {}),
            "external_apis": status_info.get("external_apis", {}),
            "version": status_info.get("version", "unknown")
        })

    except Exception as e:
        logger.error(f"Error getting system status: {e}")
        return jsonify({
            "status": "unhealthy",
            "timestamp": datetime.now().isoformat(),
            "error": "Failed to retrieve system status"
        }), 500


# === Help Documentation Routes ===
@support_bp.route("/help", methods=["GET"])
def get_help_content_route():
    """
    Retrieve help documentation and user guides.

    This endpoint provides access to help content, user guides,
    and frequently asked questions based on the requested topic.

    Query Parameters:
        - topic: Help topic to retrieve
        - language: Content language preference
        - format: Response format (html, markdown, json)

    Returns:
        JSON response with help content or not found error
    """
    try:
        topic = request.args.get("topic", "general")
        language = request.args.get("language", "en")
        format_type = request.args.get("format", "json")

        # Validate format
        valid_formats = ["html", "markdown", "json"]
        if format_type not in valid_formats:
            return jsonify({"error": f"Invalid format: {format_type}"}), 400

        # Get help content
        content = get_help_content(topic, language, format_type)

        if not content:
            return jsonify({"error": "Help content not found"}), 404

        return jsonify({
            "topic": topic,
            "language": language,
            "format": format_type,
            "content": content,
            "last_updated": datetime.now().isoformat()
        })

    except Exception as e:
        logger.error(f"Error retrieving help content: {e}")
        return jsonify({"error": "Failed to retrieve help content"}), 500


@support_bp.route("/help/topics", methods=["GET"])
def get_help_topics_route():
    """
    Get available help topics and categories.

    This endpoint provides a list of available help topics
    that users can browse for assistance.

    Returns:
        JSON response with available help topics
    """
    try:
        # Get available topics
        topics = [
            {
                "id": "getting-started",
                "title": "Getting Started",
                "description": "Learn how to use the German Class Tool",
                "category": "basics"
            },
            {
                "id": "vocabulary",
                "title": "Vocabulary Learning",
                "description": "How to learn and review vocabulary",
                "category": "learning"
            },
            {
                "id": "grammar",
                "title": "Grammar Exercises",
                "description": "Understanding German grammar concepts",
                "category": "learning"
            },
            {
                "id": "pronunciation",
                "title": "Pronunciation Guide",
                "description": "Tips for correct German pronunciation",
                "category": "learning"
            },
            {
                "id": "troubleshooting",
                "title": "Troubleshooting",
                "description": "Common issues and solutions",
                "category": "support"
            },
            {
                "id": "account",
                "title": "Account Management",
                "description": "Managing your account and settings",
                "category": "account"
            }
        ]

        return jsonify({
            "topics": topics,
            "total": len(topics)
        })

    except Exception as e:
        logger.error(f"Error retrieving help topics: {e}")
        return jsonify({"error": "Failed to retrieve help topics"}), 500

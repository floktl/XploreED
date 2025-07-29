"""
Support Routes

This module contains API routes for user support and feedback management.
All business logic has been moved to appropriate helper modules to maintain
separation of concerns.

Author: German Class Tool Team
Date: 2025
"""

import logging

from core.services.import_service import *
from features.support.support_helpers import (
    submit_feedback,
    get_feedback_list,
    get_feedback_by_id,
    delete_feedback,
    get_feedback_statistics,
    search_feedback,
    get_user_feedback,
    create_support_ticket
)


logger = logging.getLogger(__name__)


@support_bp.route('/feedback', methods=['POST'])
def post_feedback():
    """
    Store a feedback message from any user.

    This endpoint allows both authenticated and anonymous users to submit
    feedback messages for review by administrators.

    Returns:
        JSON response with submission status or error details
    """
    try:
        data = request.get_json() or {}
        message = data.get('message', '').strip()

        if not message:
            return jsonify({'error': 'Message is required and cannot be empty'}), 400

        # Get username if user is authenticated
        username = get_current_user()

        success, error_message = submit_feedback(message, username)

        if not success:
            return jsonify({'error': error_message}), 400

        return jsonify({'status': 'Feedback submitted successfully'})

    except ValueError as e:
        logger.error(f"Validation error posting feedback: {e}")
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        logger.error(f"Error posting feedback: {e}")
        return jsonify({'error': 'Server error'}), 500


@support_bp.route('/feedback', methods=['GET'])
def get_feedback_list_route():
    """
    Get a list of feedback messages (admin only).

    This endpoint provides administrators with access to all feedback
    messages with pagination support.

    Returns:
        JSON response with feedback list or error details
    """
    try:
        if not is_admin():
            return jsonify({'error': 'Unauthorized - Admin access required'}), 401

        # Get pagination parameters
        limit = request.args.get('limit', 50, type=int)
        offset = request.args.get('offset', 0, type=int)

        feedback_list = get_feedback_list(limit, offset)
        return jsonify(feedback_list)

    except ValueError as e:
        logger.error(f"Validation error getting feedback list: {e}")
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        logger.error(f"Error getting feedback list: {e}")
        return jsonify({'error': 'Server error'}), 500


@support_bp.route('/feedback/<int:feedback_id>', methods=['GET'])
def get_feedback_by_id_route(feedback_id):
    """
    Get a specific feedback message by ID (admin only).

    This endpoint allows administrators to retrieve detailed information
    about a specific feedback message.

    Args:
        feedback_id: The feedback message ID to retrieve

    Returns:
        JSON response with feedback details or error details
    """
    try:
        if not is_admin():
            return jsonify({'error': 'Unauthorized - Admin access required'}), 401

        if not feedback_id or feedback_id <= 0:
            return jsonify({'error': 'Valid feedback ID is required'}), 400

        feedback = get_feedback_by_id(feedback_id)

        if not feedback:
            return jsonify({'error': 'Feedback not found'}), 404

        return jsonify(feedback)

    except ValueError as e:
        logger.error(f"Validation error getting feedback by ID: {e}")
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        logger.error(f"Error getting feedback by ID {feedback_id}: {e}")
        return jsonify({'error': 'Server error'}), 500


@support_bp.route('/feedback/<int:feedback_id>', methods=['DELETE'])
def delete_feedback_route(feedback_id):
    """
    Delete a feedback message by ID (admin only).

    This endpoint allows administrators to remove feedback messages
    from the system.

    Args:
        feedback_id: The feedback message ID to delete

    Returns:
        JSON response with deletion status or error details
    """
    try:
        if not is_admin():
            return jsonify({'error': 'Unauthorized - Admin access required'}), 401

        if not feedback_id or feedback_id <= 0:
            return jsonify({'error': 'Valid feedback ID is required'}), 400

        success, error_message = delete_feedback(feedback_id)

        if not success:
            return jsonify({'error': error_message}), 400

        return jsonify({'status': 'Feedback deleted successfully'})

    except ValueError as e:
        logger.error(f"Validation error deleting feedback: {e}")
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        logger.error(f"Error deleting feedback {feedback_id}: {e}")
        return jsonify({'error': 'Server error'}), 500


@support_bp.route('/feedback/statistics', methods=['GET'])
def get_feedback_statistics_route():
    """
    Get feedback statistics (admin only).

    This endpoint provides administrators with comprehensive statistics
    about feedback messages including counts and trends.

    Returns:
        JSON response with feedback statistics or error details
    """
    try:
        if not is_admin():
            return jsonify({'error': 'Unauthorized - Admin access required'}), 401

        statistics = get_feedback_statistics()
        return jsonify(statistics)

    except Exception as e:
        logger.error(f"Error getting feedback statistics: {e}")
        return jsonify({'error': 'Server error'}), 500


@support_bp.route('/feedback/search', methods=['GET'])
def search_feedback_route():
    """
    Search feedback messages by content (admin only).

    This endpoint allows administrators to search through feedback
    messages using text queries.

    Returns:
        JSON response with search results or error details
    """
    try:
        if not is_admin():
            return jsonify({'error': 'Unauthorized - Admin access required'}), 401

        query = request.args.get('q', '').strip()
        limit = request.args.get('limit', 20, type=int)

        if not query:
            return jsonify({'error': 'Search query is required'}), 400

        results = search_feedback(query, limit)
        return jsonify(results)

    except ValueError as e:
        logger.error(f"Validation error searching feedback: {e}")
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        logger.error(f"Error searching feedback: {e}")
        return jsonify({'error': 'Server error'}), 500


@support_bp.route('/feedback/user/<username>', methods=['GET'])
def get_user_feedback_route(username):
    """
    Get feedback messages from a specific user (admin only).

    This endpoint allows administrators to view all feedback
    submitted by a particular user.

    Args:
        username: The username to get feedback for

    Returns:
        JSON response with user feedback or error details
    """
    try:
        if not is_admin():
            return jsonify({'error': 'Unauthorized - Admin access required'}), 401

        if not username:
            return jsonify({'error': 'Username is required'}), 400

        limit = request.args.get('limit', 20, type=int)
        feedback_list = get_user_feedback(username, limit)

        return jsonify({
            'username': username,
            'feedback_count': len(feedback_list),
            'feedback': feedback_list
        })

    except ValueError as e:
        logger.error(f"Validation error getting user feedback: {e}")
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        logger.error(f"Error getting feedback for user {username}: {e}")
        return jsonify({'error': 'Server error'}), 500


@support_bp.route('/ticket', methods=['POST'])
def create_support_ticket_route():
    """
    Create a support ticket for the current user.

    This endpoint allows authenticated users to create support tickets
    with different priority levels for technical assistance.

    Returns:
        JSON response with ticket creation status or error details
    """
    try:
        username = get_current_user()
        if not username:
            return jsonify({'error': 'Authentication required'}), 401

        data = request.get_json() or {}
        subject = data.get('subject', '').strip()
        message = data.get('message', '').strip()
        priority = data.get('priority', 'normal')

        if not subject:
            return jsonify({'error': 'Subject is required'}), 400

        if not message:
            return jsonify({'error': 'Message is required'}), 400

        success, error_message, ticket_id = create_support_ticket(username, subject, message, priority)

        if not success:
            return jsonify({'error': error_message}), 400

        return jsonify({
            'status': 'Support ticket created successfully',
            'ticket_id': ticket_id
        })

    except ValueError as e:
        logger.error(f"Validation error creating support ticket: {e}")
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        logger.error(f"Error creating support ticket: {e}")
        return jsonify({'error': 'Server error'}), 500


@support_bp.route('/help', methods=['GET'])
def get_help_resources():
    """
    Get help resources and documentation.

    This endpoint provides users with access to help documentation,
    FAQs, and support resources.

    Returns:
        JSON response with help resources or error details
    """
    try:
        # This is a placeholder implementation
        # In a real application, you would have help content stored in the database
        help_resources = {
            "faq": [
                {
                    "question": "How do I reset my password?",
                    "answer": "You can reset your password in the settings page."
                },
                {
                    "question": "How do I track my progress?",
                    "answer": "Your progress is automatically tracked and can be viewed in your profile."
                }
            ],
            "contact_info": {
                "email": "support@germanclasstool.com",
                "response_time": "24-48 hours"
            },
            "documentation": {
                "user_guide": "/docs/user-guide",
                "api_documentation": "/docs/api"
            }
        }

        return jsonify(help_resources)

    except Exception as e:
        logger.error(f"Error getting help resources: {e}")
        return jsonify({'error': 'Server error'}), 500

"""
Settings Routes

This module contains API routes for user account settings and preferences management.
All business logic has been moved to appropriate helper modules to maintain
separation of concerns.

Author: German Class Tool Team
Date: 2025
"""

import logging
from typing import Dict, Any

from core.services.import_service import *
from features.settings.settings_helpers import (
    update_user_password,
    deactivate_user_account,
    debug_delete_user_data,
    get_user_settings,
    update_user_settings
)
from features.settings.settings_helpers import get_account_statistics  # type: ignore


logger = logging.getLogger(__name__)


@settings_bp.route('/password', methods=['POST'])
def update_password_route():
    """
    Change the logged in user's password.

    This endpoint allows users to update their password with proper validation
    including current password verification and new password requirements.

    Returns:
        JSON response with update status or error details
    """
    try:
        username = get_current_user()
        if not username:
            return jsonify({'error': 'Unauthorized'}), 401

        data = request.get_json() or {}
        current_password = data.get('current_password', '')
        new_password = data.get('new_password', '')

        if not current_password or not new_password:
            return jsonify({'error': 'Missing current_password or new_password'}), 400

        success, error_message = update_user_password(username, current_password, new_password)

        if not success:
            return jsonify({'error': error_message}), 400

        return jsonify({'msg': 'Password updated successfully'})

    except Exception as e:
        logger.error(f"Error updating password: {e}")
        return jsonify({'error': 'Server error'}), 500


@settings_bp.route('/deactivate', methods=['POST'])
def deactivate_account_route():
    """
    Delete all data for the current user and deactivate their account.

    This endpoint permanently deletes all user data including AI data,
    vocabulary, game results, and account information. This action is irreversible.

    Returns:
        JSON response with deactivation status or error details
    """
    try:
        username = get_current_user()
        if not username:
            return jsonify({'error': 'Unauthorized'}), 401

        success, error_message, deletion_stats = deactivate_user_account(username)

        if not success:
            return jsonify({'error': error_message}), 400

        # Clear session cookie
        resp = make_response(jsonify({
            'message': 'Account deactivated successfully',
            'deletion_stats': deletion_stats
        }))
        resp.set_cookie('session_id', '', max_age=0)

        return resp

    except Exception as e:
        logger.error(f"Error deactivating account: {e}")
        return jsonify({'error': 'Server error'}), 500


@settings_bp.route('/debug-delete-user-data', methods=['POST'])
def debug_delete_user_data_route():
    """
    Debug function to delete all user data except core account information.

    This endpoint is for debugging purposes and deletes all user data
    from any table with a username or user_id column, except protected tables.

    Returns:
        JSON response with deletion status or error details
    """
    try:
        username = get_current_user()
        if not username:
            return jsonify({'error': 'Unauthorized'}), 401

        success, error_message, affected_tables = debug_delete_user_data(username)

        if not success:
            return jsonify({'error': error_message}), 400

        tables_str = ', '.join(affected_tables) if affected_tables else 'none'
        return jsonify({
            'status': f'All user data deleted from tables: {tables_str} (except name, password, and session).'
        })

    except Exception as e:
        logger.error(f"Error debug deleting user data: {e}")
        return jsonify({'error': 'Server error'}), 500


@settings_bp.route('/settings', methods=['GET'])
def get_settings():
    """
    Get user settings and preferences.

    This endpoint retrieves the current user's settings including
    account information, preferences, and configuration options.

    Returns:
        JSON response with user settings or error details
    """
    try:
        username = get_current_user()
        if not username:
            return jsonify({'error': 'Unauthorized'}), 401

        settings = get_user_settings(username)
        return jsonify(settings)

    except ValueError as e:
        logger.error(f"Validation error getting settings: {e}")
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        logger.error(f"Error getting settings: {e}")
        return jsonify({'error': 'Server error'}), 500


@settings_bp.route('/settings', methods=['PUT'])
def update_settings():
    """
    Update user settings and preferences.

    This endpoint allows users to update their preferences and settings
    including language, theme, notifications, and difficulty level.

    Returns:
        JSON response with update status or error details
    """
    try:
        username = get_current_user()
        if not username:
            return jsonify({'error': 'Unauthorized'}), 401

        data = request.get_json() or {}
        if not data:
            return jsonify({'error': 'No settings data provided'}), 400

        success, error_message = update_user_settings(username, data)

        if not success:
            return jsonify({'error': error_message}), 400

        return jsonify({'msg': 'Settings updated successfully'})

    except ValueError as e:
        logger.error(f"Validation error updating settings: {e}")
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        logger.error(f"Error updating settings: {e}")
        return jsonify({'error': 'Server error'}), 500


@settings_bp.route('/account-statistics', methods=['GET'])
def get_account_statistics():
    """
    Get comprehensive account statistics for the current user.

    This endpoint provides detailed statistics about the user's account
    including data usage, account age, and record counts across all tables.

    Returns:
        JSON response with account statistics or error details
    """
    try:
        username = get_current_user()
        if not username:
            return jsonify({'error': 'Unauthorized'}), 401

        statistics = get_account_statistics(str(username))  # type: ignore
        return jsonify(statistics)

    except ValueError as e:
        logger.error(f"Validation error getting account statistics: {e}")
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        logger.error(f"Error getting account statistics: {e}")
        return jsonify({'error': 'Server error'}), 500


@settings_bp.route('/export-data', methods=['GET'])
def export_user_data():
    """
    Export all user data in a structured format.

    This endpoint allows users to export their data for backup purposes
    or data portability in compliance with data protection regulations.

    Returns:
        JSON response with exported data or error details
    """
    try:
        username = get_current_user()
        if not username:
            return jsonify({'error': 'Unauthorized'}), 401

        # Get account statistics first
        statistics = get_account_statistics(str(username))  # type: ignore

        # Get user settings
        settings = get_user_settings(username)

        # Get game results
        from features.profile.profile_helpers import get_user_game_results
        game_results = get_user_game_results(username)

        # Get vocabulary data
        from features.user.vocabulary_helpers import get_user_vocabulary_entries
        vocabulary = get_user_vocabulary_entries(username)

        # Compile export data
        export_data = {
            "export_date": datetime.datetime.utcnow().isoformat(),
            "user_info": {
                "username": username,
                "account_statistics": statistics,
                "settings": settings
            },
            "data": {
                "game_results": game_results,
                "vocabulary": vocabulary
            }
        }

        return jsonify(export_data)

    except ValueError as e:
        logger.error(f"Validation error exporting user data: {e}")
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        logger.error(f"Error exporting user data: {e}")
        return jsonify({'error': 'Server error'}), 500


@settings_bp.route('/privacy-settings', methods=['GET'])
def get_privacy_settings():
    """
    Get user privacy settings and data usage preferences.

    This endpoint retrieves privacy-related settings including
    data collection preferences and sharing permissions.

    Returns:
        JSON response with privacy settings or error details
    """
    try:
        username = get_current_user()
        if not username:
            return jsonify({'error': 'Unauthorized'}), 401

        # This is a placeholder implementation
        # In a real application, you would have privacy settings stored in the database
        privacy_settings = {
            "data_collection": True,
            "analytics_tracking": True,
            "personalized_content": True,
            "data_sharing": False,
            "marketing_emails": False
        }

        return jsonify({
            "username": username,
            "privacy_settings": privacy_settings
        })

    except Exception as e:
        logger.error(f"Error getting privacy settings: {e}")
        return jsonify({'error': 'Server error'}), 500


@settings_bp.route('/privacy-settings', methods=['PUT'])
def update_privacy_settings():
    """
    Update user privacy settings and data usage preferences.

    This endpoint allows users to control their privacy settings
    including data collection, analytics, and sharing preferences.

    Returns:
        JSON response with update status or error details
    """
    try:
        username = get_current_user()
        if not username:
            return jsonify({'error': 'Unauthorized'}), 401

        data = request.get_json() or {}
        if not data:
            return jsonify({'error': 'No privacy settings data provided'}), 400

        # Validate privacy settings
        valid_settings = [
            "data_collection", "analytics_tracking", "personalized_content",
            "data_sharing", "marketing_emails"
        ]

        for key in data.keys():
            if key not in valid_settings:
                return jsonify({'error': f'Invalid privacy setting: {key}'}), 400

        # This is a placeholder implementation
        # In a real application, you would update privacy settings in the database
        logger.info(f"Updated privacy settings for user {username}: {data}")

        return jsonify({'msg': 'Privacy settings updated successfully'})

    except Exception as e:
        logger.error(f"Error updating privacy settings: {e}")
        return jsonify({'error': 'Server error'}), 500

"""
XplorED - Lesson Management API Routes

This module contains API routes for lesson content management and delivery,
following clean architecture principles as outlined in the documentation.

Route Categories:
- Lesson Content: Lesson creation, retrieval, and management
- Lesson Progress: User progress tracking and completion
- Lesson Blocks: Interactive block management and content
- Lesson Publishing: Content publishing and availability control
- Lesson Analytics: Usage statistics and performance metrics

Lesson Features:
- Dynamic lesson content creation and management
- Interactive block system for exercises and activities
- Progress tracking and completion management
- Content publishing and access control
- Usage analytics and performance insights

Business Logic:
All lesson logic has been moved to appropriate helper modules to maintain
separation of concerns and follow clean architecture principles.

For detailed architecture information, see: docs/backend_structure.md
"""

import logging
from typing import Dict, Any, Optional, List
from datetime import datetime

from flask import request, jsonify # type: ignore
from core.services.import_service import *
from core.utils.helpers import get_current_user, require_user
from core.database.connection import select_one, select_rows, insert_row, update_row
from config.blueprint import lessons_bp
from features.lessons.lesson_helpers import (
    get_user_lessons_summary,
    get_lesson_content,
    get_lesson_progress,
    update_lesson_progress,
    get_lesson_statistics,
    validate_lesson_access,
    get_lesson_blocks,
    update_lesson_content,
    publish_lesson,
    get_lesson_analytics
)
from core.utils.helpers import is_admin


# === Logging Configuration ===
logger = logging.getLogger(__name__)


# === Lesson Content Routes ===
@lessons_bp.route("/lessons", methods=["GET"])
def get_lessons_route():
    """
    Get available lessons for the current user.

    This endpoint retrieves lessons that are available to the user
    based on their skill level and access permissions.

    Query Parameters:
        - skill_level: Filter by skill level
        - published: Filter by publication status
        - limit: Maximum number of lessons to return
        - offset: Pagination offset

    Returns:
        JSON response with lesson list or unauthorized error
    """
    try:
        user = get_current_user()
        if not user:
            return jsonify({"error": "Unauthorized"}), 401

        # Get query parameters
        skill_level = request.args.get("skill_level")
        published = request.args.get("published", "true").lower() == "true"
        limit = int(request.args.get("limit", 20))
        offset = int(request.args.get("offset", 0))

        # Build query conditions
        where_conditions = []
        params = []

        if skill_level:
            where_conditions.append("skill_level = ?")
            params.append(skill_level)

        if published:
            where_conditions.append("published = 1")

        where_clause = " AND ".join(where_conditions) if where_conditions else "1=1"

        # Get lessons
        lessons = select_rows(
            "lesson_content",
            columns="id, lesson_id, title, skill_level, num_blocks, published, created_at",
            where=where_clause,
            params=tuple(params),
            order_by="created_at DESC",
            limit=limit
        )

        return jsonify({
            "lessons": lessons,
            "total": len(lessons),
            "limit": limit,
            "offset": offset
        })

    except Exception as e:
        logger.error(f"Error getting lessons: {e}")
        return jsonify({"error": "Failed to retrieve lessons"}), 500


@lessons_bp.route("/lessons/<int:lesson_id>", methods=["GET"])
def get_lesson_route(lesson_id: int):
    """
    Get detailed lesson content by ID.

    This endpoint retrieves the complete lesson content including
    all interactive blocks and metadata.

    Args:
        lesson_id: Unique identifier of the lesson

    Returns:
        JSON response with lesson content or not found error
    """
    try:
        user = get_current_user()
        if not user:
            return jsonify({"error": "Unauthorized"}), 401

        # Get lesson content
        lesson = select_one(
            "lesson_content",
            columns="*",
            where="lesson_id = ?",
            params=(lesson_id,)
        )

        if not lesson:
            return jsonify({"error": "Lesson not found"}), 404

        # Get lesson blocks
        blocks = get_lesson_blocks(lesson_id)

        # Get user progress for this lesson
        progress = select_rows(
            "lesson_progress",
            columns="block_id, completed, updated_at",
            where="user_id = ? AND lesson_id = ?",
            params=(user, lesson_id)
        )

        return jsonify({
            "lesson": lesson,
            "blocks": blocks,
            "user_progress": progress,
            "total_blocks": len(blocks),
            "completed_blocks": len([p for p in progress if p.get("completed")])
        })

    except Exception as e:
        logger.error(f"Error getting lesson {lesson_id}: {e}")
        return jsonify({"error": "Failed to retrieve lesson"}), 500


@lessons_bp.route("/lessons", methods=["POST"])
def create_lesson_route():
    """
    Create a new lesson (admin only).

    This endpoint allows administrators to create new lesson content
    with interactive blocks and metadata.

    Request Body:
        - title: Lesson title
        - content: Lesson content (HTML)
        - skill_level: Target skill level
        - num_blocks: Number of interactive blocks
        - ai_enabled: Enable AI features for this lesson

    Returns:
        JSON response with created lesson or unauthorized error
    """
    try:
        # Check admin privileges
        if not is_admin():
            return jsonify({"error": "Unauthorized - Admin access required"}), 401

        data = request.get_json()

        if not data:
            return jsonify({"error": "No data provided"}), 400

        title = data.get("title", "").strip()
        content = data.get("content", "").strip()
        skill_level = data.get("skill_level", 1)
        num_blocks = data.get("num_blocks", 0)
        ai_enabled = data.get("ai_enabled", False)

        if not title:
            return jsonify({"error": "Lesson title is required"}), 400

        if not content:
            return jsonify({"error": "Lesson content is required"}), 400

        # Validate skill level
        if not isinstance(skill_level, int) or skill_level < 1 or skill_level > 10:
            return jsonify({"error": "Skill level must be between 1 and 10"}), 400

        # Create lesson content
        lesson_data = {
            "title": title,
            "content": content,
            "skill_level": skill_level,
            "num_blocks": num_blocks,
            "ai_enabled": ai_enabled,
            "published": False,
            "created_at": datetime.now().isoformat()
        }

        lesson_id = create_lesson_content(lesson_data)

        if lesson_id:
            return jsonify({
                "message": "Lesson created successfully",
                "lesson_id": lesson_id
            })
        else:
            return jsonify({"error": "Failed to create lesson"}), 500

    except Exception as e:
        logger.error(f"Error creating lesson: {e}")
        return jsonify({"error": "Failed to create lesson"}), 500


@lessons_bp.route("/lessons/<int:lesson_id>", methods=["PUT"])
def update_lesson_route(lesson_id: int):
    """
    Update an existing lesson (admin only).

    This endpoint allows administrators to update lesson content
    and metadata.

    Args:
        lesson_id: Unique identifier of the lesson to update

    Request Body:
        - title: Updated lesson title
        - content: Updated lesson content
        - skill_level: Updated skill level
        - num_blocks: Updated number of blocks
        - ai_enabled: Updated AI feature flag

    Returns:
        JSON response with update status or error details
    """
    try:
        # Check admin privileges
        if not is_admin():
            return jsonify({"error": "Unauthorized - Admin access required"}), 401

        data = request.get_json()

        if not data:
            return jsonify({"error": "No data provided"}), 400

        # Check if lesson exists
        existing_lesson = select_one(
            "lesson_content",
            columns="id",
            where="lesson_id = ?",
            params=(lesson_id,)
        )

        if not existing_lesson:
            return jsonify({"error": "Lesson not found"}), 404

        # Prepare updates
        updates = {}

        if "title" in data:
            title = data["title"].strip()
            if title:
                updates["title"] = title
            else:
                return jsonify({"error": "Title cannot be empty"}), 400

        if "content" in data:
            content = data["content"].strip()
            if content:
                updates["content"] = content
            else:
                return jsonify({"error": "Content cannot be empty"}), 400

        if "skill_level" in data:
            skill_level = data["skill_level"]
            if isinstance(skill_level, int) and 1 <= skill_level <= 10:
                updates["skill_level"] = skill_level
            else:
                return jsonify({"error": "Skill level must be between 1 and 10"}), 400

        if "num_blocks" in data:
            num_blocks = data["num_blocks"]
            if isinstance(num_blocks, int) and num_blocks >= 0:
                updates["num_blocks"] = num_blocks
            else:
                return jsonify({"error": "Number of blocks must be non-negative"}), 400

        if "ai_enabled" in data:
            updates["ai_enabled"] = bool(data["ai_enabled"])

        if not updates:
            return jsonify({"error": "No valid updates provided"}), 400

        # Update lesson
        success = update_lesson_content(lesson_id, updates)

        if success:
            return jsonify({
                "message": "Lesson updated successfully",
                "updated_fields": list(updates.keys())
            })
        else:
            return jsonify({"error": "Failed to update lesson"}), 500

    except Exception as e:
        logger.error(f"Error updating lesson {lesson_id}: {e}")
        return jsonify({"error": "Failed to update lesson"}), 500


# === Lesson Progress Routes ===
@lessons_bp.route("/lessons/<int:lesson_id>/progress", methods=["GET"])
def get_lesson_progress_route(lesson_id: int):
    """
    Get user progress for a specific lesson.

    This endpoint retrieves the user's progress through a lesson
    including completed blocks and overall completion status.

    Args:
        lesson_id: Unique identifier of the lesson

    Returns:
        JSON response with progress data or unauthorized error
    """
    try:
        user = require_user()

        # Check if lesson exists
        lesson = select_one(
            "lesson_content",
            columns="id, title, num_blocks",
            where="lesson_id = ?",
            params=(lesson_id,)
        )

        if not lesson:
            return jsonify({"error": "Lesson not found"}), 404

        # Get user progress
        progress = select_rows(
            "lesson_progress",
            columns="block_id, completed, updated_at",
            where="user_id = ? AND lesson_id = ?",
            params=(user, lesson_id)
        )

        # Calculate completion statistics
        total_blocks = lesson.get("num_blocks", 0)
        completed_blocks = len([p for p in progress if p.get("completed")])
        completion_percentage = (completed_blocks / total_blocks * 100) if total_blocks > 0 else 0

        return jsonify({
            "lesson_id": lesson_id,
            "lesson_title": lesson.get("title"),
            "total_blocks": total_blocks,
            "completed_blocks": completed_blocks,
            "completion_percentage": round(completion_percentage, 2),
            "progress": progress,
            "last_updated": max([p.get("updated_at") for p in progress]) if progress else None
        })

    except Exception as e:
        logger.error(f"Error getting lesson progress for lesson {lesson_id}: {e}")
        return jsonify({"error": "Failed to retrieve lesson progress"}), 500


@lessons_bp.route("/lessons/<int:lesson_id>/progress", methods=["POST"])
def update_lesson_progress_route(lesson_id: int):
    """
    Update user progress for a lesson block.

    This endpoint allows users to mark lesson blocks as completed
    and track their progress through the lesson.

    Args:
        lesson_id: Unique identifier of the lesson

    Request Body:
        - block_id: Identifier of the completed block
        - completed: Completion status (true/false)

    Returns:
        JSON response with update status or error details
    """
    try:
        user = require_user()
        data = request.get_json()

        if not data:
            return jsonify({"error": "No data provided"}), 400

        block_id = data.get("block_id")
        completed = data.get("completed", True)

        if not block_id:
            return jsonify({"error": "Block ID is required"}), 400

        # Check if lesson exists
        lesson = select_one(
            "lesson_content",
            columns="id",
            where="lesson_id = ?",
            params=(lesson_id,)
        )

        if not lesson:
            return jsonify({"error": "Lesson not found"}), 404

        # Update or insert progress
        existing_progress = select_one(
            "lesson_progress",
            columns="id",
            where="user_id = ? AND lesson_id = ? AND block_id = ?",
            params=(user, lesson_id, block_id)
        )

        if existing_progress:
            # Update existing progress
            success = update_row(
                "lesson_progress",
                {"completed": completed, "updated_at": datetime.now().isoformat()},
                "WHERE user_id = ? AND lesson_id = ? AND block_id = ?",
                (user, lesson_id, block_id)
            )
        else:
            # Insert new progress
            success = insert_row("lesson_progress", {
                "user_id": user,
                "lesson_id": lesson_id,
                "block_id": block_id,
                "completed": completed,
                "updated_at": datetime.now().isoformat()
            })

        if success:
            return jsonify({
                "message": "Progress updated successfully",
                "block_id": block_id,
                "completed": completed
            })
        else:
            return jsonify({"error": "Failed to update progress"}), 500

    except Exception as e:
        logger.error(f"Error updating lesson progress for lesson {lesson_id}: {e}")
        return jsonify({"error": "Failed to update lesson progress"}), 500


# === Lesson Publishing Routes ===
@lessons_bp.route("/lessons/<int:lesson_id>/publish", methods=["POST"])
def publish_lesson_route(lesson_id: int):
    """
    Publish or unpublish a lesson (admin only).

    This endpoint allows administrators to control lesson availability
    by publishing or unpublishing lessons.

    Args:
        lesson_id: Unique identifier of the lesson

    Request Body:
        - published: Publication status (true/false)

    Returns:
        JSON response with publication status or error details
    """
    try:
        # Check admin privileges
        if not is_admin():
            return jsonify({"error": "Unauthorized - Admin access required"}), 401

        data = request.get_json()

        if not data:
            return jsonify({"error": "No data provided"}), 400

        published = data.get("published", True)

        # Check if lesson exists
        lesson = select_one(
            "lesson_content",
            columns="id, title",
            where="lesson_id = ?",
            params=(lesson_id,)
        )

        if not lesson:
            return jsonify({"error": "Lesson not found"}), 404

        # Update publication status
        success = publish_lesson(lesson_id, published)

        if success:
            status = "published" if published else "unpublished"
            return jsonify({
                "message": f"Lesson {status} successfully",
                "lesson_id": lesson_id,
                "lesson_title": lesson.get("title"),
                "published": published
            })
        else:
            return jsonify({"error": "Failed to update publication status"}), 500

    except Exception as e:
        logger.error(f"Error publishing lesson {lesson_id}: {e}")
        return jsonify({"error": "Failed to update publication status"}), 500


# === Lesson Analytics Routes ===
@lessons_bp.route("/lessons/<int:lesson_id>/analytics", methods=["GET"])
def get_lesson_analytics_route(lesson_id: int):
    """
    Get analytics for a specific lesson (admin only).

    This endpoint provides detailed analytics about lesson usage
    including completion rates, user engagement, and performance metrics.

    Args:
        lesson_id: Unique identifier of the lesson

    Query Parameters:
        - timeframe: Analytics timeframe (week, month, year)
        - include_details: Include detailed user data

    Returns:
        JSON response with lesson analytics or unauthorized error
    """
    try:
        # Check admin privileges
        if not is_admin():
            return jsonify({"error": "Unauthorized - Admin access required"}), 401

        # Get query parameters
        timeframe = request.args.get("timeframe", "month")
        include_details = request.args.get("include_details", "false").lower() == "true"

        # Check if lesson exists
        lesson = select_one(
            "lesson_content",
            columns="id, title, skill_level, num_blocks",
            where="lesson_id = ?",
            params=(lesson_id,)
        )

        if not lesson:
            return jsonify({"error": "Lesson not found"}), 404

        # Get lesson analytics
        analytics = get_lesson_analytics(lesson_id, timeframe)

        # Add lesson metadata
        analytics["lesson"] = {
            "id": lesson_id,
            "title": lesson.get("title"),
            "skill_level": lesson.get("skill_level"),
            "total_blocks": lesson.get("num_blocks", 0)
        }

        # Add detailed user data if requested
        if include_details:
            user_progress = select_rows(
                "lesson_progress",
                columns="user_id, block_id, completed, updated_at",
                where="lesson_id = ?",
                params=(lesson_id,)
            )
            analytics["user_details"] = user_progress

        return jsonify({
            "lesson_id": lesson_id,
            "timeframe": timeframe,
            "analytics": analytics,
            "generated_at": datetime.now().isoformat()
        })

    except Exception as e:
        logger.error(f"Error getting analytics for lesson {lesson_id}: {e}")
        return jsonify({"error": "Failed to retrieve lesson analytics"}), 500

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
from typing import Optional, List
from datetime import datetime

from flask import request, jsonify # type: ignore
from infrastructure.imports import Imports
from api.middleware.auth import get_current_user, require_user
from core.database.connection import select_one, select_rows, insert_row, update_row
from config.blueprint import lessons_bp
from core.services import LessonService
from features.lessons import (
    validate_block_completion,
    update_lesson_content,
    publish_lesson,
    get_lesson_analytics,
)
from api.middleware.auth import is_admin
from shared.exceptions import DatabaseError


# === Logging Configuration ===
logger = logging.getLogger(__name__)


# === Lesson Content Routes ===

@lessons_bp.route("/lesson/<int:lesson_id>", methods=["GET"])
def get_lesson_single_route(lesson_id: int):
    """
    Get detailed lesson content by ID (frontend-compatible route).

    This endpoint retrieves the complete lesson content including
    all blocks and interactive elements. This is a frontend-compatible
    version of the /lessons/{lesson_id} route.

    Path Parameters:
        - lesson_id (int, required): Unique identifier of the lesson

    JSON Response Structure:
        {
            "title": str,                       # Lesson title
            "content": str,                     # Lesson content (HTML)
            "created_at": str,                  # Creation timestamp
            "num_blocks": int,                  # Number of blocks
            "ai_enabled": bool                  # AI features enabled
        }

    Status Codes:
        - 200: Success
        - 401: Unauthorized
        - 404: Lesson not found
        - 500: Internal server error
    """
    try:
        user = get_current_user()
        if not user:
            return jsonify({"error": "Unauthorized"}), 401

        # Get lesson details
        lesson = select_one(
            "lesson_content",
            columns="title, content, created_at, num_blocks, ai_enabled",
            where="lesson_id = ? AND (target_user IS NULL OR target_user = ?) AND published = 1",
            params=(lesson_id, user)
        )

        if not lesson:
            return jsonify({"error": "Lesson not found"}), 404

        return jsonify({
            "title": lesson["title"],
            "content": lesson["content"],
            "created_at": lesson["created_at"],
            "num_blocks": lesson["num_blocks"],
            "ai_enabled": bool(lesson["ai_enabled"])
        })

    except DatabaseError as e:
        logger.error(f"Error getting lesson content: {e}")
        return jsonify({"error": "Internal server error"}), 500


@lessons_bp.route("/lesson-progress/<int:lesson_id>", methods=["GET"])
def get_lesson_progress_single_route(lesson_id: int):
    """
    Get user progress for a specific lesson (frontend-compatible route).

    This endpoint retrieves the current user's progress through a specific lesson.
    This is a frontend-compatible version of the /lessons/{lesson_id}/progress route.

    Path Parameters:
        - lesson_id (int, required): Unique identifier of the lesson

    JSON Response Structure:
        {
            "lesson_id": int,                   # Lesson identifier
            "user": str,                        # User identifier
            "progress": {
                "completed_blocks": int,        # Number of completed blocks
                "total_blocks": int,            # Total number of blocks
                "completion_percentage": float, # Completion percentage
                "last_activity": str,           # Last activity timestamp
                "is_completed": bool            # Overall completion status
            },
            "block_progress": [                 # Individual block progress
                {
                    "block_id": str,            # Block identifier
                    "completed": bool,          # Completion status
                    "completed_at": str,        # Completion timestamp
                    "time_spent": int,          # Time spent in seconds
                    "score": float              # Performance score
                }
            ]
        }

    Status Codes:
        - 200: Success
        - 401: Unauthorized
        - 404: Lesson not found
        - 500: Internal server error
    """
    try:
        user = require_user()

        # Check if lesson exists
        lesson = select_one(
            "lesson_content",
            columns="id, num_blocks",
            where="lesson_id = ?",
            params=(lesson_id,)
        )

        if not lesson:
            return jsonify({"error": "Lesson not found"}), 404

        # Get user progress for this lesson
        progress_rows = select_rows(
            "lesson_progress",
            columns="*",
            where="user_id = ? AND lesson_id = ?",
            params=(user, lesson_id)
        )

        # Calculate completion
        completed_blocks = len([p for p in progress_rows if p.get("completed")])
        total_blocks = lesson.get("num_blocks", 0)

        # For lessons with no interactive blocks but AI exercises enabled, check AI exercise completion
        if total_blocks == 0:
            # Check if AI exercises are enabled
            lesson_details = select_one(
                "lesson_content",
                columns="ai_enabled",
                where="lesson_id = ?",
                params=(lesson_id,)
            )
            ai_enabled = lesson_details.get("ai_enabled", 0) if lesson_details else 0

            if ai_enabled:
                # Check if AI exercises are completed
                ai_progress = [p for p in progress_rows if "ai" in p.get("block_id", "")]
                completion_percentage = 100.0 if ai_progress and all(p.get("completed") for p in ai_progress) else 0.0
                is_completed = bool(ai_progress and all(p.get("completed") for p in ai_progress))
            else:
                # No blocks and no AI exercises - student must manually mark as complete
                # Check if there's a manual completion record
                manual_completion = select_one(
                    "lesson_progress",
                    columns="completed",
                    where="user_id = ? AND lesson_id = ? AND block_id = 'manual_completion'",
                    params=(user, lesson_id)
                )
                completion_percentage = 100.0 if manual_completion and manual_completion.get("completed") else 0.0
                is_completed = bool(manual_completion and manual_completion.get("completed"))
        else:
            completion_percentage = (completed_blocks / total_blocks * 100) if total_blocks > 0 else 0
            is_completed = completed_blocks >= total_blocks

        # Convert to frontend-expected format: { "block_id": completed_boolean }
        progress_dict = {}
        for progress_row in progress_rows:
            block_id = progress_row.get("block_id")
            completed = bool(progress_row.get("completed"))
            if block_id:
                progress_dict[block_id] = completed

        return jsonify(progress_dict)

    except DatabaseError as e:
        logger.error(f"Error getting lesson progress for lesson {lesson_id}: {e}")
        return jsonify({"error": "Internal server error"}), 500


@lessons_bp.route("/lesson-completed", methods=["POST"])
def check_lesson_completed_route():
    """
    Check if a lesson is completed by the current user (frontend-compatible route).

    This endpoint checks whether the current user has completed a specific lesson.

    Request Body:
        - lesson_id (int, required): Unique identifier of the lesson

    JSON Response Structure:
        {
            "lesson_id": int,                   # Lesson identifier
            "user": str,                        # User identifier
            "is_completed": bool,               # Completion status
            "completed_at": str,                # Completion timestamp
            "completion_percentage": float      # Completion percentage
        }

    Status Codes:
        - 200: Success
        - 400: Invalid request data
        - 401: Unauthorized
        - 404: Lesson not found
        - 500: Internal server error
    """
    try:
        user = require_user()
        data = request.get_json()

        if not data or "lesson_id" not in data:
            return jsonify({"error": "Lesson ID is required"}), 400

        lesson_id = int(data["lesson_id"])

        # Check if lesson exists
        lesson = select_one(
            "lesson_content",
            columns="id, num_blocks",
            where="lesson_id = ?",
            params=(lesson_id,)
        )

        if not lesson:
            return jsonify({"error": "Lesson not found"}), 404

        # Get user progress for this lesson
        progress_rows = select_rows(
            "lesson_progress",
            columns="*",
            where="user_id = ? AND lesson_id = ?",
            params=(user, lesson_id)
        )

        # Calculate completion
        completed_blocks = len([p for p in progress_rows if p.get("completed")])
        total_blocks = lesson.get("num_blocks", 0)

        # For lessons with no interactive blocks but AI exercises enabled, check AI exercise completion
        if total_blocks == 0:
            # Check if AI exercises are enabled
            lesson_details = select_one(
                "lesson_content",
                columns="ai_enabled",
                where="lesson_id = ?",
                params=(lesson_id,)
            )
            ai_enabled = lesson_details.get("ai_enabled", 0) if lesson_details else 0

            if ai_enabled:
                # Check if AI exercises are completed
                ai_progress = [p for p in progress_rows if "ai" in p.get("block_id", "")]
                completion_percentage = 100.0 if ai_progress and all(p.get("completed") for p in ai_progress) else 0.0
                is_completed = bool(ai_progress and all(p.get("completed") for p in ai_progress))
            else:
                # No blocks and no AI exercises - student must manually mark as complete
                # Check if there's a manual completion record
                manual_completion = select_one(
                    "lesson_progress",
                    columns="completed",
                    where="user_id = ? AND lesson_id = ? AND block_id = 'manual_completion'",
                    params=(user, lesson_id)
                )
                completion_percentage = 100.0 if manual_completion and manual_completion.get("completed") else 0.0
                is_completed = bool(manual_completion and manual_completion.get("completed"))
        else:
            completion_percentage = (completed_blocks / total_blocks * 100) if total_blocks > 0 else 0
            is_completed = completed_blocks >= total_blocks

        # Get completion timestamp
        completed_at = None
        if is_completed and progress_rows:
            last_completed = max(progress_rows, key=lambda x: x.get("updated_at", ""))
            completed_at = last_completed.get("updated_at")

        return jsonify({
            "lesson_id": lesson_id,
            "user": user,
            "is_completed": is_completed,
            "completed_at": completed_at,
            "completion_percentage": round(completion_percentage, 2)
        })

    except ValueError as e:
        logger.error(f"Invalid lesson ID: {e}")
        return jsonify({"error": "Invalid lesson ID"}), 400
    except DatabaseError as e:
        logger.error(f"Error checking lesson completion: {e}")
        return jsonify({"error": "Internal server error"}), 500


@lessons_bp.route("/mark-as-completed", methods=["POST"])
def mark_lesson_completed_route():
    """
    Mark a lesson as completed by the current user (frontend-compatible route).

    This endpoint marks a specific lesson as completed for the current user.

    Request Body:
        - lesson_id (int, required): Unique identifier of the lesson

    JSON Response Structure:
        {
            "lesson_id": int,                   # Lesson identifier
            "user": str,                        # User identifier
            "is_completed": bool,               # Completion status
            "completed_at": str,                # Completion timestamp
            "message": str                      # Success message
        }

    Status Codes:
        - 200: Success
        - 400: Invalid request data
        - 401: Unauthorized
        - 404: Lesson not found
        - 500: Internal server error
    """
    try:
        user = require_user()
        data = request.get_json()

        if not data or "lesson_id" not in data:
            return jsonify({"error": "Lesson ID is required"}), 400

        lesson_id = int(data["lesson_id"])

        # Check if lesson exists
        lesson = select_one(
            "lesson_content",
            columns="id, num_blocks",
            where="lesson_id = ?",
            params=(lesson_id,)
        )

        if not lesson:
            return jsonify({"error": "Lesson not found"}), 404

        # Mark all blocks as completed for this lesson
        total_blocks = lesson.get("num_blocks", 0)
        current_time = datetime.now().isoformat()

        if total_blocks == 0:
            # For lessons with no blocks, create a manual completion record
            existing_manual_completion = select_one(
                "lesson_progress",
                columns="id",
                where="user_id = ? AND lesson_id = ? AND block_id = 'manual_completion'",
                params=(user, lesson_id)
            )

            if existing_manual_completion:
                # Update existing manual completion record
                update_row(
                    "lesson_progress",
                    {
                        "completed": True,
                        "updated_at": current_time
                    },
                    "user_id = ? AND lesson_id = ? AND block_id = 'manual_completion'",
                    (user, lesson_id)
                )
            else:
                # Create new manual completion record
                insert_row("lesson_progress", {
                    "user_id": user,
                    "lesson_id": lesson_id,
                    "block_id": "manual_completion",
                    "completed": True,
                    "updated_at": current_time
                })
        else:
            # Get existing blocks for this lesson
            existing_blocks = select_rows(
                "lesson_blocks",
                columns="block_id",
                where="lesson_id = ?",
                params=(lesson_id,)
            )

            # Mark each block as completed
            for block in existing_blocks:
                block_id = block["block_id"]

                # Check if progress record exists
                existing_progress = select_one(
                    "lesson_progress",
                    columns="id",
                    where="user_id = ? AND lesson_id = ? AND block_id = ?",
                    params=(user, lesson_id, block_id)
                )

                if existing_progress:
                    # Update existing progress
                    update_row(
                        "lesson_progress",
                        {
                            "completed": True,
                            "updated_at": current_time
                        },
                        "user_id = ? AND lesson_id = ? AND block_id = ?",
                        (user, lesson_id, block_id)
                    )
                else:
                    # Create new progress record
                    insert_row("lesson_progress", {
                        "user_id": user,
                        "lesson_id": lesson_id,
                        "block_id": block_id,
                        "completed": True,
                        "updated_at": current_time
                    })

        return jsonify({
            "lesson_id": lesson_id,
            "user": user,
            "is_completed": True,
            "completed_at": current_time,
            "message": "Lesson marked as completed successfully"
        })

    except ValueError as e:
        logger.error(f"Invalid lesson ID: {e}")
        return jsonify({"error": "Invalid lesson ID"}), 400
    except DatabaseError as e:
        logger.error(f"Error marking lesson as completed: {e}")
        return jsonify({"error": "Internal server error"}), 500


@lessons_bp.route("/lesson-progress", methods=["POST"])
def update_lesson_progress_single_route():
    """
    Update lesson block progress for the current user (frontend-compatible route).

    This endpoint updates the progress status of a specific block within a lesson.

    Request Body:
        - lesson_id (int, required): Unique identifier of the lesson
        - block_id (str, required): Unique identifier of the block
        - completed (bool, required): Whether the block is completed

    JSON Response Structure:
        {
            "lesson_id": int,                   # Lesson identifier
            "block_id": str,                    # Block identifier
            "user": str,                        # User identifier
            "completed": bool,                  # Completion status
            "updated_at": str,                  # Update timestamp
            "message": str                      # Success message
        }

    Status Codes:
        - 200: Success
        - 400: Invalid request data
        - 401: Unauthorized
        - 404: Lesson or block not found
        - 500: Internal server error
    """
    try:
        user = require_user()
        data = request.get_json()

        if not data:
            return jsonify({"error": "Request data is required"}), 400

        lesson_id = data.get("lesson_id")
        block_id = data.get("block_id")
        completed = data.get("completed")

        if lesson_id is None or block_id is None or completed is None:
            return jsonify({"error": "lesson_id, block_id, and completed are required"}), 400

        lesson_id = int(lesson_id)
        completed = bool(completed)

        # Check if lesson exists
        lesson = select_one(
            "lesson_content",
            columns="id",
            where="lesson_id = ?",
            params=(lesson_id,)
        )

        if not lesson:
            return jsonify({"error": "Lesson not found"}), 404

        # Check if block exists
        block = select_one(
            "lesson_blocks",
            columns="block_id",
            where="lesson_id = ? AND block_id = ?",
            params=(lesson_id, block_id)
        )

        if not block:
            return jsonify({"error": "Block not found"}), 404

        current_time = datetime.now().isoformat()

        # Check if progress record exists
        existing_progress = select_one(
            "lesson_progress",
            columns="id",
            where="user_id = ? AND lesson_id = ? AND block_id = ?",
            params=(user, lesson_id, block_id)
        )

        if existing_progress:
            # Update existing progress
            update_row(
                "lesson_progress",
                {
                    "completed": completed,
                    "updated_at": current_time
                },
                "user_id = ? AND lesson_id = ? AND block_id = ?",
                (user, lesson_id, block_id)
            )
        else:
            # Create new progress record
            insert_row("lesson_progress", {
                "user_id": user,
                "lesson_id": lesson_id,
                "block_id": block_id,
                "completed": completed,
                "updated_at": current_time
            })

        return jsonify({
            "lesson_id": lesson_id,
            "block_id": block_id,
            "user": user,
            "completed": completed,
            "updated_at": current_time,
            "message": f"Block progress updated successfully"
        })

    except ValueError as e:
        logger.error(f"Invalid request data: {e}")
        return jsonify({"error": "Invalid request data"}), 400
    except DatabaseError as e:
        logger.error(f"Error updating lesson progress: {e}")
        return jsonify({"error": "Internal server error"}), 500


@lessons_bp.route("/lessons", methods=["GET"])
def get_lessons_route():
    """
    Get available lessons for the current user.

    This endpoint retrieves lessons that are available to the user
    based on their skill level and access permissions.

    Query Parameters:
        - skill_level (str, optional): Filter by skill level
        - published (bool, optional): Filter by publication status (default: true)
        - limit (int, optional): Maximum number of lessons to return (default: 20)
        - offset (int, optional): Pagination offset (default: 0)

    JSON Response Structure:
        {
            "lessons": [                        # Array of lessons
                {
                    "id": int,                  # Lesson identifier
                    "lesson_id": int,           # Lesson ID
                    "title": str,               # Lesson title
                    "skill_level": str,         # Skill level
                    "num_blocks": int,          # Number of blocks
                    "published": bool,          # Publication status
                    "created_at": str           # Creation timestamp
                }
            ],
            "total": int,                       # Total number of lessons
            "limit": int,                       # Requested limit
            "offset": int                       # Requested offset
        }

    Status Codes:
        - 200: Success
        - 401: Unauthorized
        - 500: Internal server error
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
            limit=limit,
            offset=offset
        )

        # Get user progress for each lesson
        for lesson in lessons:
            lesson_id = lesson["lesson_id"]

            # Get user progress for this lesson
            progress_rows = select_rows(
                "lesson_progress",
                columns="*",
                where="user_id = ? AND lesson_id = ?",
                params=(user, lesson_id)
            )

            # Calculate completion
            completed_blocks = len([p for p in progress_rows if p.get("completed")])
            total_blocks = lesson.get("num_blocks", 0)

            # For lessons with no interactive blocks but AI exercises enabled, check AI exercise completion
            if total_blocks == 0:
                # Check if AI exercises are enabled
                ai_enabled = lesson.get("ai_enabled", 0)

                if ai_enabled:
                    # Check if AI exercises are completed
                    ai_progress = [p for p in progress_rows if "ai" in p.get("block_id", "")]
                    completion_percentage = 100.0 if ai_progress and all(p.get("completed") for p in ai_progress) else 0.0
                    is_completed = bool(ai_progress and all(p.get("completed") for p in ai_progress))
                else:
                    # No blocks and no AI exercises - student must manually mark as complete
                    # Check if there's a manual completion record
                    manual_completion = select_one(
                        "lesson_progress",
                        columns="completed",
                        where="user_id = ? AND lesson_id = ? AND block_id = 'manual_completion'",
                        params=(user, lesson_id)
                    )
                    completion_percentage = 100.0 if manual_completion and manual_completion.get("completed") else 0.0
                    is_completed = bool(manual_completion and manual_completion.get("completed"))
            else:
                completion_percentage = (completed_blocks / total_blocks * 100) if total_blocks > 0 else 0
                is_completed = completed_blocks >= total_blocks

            # Add progress information to lesson
            lesson["completed"] = is_completed
            lesson["percent_complete"] = round(completion_percentage, 2)
            lesson["last_attempt"] = progress_rows[-1].get("updated_at") if progress_rows else None

        # Get total count
        total_lessons = select_one(
            "lesson_content",
            columns="COUNT(*) as total",
            where=where_clause,
            params=tuple(params)
        )

        return jsonify({
            "lessons": lessons,
            "total": total_lessons.get("total", 0) if total_lessons else 0,
            "limit": limit,
            "offset": offset
        })

    except DatabaseError as e:
        logger.error(f"Error getting user lessons: {e}")
        return jsonify({"error": "Internal server error"}), 500


@lessons_bp.route("/lessons/<int:lesson_id>", methods=["GET"])
def get_lesson_route(lesson_id: int):
    """
    Get detailed lesson content by ID.

    This endpoint retrieves the complete lesson content including
    all blocks and interactive elements.

    Path Parameters:
        - lesson_id (int, required): Unique identifier of the lesson

    JSON Response Structure:
        {
            "lesson": {
                "id": int,                      # Lesson identifier
                "lesson_id": int,               # Lesson ID
                "title": str,                   # Lesson title
                "description": str,             # Lesson description
                "skill_level": str,             # Skill level
                "num_blocks": int,              # Number of blocks
                "published": bool,              # Publication status
                "created_at": str,              # Creation timestamp
                "updated_at": str               # Last update timestamp
            },
            "blocks": [                         # Lesson blocks
                {
                    "id": str,                  # Block identifier
                    "block_type": str,          # Type of block
                    "content": str,             # Block content
                    "order": int,               # Block order
                    "metadata": {}              # Block metadata
                }
            ]
        }

    Status Codes:
        - 200: Success
        - 401: Unauthorized
        - 404: Lesson not found
        - 500: Internal server error
    """
    try:
        user = get_current_user()
        if not user:
            return jsonify({"error": "Unauthorized"}), 401

        # Get lesson details
        lesson = select_one(
            "lesson_content",
            columns="*",
            where="lesson_id = ?",
            params=(lesson_id,)
        )

        if not lesson:
            return jsonify({"error": "Lesson not found"}), 404

        # Get lesson blocks
        blocks = select_rows(
            "lesson_blocks",
            columns="*",
            where="lesson_id = ?",
            params=(lesson_id,),
            order_by="block_order ASC"
        )

        return jsonify({
            "lesson": lesson,
            "blocks": blocks
        })

    except DatabaseError as e:
        logger.error(f"Error getting lesson content: {e}")
        return jsonify({"error": "Internal server error"}), 500


@lessons_bp.route("/lessons", methods=["POST"])
def create_lesson_route():
    """
    Create a new lesson.

    This endpoint creates a new lesson with the provided content
    and metadata. Admin access required.

    Request Body:
        - title (str, required): Lesson title
        - description (str, optional): Lesson description
        - skill_level (str, required): Target skill level
        - blocks (array, optional): Array of lesson blocks
        - published (bool, optional): Publication status (default: false)

    Block Structure:
        [
            {
                "block_type": str,              # Type of block
                "content": str,                 # Block content
                "order": int,                   # Block order
                "metadata": {}                  # Block metadata
            }
        ]

    JSON Response Structure:
        {
            "message": str,                     # Success message
            "lesson": {
                "id": int,                      # Created lesson ID
                "lesson_id": int,               # Lesson identifier
                "title": str,                   # Lesson title
                "created_at": str               # Creation timestamp
            }
        }

    Status Codes:
        - 200: Success
        - 400: Invalid data
        - 401: Unauthorized
        - 403: Admin access required
        - 500: Internal server error
    """
    try:
        if not is_admin():
            return jsonify({"error": "Admin access required"}), 403

        data = request.get_json()

        if not data:
            return jsonify({"error": "No data provided"}), 400

        title = data.get("title", "").strip()
        description = data.get("description", "").strip()
        skill_level = data.get("skill_level", "").strip()
        blocks = data.get("blocks", [])
        published = data.get("published", False)

        if not title:
            return jsonify({"error": "Title is required"}), 400

        if not skill_level:
            return jsonify({"error": "Skill level is required"}), 400

        # Create lesson
        lesson_data = {
            "title": title,
            "description": description,
            "skill_level": skill_level,
            "num_blocks": len(blocks),
            "published": published,
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat()
        }

        lesson_id = insert_row("lesson_content", lesson_data)

        if not lesson_id:
            return jsonify({"error": "Failed to create lesson"}), 500

        # Create blocks if provided
        if blocks:
            for block in blocks:
                block_data = {
                    "lesson_id": lesson_id,
                    "block_type": block.get("block_type", "text"),
                    "content": block.get("content", ""),
                    "block_order": block.get("order", 0),
                    "metadata": str(block.get("metadata", {}))
                }
                insert_row("lesson_blocks", block_data)

        return jsonify({
            "message": "Lesson created successfully",
            "lesson": {
                "id": lesson_id,
                "lesson_id": lesson_id,
                "title": title,
                "created_at": lesson_data["created_at"]
            }
        })

    except DatabaseError as e:
        logger.error(f"Error creating lesson: {e}")
        return jsonify({"error": "Internal server error"}), 500


@lessons_bp.route("/lessons/<int:lesson_id>", methods=["PUT"])
def update_lesson_route(lesson_id: int):
    """
    Update an existing lesson.

    This endpoint updates lesson content and metadata.
    Admin access required.

    Path Parameters:
        - lesson_id (int, required): Unique identifier of the lesson

    Request Body:
        - title (str, optional): Lesson title
        - description (str, optional): Lesson description
        - skill_level (str, optional): Target skill level
        - blocks (array, optional): Array of lesson blocks
        - published (bool, optional): Publication status

    JSON Response Structure:
        {
            "message": str,                     # Success message
            "lesson": {
                "id": int,                      # Lesson ID
                "title": str,                   # Updated title
                "updated_at": str               # Update timestamp
            }
        }

    Status Codes:
        - 200: Success
        - 400: Invalid data
        - 401: Unauthorized
        - 403: Admin access required
        - 404: Lesson not found
        - 500: Internal server error
    """
    try:
        if not is_admin():
            return jsonify({"error": "Admin access required"}), 403

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

        # Prepare update data
        update_data = {"updated_at": datetime.now().isoformat()}

        if "title" in data:
            update_data["title"] = data["title"].strip()

        if "description" in data:
            update_data["description"] = data["description"].strip()

        if "skill_level" in data:
            update_data["skill_level"] = data["skill_level"].strip()

        if "published" in data:
            update_data["published"] = data["published"]

        # Update lesson
        success = update_row(
            "lesson_content",
            update_data,
            "WHERE lesson_id = ?",
            (lesson_id,)
        )

        if not success:
            return jsonify({"error": "Failed to update lesson"}), 500

        # Update blocks if provided
        if "blocks" in data:
            blocks = data["blocks"]
            update_data["num_blocks"] = len(blocks)

            # Delete existing blocks
            update_row(
                "lesson_blocks",
                {"deleted": True},
                "WHERE lesson_id = ?",
                (lesson_id,)
            )

            # Create new blocks
            for block in blocks:
                block_data = {
                    "lesson_id": lesson_id,
                    "block_type": block.get("block_type", "text"),
                    "content": block.get("content", ""),
                    "block_order": block.get("order", 0),
                    "metadata": str(block.get("metadata", {}))
                }
                insert_row("lesson_blocks", block_data)

            # Update block count
            update_row(
                "lesson_content",
                {"num_blocks": len(blocks)},
                "WHERE lesson_id = ?",
                (lesson_id,)
            )

        return jsonify({
            "message": "Lesson updated successfully",
            "lesson": {
                "id": lesson_id,
                "title": update_data.get("title", "Updated"),
                "updated_at": update_data["updated_at"]
            }
        })

    except DatabaseError as e:
        logger.error(f"Error updating lesson {lesson_id}: {e}")
        return jsonify({"error": "Internal server error"}), 500


@lessons_bp.route("/lessons/<int:lesson_id>/progress", methods=["GET"])
def get_lesson_progress_route(lesson_id: int):
    """
    Get user progress for a specific lesson.

    This endpoint retrieves the current user's progress
    through a specific lesson.

    Path Parameters:
        - lesson_id (int, required): Unique identifier of the lesson

    JSON Response Structure:
        {
            "lesson_id": int,                   # Lesson identifier
            "user": str,                        # User identifier
            "progress": {
                "completed_blocks": int,        # Number of completed blocks
                "total_blocks": int,            # Total number of blocks
                "completion_percentage": float, # Completion percentage
                "last_activity": str,           # Last activity timestamp
                "is_completed": bool            # Overall completion status
            },
            "block_progress": [                 # Individual block progress
                {
                    "block_id": str,            # Block identifier
                    "completed": bool,          # Completion status
                    "completed_at": str,        # Completion timestamp
                    "time_spent": int,          # Time spent in seconds
                    "score": float              # Performance score
                }
            ]
        }

    Status Codes:
        - 200: Success
        - 401: Unauthorized
        - 404: Lesson not found
        - 500: Internal server error
    """
    try:
        user = require_user()

        # Check if lesson exists
        lesson = select_one(
            "lesson_content",
            columns="id, num_blocks",
            where="lesson_id = ?",
            params=(lesson_id,)
        )

        if not lesson:
            return jsonify({"error": "Lesson not found"}), 404

        # Get user progress
        progress = select_one(
            "lesson_progress",
            columns="*",
            where="user = ? AND lesson_id = ?",
            params=(user, lesson_id)
        )

        # Get block progress
        block_progress = select_rows(
            "block_progress",
            columns="*",
            where="user = ? AND lesson_id = ?",
            params=(user, lesson_id),
            order_by="block_id ASC"
        )

        # Calculate completion
        completed_blocks = len([b for b in block_progress if b.get("completed")])
        total_blocks = lesson.get("num_blocks", 0)
        completion_percentage = (completed_blocks / total_blocks * 100) if total_blocks > 0 else 0

        return jsonify({
            "lesson_id": lesson_id,
            "user": user,
            "progress": {
                "completed_blocks": completed_blocks,
                "total_blocks": total_blocks,
                "completion_percentage": round(completion_percentage, 2),
                "last_activity": progress.get("updated_at") if progress else None,
                "is_completed": completed_blocks >= total_blocks
            },
            "block_progress": block_progress
        })

    except DatabaseError as e:
        logger.error(f"Error getting lesson progress for lesson {lesson_id}: {e}")
        return jsonify({"error": "Internal server error"}), 500


@lessons_bp.route("/lessons/<int:lesson_id>/progress", methods=["POST"])
def update_lesson_progress_route(lesson_id: int):
    """
    Update user progress for a specific lesson.

    This endpoint updates the user's progress through a lesson,
    typically when completing blocks or activities.

    Path Parameters:
        - lesson_id (int, required): Unique identifier of the lesson

    Request Body:
        - block_id (str, required): Block identifier
        - completed (bool, optional): Completion status (default: true)
        - time_spent (int, optional): Time spent in seconds
        - score (float, optional): Performance score

    JSON Response Structure:
        {
            "message": str,                     # Success message
            "lesson_id": int,                   # Lesson identifier
            "block_id": str,                    # Block identifier
            "completed": bool,                  # Completion status
            "updated_at": str                   # Update timestamp
        }

    Status Codes:
        - 200: Success
        - 400: Invalid data
        - 401: Unauthorized
        - 404: Lesson not found
        - 500: Internal server error
    """
    try:
        user = require_user()
        data = request.get_json()

        if not data:
            return jsonify({"error": "No data provided"}), 400

        block_id = data.get("block_id")
        completed = data.get("completed", True)
        time_spent = data.get("time_spent")
        score = data.get("score")

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

        # Update block progress
        progress_data = {
            "user": user,
            "lesson_id": lesson_id,
            "block_id": block_id,
            "completed": completed,
            "updated_at": datetime.now().isoformat()
        }

        if time_spent is not None:
            progress_data["time_spent"] = time_spent

        if score is not None:
            progress_data["score"] = score

        # Check if progress record exists
        existing_progress = select_one(
            "block_progress",
            columns="id",
            where="user = ? AND lesson_id = ? AND block_id = ?",
            params=(user, lesson_id, block_id)
        )

        if existing_progress:
            # Update existing progress
            success = update_row(
                "block_progress",
                progress_data,
                "WHERE user = ? AND lesson_id = ? AND block_id = ?",
                (user, lesson_id, block_id)
            )
        else:
            # Create new progress record
            success = insert_row("block_progress", progress_data)

        if not success:
            return jsonify({"error": "Failed to update progress"}), 500

        return jsonify({
            "message": "Progress updated successfully",
            "lesson_id": lesson_id,
            "block_id": block_id,
            "completed": completed,
            "updated_at": progress_data["updated_at"]
        })

    except DatabaseError as e:
        logger.error(f"Error updating lesson progress for lesson {lesson_id}: {e}")
        return jsonify({"error": "Internal server error"}), 500


@lessons_bp.route("/lessons/<int:lesson_id>/publish", methods=["POST"])
def publish_lesson_route(lesson_id: int):
    """
    Publish or unpublish a lesson.

    This endpoint controls the publication status of a lesson,
    making it available or unavailable to users.
    Admin access required.

    Path Parameters:
        - lesson_id (int, required): Unique identifier of the lesson

    Request Body:
        - published (bool, required): Publication status

    JSON Response Structure:
        {
            "message": str,                     # Success message
            "lesson_id": int,                   # Lesson identifier
            "published": bool,                  # Publication status
            "updated_at": str                   # Update timestamp
        }

    Status Codes:
        - 200: Success
        - 400: Invalid data
        - 401: Unauthorized
        - 403: Admin access required
        - 404: Lesson not found
        - 500: Internal server error
    """
    try:
        if not is_admin():
            return jsonify({"error": "Admin access required"}), 403

        data = request.get_json()

        if not data:
            return jsonify({"error": "No data provided"}), 400

        published = data.get("published")

        if published is None:
            return jsonify({"error": "Published status is required"}), 400

        # Check if lesson exists
        lesson = select_one(
            "lesson_content",
            columns="id",
            where="lesson_id = ?",
            params=(lesson_id,)
        )

        if not lesson:
            return jsonify({"error": "Lesson not found"}), 404

        # Update publication status
        success = update_row(
            "lesson_content",
            {
                "published": published,
                "updated_at": datetime.now().isoformat()
            },
            "WHERE lesson_id = ?",
            (lesson_id,)
        )

        if not success:
            return jsonify({"error": "Failed to update lesson"}), 500

        return jsonify({
            "message": f"Lesson {'published' if published else 'unpublished'} successfully",
            "lesson_id": lesson_id,
            "published": published,
            "updated_at": datetime.now().isoformat()
        })

    except DatabaseError as e:
        logger.error(f"Error publishing lesson {lesson_id}: {e}")
        return jsonify({"error": "Internal server error"}), 500


@lessons_bp.route("/lessons/<int:lesson_id>/analytics", methods=["GET"])
def get_lesson_analytics_route(lesson_id: int):
    """
    Get analytics for a specific lesson.

    This endpoint retrieves usage statistics and performance
    metrics for a specific lesson.
    Admin access required.

    Path Parameters:
        - lesson_id (int, required): Unique identifier of the lesson

    Query Parameters:
        - timeframe (str, optional): Analytics timeframe (week, month, all)

    JSON Response Structure:
        {
            "lesson_id": int,                   # Lesson identifier
            "analytics": {
                "total_users": int,             # Total users who accessed lesson
                "completion_rate": float,       # Overall completion rate
                "average_time": float,          # Average completion time
                "average_score": float,         # Average performance score
                "user_engagement": {            # User engagement metrics
                    "daily_active": int,       # Daily active users
                    "weekly_active": int,      # Weekly active users
                    "monthly_active": int      # Monthly active users
                },
                "block_performance": [          # Block-level performance
                    {
                        "block_id": str,       # Block identifier
                        "completion_rate": float, # Block completion rate
                        "average_time": float, # Average time spent
                        "average_score": float # Average score
                    }
                ]
            },
            "timeframe": str,                   # Requested timeframe
            "generated_at": str                 # Analytics generation timestamp
        }

    Status Codes:
        - 200: Success
        - 401: Unauthorized
        - 403: Admin access required
        - 404: Lesson not found
        - 500: Internal server error
    """
    try:
        if not is_admin():
            return jsonify({"error": "Admin access required"}), 403

        # Check if lesson exists
        lesson = select_one(
            "lesson_content",
            columns="id",
            where="lesson_id = ?",
            params=(lesson_id,)
        )

        if not lesson:
            return jsonify({"error": "Lesson not found"}), 404

        # Get query parameters
        timeframe = request.args.get("timeframe", "all")

        # Get lesson analytics
        analytics = get_lesson_analytics(lesson_id, timeframe)

        return jsonify({
            "lesson_id": lesson_id,
            "analytics": analytics,
            "timeframe": timeframe,
            "generated_at": datetime.now().isoformat()
        })

    except DatabaseError as e:
        logger.error(f"Error getting lesson analytics for lesson {lesson_id}: {e}")
        return jsonify({"error": "Internal server error"}), 500

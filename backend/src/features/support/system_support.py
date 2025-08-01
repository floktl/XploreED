"""
XplorED - System Support Module

This module provides system status and help content functions for the XplorED platform,
following clean architecture principles as outlined in the documentation.

System Support Components:
- System Status: Monitor and report system health and status
- Help Content: Provide help content and documentation
- System Monitoring: Monitor system performance and availability
- Help Topics: Manage help topics and categories

For detailed architecture information, see: docs/backend_structure.md
"""

import logging
import os
from typing import Dict, Any, List, Optional, Tuple

# Optional import for system monitoring
try:
    import psutil
    PSUTIL_AVAILABLE = True
except ImportError:
    PSUTIL_AVAILABLE = False

from core.database.connection import select_one, select_rows, insert_row, update_row, delete_rows, fetch_one, fetch_all, fetch_custom, execute_query, get_connection
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


def get_system_status() -> Dict[str, Any]:
    """
    Get comprehensive system status and health information.

    Returns:
        Dictionary containing system status information

    Raises:
        Exception: If system monitoring fails
    """
    try:
        logger.info("Getting system status")

        # Get system information
        if PSUTIL_AVAILABLE:
            cpu_percent = psutil.cpu_percent(interval=1)
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage('/')
        else:
            cpu_percent = 0
            memory = type('Memory', (), {'percent': 0, 'available': 0})()
            disk = type('Disk', (), {'percent': 0, 'free': 0})()

        # Get database connection status
        try:
            db_connection = get_connection()
            db_status = "connected" if db_connection else "disconnected"
        except Exception as e:
            db_status = f"error: {str(e)}"

        # Get process information
        if PSUTIL_AVAILABLE:
            process = psutil.Process(os.getpid())
            process_memory = process.memory_info()
            process_cpu = process.cpu_percent()
        else:
            process_memory = type('MemoryInfo', (), {'rss': 0})()
            process_cpu = 0

        # Get system uptime
        if PSUTIL_AVAILABLE:
            uptime = datetime.fromtimestamp(psutil.boot_time())
            current_time = datetime.now()
            uptime_duration = current_time - uptime
        else:
            uptime_duration = timedelta(0)

        # Check Redis connection (if available)
        redis_status = "unknown"
        try:
            from external.redis import redis_client
            if redis_client.is_connected():
                redis_status = "connected"
            else:
                redis_status = "disconnected"
        except:
            redis_status = "disconnected"

        # Get active user sessions (if available)
        try:
            active_sessions = fetch_one("SELECT COUNT(*) as count FROM user_sessions WHERE active = 1")
            session_count = active_sessions.get("count", 0) if active_sessions else 0
        except:
            session_count = 0

        # Get recent activity counts
        try:
            recent_activities = fetch_one(
                "SELECT COUNT(*) as count FROM activity_progress WHERE completed_at >= datetime('now', '-1 hour')"
            )
            activity_count = recent_activities.get("count", 0) if recent_activities else 0
        except:
            activity_count = 0

        status = {
            "system": {
                "cpu_usage": round(cpu_percent, 2),
                "memory_usage": round(memory.percent, 2),
                "memory_available": round(memory.available / (1024**3), 2),  # GB
                "disk_usage": round(disk.percent, 2),
                "disk_free": round(disk.free / (1024**3), 2),  # GB
                "uptime": str(uptime_duration).split('.')[0],  # Remove microseconds
                "boot_time": uptime.isoformat()
            },
            "services": {
                "database": db_status,
                "redis": redis_status,
                "application": "running"
            },
            "application": {
                "process_memory_mb": round(process_memory.rss / (1024**2), 2),
                "process_cpu_percent": round(process_cpu, 2),
                "active_sessions": session_count,
                "recent_activities": activity_count
            },
            "status": "healthy" if cpu_percent < 90 and memory.percent < 90 and db_status == "connected" else "warning",
            "timestamp": datetime.utcnow().isoformat()
        }

        logger.info(f"Generated system status: {status['status']} status")
        return status

    except Exception as e:
        logger.error(f"Error getting system status: {e}")
        return {
            "error": str(e),
            "status": "error",
            "timestamp": datetime.utcnow().isoformat()
        }


def get_help_content(topic: str, language: str = "en", format_type: str = "json") -> Optional[str]:
    """
    Get help content for a specific topic.

    Args:
        topic: The help topic to retrieve
        language: Language code (en, de, etc.)
        format_type: Content format (json, html, markdown)

    Returns:
        Help content string or None if not found

    Raises:
        ValueError: If topic is invalid
    """
    try:
        if not topic or not topic.strip():
            raise ValueError("Topic is required")

        topic = topic.strip().lower()
        language = language.lower()[:2]  # Get first 2 characters

        logger.info(f"Getting help content for topic '{topic}' in {language}")

        # Define help content (in a real app, this would come from a database or CMS)
        help_content = {
            "getting_started": {
                "en": {
                    "title": "Getting Started",
                    "content": """
# Getting Started with XplorED

Welcome to XplorED, your German learning platform! Here's how to get started:

## 1. Create Your Account
- Sign up with your email address
- Choose a username and password
- Complete your profile

## 2. Take the Placement Test
- Assess your current German level
- Get personalized lesson recommendations
- Start at the right difficulty level

## 3. Begin Learning
- Complete interactive lessons
- Practice with exercises
- Track your progress

## 4. Use Additional Features
- Vocabulary trainer
- Grammar games
- AI-powered feedback

Need help? Contact our support team!
                    """,
                    "last_updated": "2025-01-01"
                },
                "de": {
                    "title": "Erste Schritte",
                    "content": """
# Erste Schritte mit XplorED

Willkommen bei XplorED, Ihrer Deutsch-Lernplattform! So beginnen Sie:

## 1. Konto erstellen
- Registrieren Sie sich mit Ihrer E-Mail-Adresse
- Wählen Sie einen Benutzernamen und ein Passwort
- Vervollständigen Sie Ihr Profil

## 2. Einstufungstest machen
- Bewerten Sie Ihr aktuelles Deutschniveau
- Erhalten Sie personalisierte Lektionen
- Beginnen Sie auf dem richtigen Schwierigkeitsgrad

## 3. Mit dem Lernen beginnen
- Absolvieren Sie interaktive Lektionen
- Üben Sie mit Aufgaben
- Verfolgen Sie Ihren Fortschritt

## 4. Zusätzliche Funktionen nutzen
- Vokabeltrainer
- Grammatikspiele
- KI-gestütztes Feedback

Brauchen Sie Hilfe? Kontaktieren Sie unser Support-Team!
                    """,
                    "last_updated": "2025-01-01"
                }
            },
            "lessons": {
                "en": {
                    "title": "How to Use Lessons",
                    "content": """
# Using Lessons in XplorED

## Lesson Structure
Each lesson contains multiple blocks:
- **Text Blocks**: Reading passages and explanations
- **Exercise Blocks**: Interactive practice activities
- **Vocabulary Blocks**: New words and phrases
- **Grammar Blocks**: Grammar explanations and practice

## Completing Lessons
1. Read through all text blocks
2. Complete exercises to practice
3. Review vocabulary and grammar
4. Mark blocks as complete when finished

## Progress Tracking
- Your progress is automatically saved
- You can return to incomplete lessons
- Review completed lessons anytime
                    """,
                    "last_updated": "2025-01-01"
                },
                "de": {
                    "title": "Lektionen verwenden",
                    "content": """
# Lektionen in XplorED verwenden

## Lektionsstruktur
Jede Lektion enthält mehrere Blöcke:
- **Textblöcke**: Lesetexte und Erklärungen
- **Übungsblöcke**: Interaktive Übungsaktivitäten
- **Vokabelblöcke**: Neue Wörter und Phrasen
- **Grammatikblöcke**: Grammatikerklärungen und Übungen

## Lektionen abschließen
1. Lesen Sie alle Textblöcke durch
2. Absolvieren Sie Übungen zum Üben
3. Wiederholen Sie Vokabeln und Grammatik
4. Markieren Sie Blöcke als abgeschlossen

## Fortschrittsverfolgung
- Ihr Fortschritt wird automatisch gespeichert
- Sie können zu unvollständigen Lektionen zurückkehren
- Überprüfen Sie abgeschlossene Lektionen jederzeit
                    """,
                    "last_updated": "2025-01-01"
                }
            },
            "exercises": {
                "en": {
                    "title": "Exercise Types",
                    "content": """
# Types of Exercises

## Multiple Choice
- Choose the correct answer from options
- Immediate feedback provided
- Explanations for correct answers

## Fill in the Blanks
- Complete sentences with missing words
- Context clues provided
- Grammar and vocabulary practice

## Translation
- Translate sentences between languages
- AI-powered evaluation
- Detailed feedback and corrections

## Listening
- Audio-based exercises
- Practice pronunciation and comprehension
- Interactive audio controls
                    """,
                    "last_updated": "2025-01-01"
                },
                "de": {
                    "title": "Übungstypen",
                    "content": """
# Arten von Übungen

## Multiple Choice
- Wählen Sie die richtige Antwort aus den Optionen
- Sofortiges Feedback wird bereitgestellt
- Erklärungen für richtige Antworten

## Lückentext
- Vervollständigen Sie Sätze mit fehlenden Wörtern
- Kontexthinweise werden bereitgestellt
- Grammatik- und Vokabelübung

## Übersetzung
- Übersetzen Sie Sätze zwischen Sprachen
- KI-gestützte Bewertung
- Detailliertes Feedback und Korrekturen

## Hören
- Audio-basierte Übungen
- Üben Sie Aussprache und Verständnis
- Interaktive Audio-Steuerung
                    """,
                    "last_updated": "2025-01-01"
                }
            },
            "vocabulary": {
                "en": {
                    "title": "Vocabulary Learning",
                    "content": """
# Learning Vocabulary

## Spaced Repetition
- Words are reviewed at optimal intervals
- Difficult words appear more frequently
- Easy words are reviewed less often

## Practice Methods
- Flashcards with audio pronunciation
- Context sentences and examples
- Interactive word games

## Progress Tracking
- Track words you know well
- Focus on challenging vocabulary
- Review statistics and improvement
                    """,
                    "last_updated": "2025-01-01"
                },
                "de": {
                    "title": "Vokabeln lernen",
                    "content": """
# Vokabeln lernen

## Spaced Repetition
- Wörter werden in optimalen Abständen wiederholt
- Schwierige Wörter erscheinen häufiger
- Einfache Wörter werden seltener wiederholt

## Übungsmethoden
- Karteikarten mit Audio-Aussprache
- Kontextsätze und Beispiele
- Interaktive Wortspiele

## Fortschrittsverfolgung
- Verfolgen Sie Wörter, die Sie gut kennen
- Konzentrieren Sie sich auf herausfordernde Vokabeln
- Überprüfen Sie Statistiken und Verbesserungen
                    """,
                    "last_updated": "2025-01-01"
                }
            }
        }

        # Get content for the requested topic and language
        if topic in help_content and language in help_content[topic]:
            content = help_content[topic][language]

            if format_type == "json":
                import json
                return json.dumps(content)
            elif format_type == "html":
                # Convert markdown to HTML (simplified)
                html_content = content["content"].replace("# ", "<h1>").replace("## ", "<h2>")
                html_content = html_content.replace("\n\n", "</p><p>")
                html_content = f"<h1>{content['title']}</h1><p>{html_content}</p>"
                return html_content
            elif format_type == "markdown":
                return content["content"]
            else:
                return content["content"]
        else:
            logger.warning(f"Help content not found for topic '{topic}' in language '{language}'")
            return None

    except ValueError as e:
        logger.error(f"Validation error getting help content: {e}")
        raise
    except Exception as e:
        logger.error(f"Error getting help content for topic '{topic}': {e}")
        return None


def get_help_topics(language: str = "en") -> List[Dict[str, Any]]:
    """
    Get list of available help topics.

    Args:
        language: Language code (en, de, etc.)

    Returns:
        List of help topics with metadata

    Raises:
        ValueError: If language is invalid
    """
    try:
        if not language:
            language = "en"

        language = language.lower()[:2]  # Get first 2 characters

        logger.info(f"Getting help topics for language {language}")

        # Define available topics
        topics = [
            {
                "id": "getting_started",
                "title": "Getting Started" if language == "en" else "Erste Schritte",
                "description": "Learn how to get started with XplorED" if language == "en" else "Erfahren Sie, wie Sie mit XplorED beginnen",
                "category": "basics",
                "popularity": 100
            },
            {
                "id": "lessons",
                "title": "Using Lessons" if language == "en" else "Lektionen verwenden",
                "description": "How to use and complete lessons" if language == "en" else "Wie Sie Lektionen verwenden und abschließen",
                "category": "learning",
                "popularity": 85
            },
            {
                "id": "exercises",
                "title": "Exercise Types" if language == "en" else "Übungstypen",
                "description": "Different types of exercises available" if language == "en" else "Verschiedene Arten von Übungen",
                "category": "learning",
                "popularity": 75
            },
            {
                "id": "vocabulary",
                "title": "Vocabulary Learning" if language == "en" else "Vokabeln lernen",
                "description": "How to learn and practice vocabulary" if language == "en" else "Wie Sie Vokabeln lernen und üben",
                "category": "learning",
                "popularity": 70
            }
        ]

        # Sort by popularity
        topics.sort(key=lambda x: x["popularity"], reverse=True)

        logger.info(f"Retrieved {len(topics)} help topics for language {language}")
        return topics

    except ValueError as e:
        logger.error(f"Validation error getting help topics: {e}")
        raise
    except Exception as e:
        logger.error(f"Error getting help topics for language {language}: {e}")
        return []


def search_help_content(query: str, language: str = "en", limit: int = 10) -> List[Dict[str, Any]]:
    """
    Search help content for specific terms.

    Args:
        query: Search query string
        language: Language code (en, de, etc.)
        limit: Maximum number of results to return

    Returns:
        List of matching help content

    Raises:
        ValueError: If query is invalid
    """
    try:
        if not query or not query.strip():
            raise ValueError("Search query is required")

        query = query.strip().lower()
        if len(query) < 2:
            raise ValueError("Search query must be at least 2 characters")

        if limit <= 0 or limit > 50:
            limit = 10

        language = language.lower()[:2]

        logger.info(f"Searching help content with query '{query}' in {language}")

        # Get all help topics
        topics = get_help_topics(language)
        results = []

        for topic in topics:
            # Get content for this topic
            content = get_help_content(topic["id"], language, "markdown")

            if content and query in content.lower():
                # Calculate relevance score (simple implementation)
                relevance = content.lower().count(query) * 10

                results.append({
                    "topic_id": topic["id"],
                    "title": topic["title"],
                    "description": topic["description"],
                    "category": topic["category"],
                    "relevance_score": relevance,
                    "snippet": _extract_snippet(content, query)
                })

        # Sort by relevance score
        results.sort(key=lambda x: x["relevance_score"], reverse=True)
        results = results[:limit]

        logger.info(f"Found {len(results)} help content matches for query '{query}'")
        return results

    except ValueError as e:
        logger.error(f"Validation error searching help content: {e}")
        raise
    except Exception as e:
        logger.error(f"Error searching help content: {e}")
        return []


def _extract_snippet(content: str, query: str, max_length: int = 150) -> str:
    """
    Extract a snippet of content around the search query.

    Args:
        content: The full content text
        query: The search query
        max_length: Maximum snippet length

    Returns:
        Extracted snippet string
    """
    try:
        # Find the first occurrence of the query
        query_pos = content.lower().find(query.lower())

        if query_pos == -1:
            # Query not found, return beginning of content
            return content[:max_length] + "..." if len(content) > max_length else content

        # Calculate start and end positions for snippet
        start = max(0, query_pos - max_length // 2)
        end = min(len(content), start + max_length)

        # Adjust start position to not break words
        while start > 0 and content[start] != ' ':
            start -= 1

        # Extract snippet
        snippet = content[start:end]

        # Add ellipsis if needed
        if start > 0:
            snippet = "..." + snippet
        if end < len(content):
            snippet = snippet + "..."

        return snippet

    except Exception as e:
        logger.error(f"Error extracting snippet: {e}")
        return content[:max_length] + "..." if len(content) > max_length else content

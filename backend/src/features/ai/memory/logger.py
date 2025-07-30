"""
Topic Memory Logger - Creates detailed logs of topic memory updates in table format
"""

import os
import json
import datetime
from typing import Any, Dict, List, Optional, Tuple
from pathlib import Path

class TopicMemoryLogger:
    """Logs topic memory updates to a structured text file"""

    def __init__(self, log_dir: str = "logs"):
        self.log_dir = Path(log_dir)
        # print(f"🔧 [LOGGER DEBUG] 🔧 Initializing logger with log_dir: {self.log_dir}", flush=True)
        self.log_dir.mkdir(exist_ok=True)
        # print(f"🔧 [LOGGER DEBUG] 🔧 Created/verified log directory: {self.log_dir}", flush=True)
        self.current_session: Optional[str] = None
        self.session_data: dict = {
            "new_entries": [],
            "updated_entries": [],
            "vocabulary_updates": [],
            "session_start": None,
            "user": None
        }
        # print(f"🔧 [LOGGER DEBUG] Logger initialized successfully", flush=True)

    def start_session(self, username: str) -> None:
        """Start a new logging session for a user"""
        # print(f"🔧 [LOGGER DEBUG] 🔧 Starting session for user: {username}", flush=True)
        self.session_data = {
            "new_entries": [],
            "updated_entries": [],
            "vocabulary_updates": [],
            "session_start": datetime.datetime.now(),
            "user": username
        }
        self.current_session = f"topic_memory_{username}_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}"
        # print(f"🔧 [LOGGER DEBUG] Session ID created: {self.current_session}", flush=True)
        print(f"📋 [TOPIC MEMORY LOGGER] Started session: {self.current_session}", flush=True)

    def log_topic_update(self,
                        username: str,
                        grammar: str,
                        skill: str,
                        quality: int,
                        is_new: bool,
                        old_values: Optional[Dict] = None,
                        new_values: Optional[Dict] = None,
                        row_id: Optional[int] = None) -> None:
        """Log a topic memory update"""

        # print(f"🔧 [LOGGER DEBUG] 🔧 log_topic_update called with: username={username}, grammar={grammar}, skill={skill}, quality={quality}, is_new={is_new}", flush=True)

        if self.current_session is None:
            # print(f"🔧 [LOGGER DEBUG] No current session, starting new one", flush=True)
            self.start_session(username)

        entry = {
            "timestamp": datetime.datetime.now().isoformat(),
            "grammar": grammar,
            "skill": skill,
            "quality": quality,
            "is_new": is_new,
            "row_id": row_id
        }

        if is_new:
            entry.update({
                "ef": new_values.get("ease_factor") if new_values else 2.5,
                "reps": new_values.get("repetitions") if new_values else 0,
                "interval": new_values.get("intervall") if new_values else 1,
                "topic": new_values.get("topic") if new_values else "unknown",
                "context": new_values.get("context") if new_values else ""
            })
            self.session_data["new_entries"].append(entry)
            # print(f"🔧 [LOGGER DEBUG] Added new entry: {entry}", flush=True)
        else:
            entry.update({
                "old_ef": old_values.get("ease_factor") if old_values else 2.5,
                "new_ef": new_values.get("ease_factor") if new_values else 2.5,
                "old_reps": old_values.get("repetitions") if old_values else 0,
                "new_reps": new_values.get("repetitions") if new_values else 0,
                "old_interval": old_values.get("intervall") if old_values else 1,
                "new_interval": new_values.get("intervall") if new_values else 1,
                "topic": new_values.get("topic") if new_values else "unknown",
                "context": new_values.get("context") if new_values else ""
            })
            self.session_data["updated_entries"].append(entry)
            # print(f"🔧 [LOGGER DEBUG] 🔧 Added updated entry: {entry}", flush=True)

    def log_vocabulary_update(self,
                             username: str,
                             word: str,
                             quality: int,
                             is_new: bool,
                             old_values: Optional[Dict] = None,
                             new_values: Optional[Dict] = None) -> None:
        """Log a vocabulary update"""
        # print(f"🔧 [LOGGER DEBUG] 🔧 log_vocabulary_update called with: username={username}, word={word}, quality={quality}, is_new={is_new}", flush=True)

        if self.current_session is None:
            # print(f"🔧 [LOGGER DEBUG] No current session, starting new one", flush=True)
            self.start_session(username)

        entry = {
            "timestamp": datetime.datetime.now().isoformat(),
            "word": word,
            "quality": quality,
            "is_new": is_new
        }

        if is_new:
            entry.update({
                "ef": new_values.get("ease_factor") if new_values else 2.5,
                "reps": new_values.get("repetitions") if new_values else 0,
                "interval": new_values.get("intervall") if new_values else 1
            })
        else:
            entry.update({
                "old_ef": old_values.get("ease_factor") if old_values else 2.5,
                "new_ef": new_values.get("ease_factor") if new_values else 2.5,
                "old_reps": old_values.get("repetitions") if old_values else 0,
                "new_reps": new_values.get("repetitions") if new_values else 0,
                "old_interval": old_values.get("intervall") if old_values else 1,
                "new_interval": new_values.get("intervall") if new_values else 1
            })

        self.session_data["vocabulary_updates"].append(entry)
        # print(f"🔧 [LOGGER DEBUG] 🔧 Added vocabulary entry: {entry}", flush=True)

    def generate_table_report(self) -> str:
        """Generate a formatted table report"""

        # print(f"🔧 [LOGGER DEBUG] 🔧 generate_table_report called", flush=True)

        if not self.session_data["user"]:
            # print(f"🔧 [LOGGER DEBUG] 🔧 No user data available", flush=True)
            return "No session data available"

        # print(f"🔧 [LOGGER DEBUG] 🔧 Generating report for user: {self.session_data['user']}", flush=True)
        # print(f"🔧 [LOGGER DEBUG] 🔧 New entries: {len(self.session_data['new_entries'])}", flush=True)
        # print(f"🔧 [LOGGER DEBUG] Updated entries: {len(self.session_data['updated_entries'])}", flush=True)
        # print(f"🔧 [LOGGER DEBUG] Vocabulary updates: {len(self.session_data['vocabulary_updates'])}", flush=True)

        report = []
        report.append("=" * 80)
        report.append(f"TOPIC MEMORY UPDATE REPORT")
        report.append(f"User: {self.session_data['user']}")
        report.append(f"Session: {self.current_session}")
        report.append(f"Started: {self.session_data['session_start']}")
        report.append("=" * 80)
        report.append("")

        # New Topic Memory Entries
        if self.session_data["new_entries"]:
            report.append("🆕 NEW TOPIC MEMORY ENTRIES")
            report.append("-" * 80)
            report.append(f"{'Topic':<20} {'Skill':<15} {'Quality':<8} {'EF':<6} {'Reps':<6} {'Interval':<8} {'Topic':<10} {'Context':<30}")
            report.append("-" * 80)

            for entry in self.session_data["new_entries"]:
                topic = entry.get('topic', 'unknown') or 'unknown'
                context = entry.get('context', '') or ''
                context = context[:27] + "..." if len(context) > 30 else context
                report.append(f"{entry['grammar']:<20} {entry['skill']:<15} {entry['quality']:<8} {entry['ef']:<6.1f} {entry['reps']:<6} {entry['interval']:<8} {topic:<10} {context:<30}")
            report.append("")

        # Updated Topic Memory Entries
        if self.session_data["updated_entries"]:
            report.append("📝 UPDATED TOPIC MEMORY ENTRIES")
            report.append("-" * 120)
            report.append(f"{'Topic':<20} {'Skill':<15} {'Quality':<8} {'Old EF':<8} {'New EF':<8} {'Old Reps':<10} {'New Reps':<10} {'Old Interval':<12} {'New Interval':<12} {'Row ID':<8} {'Context':<30}")
            report.append("-" * 120)

            for entry in self.session_data["updated_entries"]:
                topic = entry.get('topic', 'unknown') or 'unknown'
                context = entry.get('context', '') or ''
                context = context[:27] + "..." if len(context) > 30 else context
                report.append(f"{entry['grammar']:<20} {entry['skill']:<15} {entry['quality']:<8} {entry['old_ef']:<8.1f} {entry['new_ef']:<8.1f} {entry['old_reps']:<10} {entry['new_reps']:<10} {entry['old_interval']:<12} {entry['new_interval']:<12} {entry['row_id']:<8} {context:<30}")
            report.append("")

        # Vocabulary Updates
        if self.session_data["vocabulary_updates"]:
            report.append(" VOCABULARY UPDATES")
            report.append("-" * 80)
            report.append(f"{'Word':<15} {'Quality':<8} {'Old EF':<8} {'New EF':<8} {'Old Reps':<10} {'New Reps':<10} {'Old Interval':<12} {'New Interval':<12}")
            report.append("-" * 80)

            for entry in self.session_data["vocabulary_updates"]:
                if entry["is_new"]:
                    report.append(f"{entry['word']:<15} {entry['quality']:<8} {'NEW':<8} {entry['ef']:<8.1f} {'NEW':<10} {entry['reps']:<10} {'NEW':<12} {entry['interval']:<12}")
                else:
                    report.append(f"{entry['word']:<15} {entry['quality']:<8} {entry['old_ef']:<8.1f} {entry['new_ef']:<8.1f} {entry['old_reps']:<10} {entry['new_reps']:<10} {entry['old_interval']:<12} {entry['new_interval']:<12}")
            report.append("")

        # Summary
        report.append("📊 SUMMARY")
        report.append("-" * 30)
        report.append(f"New Topic Entries: {len(self.session_data['new_entries'])}")
        report.append(f"Updated Topic Entries: {len(self.session_data['updated_entries'])}")
        report.append(f"Vocabulary Updates: {len(self.session_data['vocabulary_updates'])}")
        report.append(f"Total Updates: {len(self.session_data['new_entries']) + len(self.session_data['updated_entries']) + len(self.session_data['vocabulary_updates'])}")
        report.append("")
        report.append("=" * 80)

        report_content = "\n".join(report)
        # print(f"🔧 [LOGGER DEBUG] 🔧 Generated report content length: {len(report_content)}", flush=True)
        return report_content

    def save_report(self) -> str:
        """Save the report to a file and return the file path"""

        # print(f"🔧 [LOGGER DEBUG] save_report called", flush=True)

        if not self.current_session:
            # print(f"🔧 [LOGGER DEBUG] No current session to save", flush=True)
            return ""

        report_content = self.generate_table_report()
        filename = f"{self.current_session}_report.txt"
        filepath = self.log_dir / filename

        # print(f"🔧 [LOGGER DEBUG] Attempting to save to: {filepath}", flush=True)
        # print(f"🔧 [LOGGER DEBUG] 🔧 Log directory exists: {self.log_dir.exists()}", flush=True)
        # print(f"🔧 [LOGGER DEBUG] 🔧 Log directory is writable: {os.access(self.log_dir, os.W_OK)}", flush=True)

        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(report_content)

            # print(f"🔧 [LOGGER DEBUG] 🔧 File saved successfully: {filepath}", flush=True)
            # print(f"🔧 [LOGGER DEBUG] 🔧 File exists after save: {filepath.exists()}", flush=True)
            # print(f"🔧 [LOGGER DEBUG] 🔧 File size: {filepath.stat().st_size} bytes", flush=True)

            print(f"📄 [TOPIC MEMORY LOGGER] Report saved to: {filepath}", flush=True)
            return str(filepath)
        except Exception as e:
            # print(f"🔧 [LOGGER DEBUG] Error saving file: {e}", flush=True)
            return ""

    def end_session(self) -> str:
        """End the current session and save the report"""

        # print(f"🔧 [LOGGER DEBUG] end_session called", flush=True)

        if not self.current_session:
            # print(f"🔧 [LOGGER DEBUG] No current session to end", flush=True)
            return ""

        filepath = self.save_report()
        # print(f"🔧 [LOGGER DEBUG] 🔧 Session ended, filepath: {filepath}", flush=True)
        self.current_session = None
        return filepath

# Global logger instance
topic_memory_logger = TopicMemoryLogger()
    # print(f"🔧 [LOGGER DEBUG] 🔧 Global logger instance created", flush=True)

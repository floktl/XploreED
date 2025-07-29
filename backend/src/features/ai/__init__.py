"""AI features module."""

EXERCISE_TEMPLATE = {
    "lessonId": "dynamic-ai-lesson",
    "title": "AI Feedback",
    "level": "A1",
    "exercises": [],
}

READING_TEMPLATE = {
    "lessonId": "ai-reading",
    "style": "story",
    "text": "Guten Morgen!",
    "questions": [],
    "feedbackPrompt": "",
    "vocabHelp": [],
}

CEFR_LEVELS = [
    "A1", "A1", "A2", "A2", "B1",
    "B1", "B2", "B2", "C1", "C1", "C2"
]

FEEDBACK_FILE = [
    {
        "id": "fb1",
        "title": "Feedback After Set 1",
        "instructions": "Here are notes on your first round of exercises.",
        "type": "mixed",
        "feedbackPrompt": "You mixed up some plural forms like 'wir sind' and 'sie sind'. Review the pronouns before continuing.",
        "created_at": "2025-06-12T09:00:00Z"
    },
    {
        "id": "fb2",
        "title": "Feedback After Set 2",
        "instructions": "Comments on your second round of practice.",
        "type": "mixed",
        "feedbackPrompt": "Great improvement! Keep an eye on word order in translations and continue practicing.",
        "created_at": "2025-06-12T09:10:00Z"
    }
]

"""
Gemini AI Translator for German language learning.
This module provides translation and feedback services using Google's Gemini AI.
"""

import os
import google.generativeai as genai
from dotenv import load_dotenv
from pathlib import Path

# Load environment variables
env_path = Path(__file__).resolve().parent.parent / "secrets" / ".env"
load_dotenv(dotenv_path=env_path)

# Configure the Gemini API
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
if not GEMINI_API_KEY:
    print("⚠️ Warning: GEMINI_API_KEY not found in environment variables.")

# Initialize the Gemini API
try:
    genai.configure(api_key=GEMINI_API_KEY)
    model = genai.GenerativeModel('gemini-1.5-pro')
    print("✅ Gemini AI API initialized successfully.")
except Exception as e:
    print(f"❌ Failed to initialize Gemini AI API: {e}")
    model = None

# Dictionary for fallback if API fails
from game.german_sentence_game import ENGLISH_GERMAN_DICT

def translate_with_gemini(english_text, username=None):
    """
    Translate English text to German using Gemini AI.

    Args:
        english_text (str): The English text to translate
        username (str, optional): The username for personalization

    Returns:
        dict: Dictionary containing the translation and confidence score
    """
    if not model or not GEMINI_API_KEY:
        print("⚠️ Using fallback dictionary translation as Gemini API is not available.")
        return {
            "text": fallback_translation(english_text),
            "confidence": 50  # Medium confidence for dictionary fallback
        }

    try:
        # Create a prompt that focuses on well-being of the language learner
        prompt = f"""
        Translate the following English text to German:
        "{english_text}"

        You are a supportive language teacher helping {username or 'a student'} learn German.
        Provide a natural, conversational German translation that would be used in everyday speech.
        Focus on being encouraging and supportive in your translation approach.

        After your translation, on a new line, provide a confidence score from 0-100 indicating how confident
        you are in this translation. Format it as "Confidence: [score]"
        """

        response = model.generate_content(prompt)
        response_text = response.text.strip()

        # Extract translation and confidence
        lines = response_text.split('\n')
        translation = lines[0].strip()

        # Try to extract confidence score
        confidence = 75  # Default confidence if not specified
        for line in lines:
            if "confidence:" in line.lower():
                try:
                    # Extract number from the confidence line
                    confidence_str = line.lower().split("confidence:")[1].strip()
                    confidence = int(confidence_str.split()[0])
                    # Ensure confidence is within range
                    confidence = max(0, min(100, confidence))
                except:
                    pass

        # Validate the translation (basic check)
        if not translation or len(translation) < 2:
            print("⚠️ Gemini returned an empty or very short translation. Using fallback.")
            return {
                "text": fallback_translation(english_text),
                "confidence": 50
            }

        return {
            "text": translation,
            "confidence": confidence
        }

    except Exception as e:
        print(f"❌ Gemini translation error: {e}")
        return {
            "text": fallback_translation(english_text),
            "confidence": 50
        }

def get_feedback_with_gemini(correct_german, student_input):
    """
    Provide feedback on student's German translation using Gemini AI.

    Args:
        correct_german (str): The correct German translation
        student_input (str): The student's attempt at translation

    Returns:
        tuple: (is_correct, feedback_text, confidence)
    """
    if not model or not GEMINI_API_KEY:
        print("⚠️ Using fallback feedback as Gemini API is not available.")
        from game.german_sentence_game import get_feedback
        is_correct, feedback = get_feedback(correct_german, student_input)
        return (is_correct, feedback, 50)  # Medium confidence for fallback

    try:
        # Create a prompt that focuses on well-being and encouragement
        prompt = f"""
        As a supportive German language teacher, provide feedback on a student's translation.

        Correct German: "{correct_german}"
        Student's translation: "{student_input}"

        First, determine if the translation is correct. Then provide encouraging, constructive feedback.

        Rules for your feedback:
        1. Start with "✅" if the translation is correct or "❌" if it contains errors
        2. Be encouraging and focus on the student's well-being
        3. Highlight what they did well, even if there are mistakes
        4. For errors, use <span style="color:red;">incorrect word</span> to mark mistakes
        5. Use <span style="color:green;">correct word</span> to show corrections
        6. Explain grammar concepts briefly and in a friendly way
        7. End with an encouraging message
        8. On the last line, add "Confidence: [0-100]" indicating how confident you are in your feedback

        Format your response as:
        [✅ or ❌] [Your detailed feedback with HTML spans for highlighting]
        Confidence: [score]
        """

        response = model.generate_content(prompt)
        response_text = response.text.strip()

        # Extract feedback and confidence
        lines = response_text.split('\n')
        feedback = '\n'.join([line for line in lines if not line.lower().startswith('confidence:')])

        # Try to extract confidence score
        confidence = 75  # Default confidence if not specified
        for line in lines:
            if "confidence:" in line.lower():
                try:
                    # Extract number from the confidence line
                    confidence_str = line.lower().split("confidence:")[1].strip()
                    confidence = int(confidence_str.split()[0])
                    # Ensure confidence is within range
                    confidence = max(0, min(100, confidence))
                except:
                    pass

        # Basic validation of feedback
        is_correct = "✅" in feedback

        # If feedback seems invalid, use fallback
        if not feedback or (not "✅" in feedback and not "❌" in feedback):
            print("⚠️ Gemini returned invalid feedback. Using fallback.")
            from game.german_sentence_game import get_feedback
            is_correct, feedback = get_feedback(correct_german, student_input)
            return (is_correct, feedback, 50)

        return (is_correct, feedback, confidence)

    except Exception as e:
        print(f"❌ Gemini feedback error: {e}")
        from game.german_sentence_game import get_feedback
        is_correct, feedback = get_feedback(correct_german, student_input)
        return (is_correct, feedback, 50)

def fallback_translation(english_text):
    """Fallback translation using the dictionary when Gemini API fails."""
    words = english_text.lower().split()
    translated_words = []

    for word in words:
        # Remove punctuation for lookup
        clean_word = word.strip(".,!?;:()\"'")

        # Try to find the word in our dictionary
        if clean_word in ENGLISH_GERMAN_DICT:
            german_word = ENGLISH_GERMAN_DICT[clean_word]
            # Capitalize if it's the first word in the sentence
            if len(translated_words) == 0:
                german_word = german_word.capitalize()
            translated_words.append(german_word)
        else:
            # If not found, keep the original word
            translated_words.append(clean_word)

    return " ".join(translated_words)

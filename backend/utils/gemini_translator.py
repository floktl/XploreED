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
        str: The German translation
    """
    if not model or not GEMINI_API_KEY:
        print("⚠️ Using fallback dictionary translation as Gemini API is not available.")
        return fallback_translation(english_text)
    
    try:
        # Create a prompt that focuses on well-being of the language learner
        prompt = f"""
        Translate the following English text to German:
        "{english_text}"
        
        You are a supportive language teacher helping {username or 'a student'} learn German.
        Provide a natural, conversational German translation that would be used in everyday speech.
        Focus on being encouraging and supportive in your translation approach.
        Return ONLY the German translation without any additional explanation.
        """
        
        response = model.generate_content(prompt)
        translation = response.text.strip()
        
        # Validate the translation (basic check)
        if not translation or len(translation) < 2:
            print("⚠️ Gemini returned an empty or very short translation. Using fallback.")
            return fallback_translation(english_text)
            
        return translation
        
    except Exception as e:
        print(f"❌ Gemini translation error: {e}")
        return fallback_translation(english_text)

def get_feedback_with_gemini(correct_german, student_input):
    """
    Provide feedback on student's German translation using Gemini AI.
    
    Args:
        correct_german (str): The correct German translation
        student_input (str): The student's attempt at translation
        
    Returns:
        tuple: (is_correct, feedback_text)
    """
    if not model or not GEMINI_API_KEY:
        print("⚠️ Using fallback feedback as Gemini API is not available.")
        from game.german_sentence_game import get_feedback
        return get_feedback(correct_german, student_input)
    
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
        
        Format your response as:
        [✅ or ❌] [Your detailed feedback with HTML spans for highlighting]
        """
        
        response = model.generate_content(prompt)
        feedback = response.text.strip()
        
        # Basic validation of feedback
        is_correct = "✅" in feedback
        
        # If feedback seems invalid, use fallback
        if not feedback or (not "✅" in feedback and not "❌" in feedback):
            print("⚠️ Gemini returned invalid feedback. Using fallback.")
            from game.german_sentence_game import get_feedback
            return get_feedback(correct_german, student_input)
            
        return (is_correct, feedback)
        
    except Exception as e:
        print(f"❌ Gemini feedback error: {e}")
        from game.german_sentence_game import get_feedback
        return get_feedback(correct_german, student_input)

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

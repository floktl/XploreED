"""Helper functions used by AI routes."""

import logging
import json
from flask import current_app  # type: ignore

from features.ai.memory.vocabulary_memory import review_vocab_word, extract_words
from core.database.connection import *
from features.grammar.detector import detect_language_topics
from features.ai.evaluation.translation_evaluator import _update_single_topic
from core.utils.json_helpers import extract_json
from features.ai.prompts.exercise_prompts import answers_evaluation_prompt
from external.mistral.client import send_prompt
from features.ai.memory.logger import topic_memory_logger
from features.ai.evaluation.translation_evaluator import _normalize_umlauts

logger = logging.getLogger(__name__)


def evaluate_answers_with_ai(
    exercises: list, answers: dict, mode: str = "strict"
) -> dict | None:
    """Ask Mistral to evaluate student answers and return JSON results."""
    # logger.info(f"Starting AI evaluation with mode={mode}, exercises_count={len(exercises)}, answers_count={len(answers)}")

    formatted = [
        {
            "id": ex.get("id"),
            "question": ex.get("question"),
            "type": ex.get("type"),
            "answer": answers.get(str(ex.get("id"))) or "",
        }
        for ex in exercises
    ]
    # logger.info(f"Formatted {len(formatted)} exercises for evaluation")

    instructions = (
        "Evaluate these answers for a German exercise. "
        "Return JSON with 'pass' (true/false) and a 'results' list. "
        "Each result must include 'id' and 'correct_answer'. "
        "Mark pass true only if all answers are fully correct."
    )
    if mode == "argue":
        instructions = (
            "Reevaluate the student's answers carefully. "
            "Consider possible alternative correct solutions. "
            + instructions
        )

    # logger.info(f"Generated evaluation instructions for mode={mode}")
    user_prompt = answers_evaluation_prompt(instructions, formatted)

    try:
        # logger.info(f"Sending evaluation request to Mistral API")
        # print(f"\033[92m[MISTRAL CALL] evaluate_answers_with_ai\033[0m", flush=True)
        resp = send_prompt(
            "You are a strict German teacher." if mode == "strict" else "You are a thoughtful German teacher.",
            user_prompt,
            temperature=0.3,
        )
        if resp.status_code == 200:
            # logger.info(f"Mistral evaluation response successful")
            content = resp.json()["choices"][0]["message"]["content"]
            # logger.info(f"Raw evaluation response length: {len(content)} characters")

            parsed = extract_json(content)
            if parsed:
                # logger.info(f"Successfully parsed evaluation JSON")
                return parsed
            else:
                logger.error(f"Failed to parse evaluation JSON from response")
        else:
            logger.error(f"Mistral evaluation request failed: {resp.status_code} - {resp.text}")
    except Exception as e:
        logger.error(f"AI evaluation failed: {e}")
        current_app.logger.error("AI evaluation failed: %s", e)

    # logger.error(f"AI evaluation failed - returning None")
    return None


def generate_alternative_answers(correct_sentence: str) -> list:
    """Use the AI to generate 2-3 alternative ways to say the same thing in German."""
    import re
    prompt = {
        "role": "user",
        "content": (
            f"Give up to 3 alternative ways to say the following sentence in German, with the same meaning and register. "
            f"Return only a JSON array of strings, no explanations, no extra text, no markdown, no labels.\nSentence: {correct_sentence}"
        ),
    }
    try:
        # print(f"\033[92m[MISTRAL CALL] generate_alternative_answers\033[0m", flush=True)
        resp = send_prompt(
            "You are a helpful German teacher.",
            prompt,
            temperature=0.3,
        )
        if resp.status_code == 200:
            import json as _json
            content = resp.json()["choices"][0]["message"]["content"]
            # print("[generate_alternative_answers] Raw AI response:", content, flush=True)
            # Try to extract a JSON array from the response robustly
            try:
                # Find the first [ ... ] block in the response
                match = re.search(r'\[.*?\]', content, re.DOTALL)
                if match:
                    arr_str = match.group(0)
                    alternatives = _json.loads(arr_str)
                    if isinstance(alternatives, list):
                        return alternatives
                # Fallback: try to parse the whole content
                alternatives = _json.loads(content)
                if isinstance(alternatives, list):
                    return alternatives
            except Exception as e:
                pass
    except Exception as e:
        logger.error(f"generate_alternative_answers failed: {e}")
    return []


def generate_explanation(question: str, user_answer: str, correct_answer: str) -> str:
    """Use the AI to generate a short grammar/vocab explanation for the correct answer only."""
    prompt = {
        "role": "user",
        "content": (
            "Given the following exercise and correct answer, give a very short grammar or vocabulary explanation (1-2 sentences) for a German learner. "
            "Do NOT mention the user's answer, do NOT restate the correct answer, and do NOT say if it is correct or incorrect. "
            "Only explain the grammar or vocabulary used in the correct answer, as briefly as possible.\n"
            f"Exercise: {question}\nCorrect answer: {correct_answer}\nReply in English."
        ),
    }
    try:
        # print(f"\033[92m[MISTRAL CALL] generate_explanation\033[0m", flush=True)
        resp = send_prompt(
            "You are a helpful German teacher.",
            prompt,
            temperature=0.3,
        )
        if resp.status_code == 200:
            content = resp.json()["choices"][0]["message"]["content"]
            return content.strip()
    except Exception as e:
        logger.error(f"generate_explanation failed: {e}")
    return ""


def process_ai_answers(username: str, block_id: str, answers: dict, exercise_block: dict | None = None) -> list:
    """Process AI answers and update topic memory and vocabulary."""
    # print("\033[96m🧠 [TOPIC MEMORY FLOW] 🧠 Starting process_ai_answers for user: {} block: {}\033[0m".format(username, block_id), flush=True)
    # print("\033[94m📊 [TOPIC MEMORY FLOW] Processing {} answers\033[0m".format(len(answers)), flush=True)

    # Extract block topic for all exercises
    block_topic = exercise_block.get("topic", "general") if exercise_block else "general"
            # print(f"🔍 [TOPIC MEMORY FLOW] 🔍 Using block topic: '{block_topic}' for all exercises", flush=True)
    # print(f"🔍 [TOPIC MEMORY FLOW] 🔍 Exercise block keys: {list(exercise_block.keys()) if exercise_block else 'None'}", flush=True)
    # print(f"🔍 [TOPIC MEMORY FLOW] 🔍 Exercise block topic: '{exercise_block.get('topic') if exercise_block else 'None'}'", flush=True)

    # Create exercise map for easy lookup
    all_exercises = exercise_block.get("exercises", []) if exercise_block else []
    exercise_map = {str(ex.get("id")): ex for ex in all_exercises}
    # print("\033[94m📝 [TOPIC MEMORY FLOW] 📝 Created exercise map with {} exercises\033[0m".format(len(exercise_map)), flush=True)

    results = []
    reviewed = set()

    for ex_id, user_answer in answers.items():
        # print("\033[93m🎯 [TOPIC MEMORY FLOW] 🎯 Processing exercise ID: {} with answer: '{}'\033[0m".format(ex_id, user_answer), flush=True)
        ex = exercise_map.get(ex_id)
        if not ex:
            # print(f"\033[91m⚠️ [TOPIC MEMORY FLOW] ⚠️ Exercise {ex_id} not found in exercise map\033[0m", flush=True)
            continue

        skill = ex.get("type", "unknown")
        correct_ans = ex.get("correctAnswer", "")
        quality = 2  # Default quality value, will be overridden in specific cases

        # Debug exercise structure
        # print(f"🔍 [EXERCISE DEBUG] Exercise ID: {ex_id}", flush=True)
        # print(f"🔍 [EXERCISE DEBUG] Exercise type: {skill}", flush=True)
        # print(f"🔍 [EXERCISE DEBUG] Question: '{ex.get('question', '')}'", flush=True)
        # print(f"🔍 [EXERCISE DEBUG] Correct answer: '{correct_ans}'", flush=True)
        # print(f"🔍 [EXERCISE DEBUG] User answer: '{user_answer}'", flush=True)

        # 🔥 IMPROVED GRADING LOGIC 🔥
        user_ans = user_answer.strip().lower()
        correct_ans_norm = correct_ans.strip().lower()

        # Normalize umlauts for both answers
        user_ans = _normalize_umlauts(user_ans)
        correct_ans_norm = _normalize_umlauts(correct_ans_norm)

        if user_ans == correct_ans_norm:
            is_correct = True
        else:
            # For gap-fill exercises, check if the answer makes grammatical sense
            exercise_type = ex.get("type", "")
            if exercise_type == "gap-fill":
                # Import the function from exercise_routes
                from ..exercise_routes import _check_gap_fill_correctness
                is_correct = _check_gap_fill_correctness(ex, user_ans, correct_ans_norm)
            else:
                # For other exercise types, use exact match
                is_correct = user_ans == correct_ans_norm

        # 🔥 IMPROVED SM2 GRADING LOGIC 🔥
        # Use AI topic evaluation for gap-fill exercises to get nuanced 0-5 scores
        exercise_type = ex.get("type", "")

        # Handle case where user_answer might be the entire question instead of just the gap
        if exercise_type == "gap-fill" and user_answer == ex.get('question', ''):
            # print(f"🔍 [GAP-FILL DEBUG] User answer appears to be the entire question, not just the gap", flush=True)
            # print(f"🔍 [GAP-FILL DEBUG] This suggests the frontend is sending the wrong data", flush=True)
            # For now, we'll use the original user_answer but log the issue
            # The frontend should send only the gap answer, not the entire question
            pass

        if exercise_type == "gap-fill":
            # For gap-fill exercises, use AI topic evaluation for nuanced grading
            # print("\033[96m🤖 [TOPIC MEMORY FLOW] 🤖 Using AI topic evaluation for gap-fill exercise\033[0m", flush=True)

            # Construct the complete sentences for AI evaluation
            question_text = ex.get('question', '')

            # Handle case where user_answer might be the entire question
            actual_user_answer = user_answer
            use_ai_evaluation = True

            if user_answer == question_text:
                # print(f"🔍 [GAP-FILL DEBUG] User answer is the entire question, cannot construct proper sentence", flush=True)
                # print(f"🔍 [GAP-FILL DEBUG] Using fallback evaluation method", flush=True)
                # Fallback: since we can't construct a proper sentence,
                # we'll use the simple binary grading for this exercise
                use_ai_evaluation = False
            else:
                # Normal case: user_answer is just the gap answer
                actual_user_answer = user_answer

            # print(f"🔍 [GAP-FILL DEBUG] Question: '{question_text}'", flush=True)
            # print(f"🔍 [GAP-FILL DEBUG] User's gap answer: '{user_answer}'", flush=True)
            # print(f"🔍 [GAP-FILL DEBUG] Correct gap answer: '{correct_ans}'", flush=True)

            if use_ai_evaluation:
                # Use AI topic evaluation for nuanced grading
                # Construct complete German sentences by replacing ____ with answers
                reference_sentence = question_text.replace('____', correct_ans)
                student_sentence = question_text.replace('____', actual_user_answer)

                from features.ai.evaluation.translation_evaluator import evaluate_topic_qualities_ai
                # print(f"🔍 [GAP-FILL DEBUG] 🔍 Calling evaluate_topic_qualities_ai for gap-fill exercise", flush=True)
                # print(f"🔍 [GAP-FILL DEBUG] 🔍 Reference sentence: '{reference_sentence}'", flush=True)
                # print(f"🔍 [GAP-FILL DEBUG] 🔍 Student sentence: '{student_sentence}'", flush=True)

                topic_qualities = evaluate_topic_qualities_ai(
                    english="",  # No English translation needed for gap-fill
                    reference=reference_sentence,
                    student=student_sentence
                )

                # print(f"🔍 [GAP-FILL DEBUG] AI topic qualities: {topic_qualities}", flush=True)
                # print(f"🔍 [GAP-FILL DEBUG] 🔍 GRADES CREATED HERE - Individual topic qualities:", flush=True)
                # for topic, quality in topic_qualities.items():
                #     print(f"🔍 [GAP-FILL DEBUG] 🔍   {topic}: {quality}", flush=True)

                # Use the AI topic qualities for individual grammar elements
                features = list(topic_qualities.keys()) if topic_qualities else ["unknown"]

                for feature in features:
                    feature_quality = topic_qualities.get(feature, 2)  # Default to 2 if not found
                    # print(f"\033[95m💾 [TOPIC MEMORY FLOW] 💾 Updating topic memory for user: {username}, feature: {feature}, skill: {skill}, quality: {feature_quality}\033[0m", flush=True)
                    _update_single_topic(
                        username,
                        feature,
                        skill,
                        ex.get("question", ""),
                        feature_quality,
                        block_topic  # Use the block topic for all exercises
                    )
                    # print(f"\033[92m✅ [TOPIC MEMORY FLOW] ✅ Topic memory updated for feature: {feature} with quality: {feature_quality}\033[0m", flush=True)

                # Set quality for vocabulary review (use average of topic qualities or default to 2)
                if topic_qualities:
                    quality = sum(topic_qualities.values()) // len(topic_qualities)
                else:
                    quality = 2
            else:
                # Fallback: use simple binary grading
                if is_correct:
                    quality = 5
                else:
                    quality = 2

                # print(f"🔍 [GAP-FILL DEBUG] Using fallback binary grading: {quality}", flush=True)

                # Use simple topic detection
                features = detect_language_topics(f"{question_text} {correct_ans}") or ["unknown"]
                for feature in features:
                    _update_single_topic(username, feature, skill, question_text, quality, block_topic)
        else:
            # For other exercise types, use simple binary grading
            if is_correct:
                quality = 5
            else:
                quality = 2

            # print(f"\033[92m✅ [TOPIC MEMORY FLOW] ✅ Exercise {ex_id} - Correct: {is_correct} (Quality: {quality})\033[0m", flush=True)

            # Use simple topic detection for non-gap-fill exercises
            # print(f"\033[96m🔍 [TOPIC MEMORY FLOW] 🔍 Detecting language topics for exercise: {ex_id}\033[0m", flush=True)
            features = detect_language_topics(
                f"{ex.get('question', '')} {correct_ans}"
            ) or ["unknown"]
            # print(f"\033[93m📚 [TOPIC MEMORY FLOW] 📚 Detected features: {features} for skill: {skill}\033[0m", flush=True)

            for feature in features:
                # print(f"\033[95m💾 [TOPIC MEMORY FLOW] 💾 Updating topic memory for user: {username}, feature: {feature}, skill: {skill}\033[0m", flush=True)
                _update_single_topic(
                    username,
                    feature,
                    skill,
                    ex.get("question", ""),
                    quality,
                    block_topic  # Use the block topic for all exercises
                )
                # print(f"\033[92m✅ [TOPIC MEMORY FLOW] ✅ Topic memory updated for feature: {feature}\033[0m", flush=True)

        # Extract and review vocabulary
        # print("\033[96m📖 [TOPIC MEMORY FLOW] 📖 Extracting vocabulary from exercise: {}\033[0m".format(ex_id), flush=True)
        question_text_safe = ex.get("question", "") or ""
        correct_ans_safe = correct_ans or ""

        words = (
            [w for w, _ in extract_words(question_text_safe)]
            + [w for w, _ in extract_words(correct_ans_safe)]
        )
        # print("\033[93m📝 [TOPIC MEMORY FLOW] �� Extracted {} words from exercise {}\033[0m".format(len(words), ex_id), flush=True)
        # logger.info(f"Extracted {len(words)} words from exercise {ex_id} for user {username}")

        for vocab in words:
            # print("\033[96m🔤 [TOPIC MEMORY FLOW] 🔤 Reviewing vocabulary word: '{}'\033[0m".format(vocab), flush=True)
            review_vocab_word(username, vocab, quality, seen=reviewed)
            # print("\033[92m✅ [TOPIC MEMORY FLOW] ✅ Vocabulary word '{}' reviewed\033[0m".format(vocab), flush=True)

    # print("\033[95m🎉 [TOPIC MEMORY FLOW] 🎉 Completed processing AI answers for user {}: {} results\033[0m".format(username, len(results)), flush=True)
    # logger.info(f"Completed processing AI answers for user {username}: {len(results)} results")

    # 🔥 ADD THIS: End session and generate report with debug info
    # print(f"🔧 [LOGGER DEBUG] 🔧 About to call topic_memory_logger.end_session", flush=True)
    report_path = topic_memory_logger.end_session()
    # print(f"🔧 [LOGGER DEBUG] 🔧 topic_memory_logger.end_session returned: {report_path}", flush=True)

    if report_path:
        # print(f"\033[94m📄 [TOPIC MEMORY FLOW] 📄 Report generated: {report_path}\033[0m", flush=True)
        pass # Commented out debug print
    else:
        # print(f"\033[93m⚠️ [TOPIC MEMORY FLOW] ⚠️ No session to end\033[0m", flush=True)
        pass # Commented out debug print

    return results

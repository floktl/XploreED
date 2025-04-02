import os
import sys
import subprocess
import random
import difflib
import signal
import warnings
import readline
import requests
from dotenv import load_dotenv
load_dotenv()

warnings.filterwarnings("ignore", message="Recommended: pip install sacremoses.")

# Auto-install required packages
def ensure_packages():
	required = {
		"colorama": None,
		"numpy": "<2",
		"requests": None
	}
	for pkg, version in required.items():
		try:
			__import__(pkg)
		except ImportError:
			version_str = f"{pkg}{version}" if version else pkg
			print(f"📦 Installing missing package: {version_str}")
			subprocess.check_call([sys.executable, "-m", "pip", "install", version_str])

ensure_packages()

from colorama import Fore, Style, init as colorama_init
colorama_init()

# Load model

ENC_FILE = "results.enc"

def simple_encrypt(text, shift=3):
	return ''.join(chr((ord(c) + shift) % 256) for c in text)

def translate_to_german(english_sentence):
	api_key = os.environ.get("DEEPL_API_KEY")

	if not api_key:
		return "❌ Error: DEEPL_API_KEY not set."

	url = "https://api-free.deepl.com/v2/translate"
	data = {
		"auth_key": api_key,
		"text": english_sentence,
		"target_lang": "DE"
	}
	response = requests.post(url, data=data)

	try:
		json_data = response.json()
		print("🔁 DeepL response:", response.status_code, response.text)  # ✅ print for Render logs

		if "translations" in json_data:
			return json_data["translations"][0]["text"]
		elif "message" in json_data:
			return f"❌ DeepL API Error: {json_data['message']}"
		else:
			return "❌ Unknown translation error."
	except Exception as e:
		return f"❌ API failure: {str(e)}"


def get_feedback(student_version, correct_version):
	from german_sentence_game import Fore, Style  # if needed from separate module

	student_words = student_version.strip().split()
	correct_words = correct_version.strip().split()

	output = []
	explanation = []

	# Detect sentence type (case-insensitive)
	w_question_words = [
		"wie", "was", "wann", "wo", "warum", "wer", "wieso", "woher", "wohin", "welche", "welcher", "welches"
	]

	first_word = correct_words[0].lower() if correct_words else ""
	is_question = correct_version.strip().endswith("?")
	is_w_question = is_question and first_word in w_question_words
	is_yesno_question = is_question and not is_w_question and first_word not in w_question_words and first_word.isalpha()

	# Special case: same words, wrong order (case-insensitive)
	if sorted([w.lower() for w in student_words]) == sorted([w.lower() for w in correct_words]) \
			and [w.lower() for w in student_words] != [w.lower() for w in correct_words]:

		output_colored = []
		for idx, word in enumerate(student_words):
			correct_word = correct_words[idx] if idx < len(correct_words) else ""
			if word.lower() == correct_word.lower():
				output_colored.append(Fore.GREEN + word + Style.RESET_ALL)
			elif word.lower() in [w.lower() for w in correct_words]:
				output_colored.append(Fore.RED + word + Style.RESET_ALL)
			else:
				output_colored.append(Fore.YELLOW + word + Style.RESET_ALL)

		if is_w_question:
			feedback_text = (
				"⚠️ Your words are correct, but the **word order is incorrect for a W-question**.\n"
				"📘 Rule: **W-word – Verb – Subject – ...**\n"
				"📌 Example: *Wie ist das Wetter heute?*\n"
				"🛠️ Make sure the conjugated verb comes right after the W-word.\n"
				f"\n🧩 Your version: {' '.join(output_colored)}"
			)
		elif is_yesno_question:
			feedback_text = (
				"⚠️ Your words are correct, but the **word order is incorrect for a yes/no question**.\n"
				"📘 Rule: **Verb – Subject – Object – ...**\n"
				"📌 Example: *Geht er heute zur Schule?*\n"
				"🛠️ In yes/no questions, the conjugated verb must be at the beginning.\n"
				f"\n🧩 Your version: {' '.join(output_colored)}"
			)
		else:
			feedback_text = (
				"⚠️ Your words are correct, but the **word order is incorrect for a main clause**.\n"
				"📘 Rule: **Subject – Verb – Time – Manner – Place – Object – Infinitive**\n"
				"📌 Example: *Ich gehe heute mit meinem Hund spazieren.*\n"
				"👀 Pay attention to time/place blocks and that the **conjugated verb is always in second position**.\n"
				f"\n🧩 Your version: {' '.join(output_colored)}"
			)

		return False, feedback_text

	# Else: full comparison (still colorized and case-sensitive for learner clarity)
	import difflib
	sm = difflib.SequenceMatcher(None, correct_words, student_words)
	opcodes = sm.get_opcodes()

	for tag, i1, i2, j1, j2 in opcodes:
		if tag == 'equal':
			for w in correct_words[i1:i2]:
				output.append(Fore.GREEN + w + Style.RESET_ALL)
		elif tag == 'replace':
			for w1, w2 in zip(correct_words[i1:i2], student_words[j1:j2]):
				output.append(Fore.RED + w2 + Style.RESET_ALL)
				explanation.append(f"❌ '{w2}' sollte '{w1}' sein.")
		elif tag == 'delete':
			for w in correct_words[i1:i2]:
				output.append(Fore.RED + "___" + Style.RESET_ALL)
				explanation.append(f"❌ Es fehlt das Wort '{w}'.")
		elif tag == 'insert':
			for w in student_words[j1:j2]:
				output.append(Fore.YELLOW + w + Style.RESET_ALL)
				explanation.append(f"🟡 Zusätzliches Wort: '{w}'")

	all_correct = len(explanation) == 0

	if all_correct:
		feedback_text = "✅ Deine Übersetzung ist korrekt!"
	else:
		feedback_text = " ".join(output) + "\n\n📘 Erklärungen:\n" + "\n".join(explanation)

	return all_correct, feedback_text

# Level 1 game
LEVELS = [
	"Ich heiße Anna",
	"Wir wohnen in Berlin",
	"Er trinkt jeden Morgen Kaffee",
	"Morgen fahre ich mit dem Bus zur Schule",
	"Am Wochenende spiele ich gern Fußball",
	"Sie möchte ein neues Auto kaufen",
	"Kannst du mir bitte helfen",
	"Ich habe gestern einen interessanten Film gesehen",
	"Wenn ich Zeit habe, besuche ich meine Großeltern",
	"Obwohl es regnet, gehen wir spazieren"
]

def play_level(level, sentence):
	words = sentence.split()
	scrambled = words[:]
	random.shuffle(scrambled)

	print(f"\n🧩 Level {level+1}:\n👉 Ordne die Wörter richtig:")
	print(" ".join(scrambled))

	answer = input("\n✍️ Deine Antwort:\n> ").strip()
	correct = (answer == sentence)
	status = "Richtig" if correct else "Falsch"
	return correct, status, answer

def explain_word_order(correct_sentence):
	print("\n📚 Erklärung zur Wortstellung:")
	print("➡️ Subjekt – Verb – (Zeit) – (Art und Weise) – (Ort) – Objekt – [Infinitiv am Ende]\n")
	print("👉 Korrekte Reihenfolge:")
	print(f"➡️ {correct_sentence}")
	print("🔁 Achte darauf, dass das konjugierte Verb immer an zweiter Stelle steht!")

def mode_one(name):
	score = 0
	for i, sentence in enumerate(LEVELS):
		correct, status, user_answer = play_level(i, sentence)

		if correct:
			print("✅ Richtig! Weiter so!")
			score += 1
		else:
			print("❌ Das war nicht korrekt.")
			explain_word_order(sentence)

		result_line = f"Level {i+1} - {name}: {status} ({user_answer})\n"
		encrypted = simple_encrypt(result_line)

		with open(ENC_FILE, "a") as f:
			f.write(encrypted + "\n")

	print("\n🏁 Spiel beendet!")
	print(f"🎯 {name}, dein Ergebnis: {score}/10")

def mode_two(name):
	print("\n✏️ Enter an English sentence. The system will translate it automatically into German.")
	print("Then you'll type your own translation and get feedback.\n")

	while True:
		english = input("📘 English (or 'q' to quit):\n> ").strip()
		if english.lower() == 'q':
			break

		try:
			print("⏳ Translating locally with transformer model...")
			correct_german = translate_to_german(english)

			while True:
				student_input = input("\n📙 Your German translation (or '3' to reveal solution):\n> ").strip()

				if student_input == '3':
					print(f"\n🤖 Model translation:\n➡️ {correct_german}")
					print("ℹ️ Feedback skipped.\n")
					break

				print(f"\n🤖 Model translation:\n➡️ {correct_german}")

				correct, feedback = get_feedback(student_input, correct_german)
				print(f"\n📝 Feedback:\n{feedback}")

				# Save clean version only (without color codes)
				clean_feedback = feedback.replace(Fore.GREEN, "").replace(Fore.RED, "").replace(Fore.YELLOW, "").replace(Style.RESET_ALL, "")
				result_line = f"{name} - EN: {english} | DE: {student_input} => {clean_feedback}\n"
				encrypted = simple_encrypt(result_line)

				with open(ENC_FILE, "a") as f:
					f.write(encrypted + "\n")

				if correct:
					break
				else:
					print("🔁 Try again or type '3' to reveal the solution.")

		except Exception as e:
			print("⚠️ Error during processing:", e)


def main():
	print("🧠 Willkommen zum Satz-Bau-Spiel!")
	name = input("Wie heißt du? > ")
	global ENC_FILE
	ENC_FILE = f"{name}_result.enc"

	print("\nWähle den Modus:")
	print("1️⃣ Satz-Reihenfolge-Spiel (A1–B1)")
	print("2️⃣ Freie Übersetzung + Offline-Feedback (Transformers)")

	choice = input("\nModus wählen (1 oder 2): ").strip()

	if choice == "1":
		mode_one(name)
	elif choice == "2":
		mode_two(name)
	else:
		print("❌ Ungültige Auswahl.")

if __name__ == "__main__":
	try:
		main()
	except KeyboardInterrupt:
		print("\n👋 Auf Wiedersehen!")
		sys.exit(0)

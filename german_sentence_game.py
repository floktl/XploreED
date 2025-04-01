import os
import sys
import subprocess
import random
import difflib
import signal
import warnings
warnings.filterwarnings("ignore", message="Recommended: pip install sacremoses.")

# Auto-install required packages
def ensure_packages():
	required = ["transformers", "torch", "sentencepiece", "colorama"]
	for pkg in required:
		try:
			__import__(pkg)
		except ImportError:
			print(f"📦 Installing missing package: {pkg}")
			subprocess.check_call([sys.executable, "-m", "pip", "install", pkg])

ensure_packages()

from transformers import MarianMTModel, MarianTokenizer
from colorama import Fore, Style, init as colorama_init
colorama_init()

# Load model
model_name = "Helsinki-NLP/opus-mt-en-de"
tokenizer = MarianTokenizer.from_pretrained(model_name)
model = MarianMTModel.from_pretrained(model_name)

ENC_FILE = "results.enc"

def simple_encrypt(text, shift=3):
	return ''.join(chr((ord(c) + shift) % 256) for c in text)

def translate_to_german(english_sentence):
	inputs = tokenizer([english_sentence], return_tensors="pt", padding=True)
	translated = model.generate(**inputs)
	german = tokenizer.decode(translated[0], skip_special_tokens=True)
	return german

def get_feedback(student_version, correct_version):
	student_words = student_version.strip().split()
	correct_words = correct_version.strip().split()

	output = []
	explanation = []

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

	all_correct = (len(explanation) == 0)
	feedback_text = "✅ Deine Übersetzung ist korrekt!" if all_correct else (
		" ".join(output) + "\n\n📘 Erklärungen:\n" + "\n".join(explanation)
	)
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

			student_input = input("\n📙 Your German translation:\n> ").strip()

			print(f"\n🤖 Model translation:\n➡️ {correct_german}")

			correct, feedback = get_feedback(student_input, correct_german)
			print(f"\n📝 Feedback:\n{feedback}")

			# Save clean version only (without color codes)
			clean_feedback = feedback.replace(Fore.GREEN, "").replace(Fore.RED, "").replace(Fore.YELLOW, "").replace(Style.RESET_ALL, "")
			result_line = f"{name} - EN: {english} | DE: {student_input} => {clean_feedback}\n"
			encrypted = simple_encrypt(result_line)

			with open(ENC_FILE, "a") as f:
				f.write(encrypted + "\n")

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

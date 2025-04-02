from flask import Flask, render_template, request
import re
from german_sentence_game import translate_to_german, get_feedback

def ansi_to_html(text):
    ansi_codes = {
        '\x1b[32m': '<span style="color: green;">',
        '\x1b[31m': '<span style="color: red;">',
        '\x1b[33m': '<span style="color: orange;">',
        '\x1b[0m': '</span>'
    }

    pattern = re.compile('|'.join(re.escape(code) for code in ansi_codes))
    return pattern.sub(lambda m: ansi_codes[m.group()], text)

app = Flask(__name__)

@app.route('/', methods=['GET', 'POST'])
def index():
    sentence = None
    student_input = None
    feedback = None
    correct = None
    correct_translation = None

    if request.method == 'POST':
        english = request.form.get('english', '').strip()
        student_input = request.form.get('student_input', '').strip()

        if english:
            correct_translation = translate_to_german(english)

            if student_input:
                correct, raw_feedback = get_feedback(student_input, correct_translation)
                feedback = ansi_to_html(raw_feedback)  # 💡 convert to HTML here

    return render_template(
        'index.html',
        sentence=sentence,
        student_input=student_input,
        feedback=feedback,
        correct_translation=correct_translation
    )


if __name__ == '__main__':
    app.run(debug=True)

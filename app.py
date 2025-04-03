# ✅ Updated to personalize entire app per user
# app.py adjustments (store name in session + save results per user)
from flask import Flask, render_template, request, redirect, url_for, session
import re
import os
from german_sentence_game import (
    translate_to_german, get_feedback, get_scrambled_sentence,
    evaluate_order, LEVELS, save_result, get_all_results, init_db, User
)
from dotenv import load_dotenv

import sqlite3

load_dotenv()
init_db()

ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "admin123")  # Can be set in .env

app = Flask(__name__)
app.secret_key = 'super-secret-key'

def ansi_to_html(text):
    ansi_codes = {
        '\x1b[32m': '<span style="color: green;">',
        '\x1b[31m': '<span style="color: red;">',
        '\x1b[33m': '<span style="color: orange;">',
        '\x1b[0m': '</span>'
    }
    pattern = re.compile('|'.join(re.escape(code) for code in ansi_codes))
    return pattern.sub(lambda m: ansi_codes[m.group()], text)

user_profiles = {} 

@app.route('/', methods=['GET', 'POST'])
def get_name():
    if 'name' in session:
        return redirect(url_for('menu'))  # ✅ already logged in, go to menu

    if request.method == 'POST':
        session['name'] = request.form.get('name')
        return redirect(url_for('menu'))

    return render_template('name.html')


@app.route('/menu')
def menu():
    name = session.get('name', None)
    if not name:
        return redirect('/')
    return render_template('index.html', name=name)

@app.route('/translate', methods=['GET', 'POST'])
def translate():
    name = session.get('name', None)
    if not name:
        return redirect('/')

    if request.method == 'GET':
        return render_template('translate.html', name=name)

    english = request.form.get('english', '').strip()
    student_input = request.form.get('student_input', '').strip()
    

    correct_translation = translate_to_german(english, username=name)

    feedback = ""
    if student_input:
        correct, raw_feedback = get_feedback(student_input, correct_translation)
        feedback = ansi_to_html(raw_feedback)
        save_result(name, -1, correct, student_input)

    return render_template('translate.html',
                           english=english,
                           student_input=student_input,
                           correct_translation=correct_translation,
                           feedback=feedback,
                           name=name)


@app.route('/level-game', methods=['GET', 'POST'])
def level_game():
    name = session.get('name', None)
    if not name:
        return redirect('/')

    level = int(request.form.get("level", 0))
    sentence = LEVELS[level]
    scrambled = get_scrambled_sentence(sentence)

    if request.method == 'POST' and "user_answer" in request.form:
        answer = request.form["user_answer"]
        correct, raw_feedback = evaluate_order(answer, sentence)
        feedback = ansi_to_html(raw_feedback)
        save_result(name, level, correct, answer)
        return render_template('level.html', level=level, scrambled=scrambled, feedback=feedback,
                               correct_sentence=sentence, user_answer=answer, name=name)

    return render_template('level.html', level=level, scrambled=scrambled, name=name)

@app.route('/profile')
def profile():
    name = session.get("name")
    if not name:
        return redirect("/")

    user = user_profiles.get(name, User(name))
    with sqlite3.connect("game_results.db") as conn:
        cursor = conn.execute("SELECT level, correct, answer, timestamp FROM results WHERE username = ? ORDER BY timestamp DESC", (name,))
        history = cursor.fetchall()
        for lvl, cor, ans, ts in history:
            user.add_result(lvl, cor, ans, ts)

    return render_template("profile.html", user=user)

@app.route('/admin', methods=['GET', 'POST'])
def admin():
    if request.method == 'POST':
        password = request.form.get("password")
        if password == ADMIN_PASSWORD:
            session['is_admin'] = True
            return redirect(url_for('admin_dashboard'))
        else:
            flash("❌ Wrong password.", "error")
            return redirect(url_for('admin'))

    return render_template('admin_login.html')

@app.route('/admin/dashboard')
def admin_dashboard():
    if not session.get('is_admin'):
        return redirect(url_for('admin'))
    results = get_all_results()
    return render_template('admin.html', results=results)

@app.route('/logout')
def logout():
    session.clear()
    return redirect('/')

@app.route('/vocabulary')
def vocabulary():
    name = session.get("name")
    if not name:
        return redirect("/")

    with sqlite3.connect("game_results.db") as conn:
        cursor = conn.execute("SELECT DISTINCT vocab, translation FROM vocab_log WHERE username = ?", (name,))
        vocab_list = cursor.fetchall()

    return render_template("vocabulary.html", vocab_list=vocab_list, name=name)



if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)

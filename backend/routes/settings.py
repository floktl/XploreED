"""Account settings endpoints."""

from utils.imports.imports import *

@settings_bp.route('/password', methods=['POST'])
def update_password_route():
    user = get_current_user()
    if not user:
        return jsonify({'error': 'Unauthorized'}), 401
    data = request.get_json() or {}
    current_pw = data.get('current_password', '')
    new_pw = data.get('new_password', '')
    if not current_pw or not new_pw:
        return jsonify({'error': 'Missing fields'}), 400

    row = fetch_one('users', 'WHERE username = ?', (user,))
    if not row or not check_password_hash(row['password'], current_pw):
        return jsonify({'error': 'Incorrect password'}), 400

    hashed = generate_password_hash(new_pw)
    update_row('users', {'password': hashed}, 'username = ?', (user,))
    return jsonify({'msg': 'password updated'})


@settings_bp.route('/avatar', methods=['POST'])
def upload_avatar_route():
    user = get_current_user()
    if not user:
        return jsonify({'error': 'Unauthorized'}), 401

    if 'avatar' not in request.files:
        return jsonify({'error': 'No file provided'}), 400

    file = request.files['avatar']
    if file.filename == '':
        return jsonify({'error': 'Empty filename'}), 400

    avatar_dir = os.path.join('backend', 'avatars')
    os.makedirs(avatar_dir, exist_ok=True)
    path = os.path.join(avatar_dir, f"{user}.png")
    file.save(path)
    return jsonify({'msg': 'avatar uploaded'})


@settings_bp.route('/deactivate', methods=['POST'])
def deactivate_account_route():
    user = get_current_user()
    if not user:
        return jsonify({'error': 'Unauthorized'}), 401

    data = request.get_json() or {}
    delete_all = bool(data.get('delete_all'))

    if delete_all:
        delete_rows('results', 'WHERE username = ?', (user,))
        delete_rows('vocab_log', 'WHERE username = ?', (user,))
    else:
        update_row('results', {'username': 'anon'}, 'username = ?', (user,))
        update_row('vocab_log', {'username': 'anon'}, 'username = ?', (user,))

    delete_rows('users', 'WHERE username = ?', (user,))
    session_manager.destroy_session(request.cookies.get('session_id'))
    resp = make_response(jsonify({'msg': 'account deleted'}))
    resp.set_cookie('session_id', '', max_age=0)
    return resp

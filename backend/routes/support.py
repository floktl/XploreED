from utils.imports.imports import *

@support_bp.route('/feedback', methods=['POST'])
def post_feedback():
    data = request.get_json() or {}
    message = (data.get('message') or '').strip()
    if not message:
        return jsonify({'error': 'Message required'}), 400
    insert_row('support_feedback', {'message': message})
    return jsonify({'status': 'ok'})


@support_bp.route('/feedback', methods=['GET'])
def get_feedback_list():
    if not is_admin():
        return jsonify({'msg': 'Unauthorized'}), 401
    rows = fetch_custom('SELECT id, message, created_at FROM support_feedback ORDER BY id DESC')
    return jsonify(rows or [])

"""Endpoints allowing users to send feedback messages."""

from utils.imports.imports import *

@support_bp.route('/feedback', methods=['POST'])
def post_feedback():
    """Store a short feedback message from any user."""
    data = request.get_json() or {}
    message = (data.get('message') or '').strip()
    if not message:
        return jsonify({'error': 'Message required'}), 400
    insert_row('support_feedback', {'message': message})
    return jsonify({'status': 'ok'})


@support_bp.route('/feedback', methods=['GET'])
def get_feedback_list():
    """Return a list of feedback messages (admin only)."""
    if not is_admin():
        return jsonify({'msg': 'Unauthorized'}), 401
    rows = select_rows(
        "support_feedback",
        columns=["id", "message", "created_at"],
        order_by="id DESC",
    )
    return jsonify(rows or [])

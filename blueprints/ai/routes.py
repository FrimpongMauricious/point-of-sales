from flask import Blueprint, request, jsonify, session
from flask_login import login_required, current_user
from services.ai_assistant import get_ai_response

ai_bp = Blueprint('ai', __name__, url_prefix='/ai')


@ai_bp.route('/chat', methods=['POST'])
@login_required
def chat():
    data = request.get_json() or {}
    user_message = (data.get('message') or '').strip()

    if not user_message:
        return jsonify({'success': False, 'message': 'Empty message.'}), 400

    # Maintain conversation history per user session
    history_key = f'ai_history_{current_user.id}'
    history = session.get(history_key, [])

    try:
        reply = get_ai_response(history, user_message)
    except Exception as e:
        return jsonify({'success': False, 'message': f'AI error: {str(e)}'}), 500

    # Append to history
    history.append({'role': 'user', 'content': user_message})
    history.append({'role': 'assistant', 'content': reply})

    # Keep only last 20 messages (10 exchanges) to avoid session bloat
    session[history_key] = history[-20:]
    session.modified = True

    return jsonify({'success': True, 'reply': reply})


@ai_bp.route('/clear', methods=['POST'])
@login_required
def clear_history():
    session.pop(f'ai_history_{current_user.id}', None)
    return jsonify({'success': True})

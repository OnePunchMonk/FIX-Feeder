from flask import Blueprint, jsonify, request
from dashboard.db import get_db_connection 

api_bp = Blueprint('api', __name__, url_prefix='/api')

@api_bp.route('/messages', methods=['GET'])
def get_messages():
    """Get the last N messages."""
    limit = request.args.get('limit', 50, type=int)
    
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT id, msg_seq_num, sending_time FROM fix_messages ORDER BY id DESC LIMIT %s', (limit,))
    messages = cursor.fetchall()
    cursor.close()
    conn.close()
    
    return jsonify([dict(row) for row in messages])

@api_bp.route('/message/<int:msg_id>', methods=['GET'])
def get_message_by_id(msg_id):
    """Get a specific message by its database ID."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM fix_messages WHERE id = %s', (msg_id,))
    message = cursor.fetchone()
    cursor.close()
    conn.close()
    
    if message:
        return jsonify(dict(message))
    else:
        return jsonify({"error": "Message not found"}), 404
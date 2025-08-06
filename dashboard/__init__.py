from flask import Flask, render_template
from api.routes import api_bp
from dashboard.db import get_db_connection

app = Flask(__name__)
app.register_blueprint(api_bp) # Register the API

@app.route('/')
def index():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM fix_messages ORDER BY id DESC LIMIT 50')
    messages = cursor.fetchall()
    cursor.close()
    conn.close()
    return render_template('index.html', messages=messages)

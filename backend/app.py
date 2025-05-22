import os
import psycopg2
from flask import Flask, request, jsonify
from flask_cors import CORS

app = Flask(__name__)
CORS(app, origins=["http://localhost:3000"])

db_config = {
    "host": os.getenv("DB_HOST", "db"),
    "dbname": os.getenv("POSTGRES_DB", "mydb"),
    "user": os.getenv("POSTGRES_USER", "dev"),
    "password": os.getenv("POSTGRES_PASSWORD", "dev")
}

def get_connection():
    return psycopg2.connect(**db_config)

def init_db():
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS messages (
            id SERIAL PRIMARY KEY,
            content TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
    """)
    conn.commit()
    cur.close()
    conn.close()

init_db()

@app.route("/health", methods=["GET"])
def health_check():
    return {"status": "ok"}

@app.route("/messages", methods=["GET"])
def get_messages():
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT id, content, created_at FROM messages ORDER BY created_at DESC;")
    rows = cur.fetchall()
    cur.close()
    conn.close()
    messages = [
        {"id": row[0], "content": row[1], "created_at": row[2].isoformat()}
        for row in rows
    ]
    return jsonify(messages)

@app.route("/messages", methods=["POST"])
def post_message():
    data = request.get_json()
    content = data.get("content")

    if not content:
        return jsonify({"error": "Content is required"}), 400

    conn = get_connection()
    cur = conn.cursor()
    cur.execute("INSERT INTO messages (content) VALUES (%s) RETURNING id;", (content,))
    new_id = cur.fetchone()[0]
    conn.commit()
    cur.close()
    conn.close()

    return jsonify({"message": "Message added", "id": new_id}), 201

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)

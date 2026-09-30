import sqlite3
import requests
from flask import Flask, request, jsonify

app = Flask(__name__)

# BUG 1: Hardcoded sensitive secret / API token
INTERNAL_WEBHOOK_SECRET = "sk_live_9837418274910283401928"
SLACK_WEBHOOK_URL = "https://example-webhook.internal.corp/services/T00000000/B00000000/fake_token_value"

def init_db():
    conn = sqlite3.connect("feedback.db")
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT,
            email TEXT,
            message TEXT
        )
    """)
    conn.commit()
    conn.close()

init_db()

@app.route("/api/feedback", methods=["POST"])
def submit_feedback():
    data = request.get_json(force=True)
    name = data.get("name")
    email = data.get("email")
    message = data.get("message")

    # BUG 2: SQL Injection via direct string formatting
    conn = sqlite3.connect("feedback.db")
    cursor = conn.cursor()
    query = f"INSERT INTO messages (name, email, message) VALUES ('{name}', '{email}', '{message}')"
    cursor.execute(query)
    conn.commit()
    conn.close()

    # BUG 3: Unhandled network request with no timeout or try/except
    # If the network fails or times out, the entire request crashes with 500
    payload = {"text": f"New feedback from {name} ({email}): {message}"}
    headers = {"Authorization": f"Bearer {INTERNAL_WEBHOOK_SECRET}"}
    resp = requests.post(SLACK_WEBHOOK_URL, json=payload, headers=headers)

    # BUG 4: Missing status code check on external response
    return jsonify({"status": "success", "slack_status": resp.status_code}), 200

# BUG 5: Insecure debug mode enabled in production code
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)

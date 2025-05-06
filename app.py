from flask import Flask, request
import os

app = Flask(__name__)

VERIFY_TOKEN = os.getenv("VERIFY_TOKEN", "mydrsmileverifytoken123")

@app.route("/webhook", methods=["GET", "POST"])
def webhook():
    if request.method == "GET":
        if request.args.get("hub.mode") == "subscribe" and request.args.get("hub.verify_token") == VERIFY_TOKEN:
            return request.args.get("hub.challenge"), 200
        return "Unauthorized", 403

    elif request.method == "POST":
        data = request.get_json()
        print("[📩 Incoming message]", data)
        return "EVENT_RECEIVED", 200

@app.route("/")
def home():
    return "✅ Dr. Smile Chatbot is running."

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)

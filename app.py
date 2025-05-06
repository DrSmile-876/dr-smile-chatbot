from flask import Flask, request

app = Flask(__name__)

VERIFY_TOKEN = "drsmile_secret"  # Must match what you enter on Meta

@app.route("/webhook", methods=["GET", "POST"])
def webhook():
    if request.method == "GET":
        mode = request.args.get("hub.mode")
        token = request.args.get("hub.verify_token")
        challenge = request.args.get("hub.challenge")

        if mode == "subscribe" and token == VERIFY_TOKEN:
            print("✅ WEBHOOK_VERIFIED")
            return challenge, 200
        else:
            print("❌ Invalid token")
            return "Invalid verify token", 403

    if request.method == "POST":
        data = request.json
        print("📩 New Message:", data)
        return "EVENT_RECEIVED", 200

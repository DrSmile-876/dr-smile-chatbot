import os
import requests
from flask import Flask, request, jsonify

app = Flask(__name__)

# Environment Variables (fallbacks included for local/dev)
VERIFY_TOKEN = os.getenv("VERIFY_TOKEN", "mydrsmileverifytoken123")
PAGE_ACCESS_TOKEN = os.getenv("PAGE_ACCESS_TOKEN")
FB_CLIENT_ID = os.getenv("FB_CLIENT_ID")
FB_CLIENT_SECRET = os.getenv("FB_CLIENT_SECRET")
FB_REFRESH_TOKEN = os.getenv("FB_REFRESH_TOKEN")

# ✅ Webhook Verification and Incoming Events
@app.route("/webhook", methods=["GET", "POST"])
def webhook():
    if request.method == "GET":
        mode = request.args.get("hub.mode")
        token = request.args.get("hub.verify_token")
        challenge = request.args.get("hub.challenge")

        print(f"🔍 FB Raw GET Params: {request.args}")
        print(f"🚨 Webhook GET — mode: {mode}, token: {token}, challenge: {challenge}")
        print(f"🔐 Expected VERIFY_TOKEN: {VERIFY_TOKEN}")

        # TEMPORARY override for Facebook's inconsistent GETs — revert after confirmation
        if challenge:
            return challenge, 200
        return "Missing challenge", 403

    elif request.method == "POST":
        data = request.get_json()
        print(f"[📩 Incoming] Message Payload: {data}")
        # Here you can add chatbot response logic
        return "EVENT_RECEIVED", 200

# 🔄 Token Refresh (long-lived access token generator)
@app.route("/refresh-token", methods=["GET"])
def refresh_token():
    try:
        url = "https://graph.facebook.com/v18.0/oauth/access_token"
        params = {
            "grant_type": "fb_exchange_token",
            "client_id": FB_CLIENT_ID,
            "client_secret": FB_CLIENT_SECRET,
            "fb_exchange_token": FB_REFRESH_TOKEN
        }
        res = requests.get(url, params=params)
        data = res.json()

        if "access_token" in data:
            return jsonify({
                "status": "success",
                "new_token": data["access_token"],
                "expires_in": data.get("expires_in", "unknown")
            })
        else:
            return jsonify({"status": "error", "details": data}), 400

    except Exception as e:
        return jsonify({"status": "fail", "error": str(e)}), 500

# ✅ Health Check
@app.route("/")
def home():
    return "Dr. Smile Chatbot + Token Refresher Active ✅"

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)

import os
import requests
from flask import Flask, request, jsonify
import threading
import time

app = Flask(__name__)

VERIFY_TOKEN = os.getenv("VERIFY_TOKEN", "mydrsmileverifytoken123")
PAGE_ACCESS_TOKEN = os.getenv("PAGE_ACCESS_TOKEN")
PING_INTERVAL = 840  # 14 minutes
RENDER_EXTERNAL_URL = os.getenv("RENDER_EXTERNAL_URL", "https://your-render-url.onrender.com")


# ✅ FACEBOOK CHATBOT VERIFICATION
@app.route("/webhook", methods=["GET", "POST"])
def webhook():
    if request.method == "GET":
        print(f"🔍 FB Raw GET Params: {request.args}")
        mode = request.args.get("hub.mode")
        token = request.args.get("hub.verify_token")
        challenge = request.args.get("hub.challenge")

        print(f"🚨 Webhook GET — mode: {mode}, token: {token}, challenge: {challenge}")
        print(f"🔐 Expected VERIFY_TOKEN: {VERIFY_TOKEN}")

        if mode == "subscribe" and token == VERIFY_TOKEN:
            return challenge, 200
        return "Forbidden: Token mismatch or missing params", 403

    elif request.method == "POST":
        try:
            data = request.get_json()
            print(f"[Chatbot] Incoming message: {data}")
            return "EVENT_RECEIVED", 200
        except Exception as e:
            print(f"❌ Error in POST handler: {e}")
            return "Error", 500


# 🔄 TOKEN REFRESH ENDPOINT
@app.route("/refresh-token", methods=["GET"])
def refresh_token():
    try:
        url = f"https://graph.facebook.com/v18.0/oauth/access_token"
        params = {
            "grant_type": "fb_exchange_token",
            "client_id": os.getenv("FB_CLIENT_ID"),
            "client_secret": os.getenv("FB_CLIENT_SECRET"),
            "fb_exchange_token": os.getenv("FB_REFRESH_TOKEN")
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


# ✅ HOME ROUTE
@app.route("/")
def home():
    return "Dr. Smile Chatbot + Token Refresher Active ✅"


# 🔁 KEEP-ALIVE PINGER
def keep_alive():
    while True:
        try:
            time.sleep(PING_INTERVAL)
            print(f"🔄 Pinging self at {RENDER_EXTERNAL_URL}")
            requests.get(RENDER_EXTERNAL_URL)
        except Exception as e:
            print(f"❌ Ping error: {e}")


if __name__ == "__main__":
    threading.Thread(target=keep_alive, daemon=True).start()
    app.run(host="0.0.0.0", port=10000)

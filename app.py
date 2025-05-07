import os
import threading
import time
import requests
from flask import Flask, request, jsonify

app = Flask(__name__)

VERIFY_TOKEN = os.getenv("VERIFY_TOKEN", "mydrsmileverifytoken123")
PAGE_ACCESS_TOKEN = os.getenv("PAGE_ACCESS_TOKEN")

# ✅ FACEBOOK CHATBOT VERIFICATION
@app.route("/webhook", methods=["GET", "POST"])
def webhook():
    if request.method == "GET":
        mode = request.args.get("hub.mode")
        token = request.args.get("hub.verify_token")
        challenge = request.args.get("hub.challenge")

        print(f"🚨 Webhook GET — mode: {mode}, token: {token}, challenge: {challenge}")
        print(f"🔐 Expected VERIFY_TOKEN: {VERIFY_TOKEN}")

        if mode == "subscribe" and token == VERIFY_TOKEN:
            return challenge, 200
        else:
            return "Forbidden: Token mismatch or wrong mode", 403

    elif request.method == "POST":
        data = request.get_json()
        print(f"[Chatbot] Incoming message: {data}")
        return "EVENT_RECEIVED", 200

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

# 🛡️ KEEP ALIVE PING FUNCTION
def keep_alive_ping():
    while True:
        try:
            print("🔁 Sending self-ping to keep Render app alive...")
            url = os.getenv("RENDER_EXTERNAL_URL") or "https://dr-smile-chatbot.onrender.com"
            requests.get(url)
        except Exception as e:
            print(f"⚠️ Ping failed: {e}")
        time.sleep(840)  # Every 14 minutes (840 sec)

if __name__ == "__main__":
    # 🔁 Start keep-alive thread
    threading.Thread(target=keep_alive_ping, daemon=True).start()

    # 🚀 Launch Flask app
    app.run(host="0.0.0.0", port=10000)

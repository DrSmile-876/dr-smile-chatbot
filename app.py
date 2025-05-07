import os
import requests
import threading
import time
import json
import logging
from flask import Flask, request, jsonify

app = Flask(__name__)

# ✅ Setup Logging
logging.basicConfig(level=logging.INFO, filename="app.log", filemode="a",
                    format="%(asctime)s - %(levelname)s - %(message)s")

# ✅ Load environment
VERIFY_TOKEN = os.getenv("VERIFY_TOKEN", "mydrsmileverifytoken123")
RENDER_EXTERNAL_URL = os.getenv("RENDER_EXTERNAL_URL", "https://your-render-url.onrender.com")
TOKEN_FILE = os.getenv("TOKEN_FILE", "tokens.json")
PING_INTERVAL = 840  # 14 min

# ✅ Load access token from file
def load_token():
    try:
        with open(TOKEN_FILE, "r") as f:
            data = json.load(f)
            return data.get("access_token")
    except Exception as e:
        logging.error(f"Error reading token file: {e}")
        return os.getenv("PAGE_ACCESS_TOKEN", "")

# ✅ Save access token to file
def save_token(token):
    try:
        with open(TOKEN_FILE, "w") as f:
            json.dump({"access_token": token}, f)
        logging.info("Access token saved.")
    except Exception as e:
        logging.error(f"Error writing token file: {e}")

PAGE_ACCESS_TOKEN = load_token()

# ✅ Webhook Handler
@app.route("/webhook", methods=["GET", "POST"])
def webhook():
    if request.method == "GET":
        logging.info(f"Webhook GET Params: {request.args}")
        mode = request.args.get("hub.mode")
        token = request.args.get("hub.verify_token")
        challenge = request.args.get("hub.challenge")

        if mode == "subscribe" and token == VERIFY_TOKEN and challenge:
            return challenge, 200
        return "Forbidden: Token mismatch or missing parameters", 403

    elif request.method == "POST":
        try:
            data = request.get_json(force=True)
            logging.info(f"[📩 Chatbot] Message: {data}")
            return "EVENT_RECEIVED", 200
        except Exception as e:
            logging.error(f"Webhook POST error: {e}")
            return "Error", 500

# 🔁 Token Refresh Endpoint
@app.route("/refresh-token", methods=["GET"])
def refresh_token():
    try:
        res = requests.get("https://graph.facebook.com/v18.0/oauth/access_token", params={
            "grant_type": "fb_exchange_token",
            "client_id": os.getenv("FB_CLIENT_ID"),
            "client_secret": os.getenv("FB_CLIENT_SECRET"),
            "fb_exchange_token": os.getenv("FB_REFRESH_TOKEN")
        })
        data = res.json()

        if "access_token" in data:
            new_token = data["access_token"]
            save_token(new_token)
            return jsonify({
                "status": "success",
                "new_token": new_token,
                "expires_in": data.get("expires_in", "unknown")
            })
        return jsonify({"status": "error", "details": data}), 400
    except Exception as e:
        logging.error(f"Token refresh error: {e}")
        return jsonify({"status": "fail", "error": str(e)}), 500

# ✅ Home Route
@app.route("/")
def home():
    return "Dr. Smile Chatbot + Token Auto-Refresh + Keep Alive ✅"

# 🔁 Keep Alive
def keep_alive():
    while True:
        try:
            logging.info(f"🔄 Pinging {RENDER_EXTERNAL_URL}")
            requests.get(RENDER_EXTERNAL_URL, timeout=10)
        except Exception as e:
            logging.warning(f"Keep-alive failed: {e}")
        time.sleep(PING_INTERVAL)

# ✅ Start App
if __name__ == "__main__":
    threading.Thread(target=keep_alive, daemon=True).start()
    app.run(host="0.0.0.0", port=10000)

import os
import requests
from flask import Flask, request, jsonify

app = Flask(__name__)

VERIFY_TOKEN = os.getenv("VERIFY_TOKEN", "mydrsmileverifytoken123")
PAGE_ACCESS_TOKEN = os.getenv("PAGE_ACCESS_TOKEN")

# ✅ FACEBOOK CHATBOT VERIFICATION
@app.route("/webhook", methods=["GET", "POST"])
def webhook():
    if request.method == "GET":
        if request.args.get("hub.verify_token") == VERIFY_TOKEN:
            return request.args.get("hub.challenge")
        return "Forbidden", 403

    elif request.method == "POST":
        data = request.get_json()
        # ➕ Add your chatbot logic here if needed
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

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)

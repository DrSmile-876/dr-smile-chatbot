import os
import requests
from flask import Flask, request, jsonify

app = Flask(__name__)

# ENV values you must set in your Render or GitHub secret settings
CLIENT_ID = os.getenv("FB_CLIENT_ID")  # From Facebook Developer App
CLIENT_SECRET = os.getenv("FB_CLIENT_SECRET")
REFRESH_TOKEN = os.getenv("FB_REFRESH_TOKEN")  # Long-lived user token
REDIRECT_URI = os.getenv("FB_REDIRECT_URI")

@app.route("/refresh-token", methods=["GET"])
def refresh_token():
    try:
        url = f"https://graph.facebook.com/v18.0/oauth/access_token"
        params = {
            "grant_type": "fb_exchange_token",
            "client_id": CLIENT_ID,
            "client_secret": CLIENT_SECRET,
            "fb_exchange_token": REFRESH_TOKEN
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

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10001)

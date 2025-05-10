import os
import requests
from flask import Flask, request, jsonify
import threading
import time
import logging
import json

app = Flask(__name__)
logging.basicConfig(filename='drsmile.log', level=logging.INFO, format='%(asctime)s - %(message)s')

VERIFY_TOKEN = os.getenv("VERIFY_TOKEN", "mydrsmileverifytoken123")
PAGE_ACCESS_TOKEN = os.getenv("PAGE_ACCESS_TOKEN")
RENDER_EXTERNAL_URL = os.getenv("RENDER_EXTERNAL_URL", "https://dr-smile-chatbot.onrender.com")
PING_INTERVAL = 840
TOKEN_FILE = "access_token.json"

@app.route("/webhook", methods=["GET", "POST"])
def webhook():
    if request.method == "GET":
        mode = request.args.get("hub.mode")
        token = request.args.get("hub.verify_token")
        challenge = request.args.get("hub.challenge")
        if mode == "subscribe" and token == VERIFY_TOKEN:
            return challenge, 200
        return "Forbidden: Token mismatch", 403

    elif request.method == "POST":
        try:
            payload = request.get_json(force=True)
            logging.info(f"📩 Incoming: {json.dumps(payload)}")

            for entry in payload.get("entry", []):
                for messaging_event in entry.get("messaging", []):
                    sender_id = messaging_event.get("sender", {}).get("id")
                    message_text = messaging_event.get("message", {}).get("text", "")

                    if sender_id and message_text:
                        if "order" in message_text.lower():
                            send_message(sender_id, "🦷 Please enter your Order ID to confirm delivery:")
                        elif message_text.upper().startswith("DRSM-"):
                            # Confirmation step
                            response = confirm_order_id(message_text.strip())
                            send_message(sender_id, response)
                        else:
                            send_message(sender_id, f"👋 Thanks for reaching out! We received: \"{message_text}\"")
            return "EVENT_RECEIVED", 200
        except Exception as e:
            logging.error(f"❌ POST Error: {e}")
            return "Error", 500

def send_message(recipient_id, text):
    headers = {"Content-Type": "application/json"}
    data = {"recipient": {"id": recipient_id}, "message": {"text": text}}
    params = {"access_token": get_token()}
    response = requests.post("https://graph.facebook.com/v18.0/me/messages", headers=headers, params=params, json=data)
    logging.info(f"📤 Sent to {recipient_id}: {text} | Status: {response.status_code}")

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
            with open(TOKEN_FILE, "w") as f:
                json.dump(data, f)
            return jsonify({"status": "success", "token": data["access_token"]})
        return jsonify({"status": "fail", "details": data}), 400
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

def get_token():
    if os.path.exists(TOKEN_FILE):
        try:
            with open(TOKEN_FILE, "r") as f:
                return json.load(f).get("access_token", PAGE_ACCESS_TOKEN)
        except:
            pass
    return PAGE_ACCESS_TOKEN

@app.route("/healthz", methods=["GET"])
def health_check():
    return "OK", 200

def keep_alive():
    while True:
        try:
            logging.info(f"🔄 Pinging {RENDER_EXTERNAL_URL}")
            requests.get(RENDER_EXTERNAL_URL, timeout=10)
        except Exception as e:
            logging.error(f"❌ Ping failed: {e}")
        time.sleep(PING_INTERVAL)

# ✅ ORDER ID CONFIRMATION API (uses Google Apps Script endpoint)
def confirm_order_id(order_id):
    try:
        resp = requests.post(
            os.getenv("CONFIRM_ORDER_ENDPOINT"),
            json={"order_id": order_id},
            timeout=10
        )
        result = resp.json()
        if result.get("status") == "confirmed":
            return f"✅ Order {order_id} has been successfully confirmed as delivered!"
        else:
            return f"⚠️ Order {order_id} not found or already marked as delivered."
    except Exception as e:
        logging.error(f"Confirmation failed: {e}")
        return "⚠️ We encountered a problem confirming your order. Please try again."

if __name__ == "__main__":
    threading.Thread(target=keep_alive, daemon=True).start()
    app.run(host="0.0.0.0", port=10000)

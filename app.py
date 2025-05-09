import os
import requests
from flask import Flask, request, jsonify
import threading
import time
import logging
import json

app = Flask(__name__)

# ✅ Logging setup
logging.basicConfig(filename='drsmile.log', level=logging.INFO, format='%(asctime)s - %(message)s')

# ✅ Load environment variables
VERIFY_TOKEN = os.getenv("VERIFY_TOKEN", "mydrsmileverifytoken123")
PAGE_ACCESS_TOKEN = os.getenv("PAGE_ACCESS_TOKEN")
RENDER_EXTERNAL_URL = os.getenv("RENDER_EXTERNAL_URL", "https://dr-smile-chatbot.onrender.com")
PING_INTERVAL = 840  # 14 minutes
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
                    message_text = messaging_event.get("message", {}).get("text")

                    if sender_id and message_text:
                        lowered = message_text.lower()
                        if "order" in lowered:
                            send_message(sender_id, "🦷 Great! Please send your *delivery location* to begin your Dr. Smile Tooth Kit™ order.")
                        elif "paid" in lowered or "payment" in lowered:
                            send_message(sender_id, "✅ Please upload your payment confirmation or let us know your payment method (Cash on Delivery, Bank Transfer, PayPal, Pi Coin).")
                        elif "paypal" in lowered:
                            send_message(sender_id, "🔗 Pay securely for your Dr. Smile Tooth Kit™ via PayPal:\nhttps://www.paypal.com/ncp/payment/G77UEE4UY8DQQ")
                        elif "pi coin" in lowered:
                            send_message(sender_id, "💎 Send Pi Coin payments to:\n*MBC6NRTTQLRCABQHIR5J4R4YDJWFWRAO4ZRQIM2SVI5GSIZ2HZ42QAAAAAABEX5HINA7Y*\n\n⚠️ Only send Pi on the Pi Chain. Not on other networks. Use this referral if you're new: https://minepi.com/FREECOINS2021")
                        else:
                            send_message(sender_id, f"👋 Thanks for contacting Dr. Smile! You said: \"{message_text}\"")

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

@app.route("/")
def home():
    return "Dr. Smile Chatbot is Live ✅"

def keep_alive():
    while True:
        try:
            logging.info(f"🔄 Pinging {RENDER_EXTERNAL_URL}")
            requests.get(RENDER_EXTERNAL_URL, timeout=10)
        except Exception as e:
            logging.error(f"❌ Ping failed: {e}")
        time.sleep(PING_INTERVAL)

if __name__ == "__main__":
    threading.Thread(target=keep_alive, daemon=True).start()
    app.run(host="0.0.0.0", port=10000)

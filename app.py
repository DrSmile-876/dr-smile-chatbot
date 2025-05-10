import os
import requests
from flask import Flask, request, jsonify
import threading
import time
import logging
import json
import re

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
                    message_text = messaging_event.get("message", {}).get("text", "").lower()

                    if sender_id and message_text:
                        route_message(sender_id, message_text)
            return "EVENT_RECEIVED", 200
        except Exception as e:
            logging.error(f"❌ POST Error: {e}")
            return "Error", 500

def route_message(sender_id, msg):
    msg = msg.lower().strip()

    if re.search(r"\b(order|buy|purchase|tooth\s?kit|tooth\s?replacement|replace)\b", msg):
        send_message(sender_id, "🦷 Great choice! Please send us your **location or parish** so we can match you with the nearest dentist or delivery agent.")
    elif re.search(r"\b(price|cost|how much|fee)\b", msg):
        send_message(sender_id, "💵 The Dr. Smile Tooth Kit costs **$3,500 JMD**, including delivery! Cash on delivery & PayPal accepted.")
    elif re.search(r"\b(hi|hello|hey|start|help|info)\b", msg):
        send_message(sender_id, "👋 Hey there! I'm Dr. Smile 🤗. I can help you **order a tooth kit**, book a visit, or answer questions. Just type *order* or *how much* to begin.")
    elif re.search(r"\b(location|where|available|office|dentist)\b", msg):
        send_message(sender_id, "📍 We're available across Jamaica! Just type your **parish or town**, and we’ll connect you to the closest dental office.")
    else:
        fallback_flow(sender_id, msg)

def fallback_flow(sender_id, original_msg):
    fallback_message = (
        f"🤔 I'm not sure what \"{original_msg}\" means.\n\n"
        "But no worries! Here's what you can do:\n"
        "👉 Type **order** – to start your tooth kit purchase\n"
        "👉 Type **how much** – to check the cost\n"
        "👉 Type **location** – to find the nearest dental office\n"
        "👉 Or simply say **hi** to begin\n\n"
        "Let's get that smile glowing! 😁"
    )
    send_message(sender_id, fallback_message)

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

# === DR. SMILE BOT app.py v2.8 DEBUG MODE ===
# ✅ Includes Emoji-Rich Status Replies
# ✅ Admin Message Resend Endpoint
# ✅ Arrival Trigger from Bearer QR Scan
# ✅ DEBUG fallback response for all messages

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
RENDER_EXTERNAL_URL = os.getenv("RENDER_EXTERNAL_URL")
SCRIPT_WEBHOOK_URL = os.getenv("SCRIPT_WEBHOOK_URL")
PING_INTERVAL = 840
TOKEN_FILE = "access_token.json"

user_state = {}

@app.route("/webhook", methods=["GET", "POST"])
def webhook():
    if request.method == "GET":
        if request.args.get("hub.verify_token") == VERIFY_TOKEN:
            return request.args.get("hub.challenge"), 200
        return "Forbidden", 403

    elif request.method == "POST":
        payload = request.get_json(force=True)
        logging.info(f"📩 Incoming: {json.dumps(payload)}")

        for entry in payload.get("entry", []):
            for messaging_event in entry.get("messaging", []):
                sender_id = messaging_event.get("sender", {}).get("id")
                message_text = messaging_event.get("message", {}).get("text", "").strip().lower()

                if sender_id and message_text:
                    if sender_id in user_state and user_state[sender_id] == "awaiting_location":
                        process_location(sender_id, message_text)
                        del user_state[sender_id]
                    else:
                        handle_intent(sender_id, message_text)
        return "EVENT_RECEIVED", 200

@app.route("/status-update", methods=["POST"])
def status_update():
    data = request.get_json()
    recipient_id = data.get("recipient_id")
    raw_status = data.get("message", "").lower()

    emoji_messages = {
        "confirmed": "✅ Order Confirmed! We’re prepping your smile kit.",
        "preparing": "🧪 Preparing your tooth kit in the lab...",
        "dispatched": "🚚 Your order is out for delivery!", 
        "delivered": "📦 Delivered! We hope you love your new smile.",
        "arrived": "🏥 You’ve checked in at the dentist. Good luck!"
    }

    final_msg = emoji_messages.get(raw_status, f"📢 Order update: {raw_status.title()}")
    if recipient_id:
        send_message(recipient_id, final_msg)
        return jsonify({"status": "sent"}), 200
    return jsonify({"error": "Missing fields"}), 400

@app.route("/admin-broadcast", methods=["POST"])
def admin_broadcast():
    data = request.get_json()
    try:
        recipient = data["recipient_id"]
        message = data["message"]
        send_message(recipient, message)
        return jsonify({"status": "sent"}), 200
    except:
        return jsonify({"error": "Bad request format"}), 400

def handle_intent(sender_id, msg):
    if re.search(r"\b(order|tooth kit|buy|purchase)\b", msg):
        send_message(sender_id, "📍 Enter your town or parish to match you with a dentist.")
        user_state[sender_id] = "awaiting_location"
    elif re.search(r"\b(hi|hello|start|info)\b", msg):
        send_message(sender_id, "👋 I’m Dr. Smile 🤗. Type *order* to get started!")
    else:
        send_message(sender_id, f"🧪 DEBUG: Received your message '{msg}' but didn't match any command. Type *order* to start.")

def process_location(sender_id, location_text):
    try:
        response = requests.post(SCRIPT_WEBHOOK_URL, json={"zone": location_text})
        data = response.json()
        if "office" in data:
            msg = (
                f"🦷 Appointment Confirmed!\n\n"
                f"📌 Dental Office: {data['office']}\n"
                f"📍 Address: {data['address']}\n"
                f"🗺️ Map: {data['mapLink']}\n"
                f"📞 Contact: {data['phone']}\n\n"
                f"🔁 Show this QR on arrival:\n{data['qrCode']}"
            )
            send_message(sender_id, msg)
        else:
            send_message(sender_id, "❌ Dentist not found in that location. Try another parish.")
    except Exception as e:
        logging.error(f"❌ Location error: {e}")
        send_message(sender_id, "⚠️ Something went wrong. Try again later.")

def send_message(recipient_id, text):
    headers = {"Content-Type": "application/json"}
    data = {"recipient": {"id": recipient_id}, "message": {"text": text}}
    params = {"access_token": get_token()}
    try:
        response = requests.post("https://graph.facebook.com/v18.0/me/messages", headers=headers, params=params, json=data)
        logging.info(f"📤 Sent to {recipient_id}: {text} | Status: {response.status_code}")
    except Exception as e:
        logging.error(f"❌ Failed to send message to {recipient_id}: {e}")

def get_token():
    if os.path.exists(TOKEN_FILE):
        try:
            with open(TOKEN_FILE, "r") as f:
                return json.load(f).get("access_token", PAGE_ACCESS_TOKEN)
        except:
            pass
    return PAGE_ACCESS_TOKEN

@app.route("/healthz")
def healthz():
    return "OK", 200

@app.route("/")
def home():
    return "Dr. Smile Chatbot is Live ✅"

def keep_alive():
    while True:
        try:
            requests.get(RENDER_EXTERNAL_URL)
        except:
            pass
        time.sleep(PING_INTERVAL)

if __name__ == "__main__":
    threading.Thread(target=keep_alive, daemon=True).start()
    app.run(host="0.0.0.0", port=10000)

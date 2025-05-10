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
SCRIPT_WEBHOOK_URL = os.getenv("SCRIPT_WEBHOOK_URL")  # your Google Apps Script web app URL
PING_INTERVAL = 840
TOKEN_FILE = "access_token.json"

user_state = {}  # Temporarily store user inputs

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
                    message_text = messaging_event.get("message", {}).get("text", "").strip().lower()

                    if sender_id and message_text:
                        if sender_id in user_state and user_state[sender_id] == "awaiting_location":
                            process_location(sender_id, message_text)
                            del user_state[sender_id]
                        else:
                            handle_intent(sender_id, message_text)
            return "EVENT_RECEIVED", 200
        except Exception as e:
            logging.error(f"❌ POST Error: {e}")
            return "Error", 500

def handle_intent(sender_id, msg):
    if re.search(r"\b(order|tooth kit|buy|purchase)\b", msg):
        send_message(sender_id, "📍 Please enter your **town or parish** so we can assign the nearest dentist.")
        user_state[sender_id] = "awaiting_location"
    elif re.search(r"\b(hi|hello|start|info)\b", msg):
        send_message(sender_id, "👋 Hi! I’m Dr. Smile 🤗. Type *order* to get started or *location* to find a dentist.")
    else:
        send_message(sender_id, "🤔 Not sure what that means. Type *order* to begin your tooth kit purchase.")

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
                f"🔁 Show this QR code on arrival:\n{data['qrCode']}"
            )
            send_message(sender_id, msg)
        else:
            send_message(sender_id, "❌ Sorry, we couldn’t find a dentist in that location. Please try another parish.")

    except Exception as e:
        logging.error(f"❌ Error processing location: {e}")
        send_message(sender_id, "⚠️ Something went wrong while assigning your office. Please try again later.")

def send_message(recipient_id, text):
    headers = {"Content-Type": "application/json"}
    data = {"recipient": {"id": recipient_id}, "message": {"text": text}}
    params = {"access_token": get_token()}
    requests.post("https://graph.facebook.com/v18.0/me/messages", headers=headers, params=params, json=data)

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

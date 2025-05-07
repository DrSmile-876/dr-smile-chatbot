import os
import sys
from flask import Flask, request
import requests

app = Flask(__name__)

VERIFY_TOKEN = os.getenv("VERIFY_TOKEN", "mydrsmileverifytoken123")
PAGE_ACCESS_TOKEN = os.getenv("PAGE_ACCESS_TOKEN", "YOUR_PAGE_ACCESS_TOKEN")

@app.route('/')
def home():
    return "✅ Dr. Smile Chatbot is running!"

@app.route('/webhook', methods=['GET', 'POST'])
def webhook():
    if request.method == 'GET':
        if request.args.get('hub.verify_token') == VERIFY_TOKEN:
            return request.args.get('hub.challenge')
        return 'Invalid verification token', 403

    if request.method == 'POST':
        payload = request.json
        for entry in payload.get("entry", []):
            for messaging_event in entry.get("messaging", []):
                sender_id = messaging_event["sender"]["id"]
                if "message" in messaging_event:
                    message_text = messaging_event["message"].get("text", "")
                    respond_to_user(sender_id, message_text)
        return "ok", 200

def respond_to_user(sender_id, message):
    message = message.lower()

    if "hi" in message or "hello" in message:
        text = "👋 Hi there! I'm the Dr. Smile assistant. Ask me about our Tooth Replacement Kit."
    elif "tooth kit" in message or "dr smile" in message:
        text = "🦷 Our Dr. Smile Tooth Replacement Kit restores damaged teeth within minutes using advanced dental tech in Jamaica!"
    elif "price" in message or "cost" in message:
        text = "💵 Our kits are very affordable. Send us a message to get your quote now!"
    else:
        text = "❓ I'm here to help! Ask me about the tooth kit, pricing, or how to order."

    send_message(sender_id, text)

def send_message(recipient_id, message_text):
    url = f"https://graph.facebook.com/v18.0/me/messages?access_token={PAGE_ACCESS_TOKEN}"
    payload = {
        "recipient": {"id": recipient_id},
        "message": {"text": message_text}
    }
    headers = {"Content-Type": "application/json"}
    response = requests.post(url, json=payload, headers=headers)

    if response.status_code != 200:
        print("Error sending message:", response.text, file=sys.stderr)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=10000)

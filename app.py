from flask import Flask, request
import os

app = Flask(__name__)

VERIFY_TOKEN = os.getenv("VERIFY_TOKEN", "mydrsmileverifytoken123")

@app.route('/')
def home():
    return "🤖 Dr. Smile Bot is live!"

@app.route('/webhook', methods=['GET', 'POST'])
def webhook():
    if request.method == 'GET':
        mode = request.args.get("hub.mode")
        token = request.args.get("hub.verify_token")
        challenge = request.args.get("hub.challenge")

        if mode and token:
            if mode == "subscribe" and token == VERIFY_TOKEN:
                print("✅ Webhook verified successfully!")
                return challenge, 200
            else:
                return "❌ Forbidden: Token mismatch", 403

    return "✅ Webhook received", 200

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=10000)

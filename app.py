from flask import Flask, request

app = Flask(__name__)

@app.route('/')
def home():
    return "✅ Dr. Smile Chatbot is live!"

@app.route('/webhook', methods=['GET', 'POST'])
def webhook():
    VERIFY_TOKEN = "drsmile_secure_token"

    if request.method == 'GET':
        if request.args.get("hub.verify_token") == VERIFY_TOKEN:
            return request.args.get("hub.challenge")
        return "❌ Invalid verification token.", 403

    elif request.method == 'POST':
        data = request.get_json()
        print("📩 Received webhook event:", data)
        return "✅ Webhook received", 200

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=10000)

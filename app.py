from flask import Flask, request

app = Flask(__name__)

@app.route('/', methods=["GET"])
def home():
    return "✅ Dr. Smile Messenger Bot is live!"

@app.route('/webhook', methods=["GET", "POST"])
def webhook():
    if request.method == "GET":
        VERIFY_TOKEN = "your_verify_token_here"
        if request.args.get("hub.verify_token") == VERIFY_TOKEN:
            return request.args.get("hub.challenge")
        return "❌ Verification failed."
    elif request.method == "POST":
        data = request.json
        print(data)  # Optional: log webhook events
        return "✅ Event received", 200

if __name__ == '__main__':
    app.run(host="0.0.0.0", port=10000)

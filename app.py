
import os
import requests
from flask import Flask, request

app = Flask(__name__)

VERIFY_TOKEN = os.environ.get("VERIFY_TOKEN", "")
PAGE_ACCESS_TOKEN = os.environ.get("PAGE_ACCESS_TOKEN", "")
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "")
GEMINI_MODEL = os.environ.get("GEMINI_MODEL", "gemini-2.5-flash")

BUSINESS_INFO = os.environ.get(
    "BUSINESS_INFO",
    "Amader page e products bikri hoy. Dam, delivery ar order er jonno "
    "customer ke Messenger e janate bolo.",
)

SYSTEM_PROMPT = (
    "Tumi ekta Facebook page er friendly customer support assistant. "
    "Customer je bhashay lekhe (Bangla, Banglish ba English), sei bhashay chhoto "
    "ar bhodro uttor dao. Shudhu niche deya business info onujayi uttor dao. "
    "Jodi uttor na jano, bolo je ekjon manush shighroi reply debe. "
    "Kono dam ba tottho nijer theke banio na.\n\n"
    "Business info: " + BUSINESS_INFO
)


@app.route("/", methods=["GET"])
def home():
    return "Bot is running", 200


@app.route("/webhook", methods=["GET"])
def verify():
    mode = request.args.get("hub.mode")
    token = request.args.get("hub.verify_token")
    challenge = request.args.get("hub.challenge", "")
    if mode == "subscribe" and token == VERIFY_TOKEN:
        return challenge, 200
    return "Verification failed", 403


@app.route("/webhook", methods=["POST"])
def webhook():
    data = request.get_json(silent=True) or {}
    for entry in data.get("entry", []):
        for event in entry.get("messaging", []):
            message = event.get("message", {})
            if message.get("is_echo"):
                continue
            text = message.get("text")
            sender_id = event.get("sender", {}).get("id")
            if text and sender_id:
                reply = ask_ai(text)
                send_message(sender_id, reply)
    return "ok", 200


def ask_ai(user_text):
    url = (
        "https://generativelanguage.googleapis.com/v1beta/models/"
        f"{GEMINI_MODEL}:generateContent"
    )
    headers = {"x-goog-api-key": GEMINI_API_KEY, "Content-Type": "application/json"}
    body = {
        "system_instruction": {"parts": [{"text": SYSTEM_PROMPT}]},
        "contents": [{"role": "user", "parts": [{"text": user_text}]}],
    }
    try:
        r = requests.post(url, headers=headers, json=body, timeout=20)
        r.raise_for_status()
        return r.json()["candidates"][0]["content"]["parts"][0]["text"]
    except Exception as e:
        print("AI error:", e)
        return "Dukkhito, ekhon uttor dite parchi na. Ekjon manush shighroi apnar sathe jogajog korbe."


def send_message(recipient_id, text):
    url = "https://graph.facebook.com/v21.0/me/messages"
    payload = {
        "recipient": {"id": recipient_id},
        "messaging_type": "RESPONSE",
        "message": {"text": text[:1900]},
    }
    try:
        r = requests.post(
            url, params={"access_token": PAGE_ACCESS_TOKEN}, json=payload, timeout=20
        )
        if r.status_code != 200:
            print("Send error:", r.text)
    except Exception as e:
        print("Send exception:", e)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))

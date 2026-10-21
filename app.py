import os
import csv
import io
import requests
from flask import Flask, request, jsonify

app = Flask(__name__)

BOT_TOKEN = os.environ.get("BOT_TOKEN", "").strip()
SHEET_ID = os.environ.get("SHEET_ID", "").strip()

BALE_API = f"https://tapi.bale.ai/bot{BOT_TOKEN}"

def send_message(chat_id, text):
    url = f"{BALE_API}/sendMessage"
    payload = {
        "chat_id": chat_id,
        "text": text
    }
    try:
        requests.post(url, json=payload, timeout=10)
    except Exception as e:
        print(f"Error sending message: {e}")

def get_sheet_data():
    url = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/export?format=csv"
    try:
        resp = requests.get(url, timeout=15)
        if resp.status_code == 200:
            resp.encoding = 'utf-8'
            reader = csv.reader(io.StringIO(resp.text))
            return list(reader)
    except Exception as e:
        print(f"Error fetching sheet: {e}")
    return []

def search_national_code(national_code):
    rows = get_sheet_data()
    if not rows:
        return "⚠️ در حال حاضر امکان دسترسی به اطلاعات وجود ندارد. لطفاً دقایقی دیگر تلاش کنید."

    headers = [h.strip() for h in rows[0]]
    code_clean = national_code.strip()

    for row in rows[1:]:
        row_values = [col.strip() for col in row]
        if code_clean in row_values:
            info = ["🥊 **اطلاعات پرونده ورزشی شما (کیان‌دخت رزم)** 🥊\n"]
            for i, val in enumerate(row):
                if i < len(headers) and val.strip():
                    info.append(f"▫️ **{headers[i]}:** {val.strip()}")
            return "\n".join(info)

    return "❌ کد ملی وارد شده در سیستم ثبت نشده است.\nلطفاً از صحت کد ملی اطمینان حاصل فرمایید یا با مربی تماس بگیرید."

@app.route("/", methods=["GET"])
def home():
    return "Kiandokht Razm Bot is running!", 200

@app.route("/webhook", methods=["POST"])
def webhook():
    data = request.get_json(force=True, silent=True)
    if not data:
        return jsonify({"status": "no data"}), 200

    message = data.get("message", {})
    chat = message.get("chat", {})
    chat_id = chat.get("id")
    text = message.get("text", "").strip()

    if not chat_id:
        return jsonify({"status": "ignored"}), 200

    if text in ["/start", "شروع"]:
        welcome_msg = (
            "سلام به باشگاه کیک‌بوکسینگ کیان‌دخت رزم خوش آمدید! 🥊🌸\n\n"
            "برای مشاهده وضعیت عضویت، بیمه و پرونده ورزشی، لطفاً **کد ملی** خود را ارسال کنید:"
        )
        send_message(chat_id, welcome_msg)
    elif text:
        result = search_national_code(text)
        send_message(chat_id, result)

    return jsonify({"status": "ok"}), 200

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))

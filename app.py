from flask import Flask, request, jsonify
import os
import json
import requests

# 🔑 توکن ربات بله (وارد شده به صورت مستقیم — فقط برای تست)
BOT_TOKEN = "1820733597:aCi2zuJ6nHm38iK71HxZyzPXOlQ1Jd55fgY"

# ایجاد نمونه Flask
app = Flask(__name__)

# ✅ Route برای بررسی سلامت سرویس (تست در مرورگر)
@app.route('/health', methods=['GET'])
def health_check():
    return jsonify({
        "status": "✅ alive",
        "bot_token": "✅ set (hardcoded)",
        "message": "Flask server is ready to serve Bale bot!"
    }), 200

# 🤖 Route اصلی: دریافت پیام‌های بله
@app.route('/webhook', methods=['POST'])
def webhook():
    try:
        data = request.get_json()
        print("📥 Received update:", json.dumps(data, indent=2, ensure_ascii=False))

        # پردازش پیام‌های متنی
        if data and 'message' in data and 'text' in data['message']:
            message = data['message']
            chat_id = message['chat']['id']
            text = message['text'].strip()

            # 📤 ارسال پاسخ
            reply_text = f"🤖 دریافت شد!\n\nشما نوشتید:\n<b>{text}</b>"
            send_message(chat_id, reply_text)

        return jsonify({"status": "ok"}), 200

    except Exception as e:
        print("❌ Error in webhook:", e)
        return jsonify({"error": str(e)}), 500

# 📤 تابع ارسال پیام به بله
def send_message(chat_id, text):
    url = f"https://tapi.bale.ai/bot{BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": chat_id,
        "text": text,
        "parse_mode": "HTML"
    }
    try:
        response = requests.post(url, json=payload, timeout=10)
        result = response.json()
        print("📤 Message sent:", result)
        return result
    except Exception as e:
        print("❌ Failed to send message:", e)
        return {"error": str(e)}

# 🏁 راه‌اندازی سرور — حتماً host و port را مشخص کنید!
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))  # پورت را از متغیر محیطی بخوانید
    app.run(host='0.0.0.0', port=port)       # به تمام آدرس‌ها bind کنید

from flask import Flask, request, jsonify
import requests
import time
import json
import os
import re

# ─── تنظیمات از متغیرهای محیطی ────────────────────────────────────────
BOT_TOKEN = os.environ.get("BOT_TOKEN", "1820733597:aCi2zuJ6nHm38iK71HxZyzPXOlQ1Jd55fgY")
BASE_URL = f"https://tapi.bale.ai/bot{BOT_TOKEN}"
QUESTIONS_FILE = "questions_hr_350_clean.json"

app = Flask(__name__)

# ─── بارگذاری سؤالات ────────────────────────────────────────────────
def load_questions():
    if not os.path.exists(QUESTIONS_FILE):
        return []
    try:
        with open(QUESTIONS_FILE, "r", encoding="utf-8-sig") as f:
            data = f.read().strip()
            return json.loads(data) if data else []
    except Exception as e:
        print(f"❌ خطای بارگذاری سوالات: {e}")
        return []

# ─── نرمال‌سازی متن ────────────────────────────────────────────────
def clean(text):
    if not isinstance(text, str): return ""
    text = re.sub(r"[؟?!.,:;(){}[\]\"\'\-_]", " ", text.lower())
    text = re.sub(r"\s+", " ", text).strip()
    text = text.replace("آ", "ا").replace("ی", "ي").replace("ک", "ك")
    return text

# ─── جستجوی هوشمند ────────────────────────────────────────────────
def find_matches(query, questions):
    if not query.strip(): return []
    q_clean = clean(query)
    words = [w for w in q_clean.split() if len(w) > 1] or q_clean.split()
    matches = []
    for item in questions:
        full_q = item.get("question", "").strip()
        if not full_q: continue
        if clean(full_q) == q_clean:
            return [item]
        full_clean = clean(full_q)
        score = sum(1 for w in words if w in full_clean)
        if score >= 1:
            penalty = min(len(full_clean.split()) * 0.01, 0.3)
            matches.append((score - penalty, len(full_clean), item))
    matches.sort(key=lambda x: (-x[0], x[1]))
    return [item for _, _, item in matches]

# ─── تشخیص درخواست جدول ────────────────────────────────────────────
def is_image_table_request(text):
    return any(kw in text for kw in ["تصویر جدول", "عکس جدول"]) and "شرایط نامساعد کار" in text

# ─── تولید پاسخ ────────────────────────────────────────────────────
def make_answer(items):
    if not items:
        return "لطفاً سؤال مرتبط با «کتاب مجموعه ضوابط طرح طبقه‌بندی مشاغل» طرح نمایید."
    if len(items) == 1:
        item = items[0]
        return (
            f"**1-** {item['question']}\n"
            f"   موضوع: {item.get('topic', 'عمومی')}\n"
            f"   پاسخ: {item['answer']}\n"
            f"   منبع: {item['source']}"
        )
    result = "چند سؤال مرتبط یافت شد:\n"
    for i, item in enumerate(items, 1):
        result += (
            f"**{i}-** {item['question']}\n"
            f"   موضوع: {item.get('topic', 'عمومی')}\n"
            f"   پاسخ: {item['answer']}\n"
            f"   منبع: {item['source']}\n"
        )
    return result.strip()

# ─── ارسال لینک جدول ────────────────────────────────────────────────
def send_table_link(chat_id):
    # این لینک را با لینک واقعی تصویر خود جایگزین کنید
    table_url = "https://your-image-link-here.png"  # ← اینجا را تغییر دهید!
    caption = "**منبع:** جدول امتیازات شرایط نامساعد کار — صفحهٔ 55"
    try:
        res = requests.post(
            f"{BASE_URL}/sendMessage",
            json={
                "chat_id": chat_id,
                "text": f"✅ تصویر جدول: {table_url}\n{caption}",
                "parse_mode": "Markdown"
            }
        )
        return res.ok
    except Exception as e:
        print(f"❌ خطا در ارسال لینک: {e}")
        return False

# ─── endpoint اصلی webhook ──────────────────────────────────────────
@app.route('/webhook', methods=['POST'])
def webhook():
    try:
        update = request.get_json()
        if not update or 'message' not in update:
            return jsonify({"ok": True})
        msg = update['message']
        text = msg.get('text', '').strip()
        chat_id = msg['chat']['id']
        if not text:
            return jsonify({"ok": True})

        # پاسخ به درخواست جدول
        if is_image_table_request(text):
            if send_table_link(chat_id):
                requests.post(f"{BASE_URL}/sendMessage", json={
                    "chat_id": chat_id,
                    "text": "✅ لینک جدول ارسال شد.",
                    "parse_mode": "Markdown"
                })
            return jsonify({"ok": True})

        # پاسخ به سایر سوالات
        questions = load_questions()
        matches = find_matches(text, questions)
        answer = make_answer(matches)
        requests.post(f"{BASE_URL}/sendMessage", json={
            "chat_id": chat_id,
            "text": answer,
            "parse_mode": "Markdown"
        })

        return jsonify({"ok": True})
    except Exception as e:
        print(f"❌ خطای درخواست: {e}")
        return jsonify({"ok": False})

# ─── صفحه سلامت ────────────────────────────────────────────────────
@app.route('/health')
def health():
    return jsonify({"status": "ok", "bot": "@AIHR40bot", "ready": True})

# ─── اجرای سرور (فقط برای تست محلی) ────────────────────────────────
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 8000)))
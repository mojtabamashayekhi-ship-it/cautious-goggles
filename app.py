from flask import Flask, request, jsonify
import requests
import time
import json
import os
import re
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from bidi.algorithm import get_display
import arabic_reshaper
import random

# ─── تنظیمات ───────────────────────────────────────
BOT_TOKEN = os.environ.get("BOT_TOKEN", "1820733597:aCi2zuJ6nHm38iK71HxZyzPXOlQ1Jd55fgY")
BASE_URL = f"https://tapi.bale.ai/bot{BOT_TOKEN}"
QUESTIONS_FILE = "questions_hr_350_clean.json"

app = Flask(__name__)

# ─── بارگذاری سؤالات ──────────────────────────────────
def load_questions():
    if not os.path.exists(QUESTIONS_FILE):
        return []
    try:
        with open(QUESTIONS_FILE, "r", encoding="utf-8-sig") as f:
            data = f.read().strip()
            return json.loads(data) if data else []
    except:
        return []

# ─── نرمال‌سازی متن ───────────────────────────────────
def clean(text):
    if not isinstance(text, str): return ""
    text = re.sub(r"[؟?!.,:;(){}[\]\"\'\-_]", " ", text.lower())
    text = re.sub(r"\s+", " ", text).strip()
    return text.replace("آ", "ا").replace("ی", "ي").replace("ک", "ك")

# ─── جستجوی فازی ───────────────────────────────────────
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

# ─── تولید تصویر جدول ──────────────────────────────────
def create_table_image(data, title="جدول"):
    try:
        def fix_arabic(text):
            if isinstance(text, str):
                reshaped = arabic_reshaper.reshape(text)
                return get_display(reshaped)
            return text
        
        df = pd.DataFrame(data)
        for col in df.columns:
            df[col] = df[col].apply(fix_arabic)
        cols = [fix_arabic(col) for col in df.columns]

        plt.rcParams.update({
            "figure.dpi": 150,
            "savefig.dpi": 150,
            "font.family": "DejaVu Sans",
        })

        fig, ax = plt.subplots(figsize=(10, max(4, len(data) * 0.7)))
        ax.axis('off')
        table = ax.table(
            cellText=df.values,
            colLabels=cols,
            cellLoc='center',
            loc='center',
            colColours=['#2E7D32'] * len(df.columns),
            cellColours=[['#F5F5F5'] * len(df.columns)] * len(df)
        )
        table.auto_set_font_size(False)
        table.set_fontsize(9)
        table.scale(1.1, 2.0)

        if "(" in title and ")" in title:
            parts = title.split("(", 1)
            eng = parts[0].strip()
            per = parts[1].split(")", 1)[0].strip()
            final_title = f"{fix_arabic(per)} ({eng})"
        else:
            final_title = fix_arabic(title)
        ax.set_title(final_title, fontsize=12, pad=15, fontweight='bold', color='#1B5E20')

        filename = f"table_{random.randint(1000, 9999)}.png"
        plt.savefig(filename, bbox_inches='tight', facecolor='white', dpi=150)
        plt.close()
        return filename if os.path.exists(filename) and os.path.getsize(filename) > 1000 else None
    except:
        return None

# ─── ارسال تصویر به بله ─────────────────────────────────
def send_table_image(chat_id, caption=""):
    data = [
        {"Job Title (عنوان شغل)": "کارشناس اداری", "Normal Duty (عادی)": "2200", "Full Time (مداوم)": "2200"},
        {"Job Title (عنوان شغل)": "آتش‌نشان", "Normal Duty (عادی)": "2700", "Full Time (مداوم)": "3000"},
        {"Job Title (عنوان شغل)": "نگهبان", "Normal Duty (عادی)": "2700", "Full Time (مداوم)": "3000"},
        {"Job Title (عنوان شغل)": "رانندهٔ خودروی سنگین", "Normal Duty (عادی)": "2500", "Full Time (مداوم)": "2800"},
    ]
    img_path = create_table_image(data, title="Working Conditions Table (شرایط نامساعد کار)")
    if not img_path:
        return False
    try:
        with open(img_path, 'rb') as f:
            res = requests.post(
                f"{BASE_URL}/sendPhoto",
                data={"chat_id": chat_id, "caption": caption, "parse_mode": "Markdown"},
                files={"photo": f},
                timeout=30
            )
        os.remove(img_path)
        return res.ok
    except:
        if os.path.exists(img_path):
            os.remove(img_path)
        return False

# ─── تولید پاسخ متنی ───────────────────────────────────
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

# ─── Endpoint اصلی webhook ───────────────────────────────
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

        # درخواست تصویر جدول
        if ("تصویر جدول" in text or "عکس جدول" in text) and "شرایط نامساعد کار" in text:
            caption = "**منبع:** جدول امتیازات شرایط نامساعد کار — صفحهٔ 55"
            if send_table_image(chat_id, caption):
                requests.post(f"{BASE_URL}/sendMessage", json={
                    "chat_id": chat_id,
                    "text": "✅ تصویر جدول ارسال شد.",
                    "parse_mode": "Markdown"
                })
                return jsonify({"ok": True})

        # پاسخ متنی
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
        print(f"❌ خطا در webhook: {e}")
        return jsonify({"ok": False})

# ─── صفحه سلامت (برای Render health check) ───────────────
@app.route('/health')
def health():
    return jsonify({"status": "ok", "bot": "AIHR40bot", "ready": True})

# ─── اجرای آزمایشی در لوکال (اختیاری) ─────────────────────
if __name__ == '__main__':
    print("✅ ربات @AIHR40bot آماده است (حالت webhook).")
    print("📌 برای استقرار در Render، فقط از `gunicorn` استفاده کنید.")
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 8000)))
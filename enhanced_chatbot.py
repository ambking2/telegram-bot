import telebot
from g4f.client import Client
from datetime import datetime
import json
import os
import requests
from io import BytesIO
import magic

# تنظیمات اولیه
TOKEN = os.getenv("8134270114:AAEo1_liGmb1fZPURho993Ej9nEl06GGYqo", "8134270114:AAEo1_liGmb1fZPURho993Ej9nEl06GGYqo")  # توکن از متغیر محیطی یا مستقیم
ADMIN_IDS = [5738171226]  # آیدی ادمین‌ها
bot = telebot.TeleBot(TOKEN)
client = Client()
mime = magic.Magic(mime=True)

# مسیر فایل‌های JSON
USER_DATA_FILE = "Database/user_data.json"

# ساختار اولیه فایل JSON
def init_user_data():
    if not os.path.exists("Database"):
        os.makedirs("Database")
    if not os.path.exists(USER_DATA_FILE):
        with open(USER_DATA_FILE, "w", encoding="utf-8") as f:
            json.dump({}, f, ensure_ascii=False, indent=4)

# بارگذاری داده‌های کاربر
def load_user_data():
    try:
        with open(USER_DATA_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return {}

# ذخیره داده‌های کاربر
def save_user_data(data):
    with open(USER_DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

# منوی اصلی
def show_menu(chat_id, menu_type="default"):
    markup = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    if menu_type == "default":
        buttons = ["چت بات 🤖", "تولید تصویر 🖌", "گفت‌وگوی جدید 💬"]
    elif menu_type == "text":
        buttons = ["GPT-4o", "GPT-4o-mini", "Gemini 1.5 Pro", "Llama 3.1"]
    elif menu_type == "image":
        buttons = ["Dall-e 3", "Flux", "Midjourney"]
    markup.add(*[telebot.types.KeyboardButton(btn) for btn in buttons])
    if chat_id in ADMIN_IDS:
        admin_buttons = ["لیست کاربران", "پیام همگانی"]
        markup.add(*[telebot.types.KeyboardButton(btn) for btn in admin_buttons])
    return markup

# بررسی عضویت در کانال
def check_channel_membership(chat_id):
    required_channels = ["+BgK3IxU2zdo0NmQ8"]  # جایگزین با نام کاربری کانال
    non_member_channels = []
    for channel in required_channels:
        try:
            member = bot.get_chat_member(f"@{channel}", chat_id)
            if member.status not in ["member", "administrator", "creator"]:
                non_member_channels.append(channel)
        except:
            non_member_channels.append(channel)
    return non_member_channels

# هندلر شروع
@bot.message_handler(commands=["start"])
def start(message):
    init_user_data()
    user_data = load_user_data()
    chat_id = str(message.chat.id)
    
    if chat_id not in user_data:
        user_data[chat_id] = {
            "username": message.chat.username or "",
            "model": "gpt-4o-mini",
            "chat_history": [],
            "image_history": [],
            "last_message_time": []
        }
        save_user_data(user_data)
    
    non_member_channels = check_channel_membership(chat_id)
    if non_member_channels:
        markup = telebot.types.InlineKeyboardMarkup()
        for channel in non_member_channels:
            markup.add(telebot.types.InlineKeyboardButton(
                text=f"عضویت در @{channel}", url=f"https://t.me/{channel}"))
        markup.add(telebot.types.InlineKeyboardButton(
            text="تایید عضویت", callback_data="confirm_membership"))
        bot.reply_to(message, "لطفاً در کانال‌های زیر عضو شوید 📢", reply_markup=markup)
    else:
        bot.reply_to(message, f"سلام {message.from_user.first_name} 🤖\nبه ربات هوش مصنوعی خوش آمدید! پیام یا تصویر بفرستید.", 
                     reply_markup=show_menu(chat_id))

# هندلر پیام‌های متنی
@bot.message_handler(func=lambda message: True)
def handle_message(message):
    user_data = load_user_data()
    chat_id = str(message.chat.id)
    
    if chat_id not in user_data:
        start(message)
        return
    
    non_member_channels = check_channel_membership(chat_id)
    if non_member_channels:
        start(message)
        return

    if message.text == "چت بات 🤖":
        user_data[chat_id]["model"] = "gpt-4o-mini"
        bot.reply_to(message, "مدل چت به GPT-4o-mini تغییر کرد. سوال خود را بپرسید!", reply_markup=show_menu(chat_id, "text"))
    elif message.text == "تولید تصویر 🖌":
        user_data[chat_id]["model"] = "dall-e-3"
        bot.reply_to(message, "مدل به DALL·E 3 تغییر کرد. پرامپت تصویر را بفرستید!", reply_markup=show_menu(chat_id, "image"))
    elif message.text == "گفت‌وگوی جدید 💬":
        user_data[chat_id]["chat_history"] = []
        user_data[chat_id]["image_history"] = []
        bot.reply_to(message, "چت جدید شروع شد!", reply_markup=show_menu(chat_id))
    elif message.text in ["GPT-4o", "GPT-4o-mini", "Gemini 1.5 Pro", "Llama 3.1", "Dall-e 3", "Flux", "Midjourney"]:
        model_map = {
            "GPT-4o": "gpt-4o", "GPT-4o-mini": "gpt-4o-mini", "Gemini 1.5 Pro": "gemini-1.5-pro",
            "Llama 3.1": "llama-3.1-70b", "Dall-e 3": "dall-e-3", "Flux": "flux", "Midjourney": "midjourney"
        }
        user_data[chat_id]["model"] = model_map[message.text]
        bot.reply_to(message, f"مدل به {message.text} تغییر کرد.", 
                     reply_markup=show_menu(chat_id, "text" if message.text in ["GPT-4o", "GPT-4o-mini", "Gemini 1.5 Pro", "Llama 3.1"] else "image"))
    else:
        try:
            user_data[chat_id]["last_message_time"].append(datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
            model = user_data[chat_id]["model"]
            history = user_data[chat_id]["chat_history"]
            history.append({"role": "user", "content": message.text})
            
            if model in ["dall-e-3", "flux", "midjourney"]:
                response = client.images.generate(model=model, prompt=message.text, response_format="url")
                if response.data[0].url:
                    file_bytes = BytesIO(requests.get(response.data[0].url).content)
                    file_bytes.name = "image.jpg"
                    bot.send_document(message.chat.id, file_bytes, reply_to_message_id=message.message_id, 
                                   reply_markup=show_menu(chat_id, "image"))
            else:
                response = client.chat.completions.create(model=model, messages=history)
                answer = response.choices[0].message.content
                if len(answer) > 4095:
                    answer = answer[:4092] + "..."
                bot.reply_to(message, answer, reply_markup=show_menu(chat_id, "text"))
                history.append({"role": "assistant", "content": answer})
            
            user_data[chat_id]["chat_history"] = history[-10:]  # محدود کردن تاریخچه به 10 پیام آخر
            save_user_data(user_data)
        except Exception as e:
            bot.reply_to(message, "خطایی رخ داد. لطفاً دوباره امتحان کنید. 🔄", reply_markup=show_menu(chat_id))
            for admin in ADMIN_IDS:
                bot.send_message(admin, f"خطا در چت‌بات:\nکاربر: {chat_id}\nخطا: {str(e)}")

# هندلر تصاویر (تحلیل خودکار)
@bot.message_handler(content_types=["photo"])
def handle_photo(message):
    user_data = load_user_data()
    chat_id = str(message.chat.id)
    
    if chat_id not in user_data:
        start(message)
        return
    
    non_member_channels = check_channel_membership(chat_id)
    if non_member_channels:
        start(message)
        return

    try:
        # تغییر خودکار مدل به gpt-4o برای تحلیل تصویر
        user_data[chat_id]["model"] = "gpt-4o"
        file_id = message.photo[-1].file_id
        file_info = bot.get_file(file_id)
        file_url = f"https://api.telegram.org/file/bot{TOKEN}/{file_info.file_path}"
        user_data[chat_id]["image_history"].append(file_url)
        
        # اضافه کردن پیام به تاریخچه
        user_data[chat_id]["chat_history"].append({"role": "user", "content": "تحلیل تصویر"})
        
        # ارسال پیام در حال پردازش
        processing_msg = bot.reply_to(message, "در حال تحلیل تصویر... ⏳", reply_markup=show_menu(chat_id))
        
        # درخواست تحلیل تصویر از gpt4free
        response = client.chat.completions.create(
            model="gpt-4o",
            image=file_url,
            messages=user_data[chat_id]["chat_history"] + [{"role": "user", "content": "لطفاً این تصویر را تحلیل کنید."}]
        )
        answer = response.choices[0].message.content
        if len(answer) > 4095:
            answer = answer[:4092] + "..."
        
        # حذف پیام در حال پردازش
        bot.delete_message(chat_id, processing_msg.message_id)
        
        # ارسال پاسخ تحلیل
        bot.reply_to(message, answer, reply_markup=show_menu(chat_id))  # منوی پیش‌فرض برای ادامه مکالمه
        
        # ذخیره پاسخ در تاریخچه
        user_data[chat_id]["chat_history"].append({"role": "assistant", "content": answer})
        user_data[chat_id]["chat_history"] = user_data[chat_id]["chat_history"][-10:]  # محدود کردن تاریخچه
        save_user_data(user_data)
    except Exception as e:
        bot.reply_to(message, "خطایی در تحلیل تصویر رخ داد. 🔄", reply_markup=show_menu(chat_id))
        for admin in ADMIN_IDS:
            bot.send_message(admin, f"خطا در تحلیل تصویر:\nکاربر: {chat_id}\nخطا: {str(e)}")

# هندلر دکمه تأیید عضویت
@bot.callback_query_handler(func=lambda call: call.data == "confirm_membership")
def confirm_membership(call):
    non_member_channels = check_channel_membership(call.from_user.id)
    if non_member_channels:
        markup = telebot.types.InlineKeyboardMarkup()
        for channel in non_member_channels:
            markup.add(telebot.types.InlineKeyboardButton(
                text=f"عضویت در @{channel}", url=f"https://t.me/{channel}"))
        markup.add(telebot.types.InlineKeyboardButton(
            text="تایید عضویت", callback_data="confirm_membership"))
        bot.send_message(call.message.chat.id, "لطفاً در کانال‌های زیر عضو شوید 📢", reply_markup=markup)
    else:
        bot.send_message(call.message.chat.id, "عضویت شما تأیید شد! ✅", reply_markup=show_menu(call.message.chat.id))

# شروع ربات
if __name__ == "__main__":
    bot.polling()
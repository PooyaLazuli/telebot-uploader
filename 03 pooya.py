!pip install -q python-telegram-bot nest_asyncio

import nest_asyncio
nest_asyncio.apply()

BOT_TOKEN =   '8315067884:AAH0nt84cgJxdJwQ3KZDT0Apso451HU8_FM'
ADMIN_ID = 7809280780          
import os
import logging
from telegram import Update, InputFile
from telegram.ext import (
    ApplicationBuilder, CommandHandler, MessageHandler,
    ContextTypes, filters
)


MEDIA_DIR = "media"
LOG_FILE = "download_logs.txt"
upload_mode_users = set()

os.makedirs(MEDIA_DIR, exist_ok=True)

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    if context.args:
        filename = context.args[0]
        file_path = os.path.join(MEDIA_DIR, filename)
        if os.path.exists(file_path):
            await update.message.reply_document(open(file_path, 'rb'))
            with open(LOG_FILE, "a", encoding="utf-8") as log:
                log.write(f"{user.username or user.id} دانلود کرد: {filename}\n")
            await context.bot.send_message(chat_id=ADMIN_ID, text=f"📥 {user.username or user.id} فایل {filename} را دانلود کرد.")
        else:
            await update.message.reply_text("❌ فایل یافت نشد.")
    else:
        await update.message.reply_text("سلام! برای دریافت فایل، روی لینک دانلود کلیک کن.")


async def myid(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(f"🆔 آیدی عددی شما: `{update.effective_user.id}`", parse_mode="Markdown")


async def upload(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id == ADMIN_ID:
        upload_mode_users.add(update.effective_user.id)
        await update.message.reply_text("✅ حالت آپلود فعال شد! لطفاً فایل را بفرست.")


async def handle_file(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    file = update.message.document or update.message.video or (update.message.photo[-1] if update.message.photo else None)
    if not file:
        await update.message.reply_text("❌ فایلی ارسال نشده.")
        return

    file_name = getattr(file, "file_name", f"{file.file_id}.dat")
    if update.message.photo:
        file_name = f"{file.file_id}.jpg"
    elif update.message.video:
        file_name = f"{file.file_id}.mp4"

    file_path = os.path.join(MEDIA_DIR, file_name)
    await (await file.get_file()).download_to_drive(file_path)

    bot_username = (await context.bot.get_me()).username
    link = f"https://t.me/{bot_username}?start={file_name}"
    await update.message.reply_text(f"✅ فایل ذخیره شد!\n📎 لینک دانلود: {link}")

    if user.id in upload_mode_users:
        upload_mode_users.remove(user.id)
        await context.bot.send_message(chat_id=ADMIN_ID, text=f"📤 فایل جدید آپلود شد:\n{file_name}\n🔗 {link}")
    else:
        with open(LOG_FILE, "a", encoding="utf-8") as f:
            f.write(f"{user.id} ({user.username}) دانلود کرد: {file_name}\n")
        await context.bot.send_message(chat_id=ADMIN_ID, text=f"📥 @{user.username} فایل {file_name} را دانلود کرد.")


async def logs(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        await update.message.reply_text("⛔ دسترسی ندارید.")
        return

    if not os.path.exists(LOG_FILE):
        await update.message.reply_text("📭 لاگی وجود ندارد.")
        return

    with open(LOG_FILE, "r", encoding="utf-8") as f:
        text = f.read()
    if not text.strip():
        await update.message.reply_text("📭 هیچ دانلودی ثبت نشده.")
        return

    for i in range(0, len(text), 4000):
        await update.message.reply_text(f"📜 گزارش:\n{text[i:i+4000]}")


async def log_user(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        await update.message.reply_text("⛔ دسترسی ندارید.")
        return

    if not context.args:
        await update.message.reply_text("❌ فرمت: /log username")
        return

    username = context.args[0].lstrip("@")
    if not os.path.exists(LOG_FILE):
        await update.message.reply_text("📭 لاگی وجود ندارد.")
        return

    with open(LOG_FILE, "r", encoding="utf-8") as f:
        lines = f.readlines()

    user_logs = [line for line in lines if f"@{username}" in line]
    if not user_logs:
        await update.message.reply_text(f"❌ لاگی برای @{username} پیدا نشد.")
        return

    text = "".join(user_logs)
    await update.message.reply_text(f"📋 گزارش @{username}:\n{text}")

# /clearlogs
async def clearlogs(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        await update.message.reply_text("⛔ اجازه ندارید.")
        return

    if os.path.exists(LOG_FILE):
        os.remove(LOG_FILE)
        await update.message.reply_text("🗑️ لاگ‌ها پاک شدند.")
    else:
        await update.message.reply_text("📭 لاگی وجود ندارد.")

import asyncio
from telegram.ext import Application

app = ApplicationBuilder().token(BOT_TOKEN).build()

app.add_handler(CommandHandler("start", start))
app.add_handler(CommandHandler("myid", myid))
app.add_handler(CommandHandler("upload", upload))
app.add_handler(CommandHandler("logs", logs))
app.add_handler(CommandHandler("log", log_user))
app.add_handler(CommandHandler("clearlogs", clearlogs))

app.add_handler(MessageHandler(filters.Document.ALL, handle_file))
app.add_handler(MessageHandler(filters.VIDEO, handle_file))
app.add_handler(MessageHandler(filters.PHOTO, handle_file))

async def main():
    await app.initialize()
    await app.start()
    print("🤖 ربات اجرا شد. منتظر پیام هستم...")
    await app.updater.start_polling()


await main()

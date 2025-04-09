from telegram import Update
from telegram.ext import (
    ApplicationBuilder, CommandHandler, MessageHandler,
    filters, ContextTypes, ConversationHandler
)
import requests

# Stages
EMAIL, PHONE, OTP = range(3)

user_data_store = {}

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("👋 Welcome! Please enter your Gmail address:")
    return EMAIL

async def get_email(update: Update, context: ContextTypes.DEFAULT_TYPE):
    email = update.message.text
    context.user_data['email'] = email
    await update.message.reply_text("📱 Now enter your phone number:")
    return PHONE

async def get_phone(update: Update, context: ContextTypes.DEFAULT_TYPE):
    phone = update.message.text
    context.user_data['phone'] = phone
    telegram_id = update.effective_user.id

    payload = {
        'email': context.user_data['email'],
        'phone': phone,
        'telegram_id': telegram_id
    }

    r = requests.post('http://localhost:3001/start-verification', json=payload)
    if r.status_code == 200:
        await update.message.reply_text("✅ OTP has been sent! Now enter the 6-digit OTP:")
        return OTP
    else:
        await update.message.reply_text("❌ Email not found in our system. Try again with a valid one.")
        return ConversationHandler.END

async def get_otp(update: Update, context: ContextTypes.DEFAULT_TYPE):
    otp = update.message.text
    telegram_id = update.effective_user.id

    r = requests.post('http://localhost:3001/verify-otp', json={
        'telegram_id': telegram_id,
        'otp_code': otp
    })

    if r.status_code == 200:
        await update.message.reply_text("🎉 Verification successful! You now have access.")
        return ConversationHandler.END
    else:
        await update.message.reply_text("❌ OTP verification failed. Please try again.")
        return OTP

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🚫 Process cancelled.")
    return ConversationHandler.END

app = ApplicationBuilder().token("8177749899:AAF0Rf3bnCAyxSva3OJce8_WjPtIyO-ryec").build()

conv_handler = ConversationHandler(
    entry_points=[CommandHandler("start", start)],
    states={
        EMAIL: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_email)],
        PHONE: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_phone)],
        OTP: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_otp)],
    },
    fallbacks=[CommandHandler("cancel", cancel)],
)

app.add_handler(conv_handler)
print("Bot is running...")
app.run_polling()

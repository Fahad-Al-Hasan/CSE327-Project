import os
import logging
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, CallbackContext
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from google.oauth2.service_account import Credentials

# Configure logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

# Telegram Bot Token
TELEGRAM_BOT_TOKEN = "8177749899:AAF0Rf3bnCAyxSva3OJce8_WjPtIyO-ryec"

# Dummy Gmail addresses and OTPs
dummy_gmails = [
    ("sharmin.laila1999@gmail.com", 4489),
    ("dummyuser.000111@gmail.com", 8380),
    ("ahmed.jovan2000@gmail.com", 4364),
]

# Store OTPs for verification
user_otps = {email: otp for email, otp in dummy_gmails}
verified_users = set()

# Google Drive Authentication (dummy for testing)
SCOPES = ['https://www.googleapis.com/auth/drive']
SERVICE_ACCOUNT_FILE = 'credentials.json'
creds = Credentials.from_service_account_file(SERVICE_ACCOUNT_FILE, scopes=SCOPES)
drive_service = build('drive', 'v3', credentials=creds)

# Function to send OTP (simulation, no real email sent)
def send_otp(email, otp):
    # For testing, we'll just log the email and OTP instead of sending an email
    logger.info(f"Sending OTP {otp} to {email}")
    return True

# Start command
async def start(update: Update, _: CallbackContext) -> None:
    await update.message.reply_text("Welcome! Send /login to authenticate via Gmail.")

# Login command
async def login(update: Update, _: CallbackContext) -> None:
    await update.message.reply_text("Please enter your Gmail address to receive an OTP.")

# Handle email input
async def handle_email(update: Update, _: CallbackContext) -> None:
    email = update.message.text
    if email not in [email for email, otp in dummy_gmails]:
        await update.message.reply_text("Invalid Gmail address. Please enter a valid Gmail.")
        return
    
    otp = user_otps[email]
    if send_otp(email, otp):
        await update.message.reply_text("OTP sent to your email. Please enter the OTP.")
    else:
        await update.message.reply_text("Failed to send OTP. Please try again.")

# Handle OTP verification
async def verify_otp(update: Update, _: CallbackContext) -> None:
    otp_input = int(update.message.text)
    for email, otp in user_otps.items():
        if otp == otp_input:
            verified_users.add(update.message.chat_id)
            await update.message.reply_text("Verification successful! You can now upload, browse, and delete files.")
            return
    await update.message.reply_text("Invalid OTP. Please try again.")

# Upload file
async def upload_file(update: Update, context: CallbackContext) -> None:
    if update.message.chat_id not in verified_users:
        await update.message.reply_text("Please verify your email first using /login.")
        return
    document = update.message.document
    file = await context.bot.get_file(document.file_id)
    file_path = f"downloads/{document.file_name}"
    await file.download_to_drive(file_path)
    file_metadata = {'name': document.file_name, 'parents': ['root']}
    media = MediaFileUpload(file_path, mimetype=document.mime_type)
    drive_service.files().create(body=file_metadata, media_body=media, fields='id').execute()
    await update.message.reply_text("File uploaded successfully!")
    os.remove(file_path)

# List files (dummy for testing)
async def list_files(update: Update, _: CallbackContext) -> None:
    if update.message.chat_id not in verified_users:
        await update.message.reply_text("Please verify your email first using /login.")
        return
    await update.message.reply_text("Listing files... (dummy for testing)")

# Main function
def main():
    # Create application
    application = Application.builder().token(TELEGRAM_BOT_TOKEN).build()

    # Add handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("login", login))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_email))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, verify_otp))
    application.add_handler(MessageHandler(filters.Document(), upload_file))
    application.add_handler(CommandHandler("list", list_files))

    # Run the bot
    print("Bot is running...")
    application.run_polling()

if __name__ == '__main__':
    main()
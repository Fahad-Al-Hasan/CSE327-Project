import os
import random
import smtplib
import logging
import json
import mysql.connector
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, CallbackContext, CallbackQueryHandler
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from oauth2client.service_account import ServiceAccountCredentials

# Configure logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

# Telegram Bot Token
TELEGRAM_BOT_TOKEN = "8177749899:AAF0Rf3bnCAyxSva3OJce8_WjPtIyO-ryec"

# Function to fetch email credentials from the database
def get_email_credentials():
    try:
        connection = mysql.connector.connect(

            host="localhost",
            user="root",
            password="",
            database="amazing_storage"
        )
        cursor = connection.cursor(dictionary=True)
        cursor.execute("SELECT email, password FROM email_credentials LIMIT 1")
        result = cursor.fetchone()
        cursor.close()
        connection.close()
        return result["email"], result["password"] if result else (None, None)
    except Exception as e:
        logger.error(f"Database error: {e}")
        return None, None

# Fetch email credentials
EMAIL_ADDRESS, EMAIL_PASSWORD = get_email_credentials()

# Store OTPs for verification
user_otps = {}
verified_users = set()

# Google Drive Authentication
SCOPES = ['https://www.googleapis.com/auth/drive']
SERVICE_ACCOUNT_FILE = 'credentials.json'
creds = ServiceAccountCredentials.from_json_keyfile_name(SERVICE_ACCOUNT_FILE, SCOPES)
drive_service = build('drive', 'v3', credentials=creds)

# Function to send OTP via email
def send_otp(email, otp):
    try:
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        server.login(EMAIL_ADDRESS, EMAIL_PASSWORD)
        message = f'Subject: Your OTP Code\n\nYour OTP code is {otp}'
        server.sendmail(EMAIL_ADDRESS, email, message)
        server.quit()
        return True
    except Exception as e:
        logger.error(f"Error sending email: {e}")
        return False

# Start command
async def start(update: Update, context: CallbackContext) -> None:
    await update.message.reply_text("Welcome! Send /login to authenticate via Gmail.")

# Login command
async def login(update: Update, context: CallbackContext) -> None:
    await update.message.reply_text("Please enter your Gmail address to receive an OTP.")

# Handle email input
async def handle_email(update: Update, context: CallbackContext) -> None:
    email = update.message.text
    otp = random.randint(100000, 999999)
    user_otps[email] = otp
    if send_otp(email, otp):
        await update.message.reply_text("OTP sent to your email. Please enter the OTP.")
    else:
        await update.message.reply_text("Failed to send OTP. Please try again.")

# Handle OTP verification
async def verify_otp(update: Update, context: CallbackContext) -> None:
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

# List files
async def list_files(update: Update, context: CallbackContext) -> None:
    if update.message.chat_id not in verified_users:
        await update.message.reply_text("Please verify your email first using /login.")
        return
    results = drive_service.files().list(pageSize=10, fields="files(id, name)").execute()
    files = results.get('files', [])
    if not files:
        await update.message.reply_text("No files found.")
    else:
        file_list = '\n'.join([f"{file['name']} (ID: {file['id']})" for file in files])
        await update.message.reply_text(f"Files:\n{file_list}")

# Delete file
async def delete_file(update: Update, context: CallbackContext) -> None:
    if update.message.chat_id not in verified_users:
        await update.message.reply_text("Please verify your email first using /login.")
        return
    file_id = context.args[0]
    drive_service.files().delete(fileId=file_id).execute()
    await update.message.reply_text("File deleted successfully.")

# Search file
async def search_file(update: Update, context: CallbackContext) -> None:
    if update.message.chat_id not in verified_users:
        await update.message.reply_text("Please verify your email first using /login.")
        return
    query = ' '.join(context.args)
    results = drive_service.files().list(q=f"name contains '{query}'", fields="files(id, name)").execute()
    files = results.get('files', [])
    if not files:
        await update.message.reply_text("No matching files found.")
    else:
        file_list = '\n'.join([f"{file['name']} (ID: {file['id']})" for file in files])
        await update.message.reply_text(f"Search results:\n{file_list}")

# Main function
def main():
    # Create application
    application = Application.builder().token(TELEGRAM_BOT_TOKEN).build()

    # Add handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("login", login))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_email))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, verify_otp))
    application.add_handler(MessageHandler(filters.DOCUMENT, upload_file))
    application.add_handler(CommandHandler("list", list_files))
    application.add_handler(CommandHandler("delete", delete_file))
    application.add_handler(CommandHandler("search", search_file))

    # Run the bot
    application.run_polling()

if __name__ == '__main__':
    main()

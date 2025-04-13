from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, CallbackQueryHandler, filters, ContextTypes
from dotenv import load_dotenv
import os
from db import check_email_exists, check_password, create_user
from oauth import generate_google_oauth_url, upload_to_google_drive, list_drive_files
from dropbox.oauth import DropboxOAuth2Flow
import threading
from callback_server import app as flask_app
from oauth import list_dropbox_files, upload_to_dropbox



load_dotenv()
BOT_TOKEN = os.getenv("BOT_TOKEN")
DROPBOX_APP_KEY = os.getenv("DROPBOX_APP_KEY")
DROPBOX_APP_SECRET = os.getenv("DROPBOX_APP_SECRET")

# Temporary session data
user_states = {}

# /start command
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("🔐 Log In", callback_data='login')],
        [InlineKeyboardButton("⚒ Sign Up", callback_data='signup')]
    ]
    await update.message.reply_text("Welcome! Please log in to continue.", reply_markup=InlineKeyboardMarkup(keyboard))

# Button clicks (login/signup/menu)
async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id

    if query.data == 'login':
       await query.message.reply_text("🔐 [Login](http://localhost:8080/login?user_id=%s)"%user_id,
       parse_mode="Markdown"
    )

    elif query.data == 'signup':
        signup_url = f"http://localhost:8080/signup?user_id={user_id}"
        await query.message.reply_text(
            f"📝 [Click here to sign up]({signup_url})", parse_mode="Markdown"
    )
    elif query.data == 'upload':
        await query.message.reply_text("📁 Please send the file you want to upload.")
    elif query.data == 'menu':
        await show_menu(query.message)
    elif query.data == 'connect_gdrive':
        gdrive_url = generate_google_oauth_url(str(user_id))
        await query.message.reply_text(f"🔐 Click to connect your Google Drive:\n{gdrive_url}")
    elif query.data == 'connect_dropbox':
        dropbox_url = generate_dropbox_auth_url(query.from_user.id)
        await query.message.reply_text(f"🔐 Click to connect your Dropbox:\n{dropbox_url}")
    elif query.data == 'list_gdrive':
        try:
            files = list_drive_files(str(user_id))
            if files:
                reply = "\n".join(f"📄 {file['name']} - https://drive.google.com/file/d/{file['id']}/view" for file in files)
            else:
                reply = "📂 No files found in your Google Drive."
        except Exception as e:
            reply = "❌ Error accessing your Google Drive. Please connect again."
        await query.message.reply_text(reply)

    elif query.data == 'list_dropbox':
       
        try:
            files = list_dropbox_files(str(user_id))
            if files:
                reply = "\n".join(f"📄 {name}" for name in files)
            else:
                reply = "📂 No files found in your Dropbox."
        except Exception as e:
            reply = "❌ Error accessing Dropbox. Please connect again."
        await query.message.reply_text(reply)

       


# Handles all user input
async def text_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    text = update.message.text.strip()
    state = user_states.get(user_id, {})

    if state.get('step') == 'awaiting_email':
        if check_email_exists(text):
            user_states[user_id]['email'] = text
            user_states[user_id]['step'] = 'awaiting_password'
            await update.message.reply_text("✅ Email found! Now enter your password:")
        else:
            await update.message.reply_text("❌ Email not found. Try again or Sign Up.")
    elif state.get('step') == 'awaiting_password':
        email = user_states[user_id]['email']
        if check_password(email, text):
            user_states[user_id]['step'] = 'logged_in'
            await update.message.reply_text("✅ Login successful!")
            await show_menu(update.message)
        else:
            await update.message.reply_text("❌ Incorrect password. Try again.")
    elif state.get('step') == 'signup_email':
        if check_email_exists(text):
            await update.message.reply_text("❌ Email already registered. Please log in.")
        else:
            user_states[user_id]['email'] = text
            user_states[user_id]['step'] = 'signup_password'
            await update.message.reply_text("✅ Email accepted! Now enter a password:")
    elif state.get('step') == 'signup_password':
        email = user_states[user_id]['email']
        success = create_user(email, text)
        if success:
            user_states[user_id]['step'] = 'logged_in'
            await update.message.reply_text("✅ Registration successful! You are now logged in.")
            await show_menu(update.message)
        else:
            await update.message.reply_text("❌ Registration failed. Email might already exist.")
    elif text == "🔗 Connect Google Drive":
        auth_url = generate_google_oauth_url(str(user_id))
        await update.message.reply_text(f"🌐 [Click here to connect Google Drive]({auth_url})", parse_mode='Markdown')

# File upload handler
async def handle_document(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    document = update.message.document

    if not document:
        await update.message.reply_text("❌ No file found in message.")
        return

    file = await document.get_file()
    file_path = f"{user_id}_{document.file_name}"
    await file.download_to_drive(file_path)
    await update.message.reply_text("📤 Uploading your file to Google Drive...")

    try:
        success = upload_to_google_drive(user_id, file_path)
        if success:
            await update.message.reply_text("✅ File uploaded to your Google Drive!")
        else:
            await update.message.reply_text("⚠️ Failed to upload file. Please authenticate first.")
    except Exception as e:
        await update.message.reply_text(f"❌ Upload error: {e}")

        upload_to_dropbox(user_id, file_path)
        await update.message.reply_text("✅ File uploaded to Dropbox!")

# Shared menu builder
async def show_menu(message):
    keyboard = [
        [InlineKeyboardButton("📤 Upload File", callback_data='upload')],
        [InlineKeyboardButton("🔗 Connect Google Drive", callback_data='connect_gdrive')],
        [InlineKeyboardButton("🔗 Connect Dropbox", callback_data='connect_dropbox')],
        [InlineKeyboardButton("📂 List Google Drive Files", callback_data='list_gdrive')],
        [InlineKeyboardButton("📂 List Dropbox Files", callback_data='list_dropbox')],
    ]
    await message.reply_text("Choose an option:", reply_markup=InlineKeyboardMarkup(keyboard))

# Dropbox auth helper
def generate_dropbox_auth_url(user_id):
    flow = DropboxOAuth2Flow(
        consumer_key=DROPBOX_APP_KEY,
        consumer_secret=DROPBOX_APP_SECRET,
        redirect_uri="http://localhost:8080/dropbox/callback",
        session={}, csrf_token_session_key="dropbox-auth-csrf-token"
    )
    return flow.start()

# Start Flask server
def run_flask():
    flask_app.run(port=8080)

# Main entry
def main():
    threading.Thread(target=run_flask, daemon=True).start()

    app = ApplicationBuilder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(button_handler))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, text_handler))
    app.add_handler(MessageHandler(filters.Document.ALL, handle_document))

    print("✅ Bot and Flask server running...")
    app.run_polling()

if __name__ == "__main__":
    main()
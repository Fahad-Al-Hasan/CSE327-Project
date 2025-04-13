from dotenv import load_dotenv
from flask import Flask, request, render_template, redirect,session
from flask_session import Session
from dropbox.oauth import DropboxOAuth2Flow
from google_auth_oauthlib.flow import Flow
import os
import dropbox
from oauth import save_user_credentials
import bcrypt
from telegram import Bot


load_dotenv()
app = Flask(__name__)

BOT_TOKEN = os.getenv("BOT_TOKEN")
bot = Bot(token=BOT_TOKEN)

user_tokens = {}


@app.route("/login")
def login_form():
    user_id = request.args.get("user_id")
    return render_template("login.html", user_id=user_id)

@app.route("/signup")
def signup_form():
    user_id = request.args.get("user_id")
    return render_template("signup.html", user_id=user_id)

@app.route("/submit_signup", methods=["POST"])
def submit_signup():
    email = request.form.get("email")
    password = request.form.get("password")
    user_id = request.args.get("user_id")

    if email in user_tokens:
        return "⚠️ This email is already registered. Please log in."

    # Hash the password using bcrypt
    hashed_pw = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
    user_tokens[email] = hashed_pw

    bot.send_message(chat_id=user_id, text=f"🎉 Signup successful!\nWelcome, *{email}*", parse_mode="Markdown")
    return redirect("https://t.me/YourBotUsername")

@app.route("/submit_login", methods=["POST"])
def submit_login():
    email = request.form.get("email")
    password = request.form.get("password")
    user_id = request.args.get("user_id")

    if email not in user_tokens:
        return "❌ Email not found. Please sign up."

    # Verify password using bcrypt
    hashed_pw = user_tokens[email]
    if bcrypt.checkpw(password.encode('utf-8'), hashed_pw):
        bot.send_message(chat_id=user_id, text=f"✅ Login successful!\nWelcome back, *{email}*", parse_mode="Markdown")
        return redirect("https://t.me/YourBotUsername")
    else:
        return "❌ Incorrect password. Please try again."




#google
@app.route("/google/callback")
def google_callback():
    code = request.args.get("code")
    state = request.args.get("state") 

    flow = Flow.from_client_secrets_file(
        'client_secret.json',
        scopes=["https://www.googleapis.com/auth/drive.file"],
        redirect_uri='http://localhost:8080/google/callback'
    )

    flow.fetch_token(code=code)

    credentials = flow.credentials
    
    user_tokens[state] = {
        "token": credentials.token,
        "refresh_token": credentials.refresh_token,
        "token_uri": credentials.token_uri,
        "client_id": credentials.client_id,
        "client_secret": credentials.client_secret,
        "scopes": credentials.scopes
    }

   
    save_user_credentials(state, credentials)
    return "✅ Google Drive connected successfully! You can close this tab."


# Dropbox 
@app.route('/dropbox/start')
def dropbox_start():
    user_id = request.args.get("user_id")
    session['user_id'] = user_id
    flow = DropboxOAuth2Flow(
        consumer_key=os.getenv("DROPBOX_APP_KEY"),
        consumer_secret=os.getenv("DROPBOX_APP_SECRET"),
        redirect_uri="http://localhost:8080/dropbox/callback",
        session=session,
        csrf_token_session_key="dropbox-auth-csrf-token"
    )
    return redirect(flow.start())


@app.route('/dropbox/callback')
def dropbox_callback():
    flow = DropboxOAuth2Flow(
        consumer_key=os.getenv("DROPBOX_APP_KEY"),
        consumer_secret=os.getenv("DROPBOX_APP_SECRET"),
        redirect_uri="http://localhost:8080/dropbox/callback",
        session=session,
        csrf_token_session_key="dropbox-auth-csrf-token"
    )
    try:
        access_token, dropbox_user_id, _ = flow.finish(request.args)
        print(f"✅ Dropbox authorized for Telegram user: {session['user_id']}")
        # Save access_token using session['user_id'] in your DB or file
        return "✅ Dropbox authorization successful. You can return to Telegram bot."
    except Exception as e:
        print(f"❌ Dropbox auth failed: {e}")
        return "❌ Dropbox authorization failed."

if __name__ == "__main__":
    if not os.path.exists("tokens"):
        os.makedirs("tokens")
    app.run(port=8080)
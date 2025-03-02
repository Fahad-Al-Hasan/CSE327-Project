from flask import Flask, redirect, request, session, url_for, jsonify, render_template
from google_auth_oauthlib.flow import Flow
from googleapiclient.discovery import build
import os

app = Flask(__name__)
app.secret_key = "your_secret_key"

# Replace with your client secrets file
CLIENT_SECRETS_FILE = "client_secrets.json"
SCOPES = ["https://www.googleapis.com/auth/drive.file"]
REDIRECT_URI = "http://localhost:5000/oauth2callback"

# Dictionary to store user sessions
user_tokens = {}

@app.route("/")
def home():
    return render_template("index.html", accounts=list(user_tokens.keys()))

@app.route("/login")
def login():
    flow = Flow.from_client_secrets_file(CLIENT_SECRETS_FILE, scopes=SCOPES, redirect_uri=REDIRECT_URI)
    auth_url, state = flow.authorization_url()
    session["state"] = state
    return redirect(auth_url)

@app.route("/oauth2callback")
def oauth2callback():
    state = session.get("state")
    flow = Flow.from_client_secrets_file(CLIENT_SECRETS_FILE, scopes=SCOPES, state=state, redirect_uri=REDIRECT_URI)
    flow.fetch_token(authorization_response=request.url)

    credentials = flow.credentials
    user_info_service = build("oauth2", "v2", credentials=credentials)
    user_info = user_info_service.userinfo().get().execute()
    email = user_info["email"]

    user_tokens[email] = credentials
    return redirect(url_for("home"))

@app.route("/upload", methods=["POST"])
def upload():
    email = request.form.get("email")
    file = request.files["file"]

    if email not in user_tokens:
        return jsonify({"error": "User not authenticated"}), 403

    credentials = user_tokens[email]
    drive_service = build("drive", "v3", credentials=credentials)

    file_metadata = {"name": file.filename}
    media = file.read()

    file_drive = drive_service.files().create(body=file_metadata, media_body=media).execute()
    return jsonify({"message": "File uploaded", "file_id": file_drive["id"]})

@app.route("/logout/<email>")
def logout(email):
    user_tokens.pop(email, None)
    return redirect(url_for("home"))

if __name__ == "__main__":
    app.run(debug=True)

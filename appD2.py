from flask import Flask, request, jsonify, render_template, redirect, session
import dropbox
import os
import requests
from urllib.parse import urlencode

app = Flask(__name__)
app.secret_key = "your_secret_key"

# 🔹 Dropbox Configuration
DROPBOX_ACCESS_TOKEN = "your_dropbox_access_token"
dbx = dropbox.Dropbox(DROPBOX_ACCESS_TOKEN)

# 🔹 OneDrive Configuration
ONEDRIVE_CLIENT_ID = "your_onedrive_client_id"
ONEDRIVE_CLIENT_SECRET = "your_onedrive_client_secret"
ONEDRIVE_REDIRECT_URI = "http://localhost:5000/onedrive/callback"
ONEDRIVE_AUTH_URL = "https://login.microsoftonline.com/common/oauth2/v2.0/authorize"
ONEDRIVE_TOKEN_URL = "https://login.microsoftonline.com/common/oauth2/v2.0/token"
ONEDRIVE_API_URL = "https://graph.microsoft.com/v1.0/me/drive"

UPLOAD_FOLDER = "uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# ✅ Route: Homepage
@app.route("/")
def home():
    return render_template("index.html")

# ✅ OneDrive OAuth Login
@app.route("/onedrive/login")
def onedrive_login():
    params = {
        "client_id": ONEDRIVE_CLIENT_ID,
        "response_type": "code",
        "redirect_uri": ONEDRIVE_REDIRECT_URI,
        "scope": "files.readwrite offline_access",
    }
    return redirect(f"{ONEDRIVE_AUTH_URL}?{urlencode(params)}")

# ✅ OneDrive OAuth Callback
@app.route("/onedrive/callback")
def onedrive_callback():
    code = request.args.get("code")
    data = {
        "client_id": ONEDRIVE_CLIENT_ID,
        "client_secret": ONEDRIVE_CLIENT_SECRET,
        "code": code,
        "redirect_uri": ONEDRIVE_REDIRECT_URI,
        "grant_type": "authorization_code",
    }
    response = requests.post(ONEDRIVE_TOKEN_URL, data=data).json()
    session["onedrive_token"] = response["access_token"]
    return redirect("/")

# ✅ Upload File to Dropbox
@app.route("/upload/dropbox", methods=["POST"])
def upload_to_dropbox():
    if "file" not in request.files:
        return jsonify({"message": "No file uploaded"}), 400
    file = request.files["file"]
    file_path = os.path.join(UPLOAD_FOLDER, file.filename)
    file.save(file_path)
    
    try:
        with open(file_path, "rb") as f:
            dbx.files_upload(f.read(), f"/{file.filename}")
        os.remove(file_path)
        return jsonify({"message": "File uploaded to Dropbox"}), 200
    except Exception as e:
        return jsonify({"message": f"Dropbox upload failed: {str(e)}"}), 500

# ✅ Upload File to OneDrive
@app.route("/upload/onedrive", methods=["POST"])
def upload_to_onedrive():
    if "file" not in request.files:
        return jsonify({"message": "No file uploaded"}), 400
    file = request.files["file"]
    file_path = os.path.join(UPLOAD_FOLDER, file.filename)
    file.save(file_path)
    
    if "onedrive_token" not in session:
        return jsonify({"message": "OneDrive not authenticated"}), 401
    
    headers = {"Authorization": f"Bearer {session['onedrive_token']}", "Content-Type": "application/json"}
    with open(file_path, "rb") as f:
        response = requests.put(f"{ONEDRIVE_API_URL}/root:/{file.filename}:/content", headers=headers, data=f)
    os.remove(file_path)
    return jsonify(response.json()), response.status_code

# ✅ List Files from Dropbox
@app.route("/files/dropbox", methods=["GET"])
def list_dropbox_files():
    try:
        result = dbx.files_list_folder("")
        files = [{"name": file.name, "path": file.path_lower} for file in result.entries]
        return jsonify({"files": files}), 200
    except Exception as e:
        return jsonify({"message": f"Dropbox error: {str(e)}"}), 500

# ✅ List Files from OneDrive
@app.route("/files/onedrive", methods=["GET"])
def list_onedrive_files():
    if "onedrive_token" not in session:
        return jsonify({"message": "OneDrive not authenticated"}), 401
    
    headers = {"Authorization": f"Bearer {session['onedrive_token']}"}
    response = requests.get(f"{ONEDRIVE_API_URL}/root/children", headers=headers)
    return jsonify(response.json()), response.status_code

# ✅ Download File from Dropbox
@app.route("/download/dropbox/<path:file_path>", methods=["GET"])
def download_from_dropbox(file_path):
    try:
        metadata, res = dbx.files_download(f"/{file_path}")
        return res.content, 200, {"Content-Disposition": f"attachment; filename={metadata.name}"}
    except Exception as e:
        return jsonify({"message": f"Dropbox download failed: {str(e)}"}), 500

# ✅ Download File from OneDrive
@app.route("/download/onedrive/<file_id>", methods=["GET"])
def download_from_onedrive(file_id):
    if "onedrive_token" not in session:
        return jsonify({"message": "OneDrive not authenticated"}), 401
    
    headers = {"Authorization": f"Bearer {session['onedrive_token']}"}
    response = requests.get(f"{ONEDRIVE_API_URL}/items/{file_id}/content", headers=headers, stream=True)
    return response.content, response.status_code, {"Content-Disposition": "attachment"}

if __name__ == "__main__":
    app.run(debug=True)

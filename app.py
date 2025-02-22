from flask import Flask, request, render_template, jsonify, send_file
from flask_cors import CORS
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseUpload
import dropbox
import hashlib
import io
import os
import random
import ssl
import time
import pymysql

app = Flask(__name__)
CORS(app)  # Enable CORS for all routes

# 🔹 Force TLS 1.2 or 1.3 (Fix SSL errors)
ssl._create_default_https_context = ssl._create_unverified_context

# Database connection
DB_HOST = "your_db_host"
DB_USER = "your_db_user"
DB_PASSWORD = "your_db_password"
DB_NAME = "your_db_name"

def get_db_connection():
    return pymysql.connect(host=DB_HOST, user=DB_USER, password=DB_PASSWORD, database=DB_NAME)

def init_db():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS file_chunks (
            file_hash VARCHAR(64),
            filename VARCHAR(255),
            chunk_index INT,
            platform VARCHAR(10),
            account_index INT,
            chunk_id VARCHAR(255),
            PRIMARY KEY (file_hash, chunk_index)
        )
    """)
    conn.commit()
    conn.close()

init_db()

# Google Drive service account credentials and folder IDs
GDRIVE_CREDENTIALS = ["credentials.json"]
DRIVE_FOLDERS = [
    '1RX9n3bYgmzH8g_WapDOlvbMtJuNeo0My',  # Folder ID
    '1wCYPW0SdNHpz1VdMXLFBuo2YvPdWf4eY',
    '1feL26aFdeofoebbIYMUMk33MRVS6f6SL'
]

# Dropbox Access Tokens
DROPBOX_TOKENS = [
    "dropbox_access_token_1",
    "dropbox_access_token_2"
]

CHUNK_SIZE = 512 * 1024  # 512KB chunks

# Google Drive and Dropbox Helper Functions
def get_drive_service(index):
    creds = Credentials.from_service_account_file(GDRIVE_CREDENTIALS[index], scopes=["https://www.googleapis.com/auth/drive"])
    return build("drive", "v3", credentials=creds)

def get_dropbox_client(index):
    return dropbox.Dropbox(DROPBOX_TOKENS[index])

def upload_chunk_to_drive(chunk_data, chunk_name):
    for index in range(len(GDRIVE_CREDENTIALS)):
        drive_service = get_drive_service(index)
        folder_id = DRIVE_FOLDERS[index]
        file_metadata = {"name": chunk_name, "parents": [folder_id]}
        media = MediaIoBaseUpload(io.BytesIO(chunk_data), mimetype="application/octet-stream")
        file = drive_service.files().create(body=file_metadata, media_body=media, fields="id").execute()
        return {"platform": "google", "account_index": index, "chunk_id": file["id"]}
    return None

def upload_chunk_to_dropbox(chunk_data, chunk_name):
    for index in range(len(DROPBOX_TOKENS)):
        dbx = get_dropbox_client(index)
        path = f"/{chunk_name}"
        dbx.files_upload(chunk_data, path, mode=dropbox.files.WriteMode.overwrite)
        return {"platform": "dropbox", "account_index": index, "chunk_id": path}
    return None

def upload_chunk(chunk_data, chunk_name):
    drive_result = upload_chunk_to_drive(chunk_data, chunk_name)
    if drive_result:
        return drive_result
    dropbox_result = upload_chunk_to_dropbox(chunk_data, chunk_name)
    if dropbox_result:
        return dropbox_result
    return None

@app.route("/upload", methods=["POST"])
def upload_file():
    if "file" not in request.files:
        return jsonify({"error": "No file uploaded"}), 400

    file = request.files["file"]
    file_data = file.read()
    file_hash = hashlib.sha256(file_data).hexdigest()
    file_name = file.filename
    
    chunks = [file_data[i:i + CHUNK_SIZE] for i in range(0, len(file_data), CHUNK_SIZE)]
    conn = get_db_connection()
    cursor = conn.cursor()

    for index, chunk_data in enumerate(chunks):
        chunk_name = f"{file_name}_part{index}"
        upload_info = upload_chunk(chunk_data, chunk_name)
        if not upload_info:
            return jsonify({"error": "Not enough storage available"}), 500
        cursor.execute("""
            INSERT INTO file_chunks (file_hash, filename, chunk_index, platform, account_index, chunk_id)
            VALUES (%s, %s, %s, %s, %s, %s)
        """, (file_hash, file_name, index, upload_info["platform"], upload_info["account_index"], upload_info["chunk_id"]))
    
    conn.commit()
    conn.close()
    return jsonify({"message": "File uploaded successfully", "file_hash": file_hash}), 200

@app.route("/download/<file_hash>", methods=["GET"])
def download_file(file_hash):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT filename, chunk_index, platform, account_index, chunk_id FROM file_chunks WHERE file_hash = %s ORDER BY chunk_index", (file_hash,))
    chunks = cursor.fetchall()
    conn.close()

    if not chunks:
        return jsonify({"error": "File not found"}), 404

    file_name = chunks[0][0]
    merged_file = io.BytesIO()

    for chunk in chunks:
        chunk_index, platform, account_index, chunk_id = chunk[1], chunk[2], chunk[3], chunk[4]
        if platform == "google":
            drive_service = get_drive_service(account_index)
            chunk_data = drive_service.files().get_media(fileId=chunk_id).execute()
        else:
            dbx = get_dropbox_client(account_index)
            _, res = dbx.files_download(chunk_id)
            chunk_data = res.content
        merged_file.write(chunk_data)
    
    merged_file.seek(0)
    return send_file(merged_file, as_attachment=True, download_name=file_name, mimetype="application/octet-stream")

if __name__ == "__main__":
    app.run(debug=True, port=5000)

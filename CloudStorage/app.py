from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseUpload
import dropbox
import hashlib
import io
import os
import logging

# Initialize Flask app
app = Flask(__name__)
CORS(app)  # Enable CORS for all routes

# Google Drive service account credentials and folder IDs
GDRIVE_CREDENTIALS = [
    "service_account.json"
    
]
DRIVE_FOLDERS = [
    "folder_id_1",
    "folder_id_2",
    "folder_id_3",
]

# Dropbox Access Tokens
DROPBOX_TOKENS = [
    "dropbox_access_token_1",
    "dropbox_access_token_2"
]

CHUNK_SIZE = 512 * 1024  # 512KB chunks

# File metadata storage (in-memory)
file_metadata = {}

def get_drive_service(index):
    """Returns a Google Drive service instance for the specified account."""
    creds = Credentials.from_service_account_file(GDRIVE_CREDENTIALS[index], scopes=["https://www.googleapis.com/auth/drive"])
    return build("drive", "v3", credentials=creds)

def get_dropbox_client(index):
    """Returns a Dropbox client for the specified account."""
    return dropbox.Dropbox(DROPBOX_TOKENS[index])

def get_drive_free_space(index):
    """Fetches free storage space for a Google Drive account."""
    drive_service = get_drive_service(index)
    about = drive_service.about().get(fields="storageQuota").execute()
    used = int(about['storageQuota']['usage'])
    total = int(about['storageQuota']['limit'])
    return total - used

def get_dropbox_free_space(index):
    """Fetches free storage space for a Dropbox account."""
    dbx = get_dropbox_client(index)
    usage = dbx.users_get_space_usage()
    return usage.allocation.get_individual().allocated - usage.used

def upload_chunk_to_drive(chunk_data, chunk_name):
    """Uploads a chunk to the Google Drive account with available space."""
    for index in range(len(GDRIVE_CREDENTIALS)):
        if get_drive_free_space(index) > len(chunk_data):
            drive_service = get_drive_service(index)
            folder_id = DRIVE_FOLDERS[index]
            file_metadata = {"name": chunk_name, "parents": [folder_id]}
            media = MediaIoBaseUpload(io.BytesIO(chunk_data), mimetype="application/octet-stream")
            file = drive_service.files().create(body=file_metadata, media_body=media, fields="id").execute()
            return {"platform": "google", "account_index": index, "chunk_id": file["id"]}
    return None

def upload_chunk_to_dropbox(chunk_data, chunk_name):
    """Uploads a chunk to the Dropbox account with available space."""
    for index in range(len(DROPBOX_TOKENS)):
        if get_dropbox_free_space(index) > len(chunk_data):
            dbx = get_dropbox_client(index)
            path = f"/{chunk_name}"
            dbx.files_upload(chunk_data, path, mode=dropbox.files.WriteMode.overwrite)
            return {"platform": "dropbox", "account_index": index, "chunk_id": path}
    return None

def upload_chunk(chunk_data, chunk_name):
    """Uploads a chunk to an available storage platform."""
    drive_result = upload_chunk_to_drive(chunk_data, chunk_name)
    if drive_result:
        return drive_result
    dropbox_result = upload_chunk_to_dropbox(chunk_data, chunk_name)
    if dropbox_result:
        return dropbox_result
    return None  # No available storage

@app.route("/upload", methods=["POST"])
def upload_file():
    if "file" not in request.files:
        return jsonify({"error": "No file uploaded"}), 400

    file = request.files["file"]
    file_data = file.read()
    file_hash = hashlib.sha256(file_data).hexdigest()
    file_name = file.filename
    
    chunks = [file_data[i:i + CHUNK_SIZE] for i in range(0, len(file_data), CHUNK_SIZE)]
    total_chunks = len(chunks)
    chunk_ids = {}

    for index, chunk_data in enumerate(chunks):
        chunk_name = f"{file_name}_part{index}"
        upload_info = upload_chunk(chunk_data, chunk_name)
        if not upload_info:
            return jsonify({"error": "Not enough storage available"}), 500
        chunk_ids[index] = upload_info

    file_metadata[file_hash] = {"filename": file_name, "total_chunks": total_chunks, "chunks": chunk_ids}
    return jsonify({"message": "File uploaded successfully", "file_hash": file_hash}), 200

@app.route("/download/<file_hash>", methods=["GET"])
def download_file(file_hash):
    if file_hash not in file_metadata:
        return jsonify({"error": "File not found"}), 404

    metadata = file_metadata[file_hash]
    chunks = metadata["chunks"]
    file_name = metadata["filename"]
    merged_file = io.BytesIO()

    for index in sorted(chunks.keys()):
        chunk_info = chunks[index]
        if chunk_info["platform"] == "google":
            drive_service = get_drive_service(chunk_info["account_index"])
            chunk_data = drive_service.files().get_media(fileId=chunk_info["chunk_id"]).execute()
        else:
            dbx = get_dropbox_client(chunk_info["account_index"])
            _, res = dbx.files_download(chunk_info["chunk_id"])
            chunk_data = res.content
        merged_file.write(chunk_data)
    
    merged_file.seek(0)
    return send_file(merged_file, as_attachment=True, download_name=file_name, mimetype="application/octet-stream")

if __name__ == "__main__":
    app.run(debug=True, port=5000)
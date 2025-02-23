from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseUpload
import dropbox
import hashlib
import io
import logging
import random
import time
import mimetypes
import re
from abc import ABC, abstractmethod

app = Flask(__name__)
CORS(app)

CHUNK_SIZE = 512 * 1024  # 512KB chunks

# In-memory storage for file metadata
file_metadata = {}

class StorageProvider(ABC):
    @abstractmethod
    def upload_chunk(self, chunk_data, chunk_name):
        pass
    
    @abstractmethod
    def download_chunk(self, chunk_id):
        pass
    
    @abstractmethod
    def delete_chunk(self, chunk_id):
        pass

class GoogleDriveStorage(StorageProvider):
    CREDENTIALS_FILES = ['credentials.json']
    FOLDER_IDS = ['1RX9n3bYgmzH8g_WapDOlvbMtJuNeo0My', '1wCYPW0SdNHpz1VdMXLFBuo2YvPdWf4eY', '1feL26aFdeofoebbIYMUMk33MRVS6f6SL']
    
    def __init__(self, index):
        self.index = index
        self.creds = Credentials.from_service_account_file(
            self.CREDENTIALS_FILES[index],
            scopes=["https://www.googleapis.com/auth/drive"]
        )
        self.service = build("drive", "v3", credentials=self.creds)

    def upload_chunk(self, chunk_data, chunk_name):
        folder_id = self.FOLDER_IDS[self.index]
        metadata = {"name": chunk_name, "parents": [folder_id]}
        media = MediaIoBaseUpload(io.BytesIO(chunk_data), mimetype="application/octet-stream")
        file = self.service.files().create(body=metadata, media_body=media, fields="id").execute()
        return {"platform": "google", "chunk_id": file["id"]}

    def download_chunk(self, chunk_id):
        return self.service.files().get_media(fileId=chunk_id).execute()

    def delete_chunk(self, chunk_id):
        self.service.files().delete(fileId=chunk_id).execute()

class DropboxStorage(StorageProvider):
    TOKENS = ["token"]
    
    def __init__(self, index):
        self.index = index
        self.client = dropbox.Dropbox(self.TOKENS[index])

    def upload_chunk(self, chunk_data, chunk_name):
        path = f"/{chunk_name}"
        self.client.files_upload(chunk_data, path, mode=dropbox.files.WriteMode.overwrite)
        return {"platform": "dropbox", "chunk_id": path}

    def download_chunk(self, chunk_id):
        _, res = self.client.files_download(chunk_id)
        return res.content

    def delete_chunk(self, chunk_id):
        self.client.files_delete_v2(chunk_id)

# Factory function to randomly select a storage provider
def get_storage_provider():
    providers = [GoogleDriveStorage(random.randint(0, len(GoogleDriveStorage.CREDENTIALS_FILES) - 1)),
                 DropboxStorage(random.randint(0, len(DropboxStorage.TOKENS) - 1))]
    return random.choice(providers)

@app.route("/upload", methods=["POST"])
def upload_file():
    if "file" not in request.files:
        return jsonify({"error": "No file uploaded"}), 400

    file = request.files["file"]
    file_data = file.read()
    file_hash = hashlib.sha256(file_data).hexdigest()
    file_name = file.filename
    upload_time = time.time()
    
    chunks = [file_data[i:i + CHUNK_SIZE] for i in range(0, len(file_data), CHUNK_SIZE)]
    total_chunks = len(chunks)
    chunk_ids = {}
    
    for index, chunk_data in enumerate(chunks):
        chunk_name = f"{file_name}_part{index}"
        provider = get_storage_provider()
        upload_info = provider.upload_chunk(chunk_data, chunk_name)
        chunk_ids[index] = upload_info
    
    file_metadata[file_hash] = {
        "filename": file_name,
        "total_chunks": total_chunks,
        "chunks": chunk_ids,
        "upload_time": upload_time
    }
    return jsonify({"message": "File uploaded successfully", "file_hash": file_hash}), 200

if __name__ == "__main__":
    app.run(debug=True, port=5000)

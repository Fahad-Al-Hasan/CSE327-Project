from flask import Flask, request, render_template, jsonify
from flask_cors import CORS
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
import os
import random
import ssl
import time

app = Flask(__name__)
CORS(app)

ssl._create_default_https_context = ssl._create_unverified_context

SCOPES = ['https://www.googleapis.com/auth/drive']
SERVICE_ACCOUNT_FILE = 'credentials.json'
creds = Credentials.from_service_account_file(SERVICE_ACCOUNT_FILE, scopes=SCOPES)

drive_service = build('drive', 'v3', credentials=creds)

drive_folders = [
    '1RX9n3bYgmzH8g_WapDOlvbMtJuNeo0My',
    '1wCYPW0SdNHpz1VdMXLFBuo2YvPdWf4eY',
    '1feL26aFdeofoebbIYMUMk33MRVS6f6SL'
]

CHUNK_SIZE = 50 * 1024 * 1024  # 50MB per chunk

def split_file(file_path):
    chunks = []
    with open(file_path, 'rb') as f:
        chunk_num = 0
        while True:
            chunk_data = f.read(CHUNK_SIZE)
            if not chunk_data:
                break
            chunk_filename = f"{file_path}_part{chunk_num}"
            with open(chunk_filename, 'wb') as chunk_file:
                chunk_file.write(chunk_data)
            chunks.append(chunk_filename)
            chunk_num += 1
    return chunks

def upload_to_drive(file_path, filename):
    folder_id = random.choice(drive_folders)
    print(f"📤 Uploading {filename} to Google Drive folder {folder_id}")
    try:
        file_metadata = {'name': filename, 'parents': [folder_id]}
        media = MediaFileUpload(file_path, resumable=False)
        file_drive = drive_service.files().create(body=file_metadata, media_body=media, fields='id').execute()
        time.sleep(1)
        os.remove(file_path)
        return file_drive.get('id')
    except Exception as e:
        print(f"❌ Google Drive Upload Failed: {str(e)}")
        return None

def merge_chunks(chunks, output_file):
    with open(output_file, 'wb') as output:
        for chunk in sorted(chunks):
            with open(chunk, 'rb') as f:
                output.write(f.read())
    return output_file

@app.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return jsonify({'message': "No file uploaded."}), 400
    file = request.files['file']
    if file.filename == '':
        return jsonify({'message': "No selected file."}), 400
    filename = os.path.basename(file.filename)
    file_path = os.path.join("uploads", filename)
    file.save(file_path)
    chunks = split_file(file_path)
    chunk_ids = []
    for chunk in chunks:
        chunk_id = upload_to_drive(chunk, os.path.basename(chunk))
        if chunk_id:
            chunk_ids.append(chunk_id)
    if chunk_ids:
        return jsonify({'message': "File uploaded successfully!", 'chunk_ids': chunk_ids}), 200
    else:
        return jsonify({'message': "Google Drive upload failed."}), 500

if __name__ == '__main__':
    os.makedirs("uploads", exist_ok=True)
    app.run(debug=True)

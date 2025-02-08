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
CORS(app)  # Enables cross-origin requests

# 🔹 Force TLS 1.2 or 1.3 (Fix SSL errors)
ssl._create_default_https_context = ssl._create_unverified_context

# Authenticate Google Drive API with service account
SCOPES = ['https://www.googleapis.com/auth/drive']
SERVICE_ACCOUNT_FILE = 'credentials.json'
creds = Credentials.from_service_account_file(SERVICE_ACCOUNT_FILE, scopes=SCOPES)

# Build the Google Drive API client
drive_service = build('drive', 'v3', credentials=creds)

# Google Drive Folder IDs
drive_folders = [
    '1RX9n3bYgmzH8g_WapDOlvbMtJuNeo0My',
    '1wCYPW0SdNHpz1VdMXLFBuo2YvPdWf4eY',
    '1feL26aFdeofoebbIYMUMk33MRVS6f6SL'
]

def upload_to_drive(file_path, filename):
    """ Upload file to a randomly selected Google Drive folder """
    folder_id = random.choice(drive_folders)
    print(f"📤 Uploading {filename} to Google Drive folder {folder_id}")

    try:
        file_metadata = {'name': filename, 'parents': [folder_id]}
        media = MediaFileUpload(file_path, resumable=False)

        file_drive = drive_service.files().create(body=file_metadata, media_body=media, fields='id, mimeType').execute()
        file_id = file_drive.get('id')
        mime_type = file_drive.get('mimeType')

        time.sleep(1)
        os.remove(file_path)

        return {'file_id': file_id, 'mime_type': mime_type, 'name': filename}
    except Exception as e:
        print(f"❌ Google Drive Upload Failed: {str(e)}")
        return None

def list_drive_files():
    """ Retrieve list of files from all configured Google Drive folders """
    all_files = []

    for folder_id in drive_folders:
        try:
            results = drive_service.files().list(
                q=f"'{folder_id}' in parents and trashed=false",
                fields="files(id, name, mimeType, modifiedTime)",
                orderBy="modifiedTime desc"
            ).execute()

            files = results.get('files', [])
            for file in files:
                file_id = file['id']
                mime_type = file['mimeType']

                preview_link = None
                if mime_type.startswith('image/') or mime_type.startswith('video/'):
                    preview_link = f"https://drive.google.com/uc?id={file_id}"

                file_info = {
                    'id': file_id,
                    'name': file['name'],
                    'preview_link': preview_link,
                    'download_link': f"https://drive.google.com/uc?id={file_id}&export=download"
                }
                all_files.append(file_info)

        except Exception as e:
            print(f"❌ Error fetching files from folder {folder_id}: {e}")

    return all_files

@app.route('/')
def home():
    return render_template('index.html')

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

    result = upload_to_drive(file_path, filename)

    if result:
        return jsonify({
            'message': "File uploaded successfully!", 
            'file_id': result['file_id'], 
            'mime_type': result['mime_type'], 
            'name': result['name']
        }), 200
    else:
        return jsonify({'message': "Google Drive upload failed."}), 500

@app.route('/files', methods=['GET'])
def get_files():
    """ Returns a JSON response containing list of files with download links """
    files = list_drive_files()
    return jsonify({'files': files})

@app.route('/delete/<file_id>', methods=['DELETE'])
def delete_file(file_id):
    """Delete file from Google Drive"""
    try:
        drive_service.files().delete(fileId=file_id).execute()
        return jsonify({'message': 'File deleted successfully'}), 200
    except Exception as e:
        return jsonify({'error': f'Failed to delete file: {e}'}), 500

if __name__ == '__main__':
    os.makedirs("uploads", exist_ok=True)
    app.run(debug=True)
#Code with delete functionality and A-Z Sorting only
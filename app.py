from flask import Flask, request, render_template
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
import os
import random

app = Flask(__name__)

# Authenticate Google Drive API with service account
SCOPES = ['https://www.googleapis.com/auth/drive.file']
SERVICE_ACCOUNT_FILE = 'credentials.json'
creds = Credentials.from_service_account_file(SERVICE_ACCOUNT_FILE, scopes=SCOPES)

# Build the Google Drive API client
drive_service = build('drive', 'v3', credentials=creds)

# Google Drive Folder IDs (Each belongs to a different Google Account)
drive_folders = [
    '1RX9n3bYgmzH8g_WapDOlvbMtJuNeo0My',  # Replace with actual Folder ID from Google Drive
    '1wCYPW0SdNHpz1VdMXLFBuo2YvPdWf4eY',
    '1feL26aFdeofoebbIYMUMk33MRVS6f6SL'
]

def upload_to_drive(file_path, filename):
    """ Upload file to a randomly selected Google Drive folder """
    folder_id = random.choice(drive_folders)
    
    # Create a file metadata and upload it to Google Drive
    file_metadata = {'name': filename, 'parents': [folder_id]}
    media = MediaFileUpload(file_path, resumable=True)
    file_drive = drive_service.files().create(body=file_metadata, media_body=media, fields='id').execute()
    
    os.remove(file_path)  # Delete after upload
    return f"File uploaded to Drive Folder: {folder_id}"

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return "No file uploaded."
    
    file = request.files['file']
    if file.filename == '':
        return "No selected file."
    
    # Sanitize the filename to avoid issues with different OS
    filename = os.path.basename(file.filename)
    file_path = os.path.join("uploads", filename)
    file.save(file_path)
    
    result = upload_to_drive(file_path, filename)
    return result

if __name__ == '__main__':
    os.makedirs("uploads", exist_ok=True)  # Create upload folder if not exists
    app.run(debug=False)  # Set to False in production for security
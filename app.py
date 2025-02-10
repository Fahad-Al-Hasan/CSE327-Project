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

# Google Drive Folder IDs (Each belongs to a different Google Account)
drive_folders = [
    '1RX9n3bYgmzH8g_WapDOlvbMtJuNeo0My',  # Folder ID
    '1wCYPW0SdNHpz1VdMXLFBuo2YvPdWf4eY',
    '1feL26aFdeofoebbIYMUMk33MRVS6f6SL'
] #ekhane folder Id gulo deya acche jekhane ashole file save hobe

def upload_to_drive(file_path, filename):
    """ Upload file to a randomly selected Google Drive folder """
    folder_id = random.choice(drive_folders) #Randomly ekta folder choose kortese ekhane
    print(f"📤 Uploading {filename} to Google Drive folder {folder_id}")  # Debugging message print hobe ekta

    try:
        file_metadata = {'name': filename, 'parents': [folder_id]}
        #file er name and kothay save hobe sheta defined hocche ekhane
        media = MediaFileUpload(file_path, resumable=False)  # Prevents file lock issues
        #file lock issue mane modification or deletion or something else. ekhane sheta crack hobe
        file_drive = drive_service.files().create(body=file_metadata, media_body=media, fields='id').execute()
        #body=file_metadata: Passes the metadata (filename & folder).
        #media_body=media: Attaches the file content
        # Ensure file is fully uploaded before deleting
        #fields='id': Requests only the file ID as the response.
        #.execute(): Sends the request to Google Drive API and uploads the file.
        
        time.sleep(1) #FIle uploading ensuring
        
        try: #ei try er maddhome delete kora hocche local system theke
            os.remove(file_path)  # Delete after upload
            print(f"✅ File deleted: {file_path}")
        except Exception as e:
            print(f"❌ Could not delete file: {e}")
        
        return file_drive.get('id') #File Id ta return kore dibe

    except Exception as e:
        print(f"❌ Google Drive Upload Failed: {str(e)}")  # Debugging
        return None

def list_drive_files():
    """ Retrieve list of files from all configured Google Drive folders """
    #Ekhane file fetch hoy jokhon browse e click kora hoy
    all_files = []
    
    for folder_id in drive_folders:
        try:
            results = drive_service.files().list(
                q=f"'{folder_id}' in parents and trashed=false",
                fields="files(id, name, modifiedTime)",
                orderBy="modifiedTime desc"
            ).execute()
            
            files = results.get('files', [])
            for file in files:
                file['download_link'] = f"https://drive.google.com/uc?id={file['id']}&export=download"
                all_files.append(file)
        except Exception as e:
            print(f"❌ Error fetching files from folder {folder_id}: {e}")

    return all_files

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/upload', methods=['POST']) #It handles file upload
def upload_file():
    if 'file' not in request.files:
        return jsonify({'message': "No file uploaded."}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({'message': "No selected file."}), 400
    
    filename = os.path.basename(file.filename)
    file_path = os.path.join("uploads", filename)
    file.save(file_path)

    file_id = upload_to_drive(file_path, filename)

    if file_id:
        return jsonify({'message': f"File uploaded successfully! ID: {file_id}"}), 200
    else:
        return jsonify({'message': "Google Drive upload failed."}), 500

@app.route('/files', methods=['GET']) #SHob gulo file fetch kore
def get_files():
    """ Returns a JSON response containing list of files with download links """
    files = list_drive_files()
    return jsonify({'files': files})

if __name__ == '__main__':
    os.makedirs("uploads", exist_ok=True)  # Ensure upload folder exists
    app.run(debug=True)  # Enable debug mode for troubleshooting

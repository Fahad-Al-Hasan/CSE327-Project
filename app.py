from flask import Flask, request, jsonify, send_file
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
import os

app = Flask(__name__)

# Path to your service account credentials
SERVICE_ACCOUNT_FILE = 'path/to/your/credentials.json'
SCOPES = ['https://www.googleapis.com/auth/drive.file']

# Configure credentials and Google Drive API client
credentials = Credentials.from_service_account_file(SERVICE_ACCOUNT_FILE, scopes=SCOPES)
service = build('drive', 'v3', credentials=credentials)

# Google Drive folder IDs to simulate multiple "buckets"
drive_folders = ['folder_id_1', 'folder_id_2', 'folder_id_3']

# Route to upload a file
@app.route('/upload', methods=['POST'])
def upload_file():
    file = request.files['file']
    filename = file.filename
    file_path = os.path.join('uploads', filename)
    
    # Save file temporarily
    file.save(file_path)

    # Upload to one of the Google Drive folders (buckets)
    folder_id = drive_folders[0]  # You can use round-robin or some logic to pick a bucket
    media = MediaFileUpload(file_path, resumable=True)
    
    file_metadata = {'name': filename, 'parents': [folder_id]}
    uploaded_file = service.files().create(body=file_metadata, media_body=media, fields='id').execute()
    
    os.remove(file_path)  # Clean up local file after upload
    return jsonify({'message': 'File uploaded successfully', 'file_id': uploaded_file['id']})


# Route to list files in the "buckets"
@app.route('/files', methods=['GET'])
def list_files():
    results = service.files().list(q="'{}' in parents".format(drive_folders[0]), fields="files(id, name)").execute()
    files = results.get('files', [])
    
    file_list = [{'id': file['id'], 'name': file['name']} for file in files]
    return jsonify({'files': file_list})


# Route to download a file
@app.route('/download/<file_id>', methods=['GET'])
def download_file(file_id):
    request = service.files().get_media(fileId=file_id)
    file_path = os.path.join('downloads', f"{file_id}.tmp")

    with open(file_path, 'wb') as f:
        f.write(request.execute())

    return send_file(file_path, as_attachment=True)


if __name__ == '__main__':
    app.run(debug=True)

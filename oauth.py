from googleapiclient.http import MediaFileUpload
import os
import json
from google_auth_oauthlib.flow import Flow
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
import dropbox


CREDENTIALS_DIR = 'credentials'
DROPBOX_TOKEN_DIR = 'tokens'
os.makedirs(CREDENTIALS_DIR, exist_ok=True)
os.makedirs(DROPBOX_TOKEN_DIR, exist_ok=True)


# GOOGLE DRIVE
def generate_google_oauth_url(user_id):
    flow = Flow.from_client_secrets_file(
        'client_secret.json',
        scopes=['https://www.googleapis.com/auth/drive.file'],
        redirect_uri='http://localhost:8080/google/callback'
    )
    flow.redirect_uri = 'http://localhost:8080/google/callback'
    auth_url, _ = flow.authorization_url(
        access_type='offline',
        prompt='consent',
        state=str(user_id),
        include_granted_scopes='true'
    )
    return auth_url

def save_user_credentials(user_id, credentials):
    path = os.path.join(CREDENTIALS_DIR, f"{user_id}.json")
    with open(path, 'w') as f:
        json.dump({
            'token': credentials.token,
            'refresh_token': credentials.refresh_token,
            'token_uri': credentials.token_uri,
            'client_id': credentials.client_id,
            'client_secret': credentials.client_secret,
            'scopes': credentials.scopes
        }, f)

def get_user_credentials(user_id):
    path = os.path.join(CREDENTIALS_DIR, f"{user_id}.json")
    if not os.path.exists(path):
        return None
    with open(path) as f:
        data = json.load(f)
        return Credentials(**data)

def handle_google_callback(code, state):
    flow = Flow.from_client_secrets_file(
        'client_secret.json',
        scopes=['https://www.googleapis.com/auth/drive.file'],
        redirect_uri='http://localhost:8080/google/callback'
    )
    flow.fetch_token(code=code)
    credentials = flow.credentials
    user_id = state
    save_user_credentials(user_id, credentials)
    print(f"✅ Google Drive connected for user {user_id}")

def upload_to_google_drive(user_id, file_path):
    creds = get_user_credentials(user_id)
    if not creds:
        raise Exception("User not authenticated.")
    service = build('drive', 'v3', credentials=creds)

    file_metadata = {'name': os.path.basename(file_path)}
    media = MediaFileUpload(file_path, resumable=True)

    uploaded_file = service.files().create(
        body=file_metadata,
        media_body=media,
        fields='id, name'
    ).execute()

    return uploaded_file

def list_drive_files(user_id):
    creds = get_user_credentials(user_id)
    if not creds:
        raise Exception("User not authenticated.")
    service = build('drive', 'v3', credentials=creds)

    results = service.files().list(
        pageSize=10,
        fields="files(id, name)"
    ).execute()

    return results.get('files', [])


# DROPBOX 

def save_dropbox_token(user_id, access_token):
    path = os.path.join(DROPBOX_TOKEN_DIR, f"{user_id}_dropbox_token.json")
    with open(path, 'w') as f:
        json.dump({'access_token': access_token}, f)

def get_dropbox_client(user_id):
    path = f"tokens/{user_id}_dropbox_token.json"
    if not os.path.exists(path):
        return None
    with open(path) as f:
        data = json.load(f)
        return dropbox.Dropbox(data['access_token'])

def upload_to_dropbox(user_id, file_path):
    dbx = get_dropbox_client(user_id)
    if not dbx:
        raise Exception("Dropbox not authenticated.")
    
    with open(file_path, "rb") as f:
        dbx.files_upload(f.read(), f"/{os.path.basename(file_path)}", mute=True)

    return True

def list_dropbox_files(user_id):
    dbx = get_dropbox_client(user_id)
    if not dbx:
        raise Exception("Dropbox not authenticated.")

    entries = dbx.files_list_folder('').entries
    return [entry.name for entry in entries if isinstance(entry, dropbox.files.FileMetadata)]


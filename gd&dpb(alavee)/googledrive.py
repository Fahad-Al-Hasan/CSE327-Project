from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseUpload
import io
import random
import re
from bucket import Bucket, register_bucket

GDRIVE_CREDENTIALS = ['credentials.json']
DRIVE_FOLDERS = ['1RX9n3bYgmzH8g_WapDOlvbMtJuNeo0My','1wCYPW0SdNHpz1VdMXLFBuo2YvPdWf4eY','1feL26aFdeofoebbIYMUMk33MRVS6f6SL']

class GoogleDriveBucket(Bucket):
    def get_drive_service(self, index):
        creds = Credentials.from_service_account_file(GDRIVE_CREDENTIALS[index], scopes=["https://www.googleapis.com/auth/drive"])
        return build("drive", "v3", credentials=creds)
    def upload_chunk(self, chunk_data, chunk_name):
        index = random.randint(0, len(GDRIVE_CREDENTIALS)-1)
        service = self.get_drive_service(index)
        folder_id = DRIVE_FOLDERS[index]
        metadata = {"name": chunk_name, "parents": [folder_id]}
        media = MediaIoBaseUpload(io.BytesIO(chunk_data), mimetype="application/octet-stream")
        file = service.files().create(body=metadata, media_body=media, fields="id").execute()
        return {"platform": "google", "account_index": index, "chunk_id": file["id"]}
    def download_chunk(self, chunk_info):
        service = self.get_drive_service(chunk_info["account_index"])
        return service.files().get_media(fileId=chunk_info["chunk_id"]).execute()
    def delete_chunk(self, chunk_info):
        service = self.get_drive_service(chunk_info["account_index"])
        service.files().delete(fileId=chunk_info["chunk_id"]).execute()
    def list_chunks(self, base_name):
        chunks = []
        for i, folder_id in enumerate(DRIVE_FOLDERS):
            service = self.get_drive_service(i)
            results = service.files().list(q=f"'{folder_id}' in parents and name contains '{base_name}_part'", fields="files(id, name)").execute()
            for f in results.get("files", []):
                if f["name"].startswith(f"{base_name}_part"):
                    m = re.match(r"(" + re.escape(base_name) + r")_part(\d+)$", f["name"])
                    if m:
                        part = int(m.group(2))
                        chunks.append({"base_name": base_name, "platform": "google", "account_index": i, "chunk_id": f["id"], "part": part})
        return chunks

register_bucket("google", GoogleDriveBucket)

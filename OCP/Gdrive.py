from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseUpload
from .storage_abstract import CloudStorage
import io

class GoogleDriveStorage(CloudStorage):
    """Google Drive implementation of CloudStorage."""

    def __init__(self, credentials_file: str, folder_id: str):
        self.credentials = Credentials.from_service_account_file(
            credentials_file,
            scopes=["https://www.googleapis.com/auth/drive"]
        )
        self.service = build("drive", "v3", credentials=self.credentials)
        self.folder_id = folder_id

    def upload_chunk(self, chunk_data: bytes, chunk_name: str) -> str:
        """Upload a chunk to Google Drive."""
        metadata = {"name": chunk_name, "parents": [self.folder_id]}
        media = MediaIoBaseUpload(io.BytesIO(chunk_data), mimetype="application/octet-stream")
        file = self.service.files().create(body=metadata, media_body=media, fields="id").execute()
        return file["id"]

    def download_chunk(self, chunk_id: str) -> bytes:
        """Download a chunk from Google Drive."""
        return self.service.files().get_media(fileId=chunk_id).execute()

    def delete_chunk(self, chunk_id: str) -> None:
        """Delete a chunk from Google Drive."""
        self.service.files().delete(fileId=chunk_id).execute()

    def list_chunks(self, base_name: str) -> list:
        """List all chunks matching the base name in Google Drive."""
        results = self.service.files().list(
            q=f"'{self.folder_id}' in parents and name contains '{base_name}_part'",
            fields="files(id, name)"
        ).execute()
        return results.get("files", [])
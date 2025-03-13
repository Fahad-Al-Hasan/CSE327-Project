import os
from storage.storage_abstract import CloudStorage
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseUpload
import io
import logging

#logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class GoogleDriveStorage(CloudStorage):
    
    def __init__(self, credentials_file: str, folder_id: str):
        try:
            # Verify the credentials file exists
            if not os.path.exists(credentials_file = os.path.abspath("credentials1.json")):
                raise FileNotFoundError(f"Credentials file not found: {credentials_file}")

            #credentials
            self.credentials = Credentials.from_service_account_file(
                credentials_file,
                scopes=["https://www.googleapis.com/auth/drive"]
            )
            self.service = build("drive", "v3", credentials=self.credentials)
            self.folder_id = folder_id
            logger.info("Google Drive storage initialized successfully.")
        except Exception as e:
            logger.error(f"Failed to initialize Google Drive storage: {e}")
            raise

    def upload_chunk(self, chunk_data: bytes, chunk_name: str) -> str:
        """Upload a chunk to Google Drive."""
        try:
            metadata = {"name": chunk_name, "parents": [self.folder_id]}
            media = MediaIoBaseUpload(io.BytesIO(chunk_data), mimetype="application/octet-stream")
            file = self.service.files().create(body=metadata, media_body=media, fields="id").execute()
            logger.info(f"Chunk '{chunk_name}' uploaded successfully. File ID: {file['id']}")
            return file["id"]
        except Exception as e:
            logger.error(f"Failed to upload chunk '{chunk_name}': {e}")
            raise

    def download_chunk(self, chunk_id: str) -> bytes:
        """Download a chunk from Google Drive."""
        try:
            chunk_data = self.service.files().get_media(fileId=chunk_id).execute()
            logger.info(f"Chunk '{chunk_id}' downloaded successfully.")
            return chunk_data
        except Exception as e:
            logger.error(f"Failed to download chunk '{chunk_id}': {e}")
            raise

    def delete_chunk(self, chunk_id: str) -> None:
        """Delete a chunk from Google Drive."""
        try:
            self.service.files().delete(fileId=chunk_id).execute()
            logger.info(f"Chunk '{chunk_id}' deleted successfully.")
        except Exception as e:
            logger.error(f"Failed to delete chunk '{chunk_id}': {e}")
            raise

    def list_chunks(self, base_name: str) -> list:
        """List all chunks matching the base name in Google Drive."""
        try:
            results = self.service.files().list(
                q=f"'{self.folder_id}' in parents and name contains '{base_name}_part'",
                fields="files(id, name)"
            ).execute()
            logger.info(f"Found {len(results.get('files', []))} chunks for base name '{base_name}'.")
            return results.get("files", [])
        except Exception as e:
            logger.error(f"Failed to list chunks for base name '{base_name}': {e}")
            raise
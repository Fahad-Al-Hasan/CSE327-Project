import dropbox
from storage.storage_abstract import CloudStorage

class DropboxStorage(CloudStorage):
    """Dropbox implementation of CloudStorage."""

    def __init__(self, access_token: str):
        self.dbx = dropbox.Dropbox(access_token)

    def upload_chunk(self, chunk_data: bytes, chunk_name: str) -> str:
        """Upload a chunk to Dropbox."""
        path = f"/{chunk_name}"
        self.dbx.files_upload(chunk_data, path, mode=dropbox.files.WriteMode.overwrite)
        return path

    def download_chunk(self, chunk_id: str) -> bytes:
        """Download a chunk from Dropbox."""
        _, res = self.dbx.files_download(chunk_id)
        return res.content

    def delete_chunk(self, chunk_id: str) -> None:
        """Delete a chunk from Dropbox."""
        self.dbx.files_delete_v2(chunk_id)

    def list_chunks(self, base_name: str) -> list:
        """List all chunks matching the base name in Dropbox."""
        result = self.dbx.files_list_folder("", recursive=False)
        return [entry for entry in result.entries if isinstance(entry, dropbox.files.FileMetadata) and base_name in entry.name]
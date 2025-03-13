import random
from typing import List
from storage.storage_abstract import CloudStorage

class ChunkManager:

    def __init__(self, storage_services: List[CloudStorage]):
        self.storage_services = storage_services

    def upload_chunk(self, chunk_data: bytes, chunk_name: str) -> dict:
        """Upload a chunk to a randomly selected cloud platform and account."""
        # Randomly select a platform and account
        service = random.choice(self.storage_services)
        try:
            chunk_id = service.upload_chunk(chunk_data, chunk_name)
            return {
                "platform": service.__class__.__name__,
                "account_index": self.storage_services.index(service),
                "chunk_id": chunk_id
            }
        except Exception as e:
            print(f"Error uploading chunk '{chunk_name}' to {service.__class__.__name__}: {e}")
            raise Exception("Failed to upload chunk to all available accounts.")

    def download_chunk(self, chunk_info: dict) -> bytes:
        """Download a chunk from the specified cloud platform and account."""
        service = self.storage_services[chunk_info["account_index"]]
        return service.download_chunk(chunk_info["chunk_id"])

    def delete_chunk(self, chunk_info: dict) -> None:
        """Delete a chunk from the specified cloud platform and account."""
        service = self.storage_services[chunk_info["account_index"]]
        service.delete_chunk(chunk_info["chunk_id"])

    def list_chunks(self, base_name: str) -> list:
        """List all chunks matching the base name across all platforms and accounts."""
        chunks = []
        for service in self.storage_services:
            chunks.extend(service.list_chunks(base_name))
        return chunks
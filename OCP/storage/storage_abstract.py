from abc import ABC, abstractmethod
from typing import List

class CloudStorage(ABC):
    """ Abstract base class for defining cloud storage operations. """

    @abstractmethod
    def upload_chunk(self, chunk_data: bytes, chunk_name: str) -> str:
        """ Upload a chunk of data to the cloud storage. """
        pass

    @abstractmethod
    def download_chunk(self, chunk_id: str) -> bytes:
        """  Download a chunk of data from the cloud storage.  """
        pass

    @abstractmethod
    def delete_chunk(self, chunk_id: str) -> None:
        """ Delete a chunk of data from the cloud storage.  """
        pass

    @abstractmethod
    def list_chunks(self, base_name: str) -> List[str]:
        """  List all chunks in the cloud storage that match a base name.  """
        pass
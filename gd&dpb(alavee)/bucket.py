from abc import ABC, abstractmethod

BUCKET_REGISTRY = {}

def register_bucket(name, bucket_class):
    BUCKET_REGISTRY[name] = bucket_class

def get_bucket(name):
    return BUCKET_REGISTRY.get(name)

class Bucket(ABC):
    @abstractmethod
    def upload_chunk(self, chunk_data, chunk_name):
        pass
    @abstractmethod
    def download_chunk(self, chunk_info):
        pass
    @abstractmethod
    def delete_chunk(self, chunk_info):
        pass
    @abstractmethod
    def list_chunks(self, base_name):
        pass

register_bucket("bucket", None)

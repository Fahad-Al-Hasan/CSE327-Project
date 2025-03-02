import io
from bucket import get_bucket

def merge_chunks(chunks):
    chunks.sort(key=lambda x: x["part"])
    merged_file = io.BytesIO()
    for chunk_info in chunks:
        bucket_class = get_bucket(chunk_info["platform"])
        if bucket_class:
            bucket = bucket_class()
            data = bucket.download_chunk(chunk_info)
        else:
            data = b""
        merged_file.write(data)
    merged_file.seek(0)
    return merged_file

class FileObject:
    def __init__(self, file_hash, filename, total_chunks, chunks, upload_time):
        self.file_hash = file_hash
        self.filename = filename
        self.total_chunks = total_chunks
        self.chunks = chunks
        self.upload_time = upload_time
    def merge(self):
        return merge_chunks(list(self.chunks.values()))

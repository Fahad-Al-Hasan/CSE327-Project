import dropbox
import random
import re
from bucket import Bucket, register_bucket

DROPBOX_TOKENS = []

class DropboxBucket(Bucket):
    def get_dropbox_client(self, index):
        return dropbox.Dropbox(DROPBOX_TOKENS[index])
    def upload_chunk(self, chunk_data, chunk_name):
        index = random.randint(0, len(DROPBOX_TOKENS)-1)
        client = self.get_dropbox_client(index)
        path = f"/{chunk_name}"
        client.files_upload(chunk_data, path, mode=dropbox.files.WriteMode.overwrite)
        return {"base_name": chunk_name.rsplit("_part",1)[0], "platform": "dropbox", "account_index": index, "chunk_id": path}
    def download_chunk(self, chunk_info):
        client = self.get_dropbox_client(chunk_info["account_index"])
        _, res = client.files_download(chunk_info["chunk_id"])
        return res.content
    def delete_chunk(self, chunk_info):
        client = self.get_dropbox_client(chunk_info["account_index"])
        client.files_delete_v2(chunk_info["chunk_id"])
    def list_chunks(self, base_name):
        chunks = []
        for i in range(len(DROPBOX_TOKENS)):
            client = self.get_dropbox_client(i)
            result = client.files_list_folder("", recursive=False)
            for entry in result.entries:
                if entry.name.startswith(f"{base_name}_part"):
                    m = re.match(r"(" + re.escape(base_name) + r")_part(\d+)$", entry.name)
                    if m:
                        part = int(m.group(2))
                        chunks.append({"base_name": base_name, "platform": "dropbox", "account_index": i, "chunk_id": entry.path_lower, "part": part})
        return chunks

register_bucket("dropbox", DropboxBucket)

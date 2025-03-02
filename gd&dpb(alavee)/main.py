from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
import hashlib, io, time, mimetypes, random, re
from bucket import BUCKET_REGISTRY, get_bucket
from fileobject import merge_chunks

app = Flask(__name__)
CORS(app)
CHUNK_SIZE = 512 * 1024
file_metadata = {}
preview_cache = {}
CACHE_TTL = 300

def upload_chunk_generic(chunk_data, chunk_name):
    providers = list(BUCKET_REGISTRY.keys())
    random.shuffle(providers)
    for provider in providers:
        try:
            bucket_class = get_bucket(provider)
            bucket = bucket_class()
            return bucket.upload_chunk(chunk_data, chunk_name)
        except Exception as e:
            print(f"Error uploading {chunk_name} to {provider}: {e}")
    return None

def list_all_chunks(base_name):
    chunks = []
    for provider, bucket_class in BUCKET_REGISTRY.items():
        bucket = bucket_class()
        chunks.extend(bucket.list_chunks(base_name))
    return chunks

def delete_all_chunks(base_name):
    errors = []
    for provider, bucket_class in BUCKET_REGISTRY.items():
        bucket = bucket_class()
        try:
            chunks = bucket.list_chunks(base_name)
            for chunk in chunks:
                try:
                    bucket.delete_chunk(chunk)
                except Exception as e:
                    errors.append(f"{provider} deletion error: {e}")
        except Exception as e:
            errors.append(f"{provider} listing error: {e}")
    return errors

@app.route("/upload", methods=["POST"])
def upload_file():
    if "file" not in request.files:
        return jsonify({"error":"No file uploaded"}),400
    file = request.files["file"]
    file_data = file.read()
    file_hash = hashlib.sha256(file_data).hexdigest()
    file_name = file.filename
    upload_time = time.time()
    chunks = [file_data[i:i+CHUNK_SIZE] for i in range(0, len(file_data), CHUNK_SIZE)]
    total_chunks = len(chunks)
    chunk_ids = {}
    for index, chunk_data in enumerate(chunks):
        chunk_name = f"{file_name}_part{index}"
        info = upload_chunk_generic(chunk_data, chunk_name)
        if not info:
            return jsonify({"error":f"Chunk {index} upload failed."}),500
        chunk_ids[index] = info
    file_metadata[file_hash] = {"filename":file_name,"total_chunks":total_chunks,"chunks":chunk_ids,"upload_time":upload_time}
    return jsonify({"message":"File uploaded successfully","file_hash":file_hash}),200

@app.route("/files", methods=["GET"])
def list_files():
    files = []
    for file_hash, metadata in file_metadata.items():
        files.append({"file_hash":file_hash,"filename":metadata["filename"],"total_chunks":metadata["total_chunks"],"chunks":metadata["chunks"],"upload_time":metadata["upload_time"]})
    files.sort(key=lambda x: x["upload_time"], reverse=True)
    return jsonify({"files":files}),200

@app.route("/all-files", methods=["GET"])
def all_files():
    files_dict = {}
    for provider, bucket_class in BUCKET_REGISTRY.items():
        bucket = bucket_class()
        chunks = bucket.list_chunks("")
        for chunk in chunks:
            base = chunk.get("base_name", "unknown")
            files_dict.setdefault(base, {"filename": base, "chunks": []})
            files_dict[base]["chunks"].append(chunk)
    files_list = []
    for base, data in files_dict.items():
        data["chunks"].sort(key=lambda x: x["part"])
        files_list.append(data)
    files_list.sort(key=lambda x: x["filename"])
    return jsonify({"files":files_list}),200

@app.route("/download/<file_hash>", methods=["GET"])
def download_file():
    file_hash = request.view_args.get("file_hash")
    if file_hash not in file_metadata:
        return jsonify({"error":"File not found"}),404
    metadata = file_metadata[file_hash]
    merged = merge_chunks(list(metadata["chunks"].values()))
    return send_file(merged, as_attachment=True, download_name=metadata["filename"], mimetype="application/octet-stream")

@app.route("/download_cloud/<base_name>", methods=["GET"])
def download_cloud(base_name):
    chunks = list_all_chunks(base_name)
    if not chunks:
        return jsonify({"error":"File not found in cloud storage"}),404
    merged = merge_chunks(chunks)
    mime_type, _ = mimetypes.guess_type(base_name)
    if not mime_type:
        mime_type = "application/octet-stream"
    return send_file(merged, as_attachment=True, download_name=base_name, mimetype=mime_type)

@app.route("/preview_cloud/<base_name>", methods=["GET"])
def preview_cloud(base_name):
    cached = preview_cache.get(base_name)
    if cached and (time.time()-cached[1] < CACHE_TTL):
        return send_file(io.BytesIO(cached[0]), mimetype=mimetypes.guess_type(base_name)[0] or "application/octet-stream")
    chunks = list_all_chunks(base_name)
    if not chunks:
        return jsonify({"error":"File not found in cloud storage"}),404
    merged = merge_chunks(chunks)
    preview_data = merged.getvalue()
    preview_cache[base_name] = (preview_data, time.time())
    mime_type, _ = mimetypes.guess_type(base_name)
    if not mime_type:
        mime_type = "application/octet-stream"
    return send_file(io.BytesIO(preview_data), mimetypes.guess_type(base_name)[0] or "application/octet-stream")

@app.route("/delete/<file_hash>", methods=["DELETE"])
def delete_file():
    file_hash = request.view_args.get("file_hash")
    if file_hash not in file_metadata:
        return jsonify({"error":"File not found"}),404
    metadata = file_metadata[file_hash]
    chunks = metadata["chunks"]
    for index, chunk_info in chunks.items():
        provider = chunk_info["platform"]
        bucket_class = get_bucket(provider)
        if bucket_class:
            bucket = bucket_class()
            bucket.delete_chunk(chunk_info)
    del file_metadata[file_hash]
    return jsonify({"message":"File deleted successfully"}),200

@app.route("/delete_cloud/<base_name>", methods=["DELETE"])
def delete_cloud(base_name):
    errors = delete_all_chunks(base_name)
    if errors:
        return jsonify({"error":"Some deletions failed","details": errors}),500
    else:
        return jsonify({"message":f"File '{base_name}' deleted successfully from cloud storage"}),200

if __name__ == "__main__":
    app.run(debug=True, port=5000)

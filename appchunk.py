from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseUpload
import hashlib
import io
import os
import logging

# Initialize Flask app
app = Flask(__name__)
CORS(app)  # Enable CORS for all routes

# Google Drive service account credentials and folder IDs
GDRIVE_CREDENTIALS = [
    "service_account_1.json",
    "service_account_2.json",
    "service_account_3.json",
]
DRIVE_FOLDERS = [
    "folder_id_1",
    "folder_id_2",
    "folder_id_3",
]

CHUNK_SIZE = 512 * 1024  # Chunk size of 512KB

# File metadata storage (in-memory)
file_metadata = {}

# Set up logging
logging.basicConfig(level=logging.DEBUG)

def get_drive_service(index):
    """Returns a Google Drive service instance for the specified account."""
    creds = Credentials.from_service_account_file(GDRIVE_CREDENTIALS[index], scopes=["https://www.googleapis.com/auth/drive"])
    return build("drive", "v3", credentials=creds)

def generate_file_hash(file_data):
    """Generate a SHA-256 hash for the file."""
    sha256_hash = hashlib.sha256()
    sha256_hash.update(file_data)
    return sha256_hash.hexdigest()

def upload_chunk_to_drive(chunk_data, chunk_name, drive_index):
    """Upload a chunk to Google Drive."""
    drive_service = get_drive_service(drive_index)
    folder_id = DRIVE_FOLDERS[drive_index]
    file_metadata = {"name": chunk_name, "parents": [folder_id]}
    media = MediaIoBaseUpload(io.BytesIO(chunk_data), mimetype="application/octet-stream")
    file = drive_service.files().create(body=file_metadata, media_body=media, fields="id").execute()
    return file["id"]

@app.route("/upload", methods=["POST"])
def upload_file():
    """Handle file upload and chunking."""
    if "file" not in request.files:
        return jsonify({"error": "No file uploaded"}), 400

    file = request.files["file"]
    file_data = file.read()
    file_hash = generate_file_hash(file_data)
    file_name = file.filename

    # Split the file into chunks
    chunks = [file_data[i:i + CHUNK_SIZE] for i in range(0, len(file_data), CHUNK_SIZE)]
    total_chunks = len(chunks)

    # Upload chunks to Google Drive
    chunk_ids = {}
    for index, chunk_data in enumerate(chunks):
        chunk_name = f"{file_name}_part{index}"
        drive_index = index % len(GDRIVE_CREDENTIALS)  # Distribute chunks across accounts
        chunk_id = upload_chunk_to_drive(chunk_data, chunk_name, drive_index)
        chunk_ids[index] = {"drive_index": drive_index, "chunk_id": chunk_id}

    # Store metadata
    file_metadata[file_hash] = {
        "filename": file_name,
        "total_chunks": total_chunks,
        "chunks": chunk_ids
    }

    return jsonify({"message": "File uploaded successfully", "file_hash": file_hash}), 200

@app.route("/download/<file_hash>", methods=["GET"])
def download_file(file_hash):
    """Handle file download (by merging chunks)."""
    if file_hash not in file_metadata:
        return jsonify({"error": "File not found"}), 404

    metadata = file_metadata[file_hash]
    chunks = metadata["chunks"]
    file_name = metadata["filename"]

    # Merge chunks
    merged_file = io.BytesIO()
    for index in sorted(chunks.keys()):
        chunk_info = chunks[index]
        drive_index = chunk_info["drive_index"]
        chunk_id = chunk_info["chunk_id"]

        drive_service = get_drive_service(drive_index)
        chunk_data = drive_service.files().get_media(fileId=chunk_id).execute()
        merged_file.write(chunk_data)

    merged_file.seek(0)

    return send_file(
        merged_file,
        as_attachment=True,
        download_name=file_name,
        mimetype="application/octet-stream"
    )

@app.route("/delete/<file_hash>", methods=["DELETE"])
def delete_file(file_hash):
    """Handle file deletion by removing chunks from Google Drive."""
    if file_hash not in file_metadata:
        return jsonify({"error": "File not found"}), 404

    metadata = file_metadata[file_hash]
    chunks = metadata["chunks"]

    # Delete chunks from Google Drive
    for index in chunks.keys():
        chunk_info = chunks[index]
        drive_index = chunk_info["drive_index"]
        chunk_id = chunk_info["chunk_id"]

        drive_service = get_drive_service(drive_index)
        drive_service.files().delete(fileId=chunk_id).execute()

    # Remove metadata
    del file_metadata[file_hash]

    return jsonify({"message": "File deleted successfully"}), 200

@app.route("/search/all", methods=["GET"])
def search_all_files():
    """List all files uploaded (with metadata)."""
    results = [
        {
            "file_hash": file_hash,
            "filename": metadata["filename"],
            "total_chunks": metadata["total_chunks"]
        }
        for file_hash, metadata in file_metadata.items()
    ]

    if not results:
        return jsonify({"error": "No files found."}), 404

    return jsonify({"results": results}), 200

if __name__ == "__main__":
    app.run(debug=True, port=5000)

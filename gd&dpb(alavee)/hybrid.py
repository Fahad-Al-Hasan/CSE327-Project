from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseUpload
import dropbox
import hashlib
import io
import logging
import random

# Initialize Flask app
app = Flask(__name__)
CORS(app)  # Enable CORS for all routes

# Google Drive service account credentials and folder IDs
GDRIVE_CREDENTIALS = ['credentials.json']
DRIVE_FOLDERS = [
    '1RX9n3bYgmzH8g_WapDOlvbMtJuNeo0My',  # Folder ID
    '1wCYPW0SdNHpz1VdMXLFBuo2YvPdWf4eY',
    '1feL26aFdeofoebbIYMUMk33MRVS6f6SL'
]

# Dropbox Access Tokens
DROPBOX_TOKENS = ["sl.u.AFhd4TwLuP2hCqMgWiHLxqolj1HDkx5mNoFERYrDt_vdmzvAx7xPkIiDJonsgClozVtGmY0BFE7ZuVe_WrngG6MWKIH0sP4SrVoa3iRecHIzkpP7OgZMZO6BNjJ3XJTWkMXCA7NzDKKW4npTs90lUsdnvH9aRvildTS7YZZH_59JiZGiD5S1h2INjZgL5cOYVUnnhki45WxZHPxH1y7soz4qdQUO9F2JY6N_s3Fznbqbc54csVM1BaMuXf_pwrUVpKJHaIKL5xxWtdvziXzEneGyDW30ESReeBLHFLpqysBhKL28rHcJPS3My_LK1DA1XCOuuiPFPJynUXtEWUou5walGGbg1MInfX-q-fBgyXbO94YWQhmvgGn6C-MtfCXCqA17S_5B_271kLG-JwWdfRvUaRYHz-rmIHEd6EifT7OEvGVaWQRMBhJ1-MvywUv79jT9SMdgqPXv1L_s2-vnQFRtQUBbnEEr-CJUt2SB_PKdJ4PH2JHPkP8v1Z8ez7Xu5QnMMMbRzFbfeQafhlAsGw1QrpBWGFZHqxiHFsRHLhsDR8c2jTwCbcJAVW9d6RFm3zDB2IplnMf1KOE_e6lUNWMDD6bKEzTtS82zy0YknEEZmi_9-1AaTYYEPhpVzi7Utrpz7RXLgCurHJ3SJbUiq6TGiF7nRZUg1qG_P-r-bMcKHlgQg47w6nTrF2wxvsq8EcCw3GX3XEvixbUR4NUHBkPfnl7FwIYS-NxKiHvDIK2mnBr_y-1Pz7V05VrJXaoA6cMemsQ6lZ7tiagPQObschwtfxoAfVz7khiY_1qlcpRg1Yk2DAje7YvSNDS2e62bdRWjF6HGiLhnVx3nZrfbkBf_sszuQNfD0xrRwPbpZ_t9PN-V9GuRfr6kSZ4-OWXyrTlhK0eGvi-mMiZW7HrW39gj2l-feJqYpNFLCvgvYcaMoS6wS2QXkTSQvWH1ROj3gaLh8YbmDr3fSEShiOHtfXHFiaCrQvi6mZp8smmiXLDb_Doy2YVOSNOeAJtYlMP84zOl4JR8SnURTD-9kfGUipFdSPhVgY4hlSv0pIebQMlyha9TtsSVpzhcov1_tzLSVfjyEEax6j7l7CyI1qSIMRw73cQx6UJ3WWiNySuFhtyWNgJ9d0MmIPRMIqdggoFZ_di67jhSGRMtYToUuIXUtNZ3f7gcwZQWgLzHAT5IHq5ckA9tK5yNPOrRee77qba_3uZ82hvexZ5xnn4_e42YDVssuvmFQwnoOSnkVcvOz5K84bUGuNT1ug2J2kXh21QXYiH1v8oTcNhGH-uIrHN1LrUvyIyiLnyJTs-vWIj--nptLGifsoOSmb5QQhYYdS5v7A_1BLt4HW1dSqy2qD6u6sj4x_YDrrPeew_hh5iQefkEtoRUgEY6iNNV0ypKmNlTJzkNi4qDiZAMMaiUyByNqSParUVMzxxdAJi1wWvb95i1mA"]

CHUNK_SIZE = 512 * 1024  # 512KB chunks

# File metadata storage (in-memory)
file_metadata = {}

def get_drive_service(index):
    creds = Credentials.from_service_account_file(GDRIVE_CREDENTIALS[index], scopes=["https://www.googleapis.com/auth/drive"])
    return build("drive", "v3", credentials=creds)

def get_dropbox_client(index):
    return dropbox.Dropbox(DROPBOX_TOKENS[index])

def upload_chunk_to_drive(chunk_data, chunk_name):
    index = random.randint(0, len(GDRIVE_CREDENTIALS) - 1)
    drive_service = get_drive_service(index)
    folder_id = DRIVE_FOLDERS[index]
    file_metadata = {"name": chunk_name, "parents": [folder_id]}
    media = MediaIoBaseUpload(io.BytesIO(chunk_data), mimetype="application/octet-stream")
    file = drive_service.files().create(body=file_metadata, media_body=media, fields="id").execute()
    return {"platform": "google", "account_index": index, "chunk_id": file["id"]}

def upload_chunk_to_dropbox(chunk_data, chunk_name):
    index = random.randint(0, len(DROPBOX_TOKENS) - 1)
    dbx = get_dropbox_client(index)
    path = f"/{chunk_name}"
    dbx.files_upload(chunk_data, path, mode=dropbox.files.WriteMode.overwrite)
    return {"platform": "dropbox", "account_index": index, "chunk_id": path}

def upload_chunk(chunk_data, chunk_name):
    if random.choice([True, False]):
        return upload_chunk_to_drive(chunk_data, chunk_name)
    else:
        return upload_chunk_to_dropbox(chunk_data, chunk_name)

@app.route("/upload", methods=["POST"])
def upload_file():
    if "file" not in request.files:
        return jsonify({"error": "No file uploaded"}), 400

    file = request.files["file"]
    file_data = file.read()
    file_hash = hashlib.sha256(file_data).hexdigest()
    file_name = file.filename
    
    chunks = [file_data[i:i + CHUNK_SIZE] for i in range(0, len(file_data), CHUNK_SIZE)]
    total_chunks = len(chunks)
    chunk_ids = {}
    
    for index, chunk_data in enumerate(chunks):
        chunk_name = f"{file_name}_part{index}"
        upload_info = upload_chunk(chunk_data, chunk_name)
        if not upload_info:
            return jsonify({"error": "Not enough storage available"}), 500
        chunk_ids[index] = upload_info
    
    file_metadata[file_hash] = {"filename": file_name, "total_chunks": total_chunks, "chunks": chunk_ids}
    return jsonify({"message": "File uploaded successfully", "file_hash": file_hash}), 200

@app.route("/files", methods=["GET"])
def list_files():
    """Returns a list of all uploaded files and their metadata."""
    if not file_metadata:
        return jsonify({"message": "No files uploaded yet"}), 200
    
    files = []
    for file_hash, metadata in file_metadata.items():
        files.append({
            "file_hash": file_hash,
            "filename": metadata["filename"],
            "total_chunks": metadata["total_chunks"],
            "chunks": metadata["chunks"]
        })
    return jsonify({"files": files}), 200

@app.route("/download/<file_hash>", methods=["GET"])
def download_file(file_hash):
    if file_hash not in file_metadata:
        return jsonify({"error": "File not found"}), 404
    
    metadata = file_metadata[file_hash]
    chunks = metadata["chunks"]
    file_name = metadata["filename"]
    merged_file = io.BytesIO()
    
    for index in sorted(chunks.keys()):
        chunk_info = chunks[index]
        if chunk_info["platform"] == "google":
            drive_service = get_drive_service(chunk_info["account_index"])
            chunk_data = drive_service.files().get_media(fileId=chunk_info["chunk_id"]).execute()
        else:
            dbx = get_dropbox_client(chunk_info["account_index"])
            _, res = dbx.files_download(chunk_info["chunk_id"])
            chunk_data = res.content
        merged_file.write(chunk_data)
    
    merged_file.seek(0)
    return send_file(merged_file, as_attachment=True, download_name=file_name, mimetype="application/octet-stream")

@app.route("/delete/<file_hash>", methods=["DELETE"])
def delete_file(file_hash):
    if file_hash not in file_metadata:
        return jsonify({"error": "File not found"}), 404
    
    metadata = file_metadata[file_hash]
    chunks = metadata["chunks"]
    
    for index, chunk_info in chunks.items():
        if chunk_info["platform"] == "google":
            drive_service = get_drive_service(chunk_info["account_index"])
            drive_service.files().delete(fileId=chunk_info["chunk_id"]).execute()
        else:
            dbx = get_dropbox_client(chunk_info["account_index"])
            dbx.files_delete_v2(chunk_info["chunk_id"])
    
    del file_metadata[file_hash]
    return jsonify({"message": "File deleted successfully"}), 200

if __name__ == "__main__":
    app.run(debug=True, port=5000)

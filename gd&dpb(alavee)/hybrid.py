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
import time
import mimetypes
import re

app = Flask(__name__)
CORS(app)

# Google Drive service account credentials and folder IDs
GDRIVE_CREDENTIALS = ['credentials.json']  # Update with your service account file(s)
DRIVE_FOLDERS = [
    '1RX9n3bYgmzH8g_WapDOlvbMtJuNeo0My',  
    '1wCYPW0SdNHpz1VdMXLFBuo2YvPdWf4eY',
    '1feL26aFdeofoebbIYMUMk33MRVS6f6SL'
]

<<<<<<< HEAD
# Dropbox Access Tokens
DROPBOX_TOKENS = ["sl.u.AFhd4TwLuP2hCqMgWiHLxqolj1HDkx5mNoFERYrDt_vdmzvAx7xPkIiDJonsgClozVtGmY0BFE7ZuVe_WrngG6MWKIH0sP4SrVoa3iRecHIzkpP7OgZMZO6BNjJ3XJTWkMXCA7NzDKKW4npTs90lUsdnvH9aRvildTS7YZZH_59JiZGiD5S1h2INjZgL5cOYVUnnhki45WxZHPxH1y7soz4qdQUO9F2JY6N_s3Fznbqbc54csVM1BaMuXf_pwrUVpKJHaIKL5xxWtdvziXzEneGyDW30ESReeBLHFLpqysBhKL28rHcJPS3My_LK1DA1XCOuuiPFPJynUXtEWUou5walGGbg1MInfX-q-fBgyXbO94YWQhmvgGn6C-MtfCXCqA17S_5B_271kLG-JwWdfRvUaRYHz-rmIHEd6EifT7OEvGVaWQRMBhJ1-MvywUv79jT9SMdgqPXv1L_s2-vnQFRtQUBbnEEr-CJUt2SB_PKdJ4PH2JHPkP8v1Z8ez7Xu5QnMMMbRzFbfeQafhlAsGw1QrpBWGFZHqxiHFsRHLhsDR8c2jTwCbcJAVW9d6RFm3zDB2IplnMf1KOE_e6lUNWMDD6bKEzTtS82zy0YknEEZmi_9-1AaTYYEPhpVzi7Utrpz7RXLgCurHJ3SJbUiq6TGiF7nRZUg1qG_P-r-bMcKHlgQg47w6nTrF2wxvsq8EcCw3GX3XEvixbUR4NUHBkPfnl7FwIYS-NxKiHvDIK2mnBr_y-1Pz7V05VrJXaoA6cMemsQ6lZ7tiagPQObschwtfxoAfVz7khiY_1qlcpRg1Yk2DAje7YvSNDS2e62bdRWjF6HGiLhnVx3nZrfbkBf_sszuQNfD0xrRwPbpZ_t9PN-V9GuRfr6kSZ4-OWXyrTlhK0eGvi-mMiZW7HrW39gj2l-feJqYpNFLCvgvYcaMoS6wS2QXkTSQvWH1ROj3gaLh8YbmDr3fSEShiOHtfXHFiaCrQvi6mZp8smmiXLDb_Doy2YVOSNOeAJtYlMP84zOl4JR8SnURTD-9kfGUipFdSPhVgY4hlSv0pIebQMlyha9TtsSVpzhcov1_tzLSVfjyEEax6j7l7CyI1qSIMRw73cQx6UJ3WWiNySuFhtyWNgJ9d0MmIPRMIqdggoFZ_di67jhSGRMtYToUuIXUtNZ3f7gcwZQWgLzHAT5IHq5ckA9tK5yNPOrRee77qba_3uZ82hvexZ5xnn4_e42YDVssuvmFQwnoOSnkVcvOz5K84bUGuNT1ug2J2kXh21QXYiH1v8oTcNhGH-uIrHN1LrUvyIyiLnyJTs-vWIj--nptLGifsoOSmb5QQhYYdS5v7A_1BLt4HW1dSqy2qD6u6sj4x_YDrrPeew_hh5iQefkEtoRUgEY6iNNV0ypKmNlTJzkNi4qDiZAMMaiUyByNqSParUVMzxxdAJi1wWvb95i1mA"]
=======
# Dropbox Access Tokens – update with your valid token(s)
DROPBOX_TOKENS = 
>>>>>>> be0884e1501d2d05a263301c0725e8d364de35ab

CHUNK_SIZE = 512 * 1024  # 512KB chunks

# In-memory storage for file metadata (only available during this server session)
file_metadata = {}

def get_drive_service(index):
    creds = Credentials.from_service_account_file(
        GDRIVE_CREDENTIALS[index],
        scopes=["https://www.googleapis.com/auth/drive"]
    )
    return build("drive", "v3", credentials=creds)

def get_dropbox_client(index):
    return dropbox.Dropbox(DROPBOX_TOKENS[index])

def upload_chunk_to_drive(chunk_data, chunk_name):
    index = random.randint(0, len(GDRIVE_CREDENTIALS) - 1)
    drive_service = get_drive_service(index)
    folder_id = DRIVE_FOLDERS[index]
    metadata = {"name": chunk_name, "parents": [folder_id]}
    media = MediaIoBaseUpload(io.BytesIO(chunk_data), mimetype="application/octet-stream")
    file = drive_service.files().create(body=metadata, media_body=media, fields="id").execute()
    return {"platform": "google", "account_index": index, "chunk_id": file["id"]}

def upload_chunk_to_dropbox(chunk_data, chunk_name):
    index = random.randint(0, len(DROPBOX_TOKENS) - 1)
    dbx = get_dropbox_client(index)
    path = f"/{chunk_name}"
    dbx.files_upload(chunk_data, path, mode=dropbox.files.WriteMode.overwrite)
    return {"platform": "dropbox", "account_index": index, "chunk_id": path}

def upload_chunk(chunk_data, chunk_name):
    # Try both platforms in a random order as a fallback mechanism
    platforms = ['google', 'dropbox']
    random.shuffle(platforms)
    for platform in platforms:
        try:
            if platform == 'google':
                return upload_chunk_to_drive(chunk_data, chunk_name)
            else:
                return upload_chunk_to_dropbox(chunk_data, chunk_name)
        except Exception as e:
            print(f"Error uploading chunk '{chunk_name}' to {platform}: {e}")
    # If both fail, return None
    return None

@app.route("/upload", methods=["POST"])
def upload_file():
    if "file" not in request.files:
        return jsonify({"error": "No file uploaded"}), 400

    file = request.files["file"]
    file_data = file.read()
    file_hash = hashlib.sha256(file_data).hexdigest()
    file_name = file.filename
    upload_time = time.time()

    # Split file into chunks
    chunks = [file_data[i:i + CHUNK_SIZE] for i in range(0, len(file_data), CHUNK_SIZE)]
    total_chunks = len(chunks)
    chunk_ids = {}
    
    for index, chunk_data in enumerate(chunks):
        chunk_name = f"{file_name}_part{index}"
        upload_info = upload_chunk(chunk_data, chunk_name)
        if not upload_info:
            return jsonify({"error": f"Chunk {index} upload failed. Not enough storage available."}), 500
        chunk_ids[index] = upload_info
    
    file_metadata[file_hash] = {
        "filename": file_name,
        "total_chunks": total_chunks,
        "chunks": chunk_ids,
        "upload_time": upload_time
    }
    return jsonify({"message": "File uploaded successfully", "file_hash": file_hash}), 200

@app.route("/files", methods=["GET"])
def list_files():
    """Returns files from in‑memory metadata (uploaded during this session)."""
    files = []
    for file_hash, metadata in file_metadata.items():
        files.append({
            "file_hash": file_hash,
            "filename": metadata["filename"],
            "total_chunks": metadata["total_chunks"],
            "chunks": metadata["chunks"],
            "upload_time": metadata["upload_time"]
        })
    files.sort(key=lambda x: x["upload_time"], reverse=True)
    return jsonify({"files": files}), 200

@app.route("/all-files", methods=["GET"])
def all_files():
    """
    Scans your configured Google Drive folders and Dropbox root for all file chunks
    (matching the pattern <filename>_partX) and groups them by their base file name.
    """
    files_dict = {}

    # Scan Google Drive folders
    for i, folder_id in enumerate(DRIVE_FOLDERS):
        try:
            drive_service = get_drive_service(i)
            results = drive_service.files().list(
                q=f"'{folder_id}' in parents",
                fields="files(id, name)"
            ).execute()
            for f in results.get("files", []):
                m = re.match(r"(.+)_part(\d+)$", f["name"])
                if m:
                    base_name = m.group(1)
                    part_num = int(m.group(2))
                    if base_name not in files_dict:
                        files_dict[base_name] = {"filename": base_name, "chunks": []}
                    files_dict[base_name]["chunks"].append({
                        "platform": "google",
                        "account_index": i,
                        "chunk_id": f["id"],
                        "part": part_num
                    })
        except Exception as e:
            print(f"Error listing Google Drive for account {i}: {e}")

    # Scan Dropbox root folder
    for i in range(len(DROPBOX_TOKENS)):
        try:
            dbx = get_dropbox_client(i)
            result = dbx.files_list_folder("", recursive=False)
            for entry in result.entries:
                if isinstance(entry, dropbox.files.FileMetadata):
                    m = re.match(r"(.+)_part(\d+)$", entry.name)
                    if m:
                        base_name = m.group(1)
                        part_num = int(m.group(2))
                        if base_name not in files_dict:
                            files_dict[base_name] = {"filename": base_name, "chunks": []}
                        files_dict[base_name]["chunks"].append({
                            "platform": "dropbox",
                            "account_index": i,
                            "chunk_id": entry.path_lower,
                            "part": part_num
                        })
        except Exception as e:
            print(f"Error listing Dropbox for account {i}: {e}")

    files_list = []
    for base_name, data in files_dict.items():
        data["chunks"].sort(key=lambda x: x["part"])
        files_list.append(data)
    files_list.sort(key=lambda x: x["filename"])
    return jsonify({"files": files_list}), 200

@app.route("/download/<file_hash>", methods=["GET"])
def download_file():
    """Download endpoint for files using in‑memory metadata."""
    file_hash = request.view_args.get("file_hash")
    if file_hash not in file_metadata:
        return jsonify({"error": "File not found"}), 404

    metadata = file_metadata[file_hash]
    chunks = metadata["chunks"]
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
    return send_file(merged_file, as_attachment=True, download_name=metadata["filename"], mimetype="application/octet-stream")

@app.route("/download_cloud/<base_name>", methods=["GET"])
def download_cloud(base_name):
    """
    New download endpoint that scans cloud storage for chunks matching the pattern
    <base_name>_partX, merges them, and returns the reconstructed file.
    """
    chunks = []
    for i, folder_id in enumerate(DRIVE_FOLDERS):
        try:
            drive_service = get_drive_service(i)
            results = drive_service.files().list(
                q=f"'{folder_id}' in parents and name contains '{base_name}_part'",
                fields="files(id, name)"
            ).execute()
            for f in results.get("files", []):
                m = re.match(r"(" + re.escape(base_name) + r")_part(\d+)$", f["name"])
                if m:
                    part_num = int(m.group(2))
                    chunks.append({
                        "platform": "google",
                        "account_index": i,
                        "chunk_id": f["id"],
                        "part": part_num
                    })
        except Exception as e:
            print(f"Error listing Google Drive for account {i}: {e}")
    
    for i in range(len(DROPBOX_TOKENS)):
        try:
            dbx = get_dropbox_client(i)
            result = dbx.files_list_folder("", recursive=False)
            for entry in result.entries:
                if isinstance(entry, dropbox.files.FileMetadata):
                    m = re.match(r"(" + re.escape(base_name) + r")_part(\d+)$", entry.name)
                    if m:
                        part_num = int(m.group(2))
                        chunks.append({
                            "platform": "dropbox",
                            "account_index": i,
                            "chunk_id": entry.path_lower,
                            "part": part_num
                        })
        except Exception as e:
            print(f"Error listing Dropbox for account {i}: {e}")
    
    if not chunks:
        return jsonify({"error": "File not found in cloud storage"}), 404
    
    chunks.sort(key=lambda x: x["part"])
    merged_file = io.BytesIO()
    for chunk_info in chunks:
        if chunk_info["platform"] == "google":
            drive_service = get_drive_service(chunk_info["account_index"])
            chunk_data = drive_service.files().get_media(fileId=chunk_info["chunk_id"]).execute()
        else:
            dbx = get_dropbox_client(chunk_info["account_index"])
            _, res = dbx.files_download(chunk_info["chunk_id"])
            chunk_data = res.content
        merged_file.write(chunk_data)
    
    merged_file.seek(0)
    mime_type, _ = mimetypes.guess_type(base_name)
    if not mime_type:
        mime_type = "application/octet-stream"
    return send_file(merged_file, as_attachment=True, download_name=base_name, mimetype=mime_type)

@app.route("/preview_cloud/<base_name>", methods=["GET"])
def preview_cloud(base_name):
    """
    New preview endpoint that scans cloud storage for chunks matching <base_name>_partX,
    merges them, and returns the file for inline preview.
    """
    chunks = []
    for i, folder_id in enumerate(DRIVE_FOLDERS):
        try:
            drive_service = get_drive_service(i)
            results = drive_service.files().list(
                q=f"'{folder_id}' in parents and name contains '{base_name}_part'",
                fields="files(id, name)"
            ).execute()
            for f in results.get("files", []):
                m = re.match(r"(" + re.escape(base_name) + r")_part(\d+)$", f["name"])
                if m:
                    part_num = int(m.group(2))
                    chunks.append({
                        "platform": "google",
                        "account_index": i,
                        "chunk_id": f["id"],
                        "part": part_num
                    })
        except Exception as e:
            print(f"Error listing Google Drive for account {i}: {e}")
    
    for i in range(len(DROPBOX_TOKENS)):
        try:
            dbx = get_dropbox_client(i)
            result = dbx.files_list_folder("", recursive=False)
            for entry in result.entries:
                if isinstance(entry, dropbox.files.FileMetadata):
                    m = re.match(r"(" + re.escape(base_name) + r")_part(\d+)$", entry.name)
                    if m:
                        part_num = int(m.group(2))
                        chunks.append({
                            "platform": "dropbox",
                            "account_index": i,
                            "chunk_id": entry.path_lower,
                            "part": part_num
                        })
        except Exception as e:
            print(f"Error listing Dropbox for account {i}: {e}")
    
    if not chunks:
        return jsonify({"error": "File not found in cloud storage"}), 404
    
    chunks.sort(key=lambda x: x["part"])
    merged_file = io.BytesIO()
    for chunk_info in chunks:
        if chunk_info["platform"] == "google":
            drive_service = get_drive_service(chunk_info["account_index"])
            chunk_data = drive_service.files().get_media(fileId=chunk_info["chunk_id"]).execute()
        else:
            dbx = get_dropbox_client(chunk_info["account_index"])
            _, res = dbx.files_download(chunk_info["chunk_id"])
            chunk_data = res.content
        merged_file.write(chunk_data)
    
    merged_file.seek(0)
    mime_type, _ = mimetypes.guess_type(base_name)
    if not mime_type:
        mime_type = "application/octet-stream"
    return send_file(merged_file, mimetype=mime_type)

@app.route("/delete/<file_hash>", methods=["DELETE"])
def delete_file():
    """
    Deletion endpoint for files using in‑memory metadata.
    """
    file_hash = request.view_args.get("file_hash")
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

@app.route("/delete_cloud/<base_name>", methods=["DELETE"])
def delete_cloud(base_name):
    """
    New deletion endpoint for cloud-scanned files.
    It scans for all chunks matching <base_name>_partX and attempts to delete them.
    """
    errors = []
    # Delete from Google Drive
    for i, folder_id in enumerate(DRIVE_FOLDERS):
        try:
            drive_service = get_drive_service(i)
            results = drive_service.files().list(
                q=f"'{folder_id}' in parents and name contains '{base_name}_part'",
                fields="files(id, name)"
            ).execute()
            for f in results.get("files", []):
                m = re.match(r"(" + re.escape(base_name) + r")_part(\d+)$", f["name"])
                if m:
                    try:
                        drive_service.files().delete(fileId=f["id"]).execute()
                    except Exception as e:
                        errors.append(f"Google Drive deletion error for {f['name']}: {e}")
        except Exception as e:
            errors.append(f"Error listing Google Drive for account {i}: {e}")
    
    # Delete from Dropbox
    for i in range(len(DROPBOX_TOKENS)):
        try:
            dbx = get_dropbox_client(i)
            result = dbx.files_list_folder("", recursive=False)
            for entry in result.entries:
                if isinstance(entry, dropbox.files.FileMetadata):
                    m = re.match(r"(" + re.escape(base_name) + r")_part(\d+)$", entry.name)
                    if m:
                        try:
                            dbx.files_delete_v2(entry.path_lower)
                        except Exception as e:
                            errors.append(f"Dropbox deletion error for {entry.name}: {e}")
        except Exception as e:
            errors.append(f"Error listing Dropbox for account {i}: {e}")
    
    if errors:
        return jsonify({"error": "Some deletions failed", "details": errors}), 500
    else:
        return jsonify({"message": f"File '{base_name}' deleted successfully from cloud storage"}), 200

if __name__ == "__main__":
    app.run(debug=True, port=5000)

#LastCode

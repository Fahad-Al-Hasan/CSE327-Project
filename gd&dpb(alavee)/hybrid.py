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

# Dropbox Access Tokens – update with your valid token(s)
DROPBOX_TOKENS = ["sl.u.AFl6Oy-NaSsZyd1D9qqIbPr662YVoQKctxrHDdePPEYiurzuAmRbofhQc3Q1ARzNLIFhWfzJeOZwSvc2cAAc19LvnpTqawg6fVNFiebz1Iy7lMY_BJa8KcH7VN_GEymr19yea731VI0UeQaFLECuEvyr9gr2hBprDuu5sRSp65oFGptMoRo7aXehDVfHGfAw5KBaxql8PY2W9kRq7vNj0Xjiy-kT371OsiKyKPy7CInWl84R8j4-fyT7SkAkdnZ47mutmwcytPoAOlTlxHTb1bGjNnHQB8oQmq34aoxpNO8XvSB4g-63-dqIWbF0EuJN8eiOlvCxcjTiA4kHpy6ZW2QAGlFZ9AfcARa-5mOgCYc941w08Q6GNUSkz4SchsABt-hXJeMI2jbvyKeqVwTO-AQ8D3BoM9L8FmKEnnMaVDKK_AbyT8TmkQXODsnIZLULCNMZEyNe4WGpzCAkvHHAQmt5O7K9aiGQ3DhiHiTfxlXkOyoF-yDINGrfwdTITlkjDq_PYAH99IzqJVGQOTVpS8yXujvkVrwEajxuFm4EdeoaV5lAEoA3xznNTeozwJ46fd5Y6TYcw689UjVm-247SKCHp-6qSp6c4RycPX3aQq0iBc8ix2ZyaS2XjOPntNFL9MzWiDIswXY9HEfOlyp66hBtoImmorVCx3ojebOFg8Rhtha_nb-NOX9DFBVAadDB8P3eoPUndcDE6wU_xCgqx3WEiWWh1-xb2hLkFoyZeGE4NT8gU7JCr2sNXxZFqyAkKDIal7I7ZOsYrxQ4VamiuqnbLD5VTnxlMUDTrdeeapmPnsnm0T0GGHnlUODC_D-FxXQUqPyjZK8vbGfM8XzQJJl4DnbKofhfHMPHQXyEomiiUCN2TskkeqP4sFgmQ8YI3zZ4LXU2hu8oTR76ABmUXjlDxfd5xao-p1TXfz8QCDsy3Xlln5Dra5sXeM_I_K6cEXfJkJCp6PY_hvCc4obOKD0qa8Wccazvlizi3FD7o3NmyqjHj5sNScCl3r1D_FHQsb3ZEx7NJ1Wf0R-akfe9QCLdD05kmamvvdQANBqNSJKR2vwu1JpKMLAm4jICSXK-B1wfPcGcnCDITuLNUyUo_yqNuOBXGyILfjvg_R0sR-Sl-0hKQspPBkc8NAhXft1KArFLuCrUazLUPAW7GUTc73rAjLYtWJIZGGLmLQLqoW8bI62BTauFhwEVhyuo81o2cDso52HRnomPRr6UZ9usRh_L5fI4l0K1rKPpimGTOBSTrwgRQ8jzKvWGrQZCmPP1n7RxYStQgy1PVnoKGmT2BYJUsyca31LTziVR7Hr1j9yRIshyLz13C8cekfoR-2FxMyctZuI_s4zaXkNd0Qlhw_JWUNss_trb83jkI-VFo0heyct5K4CsqkqAo_cNqMKwEKxFRxsseDGMyyx6I6gwS3ai"]

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
from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseUpload
import dropbox
import hashlib
import io
import logging

# Initialize Flask app
app = Flask(__name__)
CORS(app)  # Enable CORS for all routes

# Google Drive service account credentials and folder IDs
GDRIVE_CREDENTIALS = [
    'credentials.json'
]
DRIVE_FOLDERS = [
    "folder_id_1",
]

# Dropbox Access Tokens
DROPBOX_TOKENS = [
    "sl.u.AFgl8hON533VyJzI09MMJn16azgKZ1N-43_7VA2AD3j_I-0VWxLPTSZwI2zjHAFMwaiIz3CCUgzVu84zWh71FVhPIGzJ6X4bx7u2vZeSBWLarijkaNXDtXWPT8YjsBtRz_WylAfEq55CQp4AYDUI8U9wr-XvqDcooas9TseOl6jrIEkUw3eohKpjuR233Du2rEBMsQLxAVj5zZkdgJoZWtvokZO1RztDu5oeuuihbWaRTqx3HUNRGO664iI-ftOnZosZKSz4cEnsXd6RtmoK6m_ksvp4gnv0alfI2kICNJreKc2fHgJHk0uasrinartaP4OgR50U4C37iWIVpVublG77o6Ibjfs0SuOj2jd7hcOmZQcbcQ815AMPwcsi7HKR6BeVLzpcmFGFwHVvzm4bogERVT5hc6dTR2_pf1H1I6UDK-AaO5CQRPdZz5RNqVkQ80GYtUv0jBMD4b_Z6NN8xuqiQnY0Dv00jMnIY36VhhE57wQ7wsKwd2GERyBH1MbbyJH0lIIWjH573sJg5WCdZjimyyzR3f8tICKWZklne5ywpo6D_kdAzd722zEw8fHIAO3Y2MzMI_ccnfMJTrJzTzZLT7--XzahZYCyg73Zc966Xlq1myw0CjAyqMw6B0dYeg1V2aAPKNdzWT521w4JO19vJdnjqSeuL5i3d7kc60okHDW5GjYtWhgRJqkKq025oxyt-tSgP4UMatuIR3DkD_d57_xid_ZaTc3i9S5l8Lnvk2p2DoPGYZkn3ZXlp5fpi3M9rK-JBdOa_Yt2iMurf4OpuZ4nJAbbq2qhE_ff6nWzUXKcy5ARtSYXvk_T3BD2vYxCVywQ2uhThkYSf4ThCf_6CZJVUd-SknIM7VH7MxJtX3B7rxFb6mt_SB2AhoFNgU6sRRF02manMuM8J3hVcjCfrKjWjiPS3j5eSrQPojvED5ugbHO6tT9JFbpTyKqzrmJ6RXCWadw5Y_ETsF3tJoUhOFwOQOBCf3rWUCwBqQwpcGtXUBLcURP5yRY1U5t18E0G9LGqW4F6bAWqhxdN2DV9_W2VonMGsISMreQpfkxr2nCdrj9aIiQPDHYRA0zL9fBQEcoVS-hZPKHyKXL0lFZAFrJWmzH5WOiG_x68oDgaV7q0j_YQE70Pxu0lsQ5jQTqQlkg-BjybnWKgeN9ZeITzr6g_eXtaJiaFfV7_0GghR5K2Cm5GWwN1zobtkuYI2L6Mzkht_qTV1hqoPdRI6WSJjDg8endefY5s0GiYkPs2vNGItsXOOM90EhZfdlN7Z94JnzRC9OBDbMzSMzlObHAgh12lxGjC_Y4LBulQiF_f0uh82AtxYa1-X-WCKek9o-S_tqSZ6T9y5Finxc2upagjutJXUn3NXN_SDndblB3PNodJKgX94NqfjBWuUFJmmumiF-T2eAs1EXzRAO5UEi0G"
]

CHUNK_SIZE = 512 * 1024  # 512KB chunks

# File metadata storage (in-memory)
file_metadata = {}

def get_drive_service(index):
    """Returns a Google Drive service instance for the specified account."""
    creds = Credentials.from_service_account_file(GDRIVE_CREDENTIALS[index], scopes=["https://www.googleapis.com/auth/drive"])
    return build("drive", "v3", credentials=creds)

def get_dropbox_client(index):
    """Returns a Dropbox client for the specified account."""
    return dropbox.Dropbox(DROPBOX_TOKENS[index])

def get_drive_free_space(index):
    """Fetches free storage space for a Google Drive account."""
    drive_service = get_drive_service(index)
    about = drive_service.about().get(fields="storageQuota").execute()
    used = int(about['storageQuota']['usage'])
    total = int(about['storageQuota']['limit'])
    return total - used

def get_dropbox_free_space(index):
    """Fetches free storage space for a Dropbox account."""
    dbx = get_dropbox_client(index)
    usage = dbx.users_get_space_usage()
    return usage.allocation.get_individual().allocated - usage.used

def upload_chunk_to_drive(chunk_data, chunk_name):
    """Uploads a chunk to the Google Drive account with available space."""
    for index in range(len(GDRIVE_CREDENTIALS)):
        if get_drive_free_space(index) > len(chunk_data):
            drive_service = get_drive_service(index)
            folder_id = DRIVE_FOLDERS[index]
            file_metadata = {"name": chunk_name, "parents": [folder_id]}
            media = MediaIoBaseUpload(io.BytesIO(chunk_data), mimetype="application/octet-stream")
            file = drive_service.files().create(body=file_metadata, media_body=media, fields="id").execute()
            return {"platform": "google", "account_index": index, "chunk_id": file["id"]}
    return None

def upload_chunk_to_dropbox(chunk_data, chunk_name):
    """Uploads a chunk to the Dropbox account with available space."""
    for index in range(len(DROPBOX_TOKENS)):
        if get_dropbox_free_space(index) > len(chunk_data):
            dbx = get_dropbox_client(index)
            path = f"/{chunk_name}"
            dbx.files_upload(chunk_data, path, mode=dropbox.files.WriteMode.overwrite)
            return {"platform": "dropbox", "account_index": index, "chunk_id": path}
    return None

def upload_chunk(chunk_data, chunk_name):
    """Uploads a chunk to an available storage platform."""
    drive_result = upload_chunk_to_drive(chunk_data, chunk_name)
    if drive_result:
        return drive_result
    dropbox_result = upload_chunk_to_dropbox(chunk_data, chunk_name)
    if dropbox_result:
        return dropbox_result
    return None  # No available storage

def delete_chunk_from_drive(account_index, chunk_id):
    """Deletes a chunk from Google Drive."""
    try:
        drive_service = get_drive_service(account_index)
        drive_service.files().delete(fileId=chunk_id).execute()
        return True
    except Exception as e:
        logging.error(f"Failed to delete chunk from Google Drive: {e}")
        return False

def delete_chunk_from_dropbox(account_index, chunk_id):
    """Deletes a chunk from Dropbox."""
    try:
        dbx = get_dropbox_client(account_index)
        dbx.files_delete_v2(chunk_id)
        return True
    except Exception as e:
        logging.error(f"Failed to delete chunk from Dropbox: {e}")
        return False

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

@app.route("/files/<file_hash>", methods=["GET"])
def get_file_metadata(file_hash):
    """Returns metadata for a specific file."""
    if file_hash not in file_metadata:
        return jsonify({"error": "File not found"}), 404

    metadata = file_metadata[file_hash]
    return jsonify({
        "file_hash": file_hash,
        "filename": metadata["filename"],
        "total_chunks": metadata["total_chunks"],
        "chunks": metadata["chunks"]
    }), 200

@app.route("/delete/<file_hash>", methods=["DELETE"])
def delete_file(file_hash):
    """Deletes a file and its associated chunks from Google Drive and Dropbox."""
    if file_hash not in file_metadata:
        return jsonify({"error": "File not found"}), 404

    metadata = file_metadata[file_hash]
    chunks = metadata["chunks"]

    # Delete each chunk
    for index, chunk_info in chunks.items():
        if chunk_info["platform"] == "google":
            if not delete_chunk_from_drive(chunk_info["account_index"], chunk_info["chunk_id"]):
                return jsonify({"error": f"Failed to delete chunk {index} from Google Drive"}), 500
        elif chunk_info["platform"] == "dropbox":
            if not delete_chunk_from_dropbox(chunk_info["account_index"], chunk_info["chunk_id"]):
                return jsonify({"error": f"Failed to delete chunk {index} from Dropbox"}), 500

    # Remove file metadata
    del file_metadata[file_hash]
    return jsonify({"message": "File deleted successfully"}), 200

if __name__ == "__main__":
    app.run(debug=True, port=5000)
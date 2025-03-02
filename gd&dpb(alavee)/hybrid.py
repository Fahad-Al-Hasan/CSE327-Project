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
DROPBOX_TOKENS = ["sl.u.AFjL9alf7ojfpLaUKdpfHzF9uQ_vxxjUZC4xX-E2749NMcuxXehykUyTduK39AE7aN6MlqV_1RqExr94OCusONtbQpVRTkitZ_OCQ61F25mTZQ01ZM3uxOA6zjmtT8rooyFQeJiipTOkyZzyXsQ8Fip6A_oL62EdTdNyJP7pwW3GGj4ZrGvS72reiCaT7MQ6G6pUGd5hE5rItLFizAafOIZprFcfWO-o0NCgKC87m5oLG53i0tKeRfaSChCsWWDRORnsBVqPO1G0zmhEIPtppzs1FsxY4c4Yt7SORwsRa_82zhV2xCRmrr13LjZPZGS6kxGv8uSbndcwO6UT3jZJgrUB3nfX_GAtlEIZIESWgW_hAO6-huiaFnUaxwFkW25ZqzChVpw6lQ36YHnOt1EmXA1fZ1H-LEY_8iy_VbJBlTq7DkJrK_ZMXobKnYmgHr6vHdv89pGU3QJDMMaxGHNkEqSe0W645Wn42Bm2yN6jfSNjLa20AFmhdZJlUAmPN68Wqa60Tf5xJlQytcBVANx4KSemKWOuAjEE7gOGBOEzl5EbmWwSZkYp7_ZwXlRvI_PllWOH_cmIu6vNXQBTudFnIQXlOhmNsn4m7Em6CcI0hWLmCq9pNhuEfwWrBglmuzAzuZF1RWMqkjebxckIaC-Te5bdv4FBCEngFT2AlnKdzBPHcpf1KMVRZVk_hgXIVGVdYbR4BR8HTmov-bulFGsC-9u7L2UGmB3T9rG_9h51jQMLJlSwLcswGVwzSdgLbulOZNzxdMtiHXVpCnvmMakzD8wbkdzkCAE-Bq0JY_d7LVIW5QfSHtwVl-Rc2ok-dSlg9YIx_uysW2EgCnvVTxQiRTFp7p8NsN4fVOv2G9L4d_uQylPLnURSFdp1mPSQnJFEg-qoyNgzw230sFQGaboXJVvXwHQOzh244o8v5U1D_K8Q_7HQ_JiZZwRuuoNoPJyxvPK0FR7gpQWiNoFxY1X0uvKTE3P6eUf9gTmRZ-SH7isLxfcfSaTz7Ze44vN7NtkPjO-gYPI8d8mnYAZD7xmvFK-U1Fbjrz8HFmhWy-RWZxhWKvxN5wL4s6yfJFos2ToaoXhCROqEBFumcbkGfuc8jkS6wooAd8MClytolFVksw5eW2B_3b0a9fWjST1qFyWf1ex6OIFDUc8-xj_w9mh3uh90XJ8gyYyhF0-9bCpaTUttvICXfREdFdBTCHPUGZoHK6eb4_x4pFjcD2XK_8RHkNLdTNwr2rYC6tAowQUUBnhQHzS3Hi9Zgc4rXzkbT9oAx2elIsPR7xCwn2SzvLkXDMru8MqDqzWxHdu1JJZ2lAYL8vXHl8bnn09xD_yot83IxjE25ANEAZLdM4FvuXuwHSl1WzOrw87_OpwhSGVtliAJUjCiE4M0El7WT-UHxVbnUY_NyPx4gRlM4UXWxxsPg-DeTf1lILfQeFh0iI7hewcOcg",
                 "sl.u.AFhs5BsfFUTxObZMObPiMK30gyS3WRg21cdVNreEmU7f1dzlpb7Mtjqu_Sx6_EuDhsXqVj2rcVD1sDOlr1w6Sztl0tMxbGEGJyBBpGWZO2_1ecWI4IHko09cfP_xc8C2amEPv9FU77WjSo1OTOT2dY7Ud79rBhCVR_VViI0cwuzdiTjOtGIZAd3s_ju9XJsXaQw_UkcZmdU1z7oGs0O-6vZSuKjCoyytoy-qiFNLQ_nIZwpFLonjgp23M5ib7nVQaXzQmLCkk1CK6mIPdy3c5AFBfNSXbIeB_uDbU1iBPYk1KFeynFEFPz5JsQWMvO9GK8t_6kjxQigg5At6E7LewLbbFFmS_Uwvu6QRGAZDhgL6mWIz1ZoJQ8GiK0t56cS--XGUj6wZB4fgrTlM7OW2xsr_s7C4uFF2LLUP9xHHIE6MwH7g9huZhIxLS2o0BgOpcfYKSZaBSsXdsXqDqnvdGW1_9CBbW9C_0QFdfiodWdCFUB1ssnrg1cu-Efgm4_PekrWR7tCjFzVp9i9netqdrNLSfnyI5Esh8CL7kZ8PfG0sDxRqEFG-s2fIY9u6WXtYs_7eMR4dJ2TUcYltECbvxnLkn9slP_CRhnOZO9RVnFNLKLZH2ANZW8gHoY1MT_SHRdhmqDKj-pLEurumv9THuJlde3mX-FVCJewngIBA9OzWRcC8yk9PTVDlyvkv1KEndlVUX9mpHk3GYv1iwF90iBDhybbm8Y5v0RkWglSrfMaD2Ab_mNmapYk9K1U5BHnFCDzj9hJtkhC9wB75NrXSlS2-GlanjYds47BK97gmfKEKnbVFheVlKdmpYWqXTpqMPiQNSrrAZgi0Ka4cu1Ozhf0SRKbr1ZKMT4cF6uXJaZ_h70oAwDrpNBSfOUnwdIypFtXyHW6eLkb7vFtngwErhxLkOHv_Xd571Bxpm09GOb2TEU1TvS0rLd5oxktRs4ru5HN97YuvZZErtt96NbsBqpB7BR8slbFjrvPAaSLkqnj-XXaMR_Nvxp220Ugs_6zz40-XqiBl6qcxUTNfaEJtUdjeUQrbuaiEIAfXv6y0yaqzDVO0jS3_S_7orvEWlvgm-L1cuJtw9ZabdTulWy_9mSw4__JuvUdQ48dXP6k3YoJPV4uMBqYcal4Fg2sGyQ4goTnIBVczZ8ZdoY9dggS81vzBfzI7WGL1TkJEC6-RyZtoOjBoN1-mbww2lM6c8adAWmtTCvaLEjGGjFLWkWZVZi0WEDxGJY9c5xjfge-cQFeJ1Z62oGSQCfe5K5lFWuBUd6YgUudOG-rsZy4XexncVTAhLgYYDd5riDY286ehGB_clJZfV4UPecisEgP_HcGGLiYVpAUB8rv8svS48tINOzwubEOGf6egkmokpo-zsiPh_iDLYWMz20ondg9dVTZmrUcxqZbR3HL-37vTjVmEvTcr"] 

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
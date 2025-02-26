from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
from .Gdrive import GoogleDriveStorage
from .Drobox import DropboxStorage
from .chunkmanager import ChunkManager
import hashlib
import io
import time
import mimetypes

app = Flask(__name__)
CORS(app)

# Initialize multiple Google Drive accounts
google_drive_accounts = [
    GoogleDriveStorage("credentials1.json", '1RX9n3bYgmzH8g_WapDOlvbMtJuNeo0My'),
    GoogleDriveStorage("credentials2.json", '1wCYPW0SdNHpz1VdMXLFBuo2YvPdWf4eY'),
    GoogleDriveStorage("credentials3.json", '1feL26aFdeofoebbIYMUMk33MRVS6f6SL')
]

# Initialize multiple Dropbox accounts
dropbox_accounts = [
    DropboxStorage("sl.u.AFl6Oy-NaSsZyd1D9qqIbPr662YVoQKctxrHDdePPEYiurzuAmRbofhQc3Q1ARzNLIFhWfzJeOZwSvc2cAAc19LvnpTqawg6fVNFiebz1Iy7lMY_BJa8KcH7VN_GEymr19yea731VI0UeQaFLECuEvyr9gr2hBprDuu5sRSp65oFGptMoRo7aXehDVfHGfAw5KBaxql8PY2W9kRq7vNj0Xjiy-kT371OsiKyKPy7CInWl84R8j4-fyT7SkAkdnZ47mutmwcytPoAOlTlxHTb1bGjNnHQB8oQmq34aoxpNO8XvSB4g-63-dqIWbF0EuJN8eiOlvCxcjTiA4kHpy6ZW2QAGlFZ9AfcARa-5mOgCYc941w08Q6GNUSkz4SchsABt-hXJeMI2jbvyKeqVwTO-AQ8D3BoM9L8FmKEnnMaVDKK_AbyT8TmkQXODsnIZLULCNMZEyNe4WGpzCAkvHHAQmt5O7K9aiGQ3DhiHiTfxlXkOyoF-yDINGrfwdTITlkjDq_PYAH99IzqJVGQOTVpS8yXujvkVrwEajxuFm4EdeoaV5lAEoA3xznNTeozwJ46fd5Y6TYcw689UjVm-247SKCHp-6qSp6c4RycPX3aQq0iBc8ix2ZyaS2XjOPntNFL9MzWiDIswXY9HEfOlyp66hBtoImmorVCx3ojebOFg8Rhtha_nb-NOX9DFBVAadDB8P3eoPUndcDE6wU_xCgqx3WEiWWh1-xb2hLkFoyZeGE4NT8gU7JCr2sNXxZFqyAkKDIal7I7ZOsYrxQ4VamiuqnbLD5VTnxlMUDTrdeeapmPnsnm0T0GGHnlUODC_D-FxXQUqPyjZK8vbGfM8XzQJJl4DnbKofhfHMPHQXyEomiiUCN2TskkeqP4sFgmQ8YI3zZ4LXU2hu8oTR76ABmUXjlDxfd5xao-p1TXfz8QCDsy3Xlln5Dra5sXeM_I_K6cEXfJkJCp6PY_hvCc4obOKD0qa8Wccazvlizi3FD7o3NmyqjHj5sNScCl3r1D_FHQsb3ZEx7NJ1Wf0R-akfe9QCLdD05kmamvvdQANBqNSJKR2vwu1JpKMLAm4jICSXK-B1wfPcGcnCDITuLNUyUo_yqNuOBXGyILfjvg_R0sR-Sl-0hKQspPBkc8NAhXft1KArFLuCrUazLUPAW7GUTc73rAjLYtWJIZGGLmLQLqoW8bI62BTauFhwEVhyuo81o2cDso52HRnomPRr6UZ9usRh_L5fI4l0K1rKPpimGTOBSTrwgRQ8jzKvWGrQZCmPP1n7RxYStQgy1PVnoKGmT2BYJUsyca31LTziVR7Hr1j9yRIshyLz13C8cekfoR-2FxMyctZuI_s4zaXkNd0Qlhw_JWUNss_trb83jkI-VFo0heyct5K4CsqkqAo_cNqMKwEKxFRxsseDGMyyx6I6gwS3ai")
]

# Combine all storage services
storage_services = google_drive_accounts + dropbox_accounts

# Initialize ChunkManager
chunk_manager = ChunkManager(storage_services)

# In-memory storage for file metadata
file_metadata = {}

@app.route("/upload", methods=["POST"])
def upload_file():
    """Upload a file by chunking it and distributing across multiple cloud platforms and accounts."""
    if "file" not in request.files:
        return jsonify({"error": "No file uploaded"}), 400

    file = request.files["file"]
    file_data = file.read()
    file_hash = hashlib.sha256(file_data).hexdigest()
    file_name = file.filename
    upload_time = time.time()

    # Split file into chunks
    chunks = [file_data[i:i + 512 * 1024] for i in range(0, len(file_data), 512 * 1024)]
    total_chunks = len(chunks)
    chunk_ids = {}
    
    for index, chunk_data in enumerate(chunks):
        chunk_name = f"{file_name}_part{index}"
        try:
            chunk_info = chunk_manager.upload_chunk(chunk_data, chunk_name)
            chunk_ids[index] = chunk_info
        except Exception as e:
            return jsonify({"error": f"Failed to upload chunk {index}: {str(e)}"}), 500
    
    file_metadata[file_hash] = {
        "filename": file_name,
        "total_chunks": total_chunks,
        "chunks": chunk_ids,
        "upload_time": upload_time
    }
    return jsonify({"message": "File uploaded successfully", "file_hash": file_hash}), 200

@app.route("/download/<file_hash>", methods=["GET"])
def download_file(file_hash):
    """Download a file by merging its chunks."""
    if file_hash not in file_metadata:
        return jsonify({"error": "File not found"}), 404

    metadata = file_metadata[file_hash]
    chunks = metadata["chunks"]
    merged_file = io.BytesIO()
    
    for index in sorted(chunks.keys()):
        chunk_info = chunks[index]
        try:
            chunk_data = chunk_manager.download_chunk(chunk_info)
            merged_file.write(chunk_data)
        except Exception as e:
            return jsonify({"error": f"Failed to download chunk {index}: {str(e)}"}), 500
    
    merged_file.seek(0)
    return send_file(merged_file, as_attachment=True, download_name=metadata["filename"], mimetype="application/octet-stream")

@app.route("/delete/<file_hash>", methods=["DELETE"])
def delete_file(file_hash):
    """Delete a file by deleting all its chunks."""
    if file_hash not in file_metadata:
        return jsonify({"error": "File not found"}), 404

    metadata = file_metadata[file_hash]
    chunks = metadata["chunks"]
    
    for index, chunk_info in chunks.items():
        try:
            chunk_manager.delete_chunk(chunk_info)
        except Exception as e:
            return jsonify({"error": f"Failed to delete chunk {index}: {str(e)}"}), 500
    
    del file_metadata[file_hash]
    return jsonify({"message": "File deleted successfully"}), 200

if __name__ == "__main__":
    app.run(debug=True, port=5000)
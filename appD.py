from flask import Flask, request, jsonify, render_template
import dropbox
import os

app = Flask(__name__)

# 🔹 Dropbox Access Token (Replace with your actual token)
ACCESS_TOKEN = "sl.u.AFjkHG5q2897INGBvKnubk8t6g9HbAkyn3qukJnGqrqgP03Q18y7iodb-OEa719GuNTM8pTQeB7bw8btyERtlauz5x1gaJFZEHZCSHiGPUX3h4qD3h7oq1xCWt-GzL4pns3HE6sg9s5kX5VhQDaFV_7GEMYLpzdMbBgGfminu9OKuJiml9fk3Qzm63dkKlVnQLrCeg1vaP_3k3euPYnYAevvCVbT4-oNGV4bBjdWu1u-wMBMqTwuxTADnA6pfFNrXX1xIw6vMIq5lLCA7HT1LYkaQsVp6NrP60BP-drhzaOSrTPxHyIM-hC8zdCAzYGvWuyiS2TpFn_-2LyBooqoKxh4l6ACjxwwmh1nbAaJC4afqvSc7LkZ4vEYgwh_SZukoE2BEcUjs6uQFu52WzzWV1F-vC42sSphHHJDj1z0xkPO9vqJCkSO08n8prUmAMqXjYyikM7NOYbpTFqHwljNqBUa9k87JQvB0RXMwnumFX_jzSYrbXATTvhNeiuMcyYgSFDtMv6dB0evEoKIKzJQyQB5ie1i6L84I1PJOvdX5Gq6lI_b__BGC3ZaKzvR5vH4kuZi8TAJQc310QcMXAxnSpWNn31waFzOnujphxemjN6qRyHGfiY3BikK42-OU8eX7EBOgFYfizRopj-dfDPxSDxhdhGcG0BZLnb1PwkQDOJXOqcI7CD9e5dNPit67aQAUB0GKWYiXfo_Nfrn6fQ3mcen0YxAzqbsTzRUWgPL3qsMTABkzVRSm_GHgbKn98qfRwbDU5EJjwtme2S0f1DyYEH_vCSkm__H8efYdheX-v4kNn4cFqtgYKQS_YSHKxyrUEeCsdbERWNHnLtEy75Szo8SCHni8QDbYnGOx20X4vbz2TRGWvZOYHAid59z-qB6-jLNWeGsZQym4O3j70WoLnY5UmrroeQ22uGAeOWnHYstV_-388xKVA3BX8wu-NO48KmW-4-jdMGAd28zyLiJFJK-6dvwfUgOYAIZ7PmppbQWZKO_M7oHYTXIDeAKuPo5AbN1h3iGAzmi_R-DqMvgVAHn6fdodm792X5OyC9irqwVj3mFuVkarbb0ch30xEDzo5pTWiGOaH80gP7Xj3_hCgS5SZ66V1tEZZk31wN_z_dqLcBZ8KBCq01Cons8Ygg2TzngMZbLuXBk5BOTdk0-2XoliC_Zb54YRpIBdwSgZwLubx2ujcrcFRBJwaa2vsGRzffkah9p9ebkCBeAoZZP7J2SQpf8eibsE9Y8fNKc2q0G23N74wryi-OlQ1zTv4j5I6vAXh2B0uGo6BkdJKIrGFoFoBJB8hTu5EuvH1ZcFE0j9XxYz_gogPBcPyo01anPEhpwDWVVChgRDwuGSLJsrOozNnfFtnBw2mrxerd6ZziooV0YKfKsoJs_e_RHdYuRJESpOHber0nYTpmW_NzyQMIR"
dbx = dropbox.Dropbox(ACCESS_TOKEN)

UPLOAD_FOLDER = "uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# ✅ Route: Homepage
@app.route("/")
def home():
    return render_template("dropbox.html")

# ✅ Route: Upload File (Chunked Upload)
@app.route("/upload", methods=["POST"])
def upload_file():
    if "file" not in request.files:
        return jsonify({"message": "No file uploaded"}), 400
    
    file = request.files["file"]
    file_path = os.path.join(UPLOAD_FOLDER, file.filename)
    file.save(file_path)

    try:
        with open(file_path, "rb") as f:
            file_size = os.path.getsize(file_path)
            chunk_size = 4 * 1024 * 1024  # 4MB chunk size
            
            if file_size <= chunk_size:
                dbx.files_upload(f.read(), f"/{file.filename}")
            else:
                upload_session_start_result = dbx.files_upload_session_start(f.read(chunk_size))
                cursor = dropbox.files.UploadSessionCursor(session_id=upload_session_start_result.session_id, offset=f.tell())
                commit = dropbox.files.CommitInfo(path=f"/{file.filename}")

                while f.tell() < file_size:
                    if (file_size - f.tell()) <= chunk_size:
                        dbx.files_upload_session_finish(f.read(chunk_size), cursor, commit)
                    else:
                        dbx.files_upload_session_append(f.read(chunk_size), cursor.session_id, cursor.offset)
                        cursor.offset = f.tell()

        os.remove(file_path)  # Delete local file after upload
        return jsonify({"message": "File uploaded successfully"}), 200
    except Exception as e:
        return jsonify({"message": f"Upload failed: {str(e)}"}), 500

# ✅ Route: List Files
@app.route("/files", methods=["GET"])
def list_files():
    try:
        result = dbx.files_list_folder("")
        files = [{"name": file.name, "path": file.path_lower} for file in result.entries]
        return jsonify({"files": files}), 200
    except Exception as e:
        return jsonify({"message": f"Error fetching files: {str(e)}"}), 500

# ✅ Route: Download File
@app.route("/download/<path:file_path>", methods=["GET"])
def download_file(file_path):
    try:
        file_path = "/" + file_path
        metadata, res = dbx.files_download(file_path)
        
        file_content = res.content
        with open(os.path.join(UPLOAD_FOLDER, metadata.name), "wb") as f:
            f.write(file_content)

        return jsonify({"message": f"File downloaded: {metadata.name}"}), 200
    except Exception as e:
        return jsonify({"message": f"Download failed: {str(e)}"}), 500

# ✅ Route: Delete File
@app.route("/delete", methods=["POST"])
def delete_file():
    data = request.get_json()
    file_path = data.get("file_path")

    if not file_path:
        return jsonify({"message": "File path is required"}), 400

    try:
        dbx.files_delete_v2(file_path)
        return jsonify({"message": f"File deleted: {file_path}"}), 200
    except Exception as e:
        return jsonify({"message": f"Delete failed: {str(e)}"}), 500

if __name__ == "__main__":
    app.run(debug=True)

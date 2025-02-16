from flask import Flask, request, jsonify, render_template
import dropbox
import os

app = Flask(__name__)

# 🔹 Dropbox Access Token (Replace with your actual token)
ACCESS_TOKEN = "sl.u.AFggDSUdG_tid-OXTVZsPwIMNphvdRwma1_SsN-z-05LMT1l7UfB3OaQIzMguxn80hAjfDXgYDyHE23zS-tJU6cDQOWwKjY5o6uXLOFxSvSgteiNiFvYObM0XjLOPFeq8P35qeuqZsU7rIPX0gx-_ZNIgHPVaUQ8B8B6C-na1EwI1c1hLpKf2ZWfgy7msQmVytsgNP6MFEwUyRCXOMCasP4W6JZPPtD5oXieBJdf8usZbYzyTHbh1ba-x2zFF6cpFwXBKwprQiLYibncT8rGpDdCGl8C2mMAKPkVJDhgvHl5VsOJG1VJVHQqtHecCupAytk4oNQT0kBtH63wUtMUFGhyY4rz8p5Kjmz2jB0LE2yhWDMezbco_O9hcKntvoA5p4vBcEUdL8NiTKBy0vtS0KEosOrBkIhLAsRvYHXoMAQFB1au75DaSK3aY-e7MfCUrCUjwFUzFumyUUZkQpozm_yWMey0YQ7FgV4Imd6N1Q4gZS750fqs7tfDmuhXozXYUN1aZz--5mJU1Nd8SU1FDwTdyIONpYzBUztXefEVmWgm4dcEjo3rAbbqCXURcfpJWxkj5imbd52Iuo_bRKo_cteLZjNxuFH2l8kJFI7q_iwbnLR-UfOSNjI0jqc3Z1YPVNjiOnZrI0h58yFLJUILxQcPUJulQ65R0-kYRO2Io68DKMb9n3gxk0dDyLafqrIVaQVgp3yO7IYd96bUSfcn7ciI_okgpSvrMWj8wbGm4dakqTjmW2gHVEkbeVnjgdp3HH8PH2gqOe7r45ToQPuB8QA1GcayRF8NYxqBMshjugg4XxFaHOrL3CVfKQjAie19nov-JmWmh_ENuCOCzBcKcP6cmu2ZlEwZuNJxkyAa5DG9FvB0HxdpEYMs8TFRtfRuTTjhxdiGc9sgZ-UrUCmbpOerDP6JfmJHkzYy2ldSPY-fOD-cNysyt17I0CK-lG-nEc5pjzxfsG4aJgpbuoortjr0ZAqhlBBGOlD7Asq0ugCsgKQ01Vyv7MDMDl3pzBPTe5T6fpM_Jprm3jmoPxWd-Kpkig0vdHNLtFEtwVK67z6YfNzd32WrA7hewARmD55fl1TpGeJx8N_A5pmSwDoZn8kq9Gc-Zw-vmf69HGwmumIy5eKt70QNRGY4_BmJZmsR-Mr_nQjE12z6djsLBgDwr7djomKPLhQIgCZ8UGTZLDM5TkDWKYMaJHysrFQ5Yq3RO4JmymAhGHax15GaK6AVOhqJm2IRhuBgOMtH1uW0S0ipm2sDXLDdU02ASs33ERZDZSUJHOQ5BTwtes2KWKc40ONgFo_syuwsF4_blJnc5p0PiQ0GbDrQ_XOsCBQ2ShpaEmYzzdPtUPnUWZR04Xwdup7j9cfuwomgTE16RgBtqOhfsoG5HY9vDPQiNGFKYFYVCYgfqJ7h_xYkab0Pay_yKuWV"
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
            chunk_size = 512 * 1024  # 4MB chunk size = 4 * 1024 * 1024
            
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

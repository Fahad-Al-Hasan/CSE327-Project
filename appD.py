from flask import Flask, request, jsonify, render_template
import dropbox
import os

app = Flask(__name__)

# 🔹 Dropbox Access Token (Replace with your actual token)
ACCESS_TOKEN = "sl.u.AFgcl4GZ07qkSIOiCDAxNaqIJ9WOHANBzDCdAXpQlT_RlNnLJ_kaHAqXi3fxhtHzfNN6qKq37uzDugMOgD1ZeXQPiRpmljYh4fCER9EYHeYcVlrObiw_jY6oh-7TOIZXideFqwT4rx5Y0AmXzorgV3Zak5xm-NA9iKTtIz3ygz7moHpK2-Aeh6mZUJ9POxi63FUGn0uDc6-i1DWhzYD2htMGI52M5cyWeEXXUs0lBUbdRxB2yGn0YDyqJ_z7aIc5EyvyUjNMR1kY4HQejdPQvqPRDrwJKMmPz-Og23MhKFj8qyWxLP4QH7AAZzSgK5AozXlP0BR-Dz-yOq-RJFgIA-MNa8fKm3XK0jy2O4y_OUpBwgIG8T7nMcWNabW1QMCXE4iknHNNErFSzbFpEdA0yrITadAm0dlq_R8DZewHBoqrQGJyB1jIWjiUTMlCCnZxfiA5q3lDJjAxSZKP066ZuAwsqkOov5oZl8Rx91k71bWHlqNW-RHE7VBBWLWJgByzXD9OXOtKq-9mW7AR9LV2uwu5ksrDLfMxZU3EIczeD3jASKE6UbBWu-gcUiD0xScmSQ8GLLd4JN7RifrNlHLNua8sbZW34ilXa9d0rEqiqzyahmBBcbdULDbUG1cutV-xjI0uop-krFSaGLMJg8AHAUbQi40MyCbirkXpsM2ceAbhVaA2uEtnjOgiRqDhG_A6ZG7pnVO5j0-d-xytyGblNx5U4tVtFwAd8kILW5tBax99k9-sWDANbjnQrl5Y8VIW5yJKsjXy_HCQYRJiYGoy7eRJs_hH3e186U9JkjiyLKtQOggmgq4Lew7WVic4ARGroH7_TU6YRBhaIW5bX02Spq1W6IpFrf-VyTw0zTo0riFUK1bcp6ySvluT6TjlO0Rwwx9-iJa4bVg0aq-89t8K2WeOPSlGxyF--dXgF7pnBw6PBSqbXuXDW6AFuZpWZXwCMtbS7G3oreV83WCkLdeYtL6MomLAj8FyAn5775vsBvYmEIU8TvABvrCJsV08NihpyHzDXyZAj3hgCXJFpKo8cMrWiCp7BXjCoiZ95SFy-4Cwv008y8C96G8o2S7rUkI-3eOveOZhD_Z3dbJmxGW3BlAiJ4gy39RpD4mHqCJfL7hGtO0cUDnxv_oOziMxZVBcFb9_nKbrLzodbhghKySLk8i5z6OP-53FWQTnYjEJXjhCckaid5ebZWigHmB5kOIBUEc3xLdEnQkvsApvKiksmEpcXK11EvNEx4sgNO_pSIzTLqUY-WIKRBUomkn0fCtvRRWUuh5cFYsaN4fwbt460h1OBgjJrhcI1gCcElnpDFu0BfmHE2q1OZu3RPYuIF96QZk6RF5k5LtESCxyx4dc2jLBeWjT14C1LvGn20uPycas1HtM8pUa5Oukr-roFLESFWhNWa5H-tg2mw5d53b6a4aVY2r7X8nT-HY7C9FH6oQEdQn"
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

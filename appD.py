from flask import Flask, request, jsonify, render_template
import dropbox
import os

app = Flask(__name__)

# 🔹 Dropbox Access Token (Replace with your actual token)
ACCESS_TOKEN = "sl.u.AFhxcrJrJVQtDacnFL9jUXA4wkM7r_99iv1WPbTurTAy1M4p6fQ3nGIAPH6fMGPi_LKlcsGP4UBbIDMjAL73UySwDPUGjAhZYbKNui0vWj2omZZXcdvdeS_4YiM3QwRYKM-aoOQbybXprl67fHI7ifmwIjckn4l560sEmrlDszg9Hc0RzDpmssKA-dttBTckBVIKT5nHBSD3aEDPy3I_m2Jf5nXFHLCurW56jitvYnn1LCSWv8PYcJqg48z4WTehpIi6jb_m_3yAASkF_-aWcN5bUY1dXKAOmPF08qyg1eIcZUML9b--MhTjHZ9sePH2DvlEQfMIKG7teVb_ZPzjPloyeMs-7pTKqAKK2AAd-ZqpxQdOpx6L3b-HRIiiuzBqo1U2erowrQcIWDHBXa4z7_eYcqobKaJ1tew4GEd9-0vQXt4rZaKIlsXX567XRZp62FMXvE5_KkyMHAmZupDLsbjojcJXCN8HRWQs8hRDCK-D6GQAI07SWv-KYlbxqLGPYc7ihSuL-NtxEy0ExP0o1u8lIr26yoldy042S6dOPVpjInwbn5VPrGl2Vl3sXuASgmv2CTvxy2R17lNyc2fLV8B13h0GdatLPNQ3_8S1EnZMhiNukBiLnw0foVnAbe4aYW3fX1Vbu9wP_KHtNsYiKZLYu00_3Is2A2P-LzX0k_dit8GtO4c_LxUa--8UodiLQipsCpwrCVuFEf24ubdGdqHw93R6H98v3q91gppAOqt3ekdtpAHVIO5M8ExE_3lUcoyc54E0RvjScCLyUTEGnM3xAyHHjMiwt4S7hZKH29_Pfh1N1yJxKgldP5fGWGSnQkJwHd8MQ0oQfgAuAL7UYzaRoxTPIGbKXgRnM_4dDrcGxoc_oMZTFFt7hk0SrU9Xuend0afr9RwglKi_bg5S2AklvSULQ_0mCk5hT6-E7U-EvauXR79PCz5QXhdcTPhhCAtOIsHul0YbCJK9H8WPqczvze9edWsrbIcyaTTtmP7hrF3Niy83zYQ-ZNd5T0qs6vv7cWjp1OYd9vQzO7koZE3f3BtsXvZD8Pa_T9zReVlI_q6Ld2AIn_AYciYl1MWR3YVhdgtWhloW6yyQuRiZDvcotSrlX23BpqVdZhZsUi98VpHjc2Ll4D137F3mV4xtMolLj5PjVXbgxcT06ACImeLyjPb6zdprpAFZ_i-5Gqaman_NRydN-ZUZLi9gB_GWq9JtNbqm27mZPn_7O84vuZZ1ji8jwDzJOr5eiHjcus7lZbWy3WYkXp6QkCL5diVIH0TOOQTJk2urpZyEXntF5TFpFCy6R7soiAehHnjUaGIyPY1y6x0ujhtiolK0v-o3AeEZ577YMzvbAsTIN5ZBurxOuUHbM6vLYdpg5tRWtBCqKu5n_MkY1TlD19Gt4MN5Zk8q2NCbtxD0Pl_zut2_CyYCxE8bEhg_5-qM8rsK5Ly4FQ"
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

from flask import Flask, request, jsonify, render_template
import dropbox
import os

app = Flask(__name__)

# 🔹 Dropbox Access Token (Replace with your actual token)
ACCESS_TOKEN = "sl.u.AFgl8hON533VyJzI09MMJn16azgKZ1N-43_7VA2AD3j_I-0VWxLPTSZwI2zjHAFMwaiIz3CCUgzVu84zWh71FVhPIGzJ6X4bx7u2vZeSBWLarijkaNXDtXWPT8YjsBtRz_WylAfEq55CQp4AYDUI8U9wr-XvqDcooas9TseOl6jrIEkUw3eohKpjuR233Du2rEBMsQLxAVj5zZkdgJoZWtvokZO1RztDu5oeuuihbWaRTqx3HUNRGO664iI-ftOnZosZKSz4cEnsXd6RtmoK6m_ksvp4gnv0alfI2kICNJreKc2fHgJHk0uasrinartaP4OgR50U4C37iWIVpVublG77o6Ibjfs0SuOj2jd7hcOmZQcbcQ815AMPwcsi7HKR6BeVLzpcmFGFwHVvzm4bogERVT5hc6dTR2_pf1H1I6UDK-AaO5CQRPdZz5RNqVkQ80GYtUv0jBMD4b_Z6NN8xuqiQnY0Dv00jMnIY36VhhE57wQ7wsKwd2GERyBH1MbbyJH0lIIWjH573sJg5WCdZjimyyzR3f8tICKWZklne5ywpo6D_kdAzd722zEw8fHIAO3Y2MzMI_ccnfMJTrJzTzZLT7--XzahZYCyg73Zc966Xlq1myw0CjAyqMw6B0dYeg1V2aAPKNdzWT521w4JO19vJdnjqSeuL5i3d7kc60okHDW5GjYtWhgRJqkKq025oxyt-tSgP4UMatuIR3DkD_d57_xid_ZaTc3i9S5l8Lnvk2p2DoPGYZkn3ZXlp5fpi3M9rK-JBdOa_Yt2iMurf4OpuZ4nJAbbq2qhE_ff6nWzUXKcy5ARtSYXvk_T3BD2vYxCVywQ2uhThkYSf4ThCf_6CZJVUd-SknIM7VH7MxJtX3B7rxFb6mt_SB2AhoFNgU6sRRF02manMuM8J3hVcjCfrKjWjiPS3j5eSrQPojvED5ugbHO6tT9JFbpTyKqzrmJ6RXCWadw5Y_ETsF3tJoUhOFwOQOBCf3rWUCwBqQwpcGtXUBLcURP5yRY1U5t18E0G9LGqW4F6bAWqhxdN2DV9_W2VonMGsISMreQpfkxr2nCdrj9aIiQPDHYRA0zL9fBQEcoVS-hZPKHyKXL0lFZAFrJWmzH5WOiG_x68oDgaV7q0j_YQE70Pxu0lsQ5jQTqQlkg-BjybnWKgeN9ZeITzr6g_eXtaJiaFfV7_0GghR5K2Cm5GWwN1zobtkuYI2L6Mzkht_qTV1hqoPdRI6WSJjDg8endefY5s0GiYkPs2vNGItsXOOM90EhZfdlN7Z94JnzRC9OBDbMzSMzlObHAgh12lxGjC_Y4LBulQiF_f0uh82AtxYa1-X-WCKek9o-S_tqSZ6T9y5Finxc2upagjutJXUn3NXN_SDndblB3PNodJKgX94NqfjBWuUFJmmumiF-T2eAs1EXzRAO5UEi0G"
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

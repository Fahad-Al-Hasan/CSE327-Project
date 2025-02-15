function uploadFile() {
    const fileInput = document.getElementById("fileInput");
    const file = fileInput.files[0];

    if (!file) {
        alert("Please select a file to upload.");
        return;
    }

    const chunkSize = 5 * 1024 * 1024; // 5MB per chunk
    const totalChunks = Math.ceil(file.size / chunkSize);
    let uploadedChunks = 0;

    async function uploadChunk(i) {
        const start = i * chunkSize;
        const end = Math.min(file.size, start + chunkSize);
        const chunk = file.slice(start, end);

        const formData = new FormData();
        formData.append("chunk", chunk);
        formData.append("index", i);
        formData.append("total_chunks", totalChunks);
        formData.append("filename", file.name);

        try {
            const response = await fetch("http://127.0.0.1:5000/upload_chunk", {
                method: "POST",
                body: formData
            });
            const data = await response.json();
            console.log(`✅ Chunk ${i + 1}/${totalChunks} uploaded:`, data);
            uploadedChunks++;
            
            if (uploadedChunks === totalChunks) {
                finalizeUpload(file.name);
            }
        } catch (error) {
            console.error(`❌ Upload Error on chunk ${i + 1}:`, error);
        }
    }

    for (let i = 0; i < totalChunks; i++) {
        uploadChunk(i);
    }
}

async function finalizeUpload(filename) {
    try {
        const response = await fetch("http://127.0.0.1:5000/finalize_upload", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ filename })
        });
        const data = await response.json();
        console.log("✅ Upload finalized:", data);
        document.getElementById("uploadStatus").innerHTML = `<span style="color: green;">${data.message}</span>`;
        document.getElementById("fileInput").value = "";
        fetchFileList();
    } catch (error) {
        console.error("❌ Finalization Error:", error);
    }
}

async function fetchFileList() {
    console.log("📡 Fetching file list...");
    try {
        const response = await fetch("http://127.0.0.1:5000/files", {
            method: "GET",
            headers: { "Content-Type": "application/json", "Cache-Control": "no-cache" }
        });
        const data = await response.json();
        console.log("✅ Files received:", data);
        renderFileList(data.files);
    } catch (error) {
        console.error("❌ Error fetching files:", error);
        document.getElementById("fileList").innerHTML = '<p style="color: red;">Failed to fetch files.</p>';
    }
}

function renderFileList(files) {
    const fileListDiv = document.getElementById("fileList");
    fileListDiv.innerHTML = files.length ? "" : "<p>No files uploaded yet.</p>";

    const sortOption = document.getElementById("sortFilter").value;
    files.sort((a, b) => {
        return sortOption === "name" ? a.name.localeCompare(b.name) :
               sortOption === "time-new" ? new Date(b.modifiedTime) - new Date(a.modifiedTime) :
               new Date(a.modifiedTime) - new Date(b.modifiedTime);
    });

    files.forEach(file => {
        const fileCard = document.createElement("div");
        fileCard.classList.add("file-card");
        fileCard.setAttribute("data-hash", file.hash);

        fileCard.innerHTML = `
            <img src="https://img.icons8.com/color/48/000000/document.png" alt="File">
            <div class="file-name">${file.name}</div>
            <button class="download-btn" onclick="downloadFile('${file.hash}')">Download</button>
            <button class="delete-btn" onclick="deleteFile('${file.hash}', this.parentNode)">Delete</button>
        `;

        fileListDiv.appendChild(fileCard);
    });
}

async function downloadFile(fileHash) {
    try {
        const response = await fetch(`http://127.0.0.1:5000/download/${fileHash}`, { method: "GET" });
        const blob = await response.blob();
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement("a");
        a.style.display = "none";
        a.href = url;
        a.download = "merged_file";
        document.body.appendChild(a);
        a.click();
        window.URL.revokeObjectURL(url);
    } catch (error) {
        console.error("❌ Download Error:", error);
        alert("Failed to download file.");
    }
}

async function deleteFile(fileHash, fileCard) {
    try {
        const response = await fetch("http://127.0.0.1:5000/delete", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ file_hash: fileHash })
        });
        const data = await response.json();

        if (data.message) {
            alert("File deleted successfully.");
            fileCard.remove();
        } else {
            alert("Failed to delete file.");
        }
    } catch (error) {
        console.error("❌ Delete Error:", error);
        alert("An error occurred while deleting the file.");
    }
}

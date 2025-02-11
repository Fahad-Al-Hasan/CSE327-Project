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

    for (let i = 0; i < totalChunks; i++) {
        const start = i * chunkSize;
        const end = Math.min(file.size, start + chunkSize);
        const chunk = file.slice(start, end);

        const formData = new FormData();
        formData.append("chunk", chunk);
        formData.append("index", i);
        formData.append("total_chunks", totalChunks);
        formData.append("filename", file.name);

        fetch("http://127.0.0.1:5000/upload_chunk", {
            method: "POST",
            body: formData
        })
        .then(response => response.json())
        .then(data => {
            console.log(`Chunk ${i + 1}/${totalChunks} uploaded:`, data);
            uploadedChunks++;
            if (uploadedChunks === totalChunks) {
                finalizeUpload(file.name);
            }
        })
        .catch(error => {
            console.error(`❌ Upload Error on chunk ${i + 1}:`, error);
        });
    }
}

function finalizeUpload(filename) {
    fetch("http://127.0.0.1:5000/finalize_upload", {
        method: "POST",
        headers: {
            "Content-Type": "application/json"
        },
        body: JSON.stringify({ filename })
    })
    .then(response => response.json())
    .then(data => {
        console.log("✅ Upload finalized:", data);
        document.getElementById("uploadStatus").innerHTML = `<span style="color: green;">${data.message}</span>`;
        document.getElementById("fileInput").value = "";
        fetchFileList();
    })
    .catch(error => {
        console.error("❌ Finalization Error:", error);
    });
}
function fetchFileList() {
    console.log("📡 Fetching file list...");
    fetch("http://127.0.0.1:5000/files", {
        method: "GET",
        headers: {
            "Content-Type": "application/json",
            "Cache-Control": "no-cache"
        }
    })
    .then(response => response.json())
    .then(data => {
        console.log("✅ Files received:", data);
        renderFileList(data.files);
    })
    .catch(error => {
        console.error("❌ Error fetching files:", error);
        document.getElementById("fileList").innerHTML = '<p style="color: red;">Failed to fetch files.</p>';
    });
}

function renderFileList(files) {
    const fileListDiv = document.getElementById("fileList");
    fileListDiv.innerHTML = "";

    if (!files || files.length === 0) {
        fileListDiv.innerHTML = "<p>No files uploaded yet.</p>";
        return;
    }

    const sortOption = document.getElementById("sortFilter").value;
    files.sort((a, b) => {
        if (sortOption === "name") return a.name.localeCompare(b.name);
        if (sortOption === "time-new") return new Date(b.modifiedTime) - new Date(a.modifiedTime);
        if (sortOption === "time-old") return new Date(a.modifiedTime) - new Date(b.modifiedTime);
    });

    files.forEach(file => {
        let fileCard = document.createElement("div");
        fileCard.classList.add("file-card");
        fileCard.setAttribute("data-hash", file.hash); // Use file hash instead of ID

        let fileIcon = document.createElement("img");
        fileIcon.src = "https://img.icons8.com/color/48/000000/document.png";

        let fileName = document.createElement("div");
        fileName.classList.add("file-name");
        fileName.textContent = file.name;

        let downloadButton = document.createElement("button");
        downloadButton.textContent = "Download";
        downloadButton.classList.add("download-btn");
        downloadButton.addEventListener("click", function () {
            downloadFile(file.hash); // Use file hash instead of ID
        });

        let deleteButton = document.createElement("button");
        deleteButton.textContent = "Delete";
        deleteButton.classList.add("delete-btn");
        deleteButton.setAttribute('data-hash', file.hash); // Use file hash instead of ID
        deleteButton.addEventListener("click", function () {
            deleteFile(file.hash, fileCard); // Use file hash instead of ID
        });

        fileCard.appendChild(fileIcon);
        fileCard.appendChild(fileName);
        fileCard.appendChild(downloadButton);
        fileCard.appendChild(deleteButton);
        fileListDiv.appendChild(fileCard);
    });
}
function downloadFile(fileHash) {
    fetch(`http://127.0.0.1:5000/download/${fileHash}`, {
        method: "GET"
    })
    .then(response => response.blob())
    .then(blob => {
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement("a");
        a.style.display = "none";
        a.href = url;
        a.download = "merged_file";
        document.body.appendChild(a);
        a.click();
        window.URL.revokeObjectURL(url);
    })
    .catch(error => {
        console.error("❌ Download Error:", error);
        alert("Failed to download file.");
    });
}
function deleteFile(fileHash, fileCard) {
    fetch("http://127.0.0.1:5000/delete", {
        method: "POST",
        headers: {
            "Content-Type": "application/json"
        },
        body: JSON.stringify({ file_hash: fileHash }) // Use file hash instead of ID
    })
    .then(response => response.json())
    .then(data => {
        if (data.message) {
            alert("File deleted successfully.");
            fileCard.remove();
        } else {
            alert("Failed to delete file.");
        }
    })
    .catch(error => {
        console.error("❌ Delete Error:", error);
        alert("An error occurred while deleting the file.");
    });
}
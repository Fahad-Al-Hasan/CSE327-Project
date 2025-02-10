document.addEventListener("DOMContentLoaded", function () {
    document.getElementById("listFilesBtn").addEventListener("click", fetchFileList);
    document.getElementById("uploadForm").addEventListener("submit", function (event) {
        event.preventDefault();
        uploadFile();
    });
    document.getElementById("sortFilter").addEventListener("change", fetchFileList);
});

function uploadFile() {
    const fileInput = document.getElementById("fileInput");
    const file = fileInput.files[0];

    if (!file) {
        alert("Please select a file to upload.");
        return;
    }

    const formData = new FormData();
    formData.append("file", file);

    fetch("http://127.0.0.1:5000/upload", {
        method: "POST",
        body: formData
    })
    .then(response => response.json())
    .then(data => {
        const uploadStatus = document.getElementById("uploadStatus");
        if (data.message) {
            uploadStatus.innerHTML = `<span style="color: green;">${data.message}</span>`;
            fileInput.value = "";
            fetchFileList();
        } else {
            uploadStatus.innerHTML = `<span style="color: red;">Upload failed. Try again.</span>`;
        }
    })
    .catch(error => {
        console.error("❌ Upload Error:", error);
        document.getElementById("uploadStatus").innerHTML = `<span style="color: red;">Upload error occurred.</span>`;
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
        fileCard.setAttribute("data-id", file.id);

        let fileIcon = document.createElement("img");
        fileIcon.src = "https://img.icons8.com/color/48/000000/document.png";

        let fileName = document.createElement("div");
        fileName.classList.add("file-name");
        fileName.textContent = file.name;

        let downloadButton = document.createElement("button");
        downloadButton.textContent = "Download";
        downloadButton.classList.add("download-btn");
        downloadButton.addEventListener("click", function () {
            downloadFile(file.id);
        });

        let deleteButton = document.createElement("button");
        deleteButton.textContent = "Delete";
        deleteButton.classList.add("delete-btn");
        deleteButton.setAttribute('data-id', file.id);
        deleteButton.addEventListener("click", function () {
            deleteFile(file.id, fileCard);
        });

        fileCard.appendChild(fileIcon);
        fileCard.appendChild(fileName);
        fileCard.appendChild(downloadButton);
        fileCard.appendChild(deleteButton);
        fileListDiv.appendChild(fileCard);
    });
}

function downloadFile(fileId) {
    fetch(`http://127.0.0.1:5000/download/${fileId}`, {
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

function deleteFile(fileId, fileCard) {
    fetch("http://127.0.0.1:5000/delete", {
        method: "POST",
        headers: {
            "Content-Type": "application/json"
        },
        body: JSON.stringify({ file_id: fileId })
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

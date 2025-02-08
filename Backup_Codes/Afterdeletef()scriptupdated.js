document.getElementById("listFilesBtn").addEventListener("click", function () {
    fetchFileList();
});

document.getElementById("uploadForm").addEventListener("submit", function (event) {
    event.preventDefault();
    uploadFile();
});

document.getElementById("sortFilter").addEventListener("change", fetchFileList);

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
        if (data.message) {
            document.getElementById("uploadStatus").innerHTML = `<span style="color: green;">${data.message}</span>`;
            fileInput.value = "";
            fetchFileList();
        } else {
            document.getElementById("uploadStatus").innerHTML = `<span style="color: red;">Upload failed. Try again.</span>`;
        }
    })
    .catch(error => console.error("❌ Upload Error:", error));
}

function fetchFileList() {
    fetch("http://127.0.0.1:5000/files", {
        method: "GET"
    })
    .then(response => response.json())
    .then(data => renderFileList(data.files))
    .catch(error => console.error("❌ Error fetching files:", error));
}

function renderFileList(files) {
    const fileListDiv = document.getElementById("fileList");
    fileListDiv.innerHTML = "";

    if (!files || files.length === 0) {
        fileListDiv.innerHTML = "<p>No files uploaded yet.</p>";
        return;
    }

    // Sorting Logic
    const sortOption = document.getElementById("sortFilter").value;

    files.sort((a, b) => {
        if (sortOption === "name") {
            return a.name.localeCompare(b.name);
        } else if (sortOption === "time-new") {
            return new Date(b.modifiedTime) - new Date(a.modifiedTime);
        } else if (sortOption === "time-old") {
            return new Date(a.modifiedTime) - new Date(b.modifiedTime);
        }
    });

    files.forEach(file => {
        let fileCard = document.createElement("div");
        fileCard.classList.add("file-card");

        let fileName = document.createElement("div");
        fileName.textContent = file.name;

        let filePreview = document.createElement("div");

        if (file.preview_link) {
            if (file.preview_link.includes("image")) {
                let img = document.createElement("img");
                img.src = file.preview_link;
                img.style.width = "100px";
                filePreview.appendChild(img);
            } else if (file.preview_link.includes("video")) {
                let video = document.createElement("video");
                video.src = file.preview_link;
                video.controls = true;
                video.style.width = "160px";
                filePreview.appendChild(video);
            }
        }

        let downloadLink = document.createElement("a");
        downloadLink.href = file.download_link;
        downloadLink.textContent = "Download";
        downloadLink.classList.add("download-btn");

        let deleteButton = document.createElement("button");
        deleteButton.textContent = "Delete";
        deleteButton.classList.add("delete-btn");
        deleteButton.onclick = () => {
            if (confirm("Are you sure you want to delete this file?")) {
                deleteFile(file.id, fileCard);
            }
        };

        fileCard.append(filePreview, fileName, downloadLink, deleteButton);
        fileListDiv.appendChild(fileCard);
    });
}

function deleteFile(fileId, fileCard) {
    fetch(`http://127.0.0.1:5000/delete/${fileId}`, { method: "DELETE" })
    .then(() => fileCard.remove())
    .catch(error => alert("Failed to delete file"));
}
//Code with delete functionality and A-Z Sorting only
document.addEventListener("DOMContentLoaded", function () {
    const uploadForm = document.getElementById("uploadForm");
    const fileInput = document.getElementById("fileInput");
    const uploadStatus = document.getElementById("uploadStatus");
    const listFilesBtn = document.getElementById("listFilesBtn");
    const fileList = document.getElementById("fileList");

    uploadForm.addEventListener("submit", async function (event) {
        event.preventDefault();
        const file = fileInput.files[0];
        if (!file) {
            uploadStatus.textContent = "Please select a file to upload.";
            return;
        }
        
        const formData = new FormData();
        formData.append("file", file);

        try {
            const response = await fetch("http://localhost:5000/upload", {
                method: "POST",
                body: formData,
            });
            const result = await response.json();
            if (response.ok) {
                uploadStatus.textContent = "File uploaded successfully!";
                listFiles();
            } else {
                uploadStatus.textContent = `Error: ${result.error}`;
            }
        } catch (error) {
            uploadStatus.textContent = "Upload failed. Try again.";
        }
    });

    async function listFiles() {
        fileList.innerHTML = "";
        try {
            const response = await fetch("http://localhost:5000/search/all");
            const result = await response.json();
            if (response.ok) {
                result.results.forEach(file => {
                    const fileCard = document.createElement("div");
                    fileCard.classList.add("file-card");
                    fileCard.dataset.id = file.file_hash;
                    fileCard.innerHTML = `
                        <div class="file-name">${file.filename}</div>
                        <div class="file-buttons">
                            <button class="download-btn" data-id="${file.file_hash}">Download</button>
                            <button class="delete-btn" data-id="${file.file_hash}">Delete</button>
                        </div>
                    `;
                    fileList.appendChild(fileCard);
                });
            } else {
                fileList.innerHTML = "<p>No files found.</p>";
            }
        } catch (error) {
            fileList.innerHTML = "<p>Error loading files.</p>";
        }
    }

    fileList.addEventListener("click", async function (event) {
        if (event.target.classList.contains("download-btn")) {
            const fileId = event.target.dataset.id;
            window.location.href = `http://localhost:5000/download/${fileId}`;
        }
        
        if (event.target.classList.contains("delete-btn")) {
            const fileId = event.target.dataset.id;
            try {
                const response = await fetch(`http://localhost:5000/delete/${fileId}`, {
                    method: "DELETE",
                });
                const result = await response.json();
                if (response.ok) {
                    alert("File deleted successfully!");
                    listFiles();
                } else {
                    alert(`Error: ${result.error}`);
                }
            } catch (error) {
                alert("Deletion failed. Try again.");
            }
        }
    });

    listFilesBtn.addEventListener("click", listFiles);
    listFiles();
});

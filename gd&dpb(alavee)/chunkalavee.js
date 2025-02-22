document.addEventListener("DOMContentLoaded", function () {
    const uploadForm = document.getElementById("uploadForm");
    const fileInput = document.getElementById("fileInput");
    const uploadStatus = document.getElementById("uploadStatus");
    const listFilesBtn = document.getElementById("listFilesBtn");
    const fileList = document.getElementById("fileList");
    const sortDropdown = document.getElementById("sortDropdown");

    // Handle file upload
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
            console.log("Uploading file...");
            const response = await fetch("http://localhost:5000/upload", {
                method: "POST",
                body: formData,
            });
            const result = await response.json();
            if (!response.ok) {
                throw new Error(result.error || "Upload failed.");
            }
            uploadStatus.textContent = "File uploaded successfully!";
            uploadStatus.style.color = "green";
            listFiles();  // refresh file list after upload
        } catch (error) {
            console.error("Error during upload:", error);
            uploadStatus.textContent = `Error: ${error.message}`;
            uploadStatus.style.color = "red";
        }
    });

    // Fetch files from cloud storage using the /all-files endpoint
    async function listFiles() {
        fileList.innerHTML = "";
        try {
            const response = await fetch("http://localhost:5000/all-files");
            const result = await response.json();
            let files = result.files || [];
            const sortOption = sortDropdown.value;
            if (sortOption === "upload_desc") {
                files.sort((a, b) => b.upload_time - a.upload_time);
            } else if (sortOption === "upload_asc") {
                files.sort((a, b) => a.upload_time - b.upload_time);
            } else if (sortOption === "name_asc") {
                files.sort((a, b) => a.filename.localeCompare(b.filename));
            } else if (sortOption === "name_desc") {
                files.sort((a, b) => b.filename.localeCompare(a.filename));
            }
            if (files.length > 0) {
                files.forEach(file => {
                    // file.filename is the base file name.
                    const extension = file.filename.split('.').pop().toLowerCase();
                    let previewElement = "";
                    if (['jpg', 'jpeg', 'png', 'gif'].includes(extension)) {
                        previewElement = `<img src="http://localhost:5000/preview_cloud/${encodeURIComponent(file.filename)}" alt="${file.filename}" style="max-width:100px; max-height:100px;">`;
                    } else if (extension === 'pdf') {
                        previewElement = `<iframe src="http://localhost:5000/preview_cloud/${encodeURIComponent(file.filename)}" style="width:100px; height:100px;"></iframe>`;
                    } else {
                        previewElement = `<span>[No Preview]</span>`;
                    }
                    const fileCard = document.createElement("div");
                    fileCard.classList.add("file-card");
                    // Use base file name as data-id
                    fileCard.dataset.id = file.filename;
                    fileCard.innerHTML = `
                        <div class="file-name">${file.filename}</div>
                        <div class="file-preview">${previewElement}</div>
                        <div class="file-buttons">
                            <button class="download-btn" data-id="${file.filename}">Download</button>
                            <button class="delete-btn" data-id="${file.filename}">Delete</button>
                        </div>
                    `;
                    fileList.appendChild(fileCard);
                });
            } else {
                fileList.innerHTML = "<p>No files found.</p>";
            }
        } catch (error) {
            console.error("Error loading files:", error);
            fileList.innerHTML = "<p>Error loading files.</p>";
        }
    }

    // Handle download and deletion actions
    fileList.addEventListener("click", async function (event) {
        if (event.target.classList.contains("download-btn")) {
            const baseName = event.target.dataset.id;
            window.location.href = `http://localhost:5000/download_cloud/${encodeURIComponent(baseName)}`;
        }
        if (event.target.classList.contains("delete-btn")) {
            const baseName = event.target.dataset.id;
            try {
                const response = await fetch(`http://localhost:5000/delete_cloud/${encodeURIComponent(baseName)}`, {
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
                console.error("Error during deletion:", error);
            }
        }
    });

    listFilesBtn.addEventListener("click", listFiles);
    sortDropdown.addEventListener("change", listFiles);
    listFiles();
});
//LastCode
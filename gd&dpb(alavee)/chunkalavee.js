document.addEventListener("DOMContentLoaded", function () {
    const uploadForm = document.getElementById("uploadForm");
    const fileInput = document.getElementById("fileInput");
    const uploadStatus = document.getElementById("uploadStatus");
    const listFilesBtn = document.getElementById("listFilesBtn");
    const fileList = document.getElementById("fileList");

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
            console.log("Uploading file...");  // Debugging: confirm file upload process
            const response = await fetch("http://localhost:5000/upload", {
                method: "POST",
                body: formData,
            });

            console.log("Response:", response);  // Debugging: log response object

            const result = await response.json();
            console.log("Upload result:", result);  // Debugging: log result from the backend

            if (!response.ok) {
                throw new Error(result.error || "Upload failed.");
            }

            uploadStatus.textContent = "File uploaded successfully!";
            listFiles();  // refresh file list after upload
        } catch (error) {
            console.error("Error during upload:", error);  // Debugging: log errors
            uploadStatus.textContent = `Error: ${error.message}`;
        }
    });

    // List files in the backend
    async function listFiles() {
        fileList.innerHTML = "";
        try {
            const response = await fetch("http://localhost:5000/search/all");
            const result = await response.json();
            
            console.log("File list result:", result);  // Debugging: log file list response

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
            console.error("Error loading files:", error);  // Debugging: log error in fetching files
            fileList.innerHTML = "<p>Error loading files.</p>";
        }
    }

    // Handle file download and deletion
    fileList.addEventListener("click", async function (event) {
        if (event.target.classList.contains("download-btn")) {
            const fileId = event.target.dataset.id;
            console.log("Download file with ID:", fileId);  // Debugging: log file download ID
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
                    listFiles();  // Refresh the file list after deletion
                } else {
                    alert(`Error: ${result.error}`);
                }
            } catch (error) {
                alert("Deletion failed. Try again.");
                console.error("Error during deletion:", error);  // Debugging: log error during deletion
            }
        }
    });

    // Load files on page load and when requested
    listFilesBtn.addEventListener("click", listFiles);
    listFiles();  // Initial file listing on page load
});

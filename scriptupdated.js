document.getElementById("listFilesBtn").addEventListener("click", function () {
    fetchFileList();
});

document.getElementById("uploadForm").addEventListener("submit", function (event) {
    event.preventDefault();
    uploadFile();
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
        if (data.message) {
            document.getElementById("uploadStatus").innerHTML = `<span style="color: green;">${data.message}</span>`;
            fileInput.value = ""; // Clear input after upload
            fetchFileList(); // Refresh file list after upload
        } else {
            document.getElementById("uploadStatus").innerHTML = `<span style="color: red;">Upload failed. Try again.</span>`;
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
    .then(response => {
        if (!response.ok) {
            throw new Error(`HTTP error! Status: ${response.status}`);
        }
        return response.json();
    })
    .then(data => {
        console.log("✅ Files received:", data);
        const fileListDiv = document.getElementById("fileList");
        fileListDiv.innerHTML = ""; 

        if (!data.files || data.files.length === 0) {
            fileListDiv.innerHTML = "<p>No files uploaded yet.</p>";
            return;
        }

        data.files.forEach(file => {
            let fileCard = document.createElement("div");
            fileCard.classList.add("file-card");

            let fileIcon = document.createElement("img");
            fileIcon.src = "https://img.icons8.com/color/48/000000/document.png"; // Generic file icon

            let fileName = document.createElement("div");
            fileName.textContent = file.name;

            let downloadLink = document.createElement("a");
            downloadLink.href = file.download_link;
            downloadLink.textContent = "Download";
            downloadLink.target = "_blank";
            downloadLink.classList.add("download-btn");

            fileCard.appendChild(fileIcon);
            fileCard.appendChild(fileName);
            fileCard.appendChild(downloadLink);
            fileListDiv.appendChild(fileCard);
        });
    })
    .catch(error => {
        console.error("❌ Error fetching files:", error);
        document.getElementById("fileList").innerHTML = '<p style="color: red;">Failed to fetch files.</p>';
    });
}

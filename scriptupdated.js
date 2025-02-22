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

    // Get the selected sorting option
    const sortOption = document.getElementById("sortFilter").value;

    // Sorting Logic by fahad al hasan
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

        let fileIcon = document.createElement("img");
        fileIcon.src = "https://img.icons8.com/color/48/000000/document.png";

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
}

document.getElementById("sortFilter").addEventListener("change", fetchFileList);
//last code
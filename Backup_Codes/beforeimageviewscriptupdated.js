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

    files.forEach(file => {
        let fileCard = document.createElement("div");
        fileCard.classList.add("file-card");

        let fileName = document.createElement("div");
        fileName.textContent = file.name;

        let filePreview = document.createElement("div");

        if (file.mime_type.startsWith("image")) {
            let img = document.createElement("img");
            img.src = file.thumbnail_link || file.preview_link;
            img.style.width = "100px";
            img.style.borderRadius = "8px";
            img.onerror = function () {
                this.src = "https://img.icons8.com/color/48/000000/document.png"; // Fallback icon
            };
            filePreview.appendChild(img);
        } else if (file.mime_type.startsWith("video")) {
            let iframe = document.createElement("iframe");
            iframe.src = file.preview_link;
            iframe.width = "160px";
            iframe.height = "100px";
            iframe.allow = "autoplay";
            iframe.frameBorder = "0";
            filePreview.appendChild(iframe);
        } else {
            let fileIcon = document.createElement("img");
            fileIcon.src = "https://img.icons8.com/color/48/000000/document.png"; // Generic file icon
            filePreview.appendChild(fileIcon);
        }

        let downloadLink = document.createElement("a");
        downloadLink.href = file.download_link;
        downloadLink.textContent = "Download";
        downloadLink.classList.add("download-btn");

        fileCard.append(filePreview, fileName, downloadLink);
        fileListDiv.appendChild(fileCard);
    });
}



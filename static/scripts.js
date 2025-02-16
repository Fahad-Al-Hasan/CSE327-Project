async function uploadFile() {
    let fileInput = document.getElementById("fileInput");
    if (fileInput.files.length === 0) {
        alert("Please select a file!");
        return;
    }

    let file = fileInput.files[0];
    let formData = new FormData();
    formData.append("file", file);

    let response = await fetch("/upload", {
        method: "POST",
        body: formData
    });

    let result = await response.json();
    alert(result.message);
    fetchFiles();
}

async function fetchFiles() {
    let response = await fetch("/files");
    let data = await response.json();

    let fileList = document.getElementById("fileList");
    fileList.innerHTML = "";

    data.files.forEach(file => {
        let li = document.createElement("li");
        li.innerHTML = `${file.name} 
            <button onclick="downloadFile('${file.path}')">⬇️</button>
            <button onclick="deleteFile('${file.path}')">🗑️</button>`;
        fileList.appendChild(li);
    });
}

async function downloadFile(filePath) {
    let response = await fetch(`/download/${filePath}`);
    let result = await response.json();
    alert(result.message);
}

async function deleteFile(filePath) {
    let response = await fetch("/delete", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ file_path: filePath })
    });

    let result = await response.json();
    alert(result.message);
    fetchFiles();
}

// Fetch files on page load
fetchFiles();

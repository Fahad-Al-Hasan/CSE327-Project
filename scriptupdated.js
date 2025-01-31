document.getElementById("listFilesBtn").addEventListener("click", function() {
    // Simulating file list (replace this with actual API call)
    let files = ["Document1.pdf", "Image2.png", "Report.xlsx", "Notes.txt"];

    let fileListDiv = document.getElementById("fileList");
    fileListDiv.innerHTML = ""; // Clear previous files

    files.forEach(file => {
        let fileItem = document.createElement("div");
        fileItem.textContent = file;
        fileListDiv.appendChild(fileItem);
    });
});

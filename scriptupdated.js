document.getElementById("listFilesBtn").addEventListener("click", function() {
    /*let files = [
        { name: "Document.pdf", icon: "https://img.icons8.com/color/48/000000/pdf.png" },
        { name: "Image.png", icon: "https://img.icons8.com/color/48/000000/image.png" },
        { name: "Report.docx", icon: "https://img.icons8.com/color/48/000000/ms-word.png" },
        { name: "Notes.txt", icon: "https://img.icons8.com/color/48/000000/document.png" }
    ];*/

    let fileListDiv = document.getElementById("fileList");
    fileListDiv.innerHTML = ""; 

    files.forEach((file, index) => {
        let fileCard = document.createElement("div");
        fileCard.classList.add("file-card");

        let fileIcon = document.createElement("img");
        fileIcon.src = file.icon;

        let fileName = document.createElement("div");
        fileName.textContent = file.name;

        fileCard.appendChild(fileIcon);
        fileCard.appendChild(fileName);
        fileListDiv.appendChild(fileCard);

        setTimeout(() => {
            fileCard.style.opacity = "1";
            fileCard.style.transform = "translateY(0px)";
        }, index * 150);
    });
});

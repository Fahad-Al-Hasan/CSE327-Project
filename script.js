document.getElementById("listFilesBtn").addEventListener("click", function () {
  fetchFileList();
});

document.getElementById("uploadForm").addEventListener("submit", function (event) {
  event.preventDefault();
  uploadFile();
});

async function uploadFile() {
  const fileInput = document.getElementById("fileInput");
  const file = fileInput.files[0];

  if (!file) {
      alert("Please select a file to upload.");
      return;
  }

  document.getElementById("uploadStatus").innerHTML = "Uploading...";
  const formData = new FormData();
  formData.append("file", file);

  fetch("http://127.0.0.1:5000/upload", {
      method: "POST",
      body: formData
  })
  .then(response => response.json())
  .then(data => {
      document.getElementById("uploadStatus").innerHTML = data.message;
      fetchFileList();
  })
  .catch(error => console.error("Upload error:", error));
}

function fetchFileList() {
  fetch("http://127.0.0.1:5000/files")
  .then(response => response.json())
  .then(data => console.log(data.files))
  .catch(error => console.error("Error fetching files:", error));
}

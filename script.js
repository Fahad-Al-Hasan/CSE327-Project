document.getElementById('listFilesBtn').addEventListener('click', function () {
  fetchFileList();
});

function fetchFileList() {
  console.log("📡 Fetching file list..."); // Debugging log

  fetch('http://127.0.0.1:5000/files', {
    method: 'GET',
    headers: {
      'Content-Type': 'application/json',
      'Cache-Control': 'no-cache'  // Prevents cached results
    }
  })
  .then(response => {
    if (!response.ok) {
      throw new Error(`HTTP error! Status: ${response.status}`);
    }
    return response.json();
  })
  .then(data => {
    console.log("✅ Files received:", data); // Debugging log
    const fileList = document.getElementById('fileList');
    fileList.innerHTML = ''; // Clear previous list

    if (!data.files || data.files.length === 0) {
      fileList.innerHTML = '<p>No files uploaded yet.</p>';
      return;
    }

    const ul = document.createElement('ul');
    data.files.forEach(file => {
      const li = document.createElement('li');
      li.innerHTML = `${file.name} <a href="${file.download_link}" target="_blank">Download</a>`;
      ul.appendChild(li);
    });
    fileList.appendChild(ul);
  })
  .catch(error => {
    console.error("❌ Error fetching files:", error);
    document.getElementById('fileList').innerHTML = '<p style="color: red;">Failed to fetch files. Check console for details.</p>';
  });
}

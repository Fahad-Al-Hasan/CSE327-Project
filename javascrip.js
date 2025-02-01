document.getElementById('uploadForm').addEventListener('submit', function(event) {
    event.preventDefault();
    const fileInput = document.getElementById('fileInput');
    const formData = new FormData();
    formData.append('file', fileInput.files[0]);
  
    fetch('/upload', {
      method: 'POST',
      body: formData
    })
    .then(response => response.json())
    .then(data => {
      document.getElementById('uploadStatus').textContent = data.message;
      if (data.message.includes('successfully')) {
        listFiles();
      }
    })
    .catch(error => {
      document.getElementById('uploadStatus').textContent = 'Upload error occurred.';
    });
  });
  
  document.getElementById('listFilesBtn').addEventListener('click', listFiles);
  
  function listFiles() {
    fetch('/files')
      .then(response => response.json())
      .then(data => {
        const fileList = document.getElementById('fileList');
        fileList.innerHTML = '';
        data.files.forEach(file => {
          const fileItem = document.createElement('div');
          fileItem.className = 'file-card';
          fileItem.innerHTML = `
            <p>${file.name}</p>
            <p>Last Modified: ${file.modifiedTime}</p>
            <a href="${file.download_link}" class="download-btn">Download</a>
          `;
          fileList.appendChild(fileItem);
        });
      })
      .catch(error => {
        document.getElementById('fileList').textContent = 'Error fetching files.';
      });
  }
  
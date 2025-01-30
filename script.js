// Handle file upload functionality
document.getElementById('uploadBtn').addEventListener('click', function (e) {
    const fileInput = document.getElementById('fileInput');
    const file = fileInput.files[0]; script.js 
    
    if (file) {
      const formData = new FormData();
      formData.append('file', file);
    
      fetch('/upload', {
        method: 'POST',
        body: formData,
      })
      .then(response => response.json())
      .then(data => {
        alert(data.message);
        fileInput.value = ''; // Clear the file input
        fetchFileList(); // Update file list after upload
      })
      .catch(error => {
        console.error('Error uploading file:', error);
        alert('An error occurred while uploading the file.');
      });
    } else {
      alert('Please select a file first.');
    }
  });
  
  // Handle file browsing functionality
  document.getElementById('listFilesBtn').addEventListener('click', function () {
    fetchFileList();
  });
  
  // Fetch file list from backend and display them
  function fetchFileList() {
    fetch('/files')
      .then(response => response.json())
      .then(data => {
        const fileList = document.getElementById('fileList');
        fileList.innerHTML = ''; // Clear the list before adding new items
        
        if (data.files.length === 0) {
          fileList.innerHTML = '<p>No files uploaded yet.</p>';
        } else {
          const ul = document.createElement('ul');
          data.files.forEach(file => {
            const li = document.createElement('li');
            li.innerHTML = ${file.name} <a href="/download/${file.id}" target="_blank">Download</a>;
            ul.appendChild(li);
          });
          fileList.appendChild(ul);
        }
      })
      .catch(error => {
        console.error('Error fetching file list:', error);
      });
  }
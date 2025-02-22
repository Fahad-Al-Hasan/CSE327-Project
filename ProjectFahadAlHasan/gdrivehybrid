from fastapi import APIRouter, UploadFile, File, Depends
import aiofiles
import os
import asyncio
from db import SessionLocal
from models import FileMetadata, FileChunk
from storage_checker import get_google_drive_storage, get_onedrive_storage, get_dropbox_storage

router = APIRouter()

# Upload API
@router.post("/upload")
async def upload_file(file: UploadFile = File(...)):
    db = SessionLocal()
    
    file_size = file.file._file.tell()
    file_size_mb = file_size / (1024 * 1024)  # Convert to MB
    
    # Get available storage in all providers
    google_storage, onedrive_storage, dropbox_storage = await asyncio.gather(
        get_google_drive_storage(), get_onedrive_storage(), get_dropbox_storage()
    )

    storage_options = [
        ("google_drive", google_storage),
        ("onedrive", onedrive_storage),
        ("dropbox", dropbox_storage)
    ]
    
    # Sort storages by available space
    storage_options.sort(key=lambda x: x[1], reverse=True)

    # Create database entry
    file_entry = FileMetadata(filename=file.filename, total_size=file_size_mb, uploaded_at="now()")
    db.add(file_entry)
    db.commit()
    db.refresh(file_entry)

    chunk_size = min(file_size_mb / len(storage_options), min(opt[1] for opt in storage_options if opt[1] > 0))
    
    # Read file in chunks and upload
    chunk_num = 0
    while chunk_num * chunk_size < file_size_mb:
        storage_provider, available_space = storage_options[chunk_num % len(storage_options)]

        if available_space < chunk_size:
            return {"error": f"Not enough space in {storage_provider}"}

        chunk_path = f"chunks/{file.filename}_part{chunk_num}"
        
        async with aiofiles.open(chunk_path, "wb") as chunk_file:
            chunk_data = await file.read(int(chunk_size * 1024 * 1024))
            await chunk_file.write(chunk_data)

        # Simulating upload to cloud (Replace with actual upload functions)
        cloud_path = f"/StorageSystem/{file.filename}_part{chunk_num}"

        # Store metadata in DB
        chunk_entry = FileChunk(file_id=file_entry.id, chunk_number=chunk_num, storage_provider=storage_provider, cloud_path=cloud_path)
        db.add(chunk_entry)
        db.commit()

        chunk_num += 1

    return {"message": "File uploaded successfully!", "total_chunks": chunk_num}

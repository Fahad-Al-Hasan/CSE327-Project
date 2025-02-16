from sqlalchemy import Column, Integer, String, ForeignKey, Float
from sqlalchemy.orm import relationship
from db import Base

# File metadata table
class FileMetadata(Base):
    __tablename__ = "files"

    id = Column(Integer, primary_key=True, index=True)
    filename = Column(String(255), index=True)  # ✅ Fix: Added String(255)
    total_size = Column(Float)  # Total file size in MB
    uploaded_at = Column(String(255))  # ✅ Fix: Added String(255)

    chunks = relationship("FileChunk", back_populates="file")

# File chunk tracking table
class FileChunk(Base):
    __tablename__ = "file_chunks"

    id = Column(Integer, primary_key=True, index=True)
    file_id = Column(Integer, ForeignKey("files.id"))
    chunk_number = Column(Integer)
    storage_provider = Column(String(50))  # ✅ Fix: Added String(50)
    cloud_path = Column(String(255))  # ✅ Fix: Added String(255)

    file = relationship("FileMetadata", back_populates="chunks")

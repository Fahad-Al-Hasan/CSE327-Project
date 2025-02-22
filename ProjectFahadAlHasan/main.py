from fastapi import FastAPI
import uvicorn
from auth import router as auth_router
from upload import router as upload_router
from db import init_db

app = FastAPI()

# Initialize database
init_db()

# Include authentication & upload routes
app.include_router(auth_router)
app.include_router(upload_router)

@app.get("/")
async def root():
    return {"message": "Storage Management System API is running"}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)

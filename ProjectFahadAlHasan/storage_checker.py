import httpx
from config import user_tokens

async def get_google_drive_storage():
    access_token = user_tokens.get("google", {}).get("access_token")
    if not access_token:
        return 0

    headers = {"Authorization": f"Bearer {access_token}"}
    async with httpx.AsyncClient() as client:
        response = await client.get("https://www.googleapis.com/drive/v3/about?fields=storageQuota", headers=headers)
    
    if response.status_code == 200:
        data = response.json()
        available_storage = int(data["storageQuota"]["limit"]) - int(data["storageQuota"]["usage"])
        return available_storage / (1024 * 1024)  # Convert bytes to MB
    return 0

async def get_onedrive_storage():
    access_token = user_tokens.get("onedrive", {}).get("access_token")
    if not access_token:
        return 0

    headers = {"Authorization": f"Bearer {access_token}"}
    async with httpx.AsyncClient() as client:
        response = await client.get("https://graph.microsoft.com/v1.0/me/drive", headers=headers)
    
    if response.status_code == 200:
        data = response.json()
        available_storage = int(data["quota"]["remaining"])
        return available_storage / (1024 * 1024)  # Convert bytes to MB
    return 0

async def get_dropbox_storage():
    access_token = user_tokens.get("dropbox", {}).get("access_token")
    if not access_token:
        return 0

    headers = {"Authorization": f"Bearer {access_token}"}
    async with httpx.AsyncClient() as client:
        response = await client.post("https://api.dropboxapi.com/2/users/get_space_usage", headers=headers)
    
    if response.status_code == 200:
        data = response.json()
        available_storage = int(data["allocation"]["allocated"]) - int(data["used"])
        return available_storage / (1024 * 1024)  # Convert bytes to MB
    return 0

import os
import logging
import dropbox
import random
import io
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseUpload

# Enable logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)

# Telegram Bot Token
TELEGRAM_BOT_TOKEN = "8177749899:AAF0Rf3bnCAyxSva3OJce8_WjPtIyO-ryec"

# Google Drive service account credentials
GDRIVE_CREDENTIALS = "credentials.json"
DRIVE_FOLDERS = [
    "1RX9n3bYgmzH8g_WapDOlvbMtJuNeo0My",
    "1wCYPW0SdNHpz1VdMXLFBuo2YvPdWf4eY",
    "1feL26aFdeofoebbIYMUMk33MRVS6f6SL",
]

# Dropbox API Token 
DROPBOX_TOKEN = "sl.u.AFm4TUMKWsW2hy7lg-rX2QeLgN9f0-KO8FIXUBAarnch6EWWuV2kcQ5llU7JVHdw5W_8_L-s79GAkXPieA3T6ERAh360B67Ef7f7ipQ7gONglFePz8ostpf-pJlRohnZ38nyNwxI9glFnUNyUXhKbQjGXBHovVbfYtHfh9sknWToxcDNP5J6IGCpk1a6fOBeDV4DUfpvmj7_PRzOhqWC6BYlQlus3XAIynYFprLyhunySnYIE3yIza6hZFWxwSYPCUGL35yqJ3k6bTO1NWRMw_Wn0xRGXcopQhhkItHZgLJtbIlVdxYcEWB6TQ-KKC5d7uNvwGCwbdsw6ltcmHcS3DZT4G0asX3mf9STVNWxCpRjvwehnD5MNjCBHQDCDC3Hvpessgcsuc0GYdsgi6ndrDKdg8RynWQHOr8EqYFrnNwHkHZ9ksVZG07w-Js42AFtVLYXOTWteg5ZI7YEi3J9tOMJN_leOTFIQ17S-v5m_KnlGfaTqH1N7IV3tTYosiniO2CH-SYAR6N-P1X__6sAqmhwvuduR9WzRwASLmWKkGuZs7UcGuRo8hzyrX5mQHMNQjYR11ZzB-I1f1eI2IxFFnUgOzzng_dzf3t-NAkYS0dL6rLNbR7cWGUmujVRm7EzeWzgUztqyfI9Qco40PWTDw4C4yivsGnwvmEV-c5qgUg-2-N76JqeMSYPOK1AGa2aeNzsNaewVMPPlo-2ba1F1vE_m0s2bDCnctPnlGa8L_XUuWhVqJ1QogmY4XK8eQpBSeJAyh_DN5Gc0u33stlpRK7eHvdKUq05enLSNgVxEqGTzbz4bvfe-2cCCh83ao7ap7FS9Yq-NNtX7IoA31ylGVDUXGP_Ya3QQiy50Ka5XUszQQY4UXa0hz5I7Xpz63DJEmjlAG2VpgOlPsZQ64DLGGVOXB2ccJlN_o5vCXpXuJN4pcT6nGMmj9ErB8wlpfxKHuT-BRIfAhyZF3INwrFZtEdKqlvUv5heuj1gVulkKBaC07QlHW687cG--xcFR8w8XHAWKxsfSB7B7WXJgmLN8plN4PC38wqJiG2A_QtD3HlOH2LvNXSkcd3_UbIByDAplNOzCx5XxmimtWp88Mo6rRDtd6w6g8cEdtaii1tNU0E3hOqz1VKJI1Hzz6uRGPVB_Hi1IDauZVLnTKi_V-GJfD7P2c043uo7_2d74ybc6RdANCPXrGaoLhJ80MgrsE7uatWZueXWiHAo_HTNxEH81CEs1pF8oRprEQdl3eDO3gLCZOdx6gtqfjXp04wG8RNjnpbryQgbBNqsb8EODACZ_gnT1WqgYBGLFc6Td1lAvzbBfdg1HHdpv2eiG6_6shzS0bwH80CprNGv5ZRlWTHN2Q7VsiMAkhp7ns3_H-JTsLhtG7QMcdnAbxFfVty_344opN-iEBHDA-Pn22moEVQAvfDSYc94vj7RqqFZ0DZ7_axP9A"

# Chunk size for large files (512KB)
CHUNK_SIZE = 512 * 1024


def get_drive_service():
    """Authenticate and return a Google Drive service instance."""
    creds = Credentials.from_service_account_file(
        GDRIVE_CREDENTIALS, scopes=["https://www.googleapis.com/auth/drive"]
    )
    return build("drive", "v3", credentials=creds)


def get_dropbox_client():
    """Return a Dropbox client."""
    return dropbox.Dropbox(DROPBOX_TOKEN)


async def upload_file(file_data, file_name, upload_choice):
    """Upload a file to Google Drive or Dropbox."""
    if upload_choice == "drive":
        return await upload_to_drive(file_data, file_name)
    elif upload_choice == "dropbox":
        return await upload_to_dropbox(file_data, file_name)


async def upload_to_drive(file_data, file_name):
    """Upload a file to Google Drive."""
    try:
        drive_service = get_drive_service()
        folder_id = random.choice(DRIVE_FOLDERS)

        metadata = {"name": file_name, "parents": [folder_id]}
        media = MediaIoBaseUpload(io.BytesIO(file_data), mimetype="application/octet-stream")
        file = drive_service.files().create(body=metadata, media_body=media, fields="id").execute()

        return f"File uploaded successfully to Google Drive: https://drive.google.com/file/d/{file['id']}/view"
    except Exception as e:
        logger.error(f"Error uploading to Google Drive: {e}")
        return "Failed to upload to Google Drive."


async def upload_to_dropbox(file_data, file_name):
    """Upload a file to Dropbox."""
    try:
        dbx = get_dropbox_client()
        file_path = f"/{file_name}"
        dbx.files_upload(file_data, file_path)

        return f"File uploaded successfully to Dropbox: {file_path}"
    except Exception as e:
        logger.error(f"Error uploading to Dropbox: {e}")
        return "Failed to upload to Dropbox."


async def list_drive_files():
    """List files in Google Drive."""
    try:
        drive_service = get_drive_service()
        results = drive_service.files().list(
            q="mimeType != 'application/vnd.google-apps.folder'",
            fields="files(id, name)"
        ).execute()
        files = results.get("files", [])

        if not files:
            return "No files found in Google Drive."

        file_list = "\n".join([f"{file['name']}: https://drive.google.com/file/d/{file['id']}/view" for file in files])
        return f"Files in Google Drive:\n{file_list}"

    except Exception as e:
        logger.error(f"Error listing Google Drive files: {e}")
        return "Failed to fetch files from Google Drive."


async def list_dropbox_files():
    """List all files in Dropbox."""
    try:
        dbx = get_dropbox_client()
        result = dbx.files_list_folder('').entries  # List the root directory files
        if not result:
            return "No files found in Dropbox."

        files_list = []
        for file in result:
            if isinstance(file, dropbox.files.FileMetadata):
                files_list.append(f"File: {file.name} - {file.path_lower}")
        if files_list:
            return "\n".join(files_list)
        else:
            return "No files found in Dropbox."
    except dropbox.exceptions.ApiError as e:
        logger.error(f"Failed to fetch files from Dropbox: {e}")
        return "Failed to fetch files from Dropbox."


async def delete_file(file_name, storage_choice):
    """Delete a file from Google Drive or Dropbox."""
    if storage_choice == "drive":
        return await delete_from_drive(file_name)
    elif storage_choice == "dropbox":
        return await delete_from_dropbox(file_name)


async def delete_from_drive(file_name):
    """Delete a file from Google Drive."""
    try:
        drive_service = get_drive_service()
        results = drive_service.files().list(q=f"name = '{file_name}'", fields="files(id, name)").execute()
        files = results.get("files", [])

        if files:
            file_id = files[0]["id"]
            drive_service.files().delete(fileId=file_id).execute()
            return f"File {file_name} deleted from Google Drive."
        else:
            return f"File {file_name} not found in Google Drive."
    except Exception as e:
        logger.error(f"Error deleting from Google Drive: {e}")
        return "Failed to delete from Google Drive."


async def delete_from_dropbox(file_name):
    """Delete a file from Dropbox."""
    try:
        dbx = get_dropbox_client()
        dbx.files_delete_v2(f"/{file_name}")
        return f"File {file_name} deleted from Dropbox."
    except dropbox.exceptions.ApiError as e:
        logger.error(f"Error deleting from Dropbox: {e}")
        return "Failed to delete from Dropbox."


async def search_file(file_name, storage_choice):
    """Search for a file in Google Drive or Dropbox."""
    if storage_choice == "drive":
        return await search_in_drive(file_name)
    elif storage_choice == "dropbox":
        return await search_in_dropbox(file_name)


async def search_in_drive(file_name):
    """Search for a file in Google Drive."""
    try:
        drive_service = get_drive_service()
        results = drive_service.files().list(q=f"name = '{file_name}'", fields="files(id, name)").execute()
        files = results.get("files", [])

        if files:
            return f"File found in Google Drive: https://drive.google.com/file/d/{files[0]['id']}/view"
        else:
            return f"File {file_name} not found in Google Drive."
    except Exception as e:
        logger.error(f"Error searching in Google Drive: {e}")
        return "Failed to search in Google Drive."


async def search_in_dropbox(file_name):
    """Search for a file in Dropbox."""
    try:
        dbx = get_dropbox_client()
        result = dbx.files_list_folder('').entries  # List the root directory files
        for file in result:
            if isinstance(file, dropbox.files.FileMetadata) and file.name == file_name:
                return f"File found in Dropbox: {file.path_lower}"

        return f"File {file_name} not found in Dropbox."
    except dropbox.exceptions.ApiError as e:
        logger.error(f"Error searching in Dropbox: {e}")
        return "Failed to search in Dropbox."


async def start(update: Update, context):
    """Start command response."""
    await update.message.reply_text("Hello! Send me a file, and I'll store it in Google Drive or Dropbox.\nUse /preview to see uploaded files.")


async def handle_document(update: Update, context):
    """Handle file uploads from users."""
    file = update.message.document
    file_name = file.file_name
    file = await file.get_file()
    file_data = await file.download_as_bytearray()

    upload_choice = random.choice(["drive", "dropbox"])
    response = await upload_file(file_data, file_name, upload_choice)

    await update.message.reply_text(response)


async def preview(update: Update, context):
    """Preview the uploaded files in Google Drive and Dropbox."""
    drive_files = await list_drive_files()
    dropbox_files = await list_dropbox_files()

    response = f"{drive_files}\n\n{dropbox_files}"

    MAX_MESSAGE_LENGTH = 4096
    while len(response) > MAX_MESSAGE_LENGTH:
        # Find the last newline character within the limit
        split_point = response.rfind("\n", 0, MAX_MESSAGE_LENGTH)
        await update.message.reply_text(response[:split_point])
        response = response[split_point + 1:]

    if response:
        await update.message.reply_text(response)


async def delete(update: Update, context):
    """Delete a file from Google Drive or Dropbox."""
    file_name = ' '.join(context.args)
    if not file_name:
        await update.message.reply_text("Please provide a file name.")
        return

    storage_choice = random.choice(["drive", "dropbox"])
    response = await delete_file(file_name, storage_choice)

    await update.message.reply_text(response)


async def search(update: Update, context):
    """Search for a file in Google Drive or Dropbox."""
    file_name = ' '.join(context.args)
    if not file_name:
        await update.message.reply_text("Please provide a file name.")
        return

    storage_choice = random.choice(["drive", "dropbox"])
    response = await search_file(file_name, storage_choice)

    await update.message.reply_text(response)


def main():
    """Main bot function."""
    app = Application.builder().token(TELEGRAM_BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("preview", preview))
    app.add_handler(CommandHandler("delete", delete))
    app.add_handler(CommandHandler("search", search))
    app.add_handler(MessageHandler(filters.Document, handle_document))

    print("Bot is running...")
    app.run_polling()


if __name__ == "__main__":
    main()

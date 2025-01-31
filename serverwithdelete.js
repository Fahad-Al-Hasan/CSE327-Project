const express = require("express");
const multer = require("multer");
const { google } = require("googleapis");
const fs = require("fs-extra");
const cors = require("cors");
require("dotenv").config();

const app = express();
app.use(cors());
app.use(express.json());

const upload = multer({ dest: "uploads/" });

// Google Auth Setup
const auth = new google.auth.GoogleAuth({
    keyFile: "google-drive-key.json",
    scopes: ["https://www.googleapis.com/auth/drive"]
});
const drive = google.drive({ version: "v3", auth });

/**
 * Upload File to Google Drive
 */
app.post("/upload", upload.single("file"), async (req, res) => {
    try {
        if (!req.file) {
            return res.status(400).json({ error: "No file uploaded" });
        }

        const fileMetadata = {
            name: req.file.originalname,
            parents: [process.env.DRIVE_FOLDER_ID]
        };

        const media = {
            mimeType: req.file.mimetype,
            body: fs.createReadStream(req.file.path)
        };

        const file = await drive.files.create({
            resource: fileMetadata,
            media: media,
            fields: "id"
        });

        // Delete temporary file after upload
        await fs.remove(req.file.path);

        res.json({ success: true, fileId: file.data.id });
    } catch (error) {
        console.error("Upload Error:", error);
        res.status(500).json({ error: "File upload failed" });
    }
});

/**
 * List Files from Google Drive
 */
app.get("/files", async (req, res) => {
    try {
        const response = await drive.files.list({
            pageSize: 10,
            fields: "files(id, name)"
        });

        res.json(response.data.files);
    } catch (error) {
        console.error("List Files Error:", error);
        res.status(500).json({ error: "Failed to fetch files" });
    }
});

/**
 * Download File from Google Drive
 */
app.get("/download/:id", async (req, res) => {
    try {
        const fileId = req.params.id;

        const file = await drive.files.get(
            { fileId, alt: "media" },
            { responseType: "stream" }
        );

        res.setHeader("Content-Disposition", `attachment; filename="${fileId}"`);
        file.data.pipe(res);
    } catch (error) {
        console.error("Download Error:", error);
        res.status(500).json({ error: "File download failed" });
    }
});

/**
 * Delete File from Google Drive
 */
app.delete("/delete/:id", async (req, res) => {
    try {
        const fileId = req.params.id;

        await drive.files.delete({ fileId });

        res.json({ success: true, message: `File ${fileId} deleted successfully` });
    } catch (error) {
        console.error("Delete Error:", error);
        res.status(500).json({ error: "File deletion failed" });
    }
});

// Start Server
const PORT = process.env.PORT || 5000;
app.listen(PORT, () => console.log(`🚀 Server running on port ${PORT}`));

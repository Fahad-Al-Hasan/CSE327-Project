const express = require("express");
const multer = require("multer");
const { google } = require("googleapis"); //google apis for google drive authentication
const fs = require("fs");
const cors = require("cors");

require("dotenv").config();
const app = express();
app.use(cors());
const upload = multer({ dest: "uploads/" });
//multer for handling file uploads
const auth = new google.auth.GoogleAuth({
    keyFile: "google-drive-key.json",
    scopes: ["https://www.googleapis.com/auth/drive.file"]
});

const drive = google.drive({ version: "v3", auth });

app.post("/upload", upload.single("file"), async (req, res) => {
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
    res.json({ fileId: file.data.id });
});

app.get("/files", async (req, res) => {
    const response = await drive.files.list({
        pageSize: 10,
        fields: "files(id, name)"
    });
    res.json(response.data.files);
});

app.get("/download/:id", async (req, res) => {
    const fileId = req.params.id;
    const file = await drive.files.get({ fileId, alt: "media" }, { responseType: "stream" });
    file.data.pipe(res);
});

app.listen(5000, () => console.log("Server running on port 5000"));
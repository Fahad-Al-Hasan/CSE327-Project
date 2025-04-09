const express = require('express');
const admin = require('firebase-admin');
const bodyParser = require('body-parser');
const mysql = require('mysql2/promise');
const cors = require('cors');
require('dotenv').config();

const app = express();
app.use(cors());
app.use(bodyParser.json());

const serviceAccount = require('./firebaseServiceAccountKey.json');
admin.initializeApp({ credential: admin.credential.cert(serviceAccount) });

const db = mysql.createPool({
    host: "localhost",
    user: "root",
    password: "",
    database: "amazing_storage"
});

// In-memory OTP store (replace with Redis for scaling)
let otpSessions = {};

app.post('/start-verification', async (req, res) => {
    const { email, phone, telegram_id } = req.body;

    try {
        // Check if email exists in the database
        const [rows] = await db.query('SELECT id FROM users WHERE email = ?', [email]);
        if (rows.length === 0) return res.status(404).json({ message: 'Email not found' });

        const userId = rows[0].id;
        const phoneNumber = `+880${phone}`; 
        // Send OTP via Firebase
        const verificationId = await admin.auth().generateSignInWithPhoneNumber(phoneNumber);

        // Store session info
        otpSessions[telegram_id] = {
            email,
            userId,
            phone: phoneNumber,
            verificationId,
            verified: false,
        };

        res.json({ success: true, message: 'OTP sent via Firebase' });
    } catch (e) {
        console.error(e);
        res.status(500).json({ success: false, message: 'Server error' });
    }
});

app.post('/verify-otp', async (req, res) => {
    const { telegram_id, otp_code } = req.body;
    const session = otpSessions[telegram_id];

    if (!session) return res.status(400).json({ message: 'Session not found' });

    try {
        // Verify OTP using Firebase
        const verificationId = session.verificationId;

        const isOtpValid = await admin.auth().signInWithPhoneNumber(verificationId, otp_code);
        if (!isOtpValid) return res.status(401).json({ message: 'Invalid OTP' });

        session.verified = true;

        // Insert or update user verification in database
        await db.query(
            'INSERT INTO telegram_users (user_id, telegram_id) VALUES (?, ?) ON DUPLICATE KEY UPDATE telegram_id = ?',
            [session.userId, telegram_id, telegram_id]
        );

        res.json({ success: true });
    } catch (e) {
        console.error(e);
        res.status(500).json({ message: 'Verification failed' });
    }
});

app.get('/check-verification/:telegram_id', async (req, res) => {
    // Check if the user has completed verification
    const [rows] = await db.query('SELECT * FROM telegram_users WHERE telegram_id = ?', [req.params.telegram_id]);
    res.json({ verified: rows.length > 0 });
});

app.listen(3001, () => {
    console.log('Backend running at http://localhost:3001');
});

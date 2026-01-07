const { makeWASocket, useMultiFileAuthState, DisconnectReason, fetchLatestBaileysVersion, makeCacheableSignalKeyStore } = require('@whiskeysockets/baileys');
const express = require('express');
const cors = require('cors');
const axios = require('axios');
const QRCode = require('qrcode');
const fs = require('fs');
const path = require('path');
const pino = require('pino');

// Create pino logger for Baileys
const logger = pino({ level: 'silent' }); // Use 'debug' for more verbose logging

const app = express();
app.use(cors());
app.use(express.json());

const FASTAPI_URL = process.env.FASTAPI_URL || 'http://localhost:8001';
const PORT = process.env.PORT || 3002;

let sock = null;
let qrCode = null;
let qrDataUrl = null;
let connectionStatus = 'disconnected';
let connectedUser = null;
let pausedChats = new Set(); // Chats where bot is paused (admin intervention)

// Store for pending messages
let pendingMessages = [];

async function initWhatsApp() {
    try {
        const authPath = path.join(__dirname, 'auth_info');
        
        // Ensure auth directory exists
        if (!fs.existsSync(authPath)) {
            fs.mkdirSync(authPath, { recursive: true });
        }

        const { state, saveCreds } = await useMultiFileAuthState(authPath);
        const { version } = await fetchLatestBaileysVersion();

        sock = makeWASocket({
            version,
            logger,
            auth: {
                creds: state.creds,
                keys: makeCacheableSignalKeyStore(state.keys, logger)
            },
            printQRInTerminal: false,
            browser: ['Estonia Cobertura Bot', 'Chrome', '1.0.0'],
            syncFullHistory: false,
            generateHighQualityLinkPreview: false
        });

        sock.ev.on('connection.update', async (update) => {
            const { connection, lastDisconnect, qr } = update;

            if (qr) {
                console.log('QR Code generated');
                qrCode = qr;
                // Generate QR as data URL for frontend
                qrDataUrl = await QRCode.toDataURL(qr);
                connectionStatus = 'awaiting_qr';
            }

            if (connection === 'close') {
                const statusCode = lastDisconnect?.error?.output?.statusCode;
                const shouldReconnect = statusCode !== DisconnectReason.loggedOut;
                
                console.log('Connection closed. Reason:', lastDisconnect?.error?.message, 'Reconnecting:', shouldReconnect);
                
                connectionStatus = 'disconnected';
                connectedUser = null;
                qrCode = null;
                qrDataUrl = null;

                if (shouldReconnect) {
                    setTimeout(initWhatsApp, 5000);
                } else {
                    // Clear auth on logout
                    try {
                        fs.rmSync(authPath, { recursive: true, force: true });
                        fs.mkdirSync(authPath, { recursive: true });
                    } catch (e) {
                        console.error('Error clearing auth:', e);
                    }
                }
            } else if (connection === 'open') {
                console.log('WhatsApp connected successfully');
                connectionStatus = 'connected';
                connectedUser = sock.user;
                qrCode = null;
                qrDataUrl = null;
            }
        });

        sock.ev.on('messages.upsert', async ({ messages, type }) => {
            if (type === 'notify') {
                for (const message of messages) {
                    // Only process incoming messages (not from us)
                    if (!message.key.fromMe && message.message) {
                        await handleIncomingMessage(message);
                    }
                }
            }
        });

        sock.ev.on('creds.update', saveCreds);

    } catch (error) {
        console.error('WhatsApp initialization error:', error);
        connectionStatus = 'error';
        setTimeout(initWhatsApp, 10000);
    }
}

async function handleIncomingMessage(message) {
    try {
        const remoteJid = message.key.remoteJid;
        
        // Extract phone number - handle different formats
        // @s.whatsapp.net = standard phone
        // @lid = linked device ID
        // @g.us = group
        let phoneNumber = remoteJid;
        
        if (remoteJid.endsWith('@s.whatsapp.net')) {
            phoneNumber = remoteJid.replace('@s.whatsapp.net', '');
        } else if (remoteJid.endsWith('@g.us')) {
            // Skip group messages
            console.log('Skipping group message');
            return;
        } else if (remoteJid.includes('@lid')) {
            // LID format - keep the full JID for replies
            phoneNumber = remoteJid.replace('@lid', '');
        }
        
        // Store the original JID for replying
        const replyJid = remoteJid;
        
        console.log(`Processing message from: ${phoneNumber} (reply to: ${replyJid})`);

        // Extract message text
        let messageText = '';
        if (message.message.conversation) {
            messageText = message.message.conversation;
        } else if (message.message.extendedTextMessage?.text) {
            messageText = message.message.extendedTextMessage.text;
        } else if (message.message.imageMessage?.caption) {
            messageText = message.message.imageMessage.caption;
        }

        if (!messageText) {
            console.log('Message without text, skipping');
            return;
        }

        console.log(`Message from ${phoneNumber}: ${messageText}`);

        // Store message in pending list
        const msgData = {
            id: message.key.id,
            phone_number: phoneNumber,
            remote_jid: remoteJid,
            reply_jid: replyJid,  // Store original JID for replying
            message: messageText,
            timestamp: message.messageTimestamp,
            push_name: message.pushName || '',
            processed: false,
            bot_paused: pausedChats.has(phoneNumber)
        };
        pendingMessages.push(msgData);

        // Store JID mapping for replies
        jidMapping[phoneNumber] = replyJid;

        // Only 100 messages in memory
        if (pendingMessages.length > 100) {
            pendingMessages = pendingMessages.slice(-100);
        }

        // Check if bot is paused for this chat
        if (pausedChats.has(phoneNumber)) {
            console.log(`Bot paused for ${phoneNumber}, not auto-responding`);
            return;
        }

        // Forward to FastAPI for AI processing
        try {
            const response = await axios.post(`${FASTAPI_URL}/api/whatsapp/message`, {
                phone_number: phoneNumber,
                message: messageText,
                message_id: message.key.id,
                timestamp: message.messageTimestamp,
                push_name: message.pushName || '',
                reply_jid: replyJid  // Pass the JID for replying
            }, { timeout: 30000 });

            // Send AI response back to WhatsApp using ORIGINAL JID
            if (response.data.reply) {
                await sendMessageToJid(replyJid, response.data.reply);
            }

        } catch (apiError) {
            console.error('Error forwarding to FastAPI:', apiError.message);
        }

    } catch (error) {
        console.error('Error handling incoming message:', error);
    }
}

// Store mapping of phone numbers to JIDs
let jidMapping = {};

async function sendMessageToJid(jid, text) {
    try {
        if (!sock || connectionStatus !== 'connected') {
            throw new Error('WhatsApp not connected');
        }

        await sock.sendMessage(jid, { text });
        console.log(`Message sent to JID: ${jid}`);
        return { success: true };

    } catch (error) {
        console.error('Error sending message to JID:', error);
        return { success: false, error: error.message };
    }
}

async function sendMessage(phoneNumber, text) {
    try {
        if (!sock || connectionStatus !== 'connected') {
            throw new Error('WhatsApp not connected');
        }

        // Check if we have a JID mapping for this phone
        let jid = jidMapping[phoneNumber];
        
        if (!jid) {
            // Fallback: construct JID
            jid = phoneNumber.includes('@') ? phoneNumber : `${phoneNumber}@s.whatsapp.net`;
        }
        
        await sock.sendMessage(jid, { text });
        console.log(`Message sent to ${phoneNumber} (JID: ${jid})`);
        return { success: true };

    } catch (error) {
        console.error('Error sending message:', error);
        return { success: false, error: error.message };
    }
}

// REST API Endpoints

app.get('/status', (req, res) => {
    res.json({
        status: connectionStatus,
        connected: connectionStatus === 'connected',
        user: connectedUser ? {
            id: connectedUser.id,
            name: connectedUser.name
        } : null,
        paused_chats: Array.from(pausedChats)
    });
});

app.get('/qr', (req, res) => {
    res.json({
        qr: qrCode || null,
        qr_data_url: qrDataUrl || null,
        status: connectionStatus
    });
});

app.post('/connect', async (req, res) => {
    if (connectionStatus === 'connected') {
        return res.json({ success: true, message: 'Already connected' });
    }
    
    try {
        await initWhatsApp();
        res.json({ success: true, message: 'Connection initiated' });
    } catch (error) {
        res.status(500).json({ success: false, error: error.message });
    }
});

app.post('/disconnect', async (req, res) => {
    try {
        if (sock) {
            await sock.logout();
        }
        connectionStatus = 'disconnected';
        connectedUser = null;
        qrCode = null;
        qrDataUrl = null;
        res.json({ success: true, message: 'Disconnected' });
    } catch (error) {
        res.status(500).json({ success: false, error: error.message });
    }
});

app.post('/send', async (req, res) => {
    const { phone_number, message } = req.body;
    
    if (!phone_number || !message) {
        return res.status(400).json({ success: false, error: 'phone_number and message required' });
    }
    
    const result = await sendMessage(phone_number, message);
    res.json(result);
});

app.get('/messages', (req, res) => {
    // Return recent messages
    res.json({
        messages: pendingMessages.slice(-50),
        count: pendingMessages.length
    });
});

app.get('/conversations', (req, res) => {
    // Group messages by phone number
    const conversations = {};
    
    for (const msg of pendingMessages) {
        if (!conversations[msg.phone_number]) {
            conversations[msg.phone_number] = {
                phone_number: msg.phone_number,
                push_name: msg.push_name,
                messages: [],
                last_message_time: msg.timestamp,
                bot_paused: pausedChats.has(msg.phone_number)
            };
        }
        conversations[msg.phone_number].messages.push(msg);
        if (msg.timestamp > conversations[msg.phone_number].last_message_time) {
            conversations[msg.phone_number].last_message_time = msg.timestamp;
            conversations[msg.phone_number].push_name = msg.push_name || conversations[msg.phone_number].push_name;
        }
    }
    
    const convList = Object.values(conversations).sort((a, b) => b.last_message_time - a.last_message_time);
    
    res.json({
        conversations: convList,
        paused_chats: Array.from(pausedChats)
    });
});

app.post('/pause-chat', (req, res) => {
    const { phone_number } = req.body;
    
    if (!phone_number) {
        return res.status(400).json({ success: false, error: 'phone_number required' });
    }
    
    pausedChats.add(phone_number);
    console.log(`Bot paused for chat: ${phone_number}`);
    res.json({ success: true, paused: true, phone_number });
});

app.post('/resume-chat', (req, res) => {
    const { phone_number } = req.body;
    
    if (!phone_number) {
        return res.status(400).json({ success: false, error: 'phone_number required' });
    }
    
    pausedChats.delete(phone_number);
    console.log(`Bot resumed for chat: ${phone_number}`);
    res.json({ success: true, paused: false, phone_number });
});

app.listen(PORT, () => {
    console.log(`WhatsApp service running on port ${PORT}`);
    console.log(`FastAPI URL: ${FASTAPI_URL}`);
    
    // Auto-start connection if auth exists
    const authPath = path.join(__dirname, 'auth_info');
    if (fs.existsSync(authPath) && fs.readdirSync(authPath).length > 0) {
        console.log('Found existing auth, attempting to connect...');
        initWhatsApp();
    }
});

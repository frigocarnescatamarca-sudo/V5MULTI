const { makeWASocket, useMultiFileAuthState, DisconnectReason, fetchLatestBaileysVersion, makeCacheableSignalKeyStore, jidNormalizedUser } = require('@whiskeysockets/baileys');
const express = require('express');
const cors = require('cors');
const axios = require('axios');
const QRCode = require('qrcode');
const fs = require('fs');
const path = require('path');
const pino = require('pino');

// Create pino logger for Baileys
const logger = pino({ level: 'silent' });

const app = express();
app.use(cors());
app.use(express.json());

const FASTAPI_URL = process.env.FASTAPI_URL || 'http://localhost:8001';
const PORT = process.env.PORT || 3003;

let sock = null;
let qrCode = null;
let qrDataUrl = null;
let connectionStatus = 'disconnected';
let connectedUser = null;
let pausedChats = new Set();

let pendingMessages = [];
let lidToPhone = {};
let phoneToJid = {};

async function initWhatsApp() {
    try {
        const authPath = path.join(__dirname, 'auth_info_sandwich');
        
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
            browser: ['Sandwicheria Bot', 'Chrome', '1.0.0'],
            syncFullHistory: false,
            generateHighQualityLinkPreview: false
        });

        sock.ev.on('connection.update', async (update) => {
            const { connection, lastDisconnect, qr } = update;

            if (qr) {
                console.log('[Sandwich] QR Code generated');
                qrCode = qr;
                qrDataUrl = await QRCode.toDataURL(qr);
                connectionStatus = 'awaiting_qr';
            }

            if (connection === 'close') {
                const statusCode = lastDisconnect?.error?.output?.statusCode;
                const shouldReconnect = statusCode !== DisconnectReason.loggedOut;
                
                console.log('[Sandwich] Connection closed. Reconnecting:', shouldReconnect);
                
                connectionStatus = 'disconnected';
                connectedUser = null;
                qrCode = null;
                qrDataUrl = null;

                if (shouldReconnect) {
                    setTimeout(initWhatsApp, 5000);
                } else {
                    try {
                        fs.rmSync(authPath, { recursive: true, force: true });
                        fs.mkdirSync(authPath, { recursive: true });
                    } catch (e) {
                        console.error('[Sandwich] Error clearing auth:', e);
                    }
                }
            } else if (connection === 'open') {
                console.log('[Sandwich] WhatsApp connected successfully');
                connectionStatus = 'connected';
                connectedUser = sock.user;
                qrCode = null;
                qrDataUrl = null;
            }
        });

        sock.ev.on('messages.upsert', async ({ messages, type }) => {
            if (type === 'notify') {
                for (const message of messages) {
                    if (!message.key.fromMe && message.message) {
                        await handleIncomingMessage(message);
                    }
                }
            }
        });

        sock.ev.on('creds.update', saveCreds);

    } catch (error) {
        console.error('[Sandwich] WhatsApp initialization error:', error);
        connectionStatus = 'error';
        setTimeout(initWhatsApp, 10000);
    }
}

async function handleIncomingMessage(message) {
    try {
        const remoteJid = message.key.remoteJid;
        
        if (remoteJid.endsWith('@g.us')) {
            console.log('[Sandwich] Skipping group message');
            return;
        }
        
        let phoneNumber = null;
        let replyJid = remoteJid;
        
        if (remoteJid.endsWith('@s.whatsapp.net')) {
            phoneNumber = remoteJid.replace('@s.whatsapp.net', '');
        } else if (remoteJid.includes('@lid')) {
            const lidId = remoteJid.replace('@lid', '');
            
            if (lidToPhone[lidId]) {
                phoneNumber = lidToPhone[lidId];
            } else {
                const pushName = message.pushName || '';
                
                if (/^\+?\d{10,15}$/.test(pushName.replace(/[\s\-]/g, ''))) {
                    phoneNumber = pushName.replace(/[\s\-\+]/g, '');
                } else {
                    if (!phoneNumber) {
                        phoneNumber = lidId;
                        console.log(`[Sandwich] Warning: Using LID ${lidId} as phone`);
                    }
                }
                
                if (phoneNumber && phoneNumber !== lidId) {
                    lidToPhone[lidId] = phoneNumber;
                }
            }
        }
        
        phoneToJid[phoneNumber] = replyJid;
        
        console.log(`[Sandwich] Processing message from: ${phoneNumber}`);

        let messageText = '';
        let location = null;
        
        // Check for location message first
        if (message.message.locationMessage) {
            const loc = message.message.locationMessage;
            location = {
                latitude: loc.degreesLatitude,
                longitude: loc.degreesLongitude,
                name: loc.name || '',
                address: loc.address || ''
            };
            messageText = `📍 Ubicación compartida`;
            console.log(`[Sandwich] Location received from ${phoneNumber}: ${location.latitude}, ${location.longitude}`);
        } else if (message.message.liveLocationMessage) {
            const loc = message.message.liveLocationMessage;
            location = {
                latitude: loc.degreesLatitude,
                longitude: loc.degreesLongitude,
                name: 'Ubicación en vivo',
                address: ''
            };
            messageText = `📍 Ubicación en vivo compartida`;
            console.log(`[Sandwich] Live location received from ${phoneNumber}: ${location.latitude}, ${location.longitude}`);
        } else if (message.message.conversation) {
            messageText = message.message.conversation;
        } else if (message.message.extendedTextMessage?.text) {
            messageText = message.message.extendedTextMessage.text;
        } else if (message.message.imageMessage?.caption) {
            messageText = message.message.imageMessage.caption;
        }

        if (!messageText && !location) {
            console.log('[Sandwich] Message without text or location, skipping');
            return;
        }

        console.log(`[Sandwich] Message from ${phoneNumber}: ${messageText}`);

        const msgData = {
            id: message.key.id,
            phone_number: phoneNumber,
            remote_jid: remoteJid,
            message: messageText,
            location: location,
            timestamp: message.messageTimestamp,
            push_name: message.pushName || '',
            processed: false,
            bot_paused: pausedChats.has(phoneNumber)
        };
        pendingMessages.push(msgData);

        if (pendingMessages.length > 100) {
            pendingMessages = pendingMessages.slice(-100);
        }

        if (pausedChats.has(phoneNumber)) {
            console.log(`[Sandwich] Bot paused for ${phoneNumber}`);
            return;
        }

        // Forward to FastAPI - SANDWICH endpoint
        try {
            const payload = {
                phone_number: phoneNumber,
                message: messageText,
                message_id: message.key.id,
                timestamp: message.messageTimestamp,
                push_name: message.pushName || '',
                reply_jid: replyJid
            };
            
            // Include location if present
            if (location) {
                payload.location = location;
            }
            
            const response = await axios.post(`${FASTAPI_URL}/api/sandwich/whatsapp/message`, payload, { timeout: 30000 });

            if (response.data.reply) {
                const delay = 2000 + Math.random() * 3000;
                console.log(`[Sandwich] Waiting ${Math.round(delay/1000)}s before responding...`);
                await new Promise(resolve => setTimeout(resolve, delay));
                
                await sendMessageToJid(replyJid, response.data.reply);
            }

        } catch (apiError) {
            console.error('[Sandwich] Error forwarding to FastAPI:', apiError.message);
        }

    } catch (error) {
        console.error('[Sandwich] Error handling incoming message:', error);
    }
}

async function sendMessageToJid(jid, text) {
    try {
        if (!sock || connectionStatus !== 'connected') {
            throw new Error('WhatsApp not connected');
        }

        await sock.sendMessage(jid, { text });
        console.log(`[Sandwich] Message sent to JID: ${jid}`);
        return { success: true };

    } catch (error) {
        console.error('[Sandwich] Error sending message to JID:', error);
        return { success: false, error: error.message };
    }
}

async function sendMessage(phoneNumber, text) {
    try {
        if (!sock || connectionStatus !== 'connected') {
            throw new Error('WhatsApp not connected');
        }

        let jid = phoneToJid[phoneNumber];
        
        if (!jid) {
            jid = phoneNumber.includes('@') ? phoneNumber : `${phoneNumber}@s.whatsapp.net`;
        }
        
        await sock.sendMessage(jid, { text });
        console.log(`[Sandwich] Message sent to ${phoneNumber}`);
        return { success: true };

    } catch (error) {
        console.error('[Sandwich] Error sending message:', error);
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

app.post('/send-jid', async (req, res) => {
    const { jid, message } = req.body;
    
    if (!jid || !message) {
        return res.status(400).json({ success: false, error: 'jid and message required' });
    }
    
    console.log(`[Sandwich] Sending message to JID: ${jid}`);
    const result = await sendMessageToJid(jid, message);
    res.json(result);
});

app.get('/messages', (req, res) => {
    res.json({
        messages: pendingMessages.slice(-50),
        count: pendingMessages.length
    });
});

app.get('/conversations', (req, res) => {
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
    console.log(`[Sandwich] Bot paused for chat: ${phone_number}`);
    res.json({ success: true, paused: true, phone_number });
});

app.post('/resume-chat', (req, res) => {
    const { phone_number } = req.body;
    
    if (!phone_number) {
        return res.status(400).json({ success: false, error: 'phone_number required' });
    }
    
    pausedChats.delete(phone_number);
    console.log(`[Sandwich] Bot resumed for chat: ${phone_number}`);
    res.json({ success: true, paused: false, phone_number });
});

app.listen(PORT, () => {
    console.log(`[Sandwich] WhatsApp service running on port ${PORT}`);
    console.log(`[Sandwich] FastAPI URL: ${FASTAPI_URL}`);
    
    const authPath = path.join(__dirname, 'auth_info_sandwich');
    if (fs.existsSync(authPath) && fs.readdirSync(authPath).length > 0) {
        console.log('[Sandwich] Found existing auth, attempting to connect...');
        initWhatsApp();
    }
    
    // Setup order reminder check every 5 minutes
    const REMINDER_INTERVAL = 5 * 60 * 1000; // 5 minutes
    let wasOpen = false;
    
    setInterval(async () => {
        try {
            if (sock && sock.user) {
                // Check for pending order reminders
                console.log('[Sandwich] Checking for pending orders needing reminders...');
                const reminderResponse = await axios.post(`${FASTAPI_URL}/api/sandwich/send-reminders`, {}, { timeout: 30000 });
                if (reminderResponse.data.reminders_sent > 0) {
                    console.log(`[Sandwich] Sent ${reminderResponse.data.reminders_sent} order reminders`);
                }
                
                // Check if store just opened and process reservations
                const statusResponse = await axios.get(`${FASTAPI_URL}/api/sandwich/is-open`, { timeout: 10000 });
                const isOpen = statusResponse.data.is_open;
                
                if (isOpen && !wasOpen) {
                    console.log('[Sandwich] Store just opened! Processing pending reservations...');
                    const reservationsResponse = await axios.post(`${FASTAPI_URL}/api/sandwich/process-reservations`, {}, { timeout: 30000 });
                    if (reservationsResponse.data.reservations_processed > 0) {
                        console.log(`[Sandwich] Processed ${reservationsResponse.data.reservations_processed} reservations`);
                    }
                }
                wasOpen = isOpen;
            }
        } catch (error) {
            console.error('[Sandwich] Error in periodic check:', error.message);
        }
    }, REMINDER_INTERVAL);
    
    console.log('[Sandwich] Order reminder and reservation check enabled (every 5 minutes)');
});

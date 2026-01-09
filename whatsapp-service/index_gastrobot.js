/**
 * GastroBot SaaS - Multi-Tenant WhatsApp Service
 * Handles multiple WhatsApp connections, one per tenant (restaurant)
 */

const { makeWASocket, useMultiFileAuthState, DisconnectReason, fetchLatestBaileysVersion, makeCacheableSignalKeyStore } = require('@whiskeysockets/baileys');
const express = require('express');
const cors = require('cors');
const axios = require('axios');
const QRCode = require('qrcode');
const fs = require('fs');
const path = require('path');
const pino = require('pino');

const logger = pino({ level: 'silent' });

const app = express();
app.use(cors());
app.use(express.json());

const FASTAPI_URL = process.env.FASTAPI_URL || 'http://localhost:8001';
const PORT = process.env.GASTROBOT_PORT || 3004;

// Store for multiple tenant connections
const tenantSockets = {};       // tenantId -> socket
const tenantStatus = {};        // tenantId -> { status, user, qr, qrDataUrl }
const tenantPausedChats = {};   // tenantId -> Set of paused phone numbers
const tenantJidMap = {};        // tenantId -> { phoneNumber -> jid }

/**
 * Initialize WhatsApp connection for a specific tenant
 */
async function initTenantWhatsApp(tenantId, tenantName) {
    console.log(`[GastroBot] Initializing WhatsApp for tenant: ${tenantId} (${tenantName})`);
    
    try {
        const authPath = path.join(__dirname, 'auth_gastrobot', tenantId);
        
        if (!fs.existsSync(authPath)) {
            fs.mkdirSync(authPath, { recursive: true });
        }

        const { state, saveCreds } = await useMultiFileAuthState(authPath);
        const { version } = await fetchLatestBaileysVersion();

        // Initialize status
        tenantStatus[tenantId] = {
            status: 'connecting',
            user: null,
            qr: null,
            qrDataUrl: null,
            tenantName: tenantName
        };

        const sock = makeWASocket({
            version,
            logger,
            auth: {
                creds: state.creds,
                keys: makeCacheableSignalKeyStore(state.keys, logger)
            },
            printQRInTerminal: false,
            browser: [`GastroBot-${tenantId}`, 'Chrome', '1.0.0'],
            syncFullHistory: false,
            generateHighQualityLinkPreview: false
        });

        tenantSockets[tenantId] = sock;
        tenantPausedChats[tenantId] = new Set();
        tenantJidMap[tenantId] = {};

        sock.ev.on('connection.update', async (update) => {
            const { connection, lastDisconnect, qr } = update;

            if (qr) {
                console.log(`[GastroBot][${tenantId}] QR Code generated`);
                tenantStatus[tenantId].qr = qr;
                tenantStatus[tenantId].qrDataUrl = await QRCode.toDataURL(qr);
                tenantStatus[tenantId].status = 'awaiting_qr';
            }

            if (connection === 'close') {
                const statusCode = lastDisconnect?.error?.output?.statusCode;
                const shouldReconnect = statusCode !== DisconnectReason.loggedOut;
                
                console.log(`[GastroBot][${tenantId}] Connection closed. Reconnecting: ${shouldReconnect}`);
                
                tenantStatus[tenantId].status = 'disconnected';
                tenantStatus[tenantId].user = null;
                tenantStatus[tenantId].qr = null;
                tenantStatus[tenantId].qrDataUrl = null;

                // Update tenant in database
                await updateTenantConnectionStatus(tenantId, false);

                if (shouldReconnect) {
                    setTimeout(() => initTenantWhatsApp(tenantId, tenantName), 5000);
                } else {
                    try {
                        fs.rmSync(authPath, { recursive: true, force: true });
                        fs.mkdirSync(authPath, { recursive: true });
                    } catch (e) {
                        console.error(`[GastroBot][${tenantId}] Error clearing auth:`, e);
                    }
                    delete tenantSockets[tenantId];
                }
            } else if (connection === 'open') {
                console.log(`[GastroBot][${tenantId}] WhatsApp connected successfully`);
                tenantStatus[tenantId].status = 'connected';
                tenantStatus[tenantId].user = sock.user;
                tenantStatus[tenantId].qr = null;
                tenantStatus[tenantId].qrDataUrl = null;

                // Update tenant in database
                await updateTenantConnectionStatus(tenantId, true, sock.user?.id);
            }
        });

        sock.ev.on('messages.upsert', async ({ messages, type }) => {
            if (type === 'notify') {
                for (const message of messages) {
                    if (!message.key.fromMe && message.message) {
                        await handleIncomingMessage(tenantId, message);
                    }
                }
            }
        });

        sock.ev.on('creds.update', saveCreds);

    } catch (error) {
        console.error(`[GastroBot][${tenantId}] Initialization error:`, error);
        tenantStatus[tenantId] = {
            status: 'error',
            error: error.message,
            user: null,
            qr: null,
            qrDataUrl: null
        };
        setTimeout(() => initTenantWhatsApp(tenantId, tenantName), 10000);
    }
}

/**
 * Update tenant connection status in MongoDB
 */
async function updateTenantConnectionStatus(tenantId, connected, whatsappNumber = '') {
    try {
        await axios.put(`${FASTAPI_URL}/api/gastrobot/tenants/${tenantId}`, {
            whatsapp_connected: connected,
            whatsapp_number: whatsappNumber
        });
    } catch (error) {
        console.error(`[GastroBot][${tenantId}] Error updating connection status:`, error.message);
    }
}

/**
 * Handle incoming message for a specific tenant
 */
async function handleIncomingMessage(tenantId, message) {
    try {
        const remoteJid = message.key.remoteJid;
        
        // Skip group messages
        if (remoteJid.endsWith('@g.us')) {
            return;
        }
        
        let phoneNumber = null;
        
        if (remoteJid.endsWith('@s.whatsapp.net')) {
            phoneNumber = remoteJid.replace('@s.whatsapp.net', '');
        } else if (remoteJid.includes('@lid')) {
            phoneNumber = remoteJid.replace('@lid', '');
        }
        
        // Store JID mapping
        if (!tenantJidMap[tenantId]) tenantJidMap[tenantId] = {};
        tenantJidMap[tenantId][phoneNumber] = remoteJid;
        
        console.log(`[GastroBot][${tenantId}] Message from: ${phoneNumber}`);

        // Extract message content
        let messageText = '';
        let location = null;
        
        if (message.message.locationMessage) {
            const loc = message.message.locationMessage;
            location = {
                latitude: loc.degreesLatitude,
                longitude: loc.degreesLongitude,
                name: loc.name || '',
                address: loc.address || ''
            };
            messageText = '📍 Ubicación compartida';
        } else if (message.message.liveLocationMessage) {
            const loc = message.message.liveLocationMessage;
            location = {
                latitude: loc.degreesLatitude,
                longitude: loc.degreesLongitude,
                name: 'Ubicación en vivo',
                address: ''
            };
            messageText = '📍 Ubicación en vivo compartida';
        } else if (message.message.conversation) {
            messageText = message.message.conversation;
        } else if (message.message.extendedTextMessage?.text) {
            messageText = message.message.extendedTextMessage.text;
        } else if (message.message.imageMessage?.caption) {
            messageText = message.message.imageMessage.caption;
        }

        if (!messageText && !location) {
            return;
        }

        // Check if bot is paused for this chat
        if (tenantPausedChats[tenantId]?.has(phoneNumber)) {
            console.log(`[GastroBot][${tenantId}] Bot paused for ${phoneNumber}`);
            return;
        }

        // Forward to GastroBot API
        try {
            const payload = {
                tenant_id: tenantId,
                phone_number: phoneNumber,
                message: messageText,
                push_name: message.pushName || ''
            };
            
            if (location) {
                payload.location = location;
            }
            
            const response = await axios.post(`${FASTAPI_URL}/api/gastrobot/message`, payload, { timeout: 30000 });

            if (response.data.reply) {
                // Natural delay before responding
                const delay = 1500 + Math.random() * 2000;
                await new Promise(resolve => setTimeout(resolve, delay));
                
                await sendMessageToTenant(tenantId, remoteJid, response.data.reply);
            }

        } catch (apiError) {
            console.error(`[GastroBot][${tenantId}] API error:`, apiError.message);
        }

    } catch (error) {
        console.error(`[GastroBot][${tenantId}] Message handling error:`, error);
    }
}

/**
 * Send message to a specific JID for a tenant
 */
async function sendMessageToTenant(tenantId, jid, text) {
    try {
        const sock = tenantSockets[tenantId];
        if (!sock || tenantStatus[tenantId]?.status !== 'connected') {
            throw new Error('WhatsApp not connected for tenant');
        }

        await sock.sendMessage(jid, { text });
        console.log(`[GastroBot][${tenantId}] Message sent to ${jid}`);
        return { success: true };

    } catch (error) {
        console.error(`[GastroBot][${tenantId}] Send error:`, error);
        return { success: false, error: error.message };
    }
}

/**
 * Send message by phone number for a tenant
 */
async function sendMessageByPhone(tenantId, phoneNumber, text) {
    try {
        let jid = tenantJidMap[tenantId]?.[phoneNumber];
        if (!jid) {
            jid = `${phoneNumber}@s.whatsapp.net`;
        }
        return await sendMessageToTenant(tenantId, jid, text);
    } catch (error) {
        return { success: false, error: error.message };
    }
}

/**
 * Disconnect a tenant's WhatsApp
 */
async function disconnectTenant(tenantId) {
    try {
        const sock = tenantSockets[tenantId];
        if (sock) {
            await sock.logout();
        }
        
        tenantStatus[tenantId] = {
            status: 'disconnected',
            user: null,
            qr: null,
            qrDataUrl: null
        };
        
        delete tenantSockets[tenantId];
        
        await updateTenantConnectionStatus(tenantId, false);
        
        return { success: true };
    } catch (error) {
        console.error(`[GastroBot][${tenantId}] Disconnect error:`, error);
        return { success: false, error: error.message };
    }
}

// ============ REST API ENDPOINTS ============

// Get all tenant statuses
app.get('/status', (req, res) => {
    const statuses = {};
    for (const [tenantId, status] of Object.entries(tenantStatus)) {
        statuses[tenantId] = {
            status: status.status,
            connected: status.status === 'connected',
            user: status.user ? {
                id: status.user.id,
                name: status.user.name
            } : null,
            tenantName: status.tenantName
        };
    }
    res.json({
        active_tenants: Object.keys(tenantSockets).length,
        tenants: statuses
    });
});

// Get specific tenant status
app.get('/tenant/:tenantId/status', (req, res) => {
    const { tenantId } = req.params;
    const status = tenantStatus[tenantId];
    
    if (!status) {
        return res.json({
            status: 'not_initialized',
            connected: false,
            user: null
        });
    }
    
    res.json({
        status: status.status,
        connected: status.status === 'connected',
        user: status.user ? {
            id: status.user.id,
            name: status.user.name
        } : null,
        tenantName: status.tenantName
    });
});

// Get QR code for tenant
app.get('/tenant/:tenantId/qr', (req, res) => {
    const { tenantId } = req.params;
    const status = tenantStatus[tenantId];
    
    res.json({
        qr: status?.qr || null,
        qr_data_url: status?.qrDataUrl || null,
        status: status?.status || 'not_initialized'
    });
});

// Initialize/Connect tenant WhatsApp
app.post('/tenant/:tenantId/connect', async (req, res) => {
    const { tenantId } = req.params;
    const { tenant_name } = req.body;
    
    if (tenantStatus[tenantId]?.status === 'connected') {
        return res.json({ success: true, message: 'Already connected' });
    }
    
    try {
        await initTenantWhatsApp(tenantId, tenant_name || tenantId);
        res.json({ success: true, message: 'Connection initiated' });
    } catch (error) {
        res.status(500).json({ success: false, error: error.message });
    }
});

// Disconnect tenant WhatsApp
app.post('/tenant/:tenantId/disconnect', async (req, res) => {
    const { tenantId } = req.params;
    const result = await disconnectTenant(tenantId);
    res.json(result);
});

// Send message for tenant
app.post('/tenant/:tenantId/send', async (req, res) => {
    const { tenantId } = req.params;
    const { phone_number, message } = req.body;
    
    if (!phone_number || !message) {
        return res.status(400).json({ success: false, error: 'phone_number and message required' });
    }
    
    const result = await sendMessageByPhone(tenantId, phone_number, message);
    res.json(result);
});

// Send message by JID for tenant
app.post('/tenant/:tenantId/send-jid', async (req, res) => {
    const { tenantId } = req.params;
    const { jid, message } = req.body;
    
    if (!jid || !message) {
        return res.status(400).json({ success: false, error: 'jid and message required' });
    }
    
    const result = await sendMessageToTenant(tenantId, jid, message);
    res.json(result);
});

// Pause bot for a chat
app.post('/tenant/:tenantId/pause-chat', (req, res) => {
    const { tenantId } = req.params;
    const { phone_number } = req.body;
    
    if (!phone_number) {
        return res.status(400).json({ success: false, error: 'phone_number required' });
    }
    
    if (!tenantPausedChats[tenantId]) {
        tenantPausedChats[tenantId] = new Set();
    }
    tenantPausedChats[tenantId].add(phone_number);
    
    console.log(`[GastroBot][${tenantId}] Bot paused for: ${phone_number}`);
    res.json({ success: true, paused: true, phone_number });
});

// Resume bot for a chat
app.post('/tenant/:tenantId/resume-chat', (req, res) => {
    const { tenantId } = req.params;
    const { phone_number } = req.body;
    
    if (!phone_number) {
        return res.status(400).json({ success: false, error: 'phone_number required' });
    }
    
    tenantPausedChats[tenantId]?.delete(phone_number);
    
    console.log(`[GastroBot][${tenantId}] Bot resumed for: ${phone_number}`);
    res.json({ success: true, paused: false, phone_number });
});

// Health check
app.get('/health', (req, res) => {
    res.json({ 
        status: 'healthy', 
        service: 'GastroBot WhatsApp Multi-Tenant',
        active_connections: Object.keys(tenantSockets).length
    });
});

// ============ AUTO-RECONNECT ON STARTUP ============

async function loadAndReconnectTenants() {
    try {
        console.log('[GastroBot] Loading active tenants from database...');
        
        const response = await axios.get(`${FASTAPI_URL}/api/gastrobot/tenants`);
        const tenants = response.data.tenants || [];
        
        for (const tenant of tenants) {
            if (tenant.estado_suscripcion === 'activo' && tenant.bot_activo) {
                const authPath = path.join(__dirname, 'auth_gastrobot', tenant.id);
                
                // Only auto-reconnect if we have saved auth
                if (fs.existsSync(authPath) && fs.readdirSync(authPath).length > 0) {
                    console.log(`[GastroBot] Auto-reconnecting tenant: ${tenant.id} (${tenant.nombre_negocio})`);
                    await initTenantWhatsApp(tenant.id, tenant.nombre_negocio);
                    
                    // Small delay between connections
                    await new Promise(resolve => setTimeout(resolve, 2000));
                }
            }
        }
        
        console.log('[GastroBot] Tenant reconnection complete');
        
    } catch (error) {
        console.error('[GastroBot] Error loading tenants:', error.message);
    }
}

// ============ START SERVER ============

app.listen(PORT, () => {
    console.log(`[GastroBot] Multi-tenant WhatsApp service running on port ${PORT}`);
    console.log(`[GastroBot] FastAPI URL: ${FASTAPI_URL}`);
    
    // Load and reconnect existing tenants after a short delay
    setTimeout(loadAndReconnectTenants, 3000);
});

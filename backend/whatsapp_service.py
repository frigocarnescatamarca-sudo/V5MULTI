"""
WhatsApp AI Bot Service for Estonia Cobertura
Handles message processing with ChatGPT integration
"""

import os
import httpx
from datetime import datetime, timezone
from motor.motor_asyncio import AsyncIOMotorClient
from emergentintegrations.llm.chat import LlmChat

# MongoDB connection
mongo_url = os.environ.get('MONGO_URL', 'mongodb://localhost:27017')
db_name = os.environ.get('DB_NAME', 'estonia_seguros')

client = AsyncIOMotorClient(mongo_url)
db = client[db_name]

# WhatsApp Node.js service URL
WHATSAPP_SERVICE_URL = os.environ.get('WHATSAPP_SERVICE_URL', 'http://localhost:3002')

# Default bot configuration
DEFAULT_BOT_CONFIG = {
    "mensaje_bienvenida": """¡Hola! 👋 Soy el asistente virtual de *Estonia Cobertura Colaborativa*.

Puedo ayudarte con:
📋 Información sobre coberturas vehiculares
💰 Cotización de tu cobertura
📝 Iniciar el proceso de contratación
❓ Resolver tus dudas

¿En qué puedo ayudarte hoy?""",
    
    "instrucciones_bot": """Eres el asistente virtual de Estonia Cobertura Colaborativa, una empresa argentina de coberturas vehiculares temporales.

INFORMACIÓN DE LA EMPRESA:
- Ofrecemos coberturas temporales (30 días) para vehículos
- Tipos de vehículos: Auto, Moto, Taxi/Remis, App (Uber/Didi)
- Tipos de cobertura: 
  * Responsabilidad Civil (RC): Cubre daños a terceros
  * Terceros Completo: RC + robo + incendio

PRECIOS (en pesos argentinos):
- Auto: RC $6,000 | Completo $9,000
- Moto: RC $5,000 | Completo $7,500  
- Taxi/Remis: RC $10,000 | Completo $18,000
- App (Uber/Didi): RC $6,000 | Completo $9,000

TU COMPORTAMIENTO:
1. Sé amable, profesional y conciso
2. Usa emojis de forma moderada para ser más amigable
3. Si el cliente quiere contratar, solicita estos datos en orden:
   - Nombre completo
   - DNI
   - Email
   - Teléfono
   - Patente del vehículo
   - Marca y modelo
   - Año del vehículo
   - Tipo de vehículo
   - Tipo de cobertura deseada
4. Cuando tengas todos los datos, crea un resumen y confirma con el cliente
5. Indica que el pago se realiza por MercadoPago o transferencia
6. Si hay dudas que no puedas resolver, indica que un agente humano se comunicará pronto

DATOS BANCARIOS PARA TRANSFERENCIA:
{datos_bancarios}

IMPORTANTE:
- NO inventes información sobre coberturas que no existen
- NO des precios diferentes a los listados
- Siempre confirma la información antes de procesar""",

    "datos_bancarios": "CVU/Alias: A configurar por el administrador",
    "bot_activo": True
}


async def get_bot_config():
    """Get bot configuration from database or return defaults"""
    config = await db.whatsapp_config.find_one({"_id": "bot_config"})
    if not config:
        # Create default config
        default = {**DEFAULT_BOT_CONFIG, "_id": "bot_config"}
        await db.whatsapp_config.insert_one(default)
        return DEFAULT_BOT_CONFIG
    
    # Remove _id for clean return
    del config["_id"]
    return config


async def update_bot_config(config_data: dict):
    """Update bot configuration"""
    await db.whatsapp_config.update_one(
        {"_id": "bot_config"},
        {"$set": config_data},
        upsert=True
    )
    return await get_bot_config()


async def get_conversation_history(phone_number: str, limit: int = 10):
    """Get recent conversation history for a phone number"""
    messages = await db.whatsapp_messages.find(
        {"phone_number": phone_number}
    ).sort("timestamp", -1).limit(limit).to_list(limit)
    
    # Reverse to get chronological order
    return list(reversed(messages))


async def save_message(phone_number: str, message: str, role: str, push_name: str = ""):
    """Save a message to the database"""
    doc = {
        "phone_number": phone_number,
        "message": message,
        "role": role,  # "user" or "assistant"
        "push_name": push_name,
        "timestamp": datetime.now(timezone.utc).isoformat()
    }
    await db.whatsapp_messages.insert_one(doc)
    return doc


async def process_message_with_ai(phone_number: str, message: str, push_name: str = ""):
    """Process incoming message with ChatGPT and return response"""
    
    # Get bot config
    config = await get_bot_config()
    
    if not config.get("bot_activo", True):
        return None  # Bot is disabled globally
    
    # Save incoming message
    await save_message(phone_number, message, "user", push_name)
    
    # Get conversation history
    history = await get_conversation_history(phone_number, limit=10)
    
    # Build system prompt with instructions
    instrucciones = config.get("instrucciones_bot", DEFAULT_BOT_CONFIG["instrucciones_bot"])
    datos_bancarios = config.get("datos_bancarios", DEFAULT_BOT_CONFIG["datos_bancarios"])
    system_prompt = instrucciones.replace("{datos_bancarios}", datos_bancarios)
    
    # Build messages for ChatGPT
    messages = [
        {"role": "system", "content": system_prompt}
    ]
    
    # Check if this is a new conversation (first message or no recent history)
    is_new_conversation = len(history) <= 1
    
    # Add welcome context if new conversation
    if is_new_conversation:
        welcome_msg = config.get("mensaje_bienvenida", DEFAULT_BOT_CONFIG["mensaje_bienvenida"])
        messages.append({
            "role": "assistant",
            "content": welcome_msg
        })
    
    # Add conversation history
    for msg in history:
        role = msg.get("role", "user")
        content = msg.get("message", "")
        if content:
            messages.append({"role": role, "content": content})
    
    # Add current message if not already in history
    if not history or history[-1].get("message") != message:
        messages.append({"role": "user", "content": message})
    
    try:
        # Get Emergent LLM Key
        llm_key = os.environ.get('EMERGENT_LLM_KEY')
        if not llm_key:
            raise ValueError("EMERGENT_LLM_KEY not configured")
        
        # Call ChatGPT via emergentintegrations
        response = await chat(
            api_key=llm_key,
            model=LlmModel.GPT_4O_MINI,
            messages=messages
        )
        
        ai_response = response.message if hasattr(response, 'message') else str(response)
        
        # Save AI response
        await save_message(phone_number, ai_response, "assistant")
        
        return ai_response
        
    except Exception as e:
        print(f"Error processing message with AI: {e}")
        # Return a fallback message
        fallback = "Disculpa, estoy teniendo dificultades técnicas. Un agente se comunicará contigo pronto. 🙏"
        await save_message(phone_number, fallback, "assistant")
        return fallback


async def send_whatsapp_message(phone_number: str, message: str):
    """Send a message via WhatsApp service"""
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{WHATSAPP_SERVICE_URL}/send",
                json={"phone_number": phone_number, "message": message},
                timeout=30.0
            )
            return response.json()
    except Exception as e:
        print(f"Error sending WhatsApp message: {e}")
        return {"success": False, "error": str(e)}


async def get_whatsapp_status():
    """Get WhatsApp connection status"""
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{WHATSAPP_SERVICE_URL}/status", timeout=10.0)
            return response.json()
    except Exception as e:
        return {"status": "error", "connected": False, "error": str(e)}


async def get_whatsapp_qr():
    """Get WhatsApp QR code"""
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{WHATSAPP_SERVICE_URL}/qr", timeout=10.0)
            return response.json()
    except Exception as e:
        return {"qr": None, "qr_data_url": None, "error": str(e)}


async def connect_whatsapp():
    """Initiate WhatsApp connection"""
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(f"{WHATSAPP_SERVICE_URL}/connect", timeout=10.0)
            return response.json()
    except Exception as e:
        return {"success": False, "error": str(e)}


async def disconnect_whatsapp():
    """Disconnect WhatsApp"""
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(f"{WHATSAPP_SERVICE_URL}/disconnect", timeout=10.0)
            return response.json()
    except Exception as e:
        return {"success": False, "error": str(e)}


async def get_conversations():
    """Get all conversations from WhatsApp service"""
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{WHATSAPP_SERVICE_URL}/conversations", timeout=10.0)
            return response.json()
    except Exception as e:
        return {"conversations": [], "error": str(e)}


async def pause_chat(phone_number: str):
    """Pause bot for a specific chat"""
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{WHATSAPP_SERVICE_URL}/pause-chat",
                json={"phone_number": phone_number},
                timeout=10.0
            )
            return response.json()
    except Exception as e:
        return {"success": False, "error": str(e)}


async def resume_chat(phone_number: str):
    """Resume bot for a specific chat"""
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{WHATSAPP_SERVICE_URL}/resume-chat",
                json={"phone_number": phone_number},
                timeout=10.0
            )
            return response.json()
    except Exception as e:
        return {"success": False, "error": str(e)}


async def get_chat_history(phone_number: str, limit: int = 50):
    """Get chat history from database for a specific number"""
    messages = await db.whatsapp_messages.find(
        {"phone_number": phone_number},
        {"_id": 0}
    ).sort("timestamp", -1).limit(limit).to_list(limit)
    
    return list(reversed(messages))


async def create_pending_coverage(phone_number: str, data: dict):
    """Create a pending coverage from WhatsApp conversation"""
    from uuid import uuid4
    from datetime import timedelta
    
    coverage_id = str(uuid4())
    numero_recibo = str(uuid4())[:8].upper()
    fecha_inicio = datetime.now(timezone.utc)
    fecha_fin = fecha_inicio + timedelta(days=30)
    
    # Calculate price
    PRICING = {
        "auto": {"rc": 6000, "completo": 9000},
        "moto": {"rc": 5000, "completo": 7500},
        "taxi": {"rc": 10000, "completo": 18000},
        "app": {"rc": 6000, "completo": 9000}
    }
    
    tipo_vehiculo = data.get("tipo_vehiculo", "auto")
    cobertura = data.get("cobertura", "rc")
    precio = PRICING.get(tipo_vehiculo, {}).get(cobertura, 6000)
    
    coverage_doc = {
        "_id": coverage_id,
        "numero_recibo": numero_recibo,
        "dni": data.get("dni", ""),
        "nombre": data.get("nombre", ""),
        "email": data.get("email", ""),
        "telefono": phone_number,
        "patente": data.get("patente", ""),
        "marca": data.get("marca", ""),
        "modelo": data.get("modelo", ""),
        "ano": data.get("ano", datetime.now().year),
        "tipo_vehiculo": tipo_vehiculo,
        "cobertura": cobertura,
        "precio_original": precio,
        "precio_final": precio,
        "estado": "pendiente_pago",
        "vigencia_desde": fecha_inicio.isoformat(),
        "vigencia_hasta": fecha_fin.isoformat(),
        "origen": "whatsapp",
        "whatsapp_phone": phone_number,
        "created_at": fecha_inicio.isoformat()
    }
    
    await db.seguros.insert_one(coverage_doc)
    return coverage_doc

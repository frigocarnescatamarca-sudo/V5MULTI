"""
WhatsApp AI Bot Service for Estonia Cobertura
Handles message processing with ChatGPT integration
"""

import os
import httpx
from datetime import datetime, timezone, timedelta
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

from motor.motor_asyncio import AsyncIOMotorClient
from emergentintegrations.llm.chat import LlmChat, UserMessage

# MongoDB connection
mongo_url = os.environ.get('MONGO_URL', 'mongodb://localhost:27017')
db_name = os.environ.get('DB_NAME', 'estonia_seguros')

client = AsyncIOMotorClient(mongo_url)
db = client[db_name]

# WhatsApp Node.js service URL
WHATSAPP_SERVICE_URL = os.environ.get('WHATSAPP_SERVICE_URL', 'http://localhost:3002')

# Default bot configuration
DEFAULT_BOT_CONFIG = {
    "mensaje_bienvenida": """¡Hola! 👋 Soy el asistente de ventas de *Estonia Cobertura Colaborativa*.

🚗 Ofrecemos coberturas vehiculares temporales (30 días) para:
• Autos • Motos • Taxis/Remis • Apps (Uber/Didi)

💰 *Precios desde $5,000*

¿Querés cotizar una cobertura? Contame qué tipo de vehículo tenés.""",
    
    "instrucciones_bot": """Sos el asistente de ventas de Estonia Cobertura Colaborativa. Tu objetivo es vender coberturas vehiculares y recopilar los datos necesarios para generar la póliza.

=== INFORMACIÓN DE PRODUCTOS ===
Coberturas temporales de 30 días para vehículos.

TIPOS DE COBERTURA:
• RC (Responsabilidad Civil): Cubre daños a terceros
• Terceros Completo: RC + robo + incendio

PRECIOS FIJOS (NO NEGOCIABLES):
| Vehículo     | RC      | Completo |
|--------------|---------|----------|
| Auto         | $6,000  | $9,000   |
| Moto         | $3,500  | $5,500   |
| Taxi/Remis   | $10,000 | $18,000  |
| App (Uber)   | $6,000  | $9,000   |

=== TU PERSONALIDAD ===
- Sos argentino, usá "vos" en lugar de "tú"
- Sé amable pero directo, no des vueltas
- Usá emojis con moderación (1-2 por mensaje)
- Respuestas cortas y claras

=== FLUJO DE VENTA ===

PASO 1 - IDENTIFICAR NECESIDAD:
Preguntá qué tipo de vehículo tiene (auto, moto, taxi, app)

PASO 2 - OFRECER OPCIONES:
Mostrá los 2 tipos de cobertura con precios para su vehículo.
Ejemplo: "Para tu auto tenés:
• RC (daños a terceros): $6,000
• Completo (RC + robo + incendio): $9,000
¿Cuál preferís?"

PASO 3 - RECOPILAR DATOS:
Una vez que elija la cobertura, pedí TODOS los datos juntos en un solo mensaje:
"¡Genial! Para generar tu cobertura necesito estos datos:

📝 *Enviame en un mensaje:*
1. Nombre completo (como figura en tu DNI)
2. DNI (sin puntos)
3. Email
4. Patente del vehículo
5. Marca y modelo (ej: Toyota Corolla, Honda Wave, Ford Ka)
6. Año del vehículo (ej: 2020)

Ejemplo:
Juan Carlos Pérez
12345678
juan@email.com
ABC123
Toyota Corolla
2020"

IMPORTANTE: 
- No pidas los datos uno por uno, pedilos todos juntos.
- Siempre aclarás que "modelo" es el NOMBRE del vehículo (Corolla, Onix, Wave), NO el año.
- Siempre pedí el nombre completo como figura en el DNI, no uses el nombre de WhatsApp.

PASO 4 - CONFIRMAR:
Cuando tengas TODOS los datos, mostrá un resumen:
"📋 *RESUMEN DE TU COBERTURA*
👤 Titular: [nombre]
📄 DNI: [dni]
🚗 Vehículo: [marca modelo año]
🔢 Patente: [patente]
📧 Email: [email]
📋 Cobertura: [tipo]
💰 Precio: $[precio]
⏰ Vigencia: 30 días

¿Confirmás los datos? Respondé *SÍ* para continuar."

PASO 5 - PAGO:
Si confirma, indicá:
"✅ ¡Perfecto! Para activar tu cobertura, realizá el pago de $[precio]:

💳 *Por transferencia:*
{datos_bancarios}

📱 *Por MercadoPago:* Te envío el link de pago

Una vez que pagues, enviame el comprobante y activo tu cobertura al instante."

=== REGLAS ESTRICTAS ===
- NUNCA inventes precios diferentes
- NUNCA ofrezcas productos que no existen
- NUNCA des información falsa sobre coberturas
- Si no sabés algo, decí "Voy a consultar con un agente y te respondo"
- Si el cliente pregunta algo fuera de tema, redirigí a la venta

=== PALABRAS PROHIBIDAS ===
NUNCA uses estas palabras:
- seguro / seguros
- aseguradora
- póliza
- prima
- indemnización

SIEMPRE usá estos términos:
- cobertura
- certificado
- activación
- circular
- fondo solidario (solo si preguntan)

=== TÉCNICAS DE VENTA (OBLIGATORIO) ===

ESTILO DE COMUNICACIÓN:
- Mensajes CORTOS
- Lenguaje SIMPLE
- Tono SEGURO y DIRECTO
- Evitar explicaciones innecesarias
- Priorizar preguntas que avancen la venta
- No educar. No justificar. No debatir.

COMPORTAMIENTO COMERCIAL:

1) Siempre confirmar utilidad:
Después de responder precio o cobertura, agregar:
"Sirve sin problema para eso 👍"

2) Activar urgencia suave:
Luego de informar, sumar siempre:
"¿Lo necesitás para activarlo hoy?"

3) Reducción de dudas:
Si el usuario duda o hace preguntas amplias, responder breve y volver al cierre:
"La mayoría lo contrata para poder circular y trabajar tranquilo."
Luego: "¿Lo activamos ahora?"

4) Cuando el usuario acepta:
Reforzar seguridad: "Genial 👍 lo activamos en el momento."
Luego continuar con el proceso de datos.

FRASE DE REFUERZO (usar cuando sea coherente):
"Te queda el certificado listo para circular."

RESULTADO: Conversaciones más cortas, menos idas y vueltas, más activaciones.

=== DERIVACIÓN A HUMANO ===
Si el cliente pide hablar con una persona/humano/asesor:
- Respondé: "Un momento, te comunico con un asesor 👤"
- El sistema notificará al administrador automáticamente.

=== DATOS BANCARIOS ===
{datos_bancarios}""",

    "datos_bancarios": "CBU/Alias: A configurar por el administrador",
    "whatsapp_ventas": "",
    "admin_lid": "",
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


async def is_chat_paused(phone_number: str) -> bool:
    """Check if a chat is paused for human attention"""
    paused = await db.whatsapp_paused.find_one({"phone_number": phone_number})
    return paused is not None


async def pause_chat(phone_number: str, admin_phone: str):
    """Pause bot for a specific chat - human will attend"""
    await db.whatsapp_paused.update_one(
        {"phone_number": phone_number},
        {"$set": {
            "phone_number": phone_number,
            "paused_by": admin_phone,
            "paused_at": datetime.now(timezone.utc).isoformat()
        }},
        upsert=True
    )


async def resume_chat(phone_number: str):
    """Resume bot for a specific chat"""
    await db.whatsapp_paused.delete_one({"phone_number": phone_number})


async def get_paused_chats():
    """Get list of all paused chats"""
    paused = await db.whatsapp_paused.find({}, {"_id": 0}).to_list(100)
    return paused


async def notify_admin_human_request(client_phone: str, client_name: str = ""):
    """Notify admin that a client wants human attention"""
    config = await get_bot_config()
    admin_number = config.get('numero_admin', '')
    admin_lid = config.get('admin_lid', '')
    
    if not admin_number and not admin_lid:
        print("[WhatsApp Bot] No admin configured for human request notification")
        return
    
    # Build notification message
    name_text = f"👤 Nombre: {client_name}\n" if client_name else ""
    notification = f"""🔔 *CLIENTE SOLICITA ATENCIÓN HUMANA*

📱 Número: {client_phone}
{name_text}
Para atenderlo manualmente, escribí:
*PAUSAR {client_phone}*

Cuando termines, escribí:
*REANUDAR {client_phone}*"""
    
    try:
        # Try to send to admin
        if admin_lid:
            await send_whatsapp_message_to_jid(f"{admin_lid}@lid", notification)
        elif admin_number:
            await send_whatsapp_message(admin_number, notification)
        print(f"[WhatsApp Bot] Notified admin about human request from {client_phone}")
    except Exception as e:
        print(f"[WhatsApp Bot] Error notifying admin: {e}")


async def get_client_memory(phone_number: str):
    """Get stored client information from memory"""
    client = await db.whatsapp_clients.find_one({"phone_number": phone_number}, {"_id": 0})
    return client


async def save_client_memory(phone_number: str, data: dict):
    """Save or update client information in memory"""
    await db.whatsapp_clients.update_one(
        {"phone_number": phone_number},
        {"$set": {**data, "phone_number": phone_number, "updated_at": datetime.now(timezone.utc).isoformat()}},
        upsert=True
    )


async def update_conversation_activity(phone_number: str, has_client_response: bool = True):
    """Update last activity timestamp for a conversation"""
    update_data = {
        "last_activity": datetime.now(timezone.utc).isoformat(),
        "status": "active"
    }
    if has_client_response:
        update_data["last_client_message"] = datetime.now(timezone.utc).isoformat()
        update_data["followup_sent"] = False
    
    await db.whatsapp_conversations.update_one(
        {"phone_number": phone_number},
        {"$set": update_data},
        upsert=True
    )


async def get_inactive_conversations(minutes: int = 10):
    """Get conversations that have been inactive for X minutes"""
    cutoff_time = (datetime.now(timezone.utc) - timedelta(minutes=minutes)).isoformat()
    
    inactive = await db.whatsapp_conversations.find({
        "status": "active",
        "followup_sent": {"$ne": True},
        "last_client_message": {"$lt": cutoff_time}
    }).to_list(100)
    
    return inactive


async def send_followup_messages():
    """Send followup messages to inactive conversations"""
    inactive = await get_inactive_conversations(minutes=10)
    
    for conv in inactive:
        phone = conv.get('phone_number')
        
        # Get client memory to personalize
        client = await get_client_memory(phone)
        client_name = client.get('nombre', '') if client else ''
        
        if client_name:
            farewell_msg = f"""👋 ¡Hola {client_name}! 

Noté que no pudimos terminar. Si tenés alguna duda o querés continuar con tu cobertura, escribime cuando puedas.

¡Te espero! 🚗"""
        else:
            farewell_msg = """👋 ¡Hola! 

Noté que no pudimos terminar la conversación. Si tenés alguna duda o querés continuar con tu cobertura, escribime cuando puedas.

¡Te espero! 🚗"""
        
        try:
            # Try to get JID
            jid_mapping = await db.whatsapp_jid_mapping.find_one({"phone_number": phone})
            if jid_mapping and jid_mapping.get('jid'):
                await send_whatsapp_message_to_jid(jid_mapping['jid'], farewell_msg)
            else:
                await send_whatsapp_message(phone, farewell_msg)
            
            # Mark as followup sent and conversation ended
            await db.whatsapp_conversations.update_one(
                {"phone_number": phone},
                {"$set": {"followup_sent": True, "status": "ended"}}
            )
            
            # Save the farewell message
            await save_message(phone, farewell_msg, "assistant")
            
            print(f"[WhatsApp Bot] Sent followup to {phone}")
        except Exception as e:
            print(f"[WhatsApp Bot] Error sending followup to {phone}: {e}")


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


async def check_coverages_by_dni(dni: str):
    """Check coverages for a DNI and return formatted response for WhatsApp"""
    try:
        # Clean DNI - remove dots and spaces
        dni_clean = dni.replace('.', '').replace(' ', '').strip()
        
        # Query coverages by DNI
        coberturas = await db.seguros.find(
            {"dni": dni_clean},
            {"_id": 0}
        ).sort("created_at", -1).to_list(100)
        
        if not coberturas:
            return f"""🔍 *Consulta de Coberturas*

No encontré coberturas registradas para el DNI *{dni_clean}*.

¿Querés contratar una cobertura? Contame qué tipo de vehículo tenés 🚗"""
        
        # Build response
        response = f"""🔍 *Coberturas para DNI {dni_clean}*

Encontré *{len(coberturas)}* cobertura(s):

"""
        backend_url = os.environ.get('REACT_APP_BACKEND_URL', 'https://autocare-12.preview.emergentagent.com')
        
        for i, cob in enumerate(coberturas, 1):
            estado = cob.get('estado', 'desconocido')
            estado_emoji = '✅' if estado in ['pagado', 'gratis'] else '⏳' if estado == 'pendiente_pago' else '❌'
            
            # Check if expired
            vigencia_hasta = cob.get('vigencia_hasta', '')
            if vigencia_hasta:
                try:
                    fecha_fin = datetime.fromisoformat(vigencia_hasta)
                    if fecha_fin < datetime.now(timezone.utc):
                        estado_emoji = '⛔'
                        estado = 'vencida'
                except:
                    pass
            
            cobertura_tipo = 'Terceros Completo' if cob.get('cobertura') == 'completo' else 'Responsabilidad Civil'
            
            response += f"""*{i}. {cob.get('patente', 'N/A')}* {estado_emoji}
   📋 Recibo: {cob.get('numero_recibo', 'N/A')}
   🚗 {cob.get('marca', '')} {cob.get('modelo', '')} ({cob.get('ano', '')})
   📄 {cobertura_tipo}
   📅 Vigencia: {cob.get('vigencia_desde', '')[:10]} al {vigencia_hasta[:10] if vigencia_hasta else 'N/A'}
   💰 ${cob.get('precio_final', 0):,}
   Estado: *{estado.upper()}*

"""
            # Add verification link for paid coverages
            if estado in ['pagado', 'gratis']:
                response += f"   🔗 Verificar: {backend_url}/verificar/{cob.get('numero_recibo')}\n\n"
        
        response += """---
Para más detalles, visitá nuestro portal web o escribime tu consulta."""
        
        return response
        
    except Exception as e:
        print(f"[WhatsApp Bot] Error checking coverages by DNI: {e}")
        return None


async def admin_confirm_payment(recibo: str, admin_phone: str):
    """Admin confirms a payment - sends confirmation to client"""
    try:
        # Find the coverage by recibo
        coverage = await db.seguros.find_one({"numero_recibo": recibo})
        
        if not coverage:
            return f"❌ No encontré la cobertura con recibo {recibo}"
        
        if coverage.get('estado') == 'pagado':
            return f"⚠️ La cobertura {recibo} ya está marcada como PAGADA"
        
        # Find pending record to get client phone
        pending = await db.whatsapp_pending.find_one({"coverage_id": coverage['_id']})
        client_phone = pending.get('client_phone') if pending else coverage.get('whatsapp_phone')
        
        # Also try telefono field
        if not client_phone:
            client_phone = coverage.get('telefono')
        
        # Also try whatsapp_jid directly
        client_jid = coverage.get('whatsapp_jid')
        
        # Mark as paid regardless of phone availability
        await db.seguros.update_one(
            {"_id": coverage['_id']},
            {"$set": {
                "estado": "pagado",
                "fecha_pago": datetime.now(timezone.utc).isoformat(),
                "confirmado_por": admin_phone
            }}
        )
        
        # Get updated coverage
        coverage = await db.seguros.find_one({"_id": coverage['_id']})
        
        backend_url = os.environ.get('REACT_APP_BACKEND_URL', 'https://autocare-12.preview.emergentagent.com')
        
        # Try to send confirmation to client if we have contact info
        client_notified = False
        
        if client_phone or client_jid:
            # Get the correct JID for the client if not already have it
            if not client_jid and client_phone:
                jid_mapping = await db.whatsapp_jid_mapping.find_one({"phone_number": client_phone})
                client_jid = jid_mapping.get('jid') if jid_mapping else None
            
            # Send confirmation to CLIENT
            client_msg = f"""✅ *¡PAGO CONFIRMADO!*

🎉 Tu cobertura está *ACTIVA*

📋 *Recibo:* {coverage['numero_recibo']}
👤 *Titular:* {coverage['nombre']}
🚗 *Vehículo:* {coverage['marca']} {coverage['modelo']}
🔢 *Patente:* {coverage['patente']}
📅 *Vigencia:* {coverage['vigencia_desde'][:10]} al {coverage['vigencia_hasta'][:10]}

📥 *Descargá tus comprobantes:*
• PDF: {backend_url}/api/seguros/{coverage['_id']}/comprobante/pdf
• Imagen: {backend_url}/api/seguros/{coverage['_id']}/comprobante/imagen

🔍 *Verificar cobertura online:*
{backend_url}/verificar/{coverage['numero_recibo']}

¡Gracias por confiar en Estonia Cobertura! 🙏"""
            
            try:
                # Use JID if available, otherwise try phone
                if client_jid:
                    print(f"[WhatsApp Bot] Sending to client using JID: {client_jid}")
                    await send_whatsapp_message_to_jid(client_jid, client_msg)
                    client_notified = True
                elif client_phone:
                    print(f"[WhatsApp Bot] No JID found, trying phone: {client_phone}")
                    await send_whatsapp_message(client_phone, client_msg)
                    client_notified = True
            except Exception as send_error:
                print(f"[WhatsApp Bot] Error sending to client: {send_error}")
        
        # Clean up pending
        if pending:
            await db.whatsapp_pending.delete_one({"_id": pending['_id']})
        
        print(f"[WhatsApp Bot] Payment confirmed by admin for {recibo}, client_notified={client_notified}")
        
        # Confirm to admin
        if client_notified:
            return f"""✅ *PAGO CONFIRMADO*

Cobertura {recibo} activada.
Se enviaron los comprobantes al cliente.

👤 {coverage['nombre']}
🚗 {coverage['marca']} {coverage['modelo']}
💰 ${coverage['precio_final']:,}"""
        else:
            return f"""✅ *PAGO CONFIRMADO*

Cobertura {recibo} activada.
⚠️ No se pudo notificar al cliente (sin WhatsApp registrado).

👤 {coverage['nombre']}
🚗 {coverage['marca']} {coverage['modelo']}
💰 ${coverage['precio_final']:,}

📥 Comprobantes:
• {backend_url}/verificar/{coverage['numero_recibo']}"""
        
    except Exception as e:
        print(f"[WhatsApp Bot] Error in admin_confirm_payment: {e}")
        import traceback
        traceback.print_exc()
        return f"❌ Error al confirmar pago: {str(e)}"


async def process_message_with_ai(phone_number: str, message: str, push_name: str = ""):
    """Process incoming message with ChatGPT and return response"""
    import re
    
    # Get bot config
    config = await get_bot_config()
    
    if not config.get("bot_activo", True):
        return None  # Bot is disabled globally
    
    # Normalize phone number for comparison (remove any non-digits)
    def normalize_phone(phone):
        if not phone:
            return ""
        return ''.join(filter(str.isdigit, str(phone)))[-10:]  # Last 10 digits
    
    # Check if this is the ADMIN confirming a payment
    admin_number = config.get('numero_admin', '')
    admin_lid = config.get('admin_lid', '')  # LID stored when admin is identified
    normalized_admin = normalize_phone(admin_number)
    normalized_phone = normalize_phone(phone_number)
    
    # Extract just the number part from phone_number (could be LID like "122441598795892" or phone like "5491123456789")
    phone_digits = ''.join(filter(str.isdigit, str(phone_number)))
    
    print(f"[WhatsApp Bot] Checking admin: incoming_phone={phone_number}, phone_digits={phone_digits}")
    print(f"[WhatsApp Bot] Admin config: numero_admin={admin_number}, admin_lid={admin_lid}")
    
    # Check if admin by multiple methods:
    # 1. By LID match (if we have the admin's LID stored)
    # 2. By phone number match (normalized)
    is_admin = False
    
    # Method 1: Check by stored LID
    if admin_lid and phone_digits:
        if phone_digits == admin_lid or phone_number == admin_lid:
            is_admin = True
            print(f"[WhatsApp Bot] Admin matched by LID: {admin_lid}")
    
    # Method 2: Check by phone number
    if not is_admin and normalized_admin and normalized_phone:
        if (normalized_phone == normalized_admin or
            normalized_phone.endswith(normalized_admin) or
            normalized_admin.endswith(normalized_phone)):
            is_admin = True
            print(f"[WhatsApp Bot] Admin matched by phone number")
            # Save this LID for future reference if it looks like a LID (long number without country code pattern)
            if len(phone_digits) > 12 and not admin_lid:
                await db.whatsapp_config.update_one(
                    {"_id": "bot_config"},
                    {"$set": {"admin_lid": phone_digits}}
                )
                print(f"[WhatsApp Bot] Saved admin LID for future: {phone_digits}")
    
    # Method 3: If incoming is a LID-like number, check against JID mapping
    if not is_admin and admin_number:
        # Check if we have a JID mapping for the admin number
        admin_mapping = await db.whatsapp_jid_mapping.find_one({"phone_number": admin_number})
        if admin_mapping:
            admin_jid = admin_mapping.get('jid', '')
            # Extract number from JID
            admin_jid_number = ''.join(filter(str.isdigit, admin_jid.split('@')[0] if '@' in admin_jid else admin_jid))
            if phone_digits == admin_jid_number:
                is_admin = True
                print(f"[WhatsApp Bot] Admin matched by JID mapping")
    
    if is_admin:
        print(f"[WhatsApp Bot] ✅ ADMIN DETECTED! Message: {message[:50]}")
        
        # Check for CONFIRMAR command from admin
        confirm_match = re.match(r'(?:CONFIRMAR|confirmar|Confirmar)\s+([A-Za-z0-9]+)', message.strip())
        if confirm_match:
            recibo = confirm_match.group(1).upper()
            print(f"[WhatsApp Bot] Admin confirming payment for recibo: {recibo}")
            result = await admin_confirm_payment(recibo, phone_number)
            return result
        
        # Check for other admin commands or just greeting
        message_lower = message.lower().strip()
        
        # If admin says hi or asks something general, respond as admin
        if message_lower in ['hola', 'hi', 'hey', 'buenas', 'buen dia', 'buenos dias', 'buenas tardes', 'buenas noches']:
            # Get pending count
            pending_count = await db.seguros.count_documents({"estado": "pendiente_pago"})
            return f"""👋 *¡Hola Admin!*

Te reconozco como administrador. 

📊 *Coberturas pendientes:* {pending_count}

📋 *Comandos disponibles:*
• *CONFIRMAR [RECIBO]* - Confirma un pago
• *ESTADO* - Ver coberturas pendientes

Ejemplo: CONFIRMAR ABC123"""
        
        if message_lower == 'estado':
            # Show pending coverages
            pending = await db.seguros.find({"estado": "pendiente_pago"}).to_list(10)
            if pending:
                msg = "📊 *Coberturas pendientes de pago:*\n\n"
                for p in pending:
                    msg += f"• *{p['numero_recibo']}* - {p['nombre']} - ${p['precio_final']:,}\n"
                msg += f"\nPara confirmar: *CONFIRMAR [RECIBO]*"
                return msg
            else:
                return "✅ No hay coberturas pendientes de pago"
        
        # If admin writes something else, don't treat as client - just acknowledge
        if not confirm_match:
            return f"👋 Hola Admin. Para confirmar un pago escribí:\n*CONFIRMAR [NÚMERO DE RECIBO]*\n\nPara ver pendientes: *ESTADO*"
    else:
        print(f"[WhatsApp Bot] Not admin, treating as client")
    
    # Save incoming message
    await save_message(phone_number, message, "user", push_name)
    
    # Update conversation activity (client responded)
    await update_conversation_activity(phone_number, has_client_response=True)
    
    # Get client memory (stored name, previous interactions)
    # NOTE: Do NOT use push_name as client name - always ask for real name
    client_memory = await get_client_memory(phone_number)
    
    # Check if user explicitly wants to check existing coverages
    message_lower = message.lower().strip()
    check_keywords = ['consultar cobertura', 'ver mi cobertura', 'mis coberturas', 'tengo cobertura', 'estado de mi cobertura', 'verificar cobertura']
    wants_to_check = any(keyword in message_lower for keyword in check_keywords)
    
    # Only check DNI for coverages if user explicitly asks to check
    if wants_to_check:
        # Extract DNI from message if present
        clean_message = message.strip().replace('.', '').replace(' ', '')
        dni_match = ''.join(filter(str.isdigit, message))
        if dni_match and 7 <= len(dni_match) <= 8:
            dni_response = await check_coverages_by_dni(dni_match)
            if dni_response:
                await save_message(phone_number, dni_response, "assistant")
                return dni_response
    
    # Get conversation history
    history = await get_conversation_history(phone_number, limit=10)
    
    # Build system prompt with instructions
    instrucciones = config.get("instrucciones_bot", DEFAULT_BOT_CONFIG["instrucciones_bot"])
    datos_bancarios = config.get("datos_bancarios", DEFAULT_BOT_CONFIG["datos_bancarios"])
    system_prompt = instrucciones.replace("{datos_bancarios}", datos_bancarios)
    
    # Add client memory context to system prompt
    if client_memory:
        memory_context = "\n\n=== MEMORIA DEL CLIENTE ===\n"
        memory_context += f"Este cliente ya te escribió antes. Información guardada:\n"
        if client_memory.get('nombre'):
            memory_context += f"- Nombre: {client_memory['nombre']}\n"
        if client_memory.get('dni'):
            memory_context += f"- DNI: {client_memory['dni']}\n"
        if client_memory.get('email'):
            memory_context += f"- Email: {client_memory['email']}\n"
        if client_memory.get('vehiculo'):
            memory_context += f"- Vehículo anterior: {client_memory['vehiculo']}\n"
        memory_context += "\nSi el cliente ya dio su nombre, saludalo por su nombre. No le pidas datos que ya tenés."
        system_prompt += memory_context
    
    # Check if this is a new conversation (first message or no recent history)
    is_new_conversation = len(history) <= 1
    
    try:
        # Get Emergent LLM Key
        llm_key = os.environ.get('EMERGENT_LLM_KEY')
        print(f"[WhatsApp Bot] LLM Key found: {bool(llm_key)}")
        print(f"[WhatsApp Bot] System prompt length: {len(system_prompt)}")
        
        if not llm_key:
            raise ValueError("EMERGENT_LLM_KEY not configured")
        
        # Build initial messages for context - MUST include system message first!
        initial_messages = [{"role": "system", "content": system_prompt}]
        
        # Add welcome message for new conversations
        if is_new_conversation:
            welcome_msg = config.get("mensaje_bienvenida", DEFAULT_BOT_CONFIG["mensaje_bienvenida"])
            # Personalize welcome if we know the client
            if client_memory and client_memory.get('nombre'):
                welcome_msg = f"¡Hola {client_memory['nombre']}! 👋 Qué gusto verte de nuevo.\n\n" + welcome_msg.split('\n\n', 1)[-1] if '\n\n' in welcome_msg else welcome_msg
            initial_messages.append({"role": "assistant", "content": welcome_msg})
        
        # Add conversation history
        for msg in history:
            role = msg.get("role", "user")
            content = msg.get("message", "")
            if content:
                initial_messages.append({"role": role, "content": content})
        
        # Create LlmChat - pass initial_messages which already includes system message
        llm = LlmChat(
            api_key=llm_key,
            session_id=f"whatsapp-{phone_number}",
            system_message="",  # Empty since we're passing it in initial_messages
            initial_messages=initial_messages
        )
        
        # Set model to GPT-4o for better instruction following
        llm = llm.with_model('openai', 'gpt-4o')
        
        # Send the user message and get response
        ai_response = await llm.send_message(UserMessage(text=message))
        
        # Process special commands in the response
        ai_response, actions_taken = await process_bot_commands(phone_number, ai_response)
        
        # Save AI response (cleaned)
        await save_message(phone_number, ai_response, "assistant")
        
        return ai_response
        
    except Exception as e:
        print(f"Error processing message with AI: {e}")
        import traceback
        traceback.print_exc()
        # Return a fallback message
        fallback = "Disculpa, estoy teniendo dificultades técnicas. Un agente se comunicará contigo pronto. 🙏"
        await save_message(phone_number, fallback, "assistant")
        return fallback


async def process_bot_commands(phone_number: str, ai_response: str):
    """Process special commands in bot response and execute actions"""
    import re
    actions_taken = []
    
    # Check for CREAR_COBERTURA command
    crear_match = re.search(r'\[CREAR_COBERTURA\](.*?)\[/CREAR_COBERTURA\]', ai_response, re.DOTALL)
    if crear_match:
        try:
            data_text = crear_match.group(1)
            # Parse the data
            data = {}
            for line in data_text.strip().split('\n'):
                if ':' in line:
                    key, value = line.split(':', 1)
                    data[key.strip().lower()] = value.strip()
            
            print(f"[WhatsApp Bot] Creating coverage with data: {data}")
            
            # Save client data to memory for future conversations
            client_data = {}
            if data.get('nombre'):
                client_data['nombre'] = data['nombre']
            if data.get('dni'):
                client_data['dni'] = data['dni']
            if data.get('email'):
                client_data['email'] = data['email']
            if data.get('marca') and data.get('modelo'):
                client_data['vehiculo'] = f"{data.get('marca')} {data.get('modelo')}"
            
            if client_data:
                await save_client_memory(phone_number, client_data)
                print(f"[WhatsApp Bot] Saved client memory: {client_data}")
            
            # Create the coverage
            coverage = await create_coverage_from_whatsapp(phone_number, data)
            
            if coverage:
                actions_taken.append('coverage_created')
                
                # Get backend URL for links
                backend_url = os.environ.get('REACT_APP_BACKEND_URL', 'https://autocare-12.preview.emergentagent.com')
                
                # Replace the command with success message
                success_msg = f"""✅ *¡COBERTURA CREADA!*

📋 *Número de Recibo:* {coverage['numero_recibo']}
👤 *Titular:* {coverage['nombre']}
🚗 *Vehículo:* {coverage['marca']} {coverage['modelo']} ({coverage['ano']})
🔢 *Patente:* {coverage['patente']}
📧 *Email:* {coverage['email']}
📋 *Cobertura:* {'Terceros Completo' if coverage['cobertura'] == 'completo' else 'Responsabilidad Civil'}
💰 *Precio:* ${coverage['precio_final']:,}
⏰ *Vigencia:* 30 días desde el pago

Para activar tu cobertura, realizá el pago de *${coverage['precio_final']:,}*:

💳 *Por transferencia:*
{os.environ.get('DATOS_BANCARIOS', 'CBU/Alias: A configurar')}

Una vez que pagues, enviame el comprobante y activo tu cobertura al instante. 📸"""
                
                ai_response = re.sub(r'\[CREAR_COBERTURA\].*?\[/CREAR_COBERTURA\]', '', ai_response, flags=re.DOTALL)
                ai_response = ai_response.replace('Procesando tu cobertura... ⏳', success_msg)
                
                # Store coverage ID for this phone
                await db.whatsapp_pending.update_one(
                    {"phone_number": phone_number},
                    {"$set": {"coverage_id": coverage['_id'], "numero_recibo": coverage['numero_recibo']}},
                    upsert=True
                )
        except Exception as e:
            print(f"[WhatsApp Bot] Error creating coverage: {e}")
            import traceback
            traceback.print_exc()
            ai_response = re.sub(r'\[CREAR_COBERTURA\].*?\[/CREAR_COBERTURA\]', '', ai_response, flags=re.DOTALL)
            ai_response = ai_response.replace('Procesando tu cobertura... ⏳', '❌ Hubo un error al crear la cobertura. Por favor, verificá los datos e intentá de nuevo.')
    
    # Check for CONFIRMAR_PAGO command - Now notifies admin instead of auto-confirming
    pago_match = re.search(r'\[CONFIRMAR_PAGO\](.*?)\[/CONFIRMAR_PAGO\]', ai_response, re.DOTALL)
    if pago_match:
        try:
            # Get pending coverage for this phone
            pending = await db.whatsapp_pending.find_one({"phone_number": phone_number})
            
            if pending and pending.get('coverage_id'):
                coverage_id = pending['coverage_id']
                coverage = await get_coverage_by_id(coverage_id)
                
                if coverage:
                    # Get admin number from config
                    config = await get_bot_config()
                    admin_number = config.get('numero_admin', '')
                    
                    if admin_number:
                        # Send notification to admin
                        admin_msg = f"""🔔 *NUEVO PAGO PENDIENTE*

📋 *Recibo:* {coverage['numero_recibo']}
👤 *Cliente:* {coverage['nombre']}
📱 *Teléfono:* {phone_number}
🚗 *Vehículo:* {coverage['marca']} {coverage['modelo']} ({coverage.get('ano', 'N/A')})
🔢 *Patente:* {coverage['patente']}
💰 *Monto:* ${coverage['precio_final']:,}

El cliente dice que ya pagó.
Para confirmar, respondé: *CONFIRMAR {coverage['numero_recibo']}*"""
                        
                        await send_whatsapp_message(admin_number, admin_msg)
                        actions_taken.append('admin_notified')
                        
                        # Store pending approval
                        await db.whatsapp_pending.update_one(
                            {"phone_number": phone_number},
                            {"$set": {
                                "awaiting_admin_approval": True,
                                "client_phone": phone_number
                            }}
                        )
                        
                        # Tell client we're verifying
                        client_msg = """⏳ *Verificando tu pago...*

Estamos confirmando la recepción del pago. Te avisamos en unos minutos.

Si tenés alguna duda, podés escribirnos."""
                        
                        ai_response = re.sub(r'\[CONFIRMAR_PAGO\].*?\[/CONFIRMAR_PAGO\]', '', ai_response, flags=re.DOTALL)
                        ai_response = ai_response.replace('Verificando pago... ⏳', client_msg)
                    else:
                        # No admin number configured - auto confirm (fallback)
                        await mark_coverage_paid(coverage_id)
                        backend_url = os.environ.get('REACT_APP_BACKEND_URL', 'https://autocare-12.preview.emergentagent.com')
                        
                        success_msg = f"""✅ *¡PAGO CONFIRMADO!*

🎉 Tu cobertura está *ACTIVA*

📋 *Recibo:* {coverage['numero_recibo']}
📅 *Vigencia:* {coverage['vigencia_desde'][:10]} al {coverage['vigencia_hasta'][:10]}

📥 *Descargá tus comprobantes:*
• PDF: {backend_url}/api/seguros/{coverage_id}/comprobante/pdf
• Imagen: {backend_url}/api/seguros/{coverage_id}/comprobante/imagen

🔍 *Verificar cobertura:*
{backend_url}/verificar/{coverage['numero_recibo']}

¡Gracias por confiar en Estonia Cobertura! 🙏"""
                        
                        ai_response = re.sub(r'\[CONFIRMAR_PAGO\].*?\[/CONFIRMAR_PAGO\]', '', ai_response, flags=re.DOTALL)
                        ai_response = ai_response.replace('Verificando pago... ⏳', success_msg)
                        await db.whatsapp_pending.delete_one({"phone_number": phone_number})
            else:
                ai_response = re.sub(r'\[CONFIRMAR_PAGO\].*?\[/CONFIRMAR_PAGO\]', '', ai_response, flags=re.DOTALL)
                ai_response = ai_response.replace('Verificando pago... ⏳', '⚠️ No encontré una cobertura pendiente de pago. ¿Querés crear una nueva cobertura?')
                
        except Exception as e:
            print(f"[WhatsApp Bot] Error in payment flow: {e}")
            import traceback
            traceback.print_exc()
            ai_response = re.sub(r'\[CONFIRMAR_PAGO\].*?\[/CONFIRMAR_PAGO\]', '', ai_response, flags=re.DOTALL)
            ai_response = ai_response.replace('Verificando pago... ⏳', '❌ Hubo un error. Un agente revisará tu caso.')
    
    # Clean up any remaining command tags
    ai_response = re.sub(r'\[/?CREAR_COBERTURA\]', '', ai_response)
    ai_response = re.sub(r'\[/?CONFIRMAR_PAGO\]', '', ai_response)
    ai_response = ai_response.strip()
    
    return ai_response, actions_taken


async def create_coverage_from_whatsapp(phone_number: str, data: dict):
    """Create a coverage from WhatsApp conversation data"""
    from uuid import uuid4
    
    coverage_id = str(uuid4())
    numero_recibo = str(uuid4())[:8].upper()
    fecha_inicio = datetime.now(timezone.utc)
    fecha_fin = fecha_inicio + timedelta(days=30)
    
    # Parse and validate data
    tipo_vehiculo = data.get('tipo_vehiculo', 'auto').lower()
    tipo_cobertura = data.get('cobertura', 'rc').lower()
    
    # Calculate price
    PRICING = {
        "auto": {"rc": 6000, "completo": 9000},
        "moto": {"rc": 5000, "completo": 7500},
        "taxi": {"rc": 10000, "completo": 18000},
        "app": {"rc": 6000, "completo": 9000}
    }
    
    precio = PRICING.get(tipo_vehiculo, {}).get(tipo_cobertura, 6000)
    
    # Try to parse price from data if provided
    try:
        if 'precio' in data:
            parsed_price = int(data['precio'].replace('.', '').replace(',', ''))
            if parsed_price in [5000, 6000, 7500, 9000, 10000, 18000]:
                precio = parsed_price
    except:
        pass
    
    # Parse year
    try:
        ano = int(data.get('ano', datetime.now().year))
    except:
        ano = datetime.now().year
    
    coverage_doc = {
        "_id": coverage_id,
        "numero_recibo": numero_recibo,
        "dni": data.get('dni', '').replace('.', ''),
        "nombre": data.get('nombre', ''),
        "email": data.get('email', ''),
        "telefono": phone_number,
        "patente": data.get('patente', '').upper(),
        "marca": data.get('marca', ''),
        "modelo": data.get('modelo', ''),
        "ano": ano,
        "tipo_vehiculo": tipo_vehiculo,
        "cobertura": tipo_cobertura,
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
    print(f"[WhatsApp Bot] Coverage created: {numero_recibo}")
    return coverage_doc


async def send_whatsapp_message(phone_number: str, message: str):
    """Send a message via WhatsApp service using phone number"""
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


async def send_whatsapp_message_to_jid(jid: str, message: str):
    """Send a message via WhatsApp service using JID directly"""
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{WHATSAPP_SERVICE_URL}/send-jid",
                json={"jid": jid, "message": message},
                timeout=30.0
            )
            return response.json()
    except Exception as e:
        print(f"Error sending WhatsApp message to JID: {e}")
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
    """Get all conversations from WhatsApp service and MongoDB"""
    conversations = {}
    
    # Get conversations from MongoDB (our simulated/stored messages)
    try:
        # Get unique phone numbers with messages
        pipeline = [
            {"$group": {
                "_id": "$phone_number",
                "push_name": {"$last": "$push_name"},
                "last_message": {"$last": "$message"},
                "last_timestamp": {"$max": "$timestamp"},
                "message_count": {"$sum": 1}
            }},
            {"$sort": {"last_timestamp": -1}}
        ]
        
        results = await db.whatsapp_messages.aggregate(pipeline).to_list(100)
        
        for result in results:
            phone = result["_id"]
            if phone:
                conversations[phone] = {
                    "phone_number": phone,
                    "push_name": result.get("push_name", ""),
                    "last_message": result.get("last_message", ""),
                    "last_message_time": result.get("last_timestamp", ""),
                    "message_count": result.get("message_count", 0),
                    "bot_paused": False
                }
    except Exception as e:
        print(f"Error getting MongoDB conversations: {e}")
    
    # Also try to get live conversations from WhatsApp service
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{WHATSAPP_SERVICE_URL}/conversations", timeout=10.0)
            ws_data = response.json()
            
            # Merge with existing conversations
            for conv in ws_data.get("conversations", []):
                phone = conv.get("phone_number")
                if phone:
                    if phone in conversations:
                        # Update bot_paused status from WhatsApp service
                        conversations[phone]["bot_paused"] = conv.get("bot_paused", False)
                    else:
                        conversations[phone] = conv
            
            # Get paused chats
            paused_chats = ws_data.get("paused_chats", [])
            for phone in paused_chats:
                if phone in conversations:
                    conversations[phone]["bot_paused"] = True
                    
    except Exception as e:
        print(f"Error getting WhatsApp service conversations: {e}")
    
    # Convert to list and sort by last_message_time
    conv_list = list(conversations.values())
    conv_list.sort(key=lambda x: x.get("last_message_time", ""), reverse=True)
    
    return {"conversations": conv_list, "paused_chats": []}


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


async def mark_coverage_paid(coverage_id: str):
    """Mark a coverage as paid"""
    result = await db.seguros.update_one(
        {"_id": coverage_id},
        {"$set": {
            "estado": "pagado",
            "fecha_pago": datetime.now(timezone.utc).isoformat()
        }}
    )
    return result.modified_count > 0


async def get_coverage_by_id(coverage_id: str):
    """Get coverage by ID"""
    coverage = await db.seguros.find_one({"_id": coverage_id})
    return coverage


async def get_pending_coverage_by_phone(phone_number: str):
    """Get pending coverage for a phone number"""
    coverage = await db.seguros.find_one({
        "whatsapp_phone": phone_number,
        "estado": "pendiente_pago"
    })
    return coverage


async def simulate_conversation_flow(phone_number: str, client_data: dict):
    """
    Simulate a complete WhatsApp conversation flow:
    1. Client initiates contact
    2. AI collects data
    3. Coverage is created
    4. Payment is simulated
    5. Receipt is sent
    """
    import os
    
    conversation_log = []
    
    # Step 1: Initial greeting from client
    initial_message = "Hola, quiero contratar una cobertura para mi auto"
    await save_message(phone_number, initial_message, "user", client_data.get("nombre", "Cliente"))
    conversation_log.append({"role": "user", "message": initial_message})
    
    # Step 2: AI responds with welcome
    config = await get_bot_config()
    welcome = config.get("mensaje_bienvenida", "¡Hola! ¿En qué puedo ayudarte?")
    await save_message(phone_number, welcome, "assistant")
    conversation_log.append({"role": "assistant", "message": welcome})
    
    # Step 3: Client provides vehicle info
    vehicle_message = f"Mi auto es un {client_data.get('marca', 'Toyota')} {client_data.get('modelo', 'Corolla')} año {client_data.get('ano', 2020)}, patente {client_data.get('patente', 'ABC123')}"
    await save_message(phone_number, vehicle_message, "user", client_data.get("nombre", "Cliente"))
    conversation_log.append({"role": "user", "message": vehicle_message})
    
    # Step 4: AI asks for personal data
    ai_response = f"""¡Perfecto! Un {client_data.get('marca', 'Toyota')} {client_data.get('modelo', 'Corolla')} {client_data.get('ano', 2020)} 🚗

Para continuar, necesito tus datos personales:
- Nombre completo
- DNI
- Email

¿Me los proporcionas?"""
    await save_message(phone_number, ai_response, "assistant")
    conversation_log.append({"role": "assistant", "message": ai_response})
    
    # Step 5: Client provides personal data
    personal_message = f"Soy {client_data.get('nombre', 'Juan Pérez')}, DNI {client_data.get('dni', '12345678')}, email {client_data.get('email', 'cliente@email.com')}"
    await save_message(phone_number, personal_message, "user", client_data.get("nombre", "Cliente"))
    conversation_log.append({"role": "user", "message": personal_message})
    
    # Step 6: AI confirms and shows price
    tipo_vehiculo = client_data.get("tipo_vehiculo", "auto")
    tipo_cobertura = client_data.get("cobertura", "rc")
    
    PRICING = {
        "auto": {"rc": 6000, "completo": 9000},
        "moto": {"rc": 5000, "completo": 7500},
        "taxi": {"rc": 10000, "completo": 18000},
        "app": {"rc": 6000, "completo": 9000}
    }
    precio = PRICING.get(tipo_vehiculo, {}).get(tipo_cobertura, 6000)
    
    cobertura_nombre = "Responsabilidad Civil" if tipo_cobertura == "rc" else "Terceros Completo"
    
    confirmation_msg = f"""✅ *RESUMEN DE TU COBERTURA*

👤 *Titular:* {client_data.get('nombre', 'Juan Pérez')}
📄 *DNI:* {client_data.get('dni', '12345678')}
📧 *Email:* {client_data.get('email', 'cliente@email.com')}

🚗 *Vehículo:* {client_data.get('marca', 'Toyota')} {client_data.get('modelo', 'Corolla')} ({client_data.get('ano', 2020)})
🔢 *Patente:* {client_data.get('patente', 'ABC123')}

📋 *Cobertura:* {cobertura_nombre}
💰 *Precio:* ${precio:,}
⏰ *Vigencia:* 30 días

¿Confirmamos la cobertura? Responde *SÍ* para continuar."""
    await save_message(phone_number, confirmation_msg, "assistant")
    conversation_log.append({"role": "assistant", "message": confirmation_msg})
    
    # Step 7: Client confirms
    await save_message(phone_number, "Sí, confirmo", "user", client_data.get("nombre", "Cliente"))
    conversation_log.append({"role": "user", "message": "Sí, confirmo"})
    
    # Step 8: Create coverage
    coverage = await create_pending_coverage(phone_number, client_data)
    
    # Step 9: AI sends payment instructions
    datos_bancarios = config.get("datos_bancarios", "CVU: A configurar por el administrador")
    
    payment_msg = f"""🎉 *¡Cobertura creada exitosamente!*

📝 *Número de recibo:* {coverage['numero_recibo']}

Para activar tu cobertura, realiza el pago de *${precio:,}* por transferencia:

💳 *Datos para transferencia:*
{datos_bancarios}

Una vez realizado el pago, envíame el comprobante y activaré tu cobertura inmediatamente. ✅"""
    await save_message(phone_number, payment_msg, "assistant")
    conversation_log.append({"role": "assistant", "message": payment_msg})
    
    # Step 10: Simulate payment confirmation
    await save_message(phone_number, "Ya transferí, te envío el comprobante 📄", "user", client_data.get("nombre", "Cliente"))
    conversation_log.append({"role": "user", "message": "Ya transferí, te envío el comprobante 📄"})
    
    # Step 11: Mark as paid
    await mark_coverage_paid(coverage["_id"])
    
    # Step 12: Send receipt confirmation
    backend_url = os.environ.get('REACT_APP_BACKEND_URL', 'http://localhost:3000')
    
    receipt_msg = f"""✅ *¡PAGO CONFIRMADO!*

Tu cobertura ha sido activada exitosamente. 🎉

📋 *Detalles de tu cobertura:*
• Número de recibo: *{coverage['numero_recibo']}*
• Vigencia: {coverage['vigencia_desde'][:10]} al {coverage['vigencia_hasta'][:10]}
• Estado: ✅ PAGADO

📥 *Descarga tu comprobante:*
• PDF: {backend_url}/api/seguros/{coverage['_id']}/comprobante/pdf
• Imagen: {backend_url}/api/seguros/{coverage['_id']}/comprobante/imagen

🔍 También puedes verificar tu cobertura en:
{backend_url}/verificar/{coverage['numero_recibo']}

¡Gracias por confiar en Estonia Cobertura Colaborativa! 🙏
Si tienes alguna duda, estoy aquí para ayudarte."""
    await save_message(phone_number, receipt_msg, "assistant")
    conversation_log.append({"role": "assistant", "message": receipt_msg})
    
    return {
        "success": True,
        "coverage": coverage,
        "conversation_log": conversation_log,
        "pdf_url": f"{backend_url}/api/seguros/{coverage['_id']}/comprobante/pdf",
        "image_url": f"{backend_url}/api/seguros/{coverage['_id']}/comprobante/imagen",
        "verification_url": f"{backend_url}/verificar/{coverage['numero_recibo']}"
    }

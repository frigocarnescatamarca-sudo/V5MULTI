"""
WhatsApp AI Bot Service for Sandwichería "Modo Cocina"
Handles message processing with ChatGPT integration for food orders
Version 2.0 - Enhanced with sequential orders, delivery role, human handover, etc.
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

# WhatsApp Sandwich Service URL
WHATSAPP_SANDWICH_URL = os.environ.get('WHATSAPP_SANDWICH_URL', 'http://localhost:3003')

# Timeout for human handover auto-resume (2 hours)
HANDOVER_TIMEOUT_HOURS = 2

# Reminder interval for unconfirmed orders (minutes)
ORDER_REMINDER_MINUTES = 5

# Master admin password (for initial setup)
MASTER_ADMIN_PASSWORD = os.environ.get('SANDWICH_MASTER_PASSWORD', 'ModoAdmin2025!')

# Default bot configuration for Sandwich
DEFAULT_SANDWICH_CONFIG = {
    "nombre_negocio": "Modo Cocina",
    "mensaje_bienvenida": """¡Hola! 👋 Bienvenido a *Modo Cocina*

🥪 Preparamos los mejores sándwiches de la zona

¿Querés ver nuestro menú? Escribí *MENÚ*

🛵 Hacemos delivery
🏪 También podés retirar en el local""",
    
    "horario_apertura": "10:00",
    "horario_cierre": "22:00",
    "dias_abierto": ["lunes", "martes", "miércoles", "jueves", "viernes", "sábado"],
    "direccion_local": "Av. Principal 123",
    "costo_delivery": 500,
    "pedido_minimo_delivery": 2000,
    "tiempo_preparacion": "20-30 minutos",
    "zona_restringida": "Valle Viejo",
    "admin_phone": "",
    "admin_lid": "",
    "delivery_phones": [],  # List of delivery person phone numbers
    "bot_activo": True,
    
    "instrucciones_bot": """Sos "Cocibot", el asistente de pedidos de {nombre_negocio}. Tu objetivo es tomar pedidos de comida de forma amable, eficiente y con personalidad humana.

=== MENÚ DISPONIBLE ===
{menu_formateado}

=== TU PERSONALIDAD ===
- Sos argentino, usá "vos" en lugar de "tú"
- Sé amable y servicial, pero también un poco gracioso
- Usá emojis con moderación (1-2 por mensaje)
- Respuestas cortas y claras
- Variá tus respuestas para sonar más humano

=== HORARIO DE ATENCIÓN ===
⏰ Abierto de {horario_apertura} a {horario_cierre}
- DENTRO del horario: Tomás pedidos normalmente
- FUERA del horario: Tomás el pedido como RESERVA y le avisás que se enviará cuando abramos

=== PROMOCIÓN ESPECIAL (OBLIGATORIA) ===
🔥 *PROMO 3 PRODUCTOS POR $23.000*
- Cuando el cliente pide 3 productos (cualquier combinación), AUTOMÁTICAMENTE entra en la promo de $23.000
- La Pizza Argentina ($12.000) NO entra en la promo
- Si pide 3 productos incluyendo Pizza Argentina, solo los otros 2 entran en promo + el precio de la Pizza Argentina aparte
- NO preguntes si quiere la promo, APLICALA directamente cuando pida 3 productos
- Ejemplo: "2 zapping y 1 lomo" = $23.000 (promo automática)

=== FLUJO DE PEDIDO ===

PASO 1 - MOSTRAR MENÚ:
Si el cliente pide ver el menú o no sabe qué pedir, mostrá las opciones disponibles. Siempre mencioná la promo de 3 productos por $23.000.

PASO 2 - TOMAR PEDIDO:
Cuando el cliente elija:
- Confirmá qué productos quiere
- Si son 3 o más productos, aplicá la promo automáticamente
- Preguntá si quiere agregar algo más

PASO 3 - PREGUNTAR MODIFICACIONES:
Antes de confirmar, preguntá brevemente:
"¿Alguna modificación? (sin mayo, extra queso, etc.)"

PASO 4 - DELIVERY O RETIRO:
Preguntá: "¿Te lo mando o lo retirás por el local?"

PASO 5 - DATOS DEL CLIENTE:
Si es DELIVERY:
- Pedí nombre
- SI EL CLIENTE YA COMPARTIÓ SU UBICACIÓN (GPS): NO pidas dirección escrita, ya tenés la ubicación. Solo confirmá que la recibiste y continuá.
- SI NO compartió ubicación: Pedí dirección y entre qué calles está

ZONA RESTRINGIDA: Si la dirección menciona "{zona_restringida}", informá que no hacemos delivery ahí pero puede retirar en el local.

Si es RETIRO:
- Solo pedí el nombre

PASO 6 - CONFIRMAR PEDIDO:
Mostrá resumen:
"📋 *Tu pedido:*
👤 [nombre del cliente]
📍 [delivery o retiro]
🛒 [items]
💰 Total: $[total]
¿Confirmo?"

PASO 7 - CREAR PEDIDO:
Cuando confirme, usá EXACTAMENTE este formato:

[CREAR_PEDIDO]
nombre: [nombre]
telefono: [telefono del chat]
direccion: [dirección o "Ubicación compartida" o "Retira en local"]
tipo_entrega: [delivery/retiro]
items: [lista de items separados por coma]
cantidades: [cantidades separadas por coma]
modificaciones: [modificaciones o "ninguna"]
subtotal: [subtotal]
delivery: [costo delivery o 0]
total: [total final]
[/CREAR_PEDIDO]

Procesando tu pedido... ⏳

IMPORTANTE: Después de [CREAR_PEDIDO] NO agregues nada más. El sistema genera el mensaje de confirmación.

=== ESTADOS DEL PEDIDO ===
- RESERVA: Fuera de horario, se enviará cuando abramos
- PENDIENTE: Esperando confirmación del local
- CONFIRMADO: El local lo aceptó
- LISTO: Preparado
- EN CAMINO: Delivery en camino
- ENTREGADO: Entregado

NUNCA digas que está "confirmado", "en camino" o "listo" por tu cuenta. Solo el sistema puede cambiar estados.

=== COMANDOS DEL CLIENTE ===
- "CANCELAR" → Preguntá si está seguro, luego usá [CANCELAR_PEDIDO]
- "MODIFICAR" → Preguntá qué quiere cambiar
- "HABLAR CON ALGUIEN" / "ENCARGADO" → Respondé: "Te comunico con el encargado 👤" y usá [PAUSAR_BOT]
- "¿Cómo va mi pedido?" → Respondé: "Déjame consultar... 🔍" y usá [CONSULTAR_ESTADO]

=== REGLAS ===
- NUNCA inventes productos
- NUNCA cambies precios
- NUNCA confirmes pedidos vos - el local confirma
- Costo delivery: ${costo_delivery}
- Pedido mínimo delivery: ${pedido_minimo}
- Tiempo: {tiempo_preparacion}

=== UBICACIÓN COMPARTIDA ===
Si el cliente comparte ubicación GPS:
"¡Perfecto! Ya guardé tu ubicación 📍"
Y continuá con el pedido SIN pedir dirección escrita.
"""
}

# Default menu categories and products
DEFAULT_MENU = [
    {
        "categoria": "Sándwiches Clásicos",
        "emoji": "🥪",
        "productos": [
            {"nombre": "Sándwich de Milanesa", "precio": 2500, "descripcion": "Milanesa de carne con lechuga y tomate", "activo": True},
            {"nombre": "Sándwich de Milanesa Completo", "precio": 3000, "descripcion": "Milanesa con jamón, queso, lechuga, tomate y huevo", "activo": True},
            {"nombre": "Sándwich de Lomito", "precio": 3500, "descripcion": "Lomito con lechuga, tomate y mayonesa", "activo": True},
            {"nombre": "Sándwich de Lomito Completo", "precio": 4000, "descripcion": "Lomito con jamón, queso, lechuga, tomate, huevo y papas", "activo": True},
        ]
    },
    {
        "categoria": "Hamburguesas",
        "emoji": "🍔",
        "productos": [
            {"nombre": "Hamburguesa Simple", "precio": 2000, "descripcion": "Medallón de carne con lechuga y tomate", "activo": True},
            {"nombre": "Hamburguesa Completa", "precio": 2800, "descripcion": "Medallón con queso, panceta, lechuga, tomate y cebolla", "activo": True},
            {"nombre": "Hamburguesa Doble", "precio": 3500, "descripcion": "Doble medallón con doble queso y panceta", "activo": True},
        ]
    },
    {
        "categoria": "Bebidas",
        "emoji": "🥤",
        "productos": [
            {"nombre": "Coca Cola 500ml", "precio": 800, "descripcion": "", "activo": True},
            {"nombre": "Sprite 500ml", "precio": 800, "descripcion": "", "activo": True},
            {"nombre": "Agua 500ml", "precio": 500, "descripcion": "", "activo": True},
            {"nombre": "Cerveza Quilmes 1L", "precio": 1500, "descripcion": "", "activo": True},
        ]
    },
    {
        "categoria": "Extras",
        "emoji": "➕",
        "productos": [
            {"nombre": "Papas Fritas", "precio": 1000, "descripcion": "Porción grande", "activo": True},
            {"nombre": "Huevo Frito", "precio": 300, "descripcion": "", "activo": True},
            {"nombre": "Queso Extra", "precio": 400, "descripcion": "", "activo": True},
            {"nombre": "Panceta Extra", "precio": 500, "descripcion": "", "activo": True},
        ]
    }
]


async def get_sandwich_config():
    """Get sandwich bot configuration from database or return defaults"""
    config = await db.sandwich_config.find_one({"_id": "bot_config"})
    if not config:
        default = {**DEFAULT_SANDWICH_CONFIG, "_id": "bot_config"}
        await db.sandwich_config.insert_one(default)
        return DEFAULT_SANDWICH_CONFIG
    
    del config["_id"]
    return config


async def update_sandwich_config(config_data: dict):
    """Update sandwich bot configuration"""
    await db.sandwich_config.update_one(
        {"_id": "bot_config"},
        {"$set": config_data},
        upsert=True
    )
    return await get_sandwich_config()


async def get_menu():
    """Get menu from database or return defaults"""
    menu = await db.sandwich_menu.find({}, {"_id": 0}).to_list(100)
    if not menu:
        for cat in DEFAULT_MENU:
            await db.sandwich_menu.insert_one(cat)
        return DEFAULT_MENU
    return menu


async def format_menu_for_bot():
    """Format menu for bot instructions"""
    menu = await get_menu()
    formatted = ""
    for cat in menu:
        formatted += f"\n{cat['emoji']} *{cat['categoria']}*\n"
        for prod in cat.get('productos', []):
            if prod.get('activo', True):
                formatted += f"  • {prod['nombre']}: ${prod['precio']:,}"
                if prod.get('descripcion'):
                    formatted += f" - {prod['descripcion']}"
                formatted += "\n"
    return formatted


# ============ USER MANAGEMENT SYSTEM ============

async def create_bot_user(username: str, password: str, role: str, created_by: str):
    """Create a new bot user (admin or delivery)"""
    existing = await db.sandwich_bot_users.find_one({"username": username.lower()})
    if existing:
        return None, f"El usuario '{username}' ya existe"
    
    user_doc = {
        "username": username.lower(),
        "password": password,  # In production, hash this
        "role": role,  # "admin" or "delivery"
        "activo": True,
        "created_by": created_by,
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    
    await db.sandwich_bot_users.insert_one(user_doc)
    return user_doc, f"✅ Usuario *{username}* creado como *{role.upper()}*"


async def delete_bot_user(username: str):
    """Delete a bot user and close their sessions"""
    user = await db.sandwich_bot_users.find_one({"username": username.lower()})
    if not user:
        return False, f"❌ Usuario '{username}' no encontrado"
    
    # Close all sessions for this user
    await db.sandwich_bot_sessions.delete_many({"username": username.lower()})
    
    # Delete user
    await db.sandwich_bot_users.delete_one({"username": username.lower()})
    return True, f"✅ Usuario *{username}* eliminado"


async def get_all_bot_users():
    """Get all bot users"""
    users = await db.sandwich_bot_users.find({}, {"_id": 0, "password": 0}).to_list(100)
    return users


async def authenticate_user(username: str, password: str):
    """Authenticate a user by username and password"""
    user = await db.sandwich_bot_users.find_one({
        "username": username.lower(),
        "password": password,
        "activo": True
    })
    return user


async def create_session(phone_number: str, username: str, role: str):
    """Create a login session for a phone number"""
    await db.sandwich_bot_sessions.update_one(
        {"phone_number": phone_number},
        {"$set": {
            "phone_number": phone_number,
            "username": username.lower(),
            "role": role,
            "logged_in_at": datetime.now(timezone.utc).isoformat()
        }},
        upsert=True
    )


async def close_session(phone_number: str):
    """Close session for a phone number"""
    result = await db.sandwich_bot_sessions.delete_one({"phone_number": phone_number})
    return result.deleted_count > 0


async def close_session_by_username(username: str):
    """Close all sessions for a username (admin kicks user)"""
    result = await db.sandwich_bot_sessions.delete_many({"username": username.lower()})
    return result.deleted_count


async def get_session(phone_number: str):
    """Get active session for a phone number"""
    session = await db.sandwich_bot_sessions.find_one({"phone_number": phone_number})
    return session


async def get_active_sessions_by_role(role: str):
    """Get all active sessions for a role (admin or delivery)"""
    sessions = await db.sandwich_bot_sessions.find({"role": role}).to_list(100)
    return sessions


async def is_master_admin(phone_number: str):
    """Check if phone is the master admin (from config)"""
    config = await get_sandwich_config()
    admin_phone = config.get('admin_phone', '')
    admin_lid = config.get('admin_lid', '')
    
    phone_digits = ''.join(filter(str.isdigit, str(phone_number)))[-10:]
    
    if admin_lid:
        lid_digits = ''.join(filter(str.isdigit, str(admin_lid)))[-10:]
        if phone_digits == lid_digits or phone_digits.endswith(lid_digits) or lid_digits.endswith(phone_digits):
            return True
    
    if admin_phone:
        admin_digits = ''.join(filter(str.isdigit, str(admin_phone)))[-10:]
        if phone_digits == admin_digits or phone_digits.endswith(admin_digits) or admin_digits.endswith(phone_digits):
            return True
    
    return False


async def get_user_role(phone_number: str):
    """Get the role of a phone number (master_admin, admin, delivery, or None)"""
    # Check if master admin
    if await is_master_admin(phone_number):
        return "master_admin"
    
    # Check active session
    session = await get_session(phone_number)
    if session:
        return session.get("role")
    
    return None


# ============ MULTI-ADMIN NOTIFICATIONS ============

async def notify_all_admins(message: str, exclude_phone: str = None):
    """Send notification to all active admins"""
    # Get master admin
    config = await get_sandwich_config()
    admin_phone = config.get('admin_phone', '')
    admin_lid = config.get('admin_lid', '')
    
    notified = []
    master_notified = False
    
    # Try to notify master admin via LID first, then fallback to phone
    if admin_lid and admin_lid != exclude_phone:
        try:
            await send_sandwich_message_to_jid(f"{admin_lid}@lid", message)
            notified.append(f"master_lid:{admin_lid}")
            master_notified = True
        except Exception as e:
            print(f"[Sandwich Bot] Error notifying master admin via LID: {e}")
    
    # Also try phone if LID failed or if phone is different
    if admin_phone and admin_phone != exclude_phone and not master_notified:
        try:
            await send_sandwich_message(admin_phone, message)
            notified.append(f"master_phone:{admin_phone}")
        except Exception as e:
            print(f"[Sandwich Bot] Error notifying master admin via phone: {e}")
    
    # Notify logged-in admins
    admin_sessions = await get_active_sessions_by_role("admin")
    for session in admin_sessions:
        session_phone = session.get("phone_number")
        if session_phone and session_phone != exclude_phone:
            try:
                await send_sandwich_message(session_phone, message)
                notified.append(f"admin:{session.get('username')}")
            except Exception as e:
                print(f"[Sandwich Bot] Error notifying admin {session.get('username')}: {e}")
    
    print(f"[Sandwich Bot] Notified admins: {notified}")
    return notified


async def notify_all_deliveries(message: str):
    """Send notification to all active deliveries"""
    delivery_sessions = await get_active_sessions_by_role("delivery")
    notified = []
    
    for session in delivery_sessions:
        session_phone = session.get("phone_number")
        if session_phone:
            try:
                await send_sandwich_message(session_phone, message)
                notified.append(f"delivery:{session.get('username')}")
            except Exception as e:
                print(f"[Sandwich Bot] Error notifying delivery {session.get('username')}: {e}")
    
    print(f"[Sandwich Bot] Notified deliveries: {notified}")
    return notified


# ============ ORDER REMINDERS ============

async def get_unconfirmed_orders_needing_reminder():
    """Get orders pending for more than ORDER_REMINDER_MINUTES"""
    cutoff_time = datetime.now(timezone.utc) - timedelta(minutes=ORDER_REMINDER_MINUTES)
    
    orders = await db.sandwich_pedidos.find({
        "estado": "pendiente",
        "created_at": {"$lt": cutoff_time.isoformat()},
        "$or": [
            {"last_reminder_at": {"$exists": False}},
            {"last_reminder_at": {"$lt": (datetime.now(timezone.utc) - timedelta(minutes=ORDER_REMINDER_MINUTES)).isoformat()}}
        ]
    }).to_list(50)
    
    return orders


async def send_order_reminders():
    """Send reminders for orders pending too long"""
    orders = await get_unconfirmed_orders_needing_reminder()
    
    for order in orders:
        minutes_waiting = 0
        try:
            created_at = datetime.fromisoformat(order['created_at'].replace('Z', '+00:00'))
            minutes_waiting = int((datetime.now(timezone.utc) - created_at).total_seconds() / 60)
        except Exception:
            minutes_waiting = ORDER_REMINDER_MINUTES
        
        reminder_msg = f"""⚠️ *RECORDATORIO PEDIDO #{order['numero_pedido']}*

Este pedido lleva *{minutes_waiting} minutos* sin confirmar!

👤 {order.get('nombre', 'Sin nombre')}
💰 ${order.get('total', 0):,}
📍 {order.get('tipo_entrega', 'N/A').upper()}

Para confirmar: *CONFIRMAR {order['numero_pedido']}*
Para rechazar: *RECHAZAR {order['numero_pedido']} [motivo]*"""
        
        # Notify all admins
        await notify_all_admins(reminder_msg)
        
        # Update last reminder time
        await db.sandwich_pedidos.update_one(
            {"numero_pedido": order['numero_pedido']},
            {"$set": {"last_reminder_at": datetime.now(timezone.utc).isoformat()}}
        )
    
    return len(orders)


# ============ HORARIO Y RESERVAS ============

def is_within_operating_hours(hora_apertura: str = "20:00", hora_cierre: str = "01:00") -> bool:
    """Check if current time is within operating hours (Argentina timezone)"""
    from datetime import datetime
    import pytz
    
    # Argentina timezone
    argentina_tz = pytz.timezone('America/Argentina/Buenos_Aires')
    now = datetime.now(argentina_tz)
    current_hour = now.hour
    current_minute = now.minute
    current_time = current_hour * 60 + current_minute  # Convert to minutes
    
    # Parse opening and closing times
    open_hour, open_min = map(int, hora_apertura.split(':'))
    close_hour, close_min = map(int, hora_cierre.split(':'))
    
    open_time = open_hour * 60 + open_min
    close_time = close_hour * 60 + close_min
    
    # Handle overnight hours (e.g., 20:00 to 01:00)
    if close_time < open_time:
        # Operating hours span midnight
        # Open from 20:00 to 23:59 OR from 00:00 to 01:00
        return current_time >= open_time or current_time <= close_time
    else:
        # Normal hours (e.g., 10:00 to 22:00)
        return open_time <= current_time <= close_time


async def create_reservation(phone_number: str, data: dict):
    """Create a reservation for when the store opens"""
    seq_number = await get_next_order_number()
    numero_reserva = f"R{seq_number}"  # R1, R2, R3...
    
    location = await get_client_location(phone_number)
    has_location = location is not None
    whatsapp_contact = await get_client_whatsapp_number(phone_number)
    
    reserva_doc = {
        "numero_pedido": numero_reserva,
        "es_reserva": True,
        "sequence_number": seq_number,
        "nombre": data.get('nombre', ''),
        "telefono": phone_number,
        "whatsapp_contact": whatsapp_contact,
        "direccion": data.get('direccion', ''),
        "tipo_entrega": data.get('tipo_entrega', 'retiro'),
        "items": data.get('items', ''),
        "cantidades": data.get('cantidades', ''),
        "items_formatted": data.get('items_formatted', ''),
        "modificaciones": data.get('modificaciones', ''),
        "subtotal": int(data.get('subtotal', 0)),
        "costo_delivery": int(data.get('delivery', 0)),
        "total": int(data.get('total', 0)),
        "estado": "reserva",  # Special status for reservations
        "whatsapp_phone": phone_number,
        "has_location": has_location,
        "location": location,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "pending_whatsapp_request": not whatsapp_contact
    }
    
    await db.sandwich_pedidos.insert_one(reserva_doc)
    print(f"[Sandwich Bot] Reservation created: #{numero_reserva}")
    return reserva_doc


async def send_pending_reservations():
    """Send notifications for reservations when store opens"""
    reservations = await db.sandwich_pedidos.find({"es_reserva": True, "estado": "reserva"}).to_list(100)
    
    for reserva in reservations:
        # Convert reservation to pending order
        await db.sandwich_pedidos.update_one(
            {"numero_pedido": reserva['numero_pedido']},
            {"$set": {"estado": "pendiente", "converted_at": datetime.now(timezone.utc).isoformat()}}
        )
        
        # Notify client
        client_msg = f"""🔔 *¡Ya abrimos!*

Tu reserva #{reserva['numero_pedido']} ya fue enviada al local.
Te avisamos cuando la confirmen.

🛒 {reserva.get('items_formatted', reserva.get('items', ''))}
💰 Total: ${reserva.get('total', 0):,}"""
        
        try:
            await send_sandwich_message(reserva['telefono'], client_msg)
        except Exception as e:
            print(f"[Sandwich Bot] Error notifying client about reservation: {e}")
        
        # Notify admins
        await notify_sandwich_admin(reserva)
    
    return len(reservations)


# ============ SEQUENTIAL ORDER NUMBERS ============

async def get_next_order_number():
    """Get the next sequential order number (1, 2, 3...)"""
    counter = await db.sandwich_order_counter.find_one_and_update(
        {"_id": "order_counter"},
        {"$inc": {"sequence": 1}},
        upsert=True,
        return_document=True
    )
    return counter.get("sequence", 1)


async def reset_daily_order_counter():
    """Reset order counter daily (optional - can be called via cron or manually)"""
    await db.sandwich_order_counter.update_one(
        {"_id": "order_counter"},
        {"$set": {"sequence": 0, "reset_at": datetime.now(timezone.utc).isoformat()}},
        upsert=True
    )


# ============ PAUSE/RESUME WITH AUTO-RESUME ============

async def is_sandwich_chat_paused(phone_number: str) -> bool:
    """Check if a chat is paused for human attention"""
    paused = await db.sandwich_paused.find_one({"phone_number": phone_number})
    if not paused:
        return False
    
    # Check if auto-resume time has passed
    paused_at = paused.get("paused_at", "")
    if paused_at:
        try:
            paused_time = datetime.fromisoformat(paused_at.replace('Z', '+00:00'))
            if datetime.now(timezone.utc) > paused_time + timedelta(hours=HANDOVER_TIMEOUT_HOURS):
                # Auto-resume after timeout
                await resume_sandwich_chat(phone_number)
                print(f"[Sandwich Bot] Auto-resumed chat {phone_number} after {HANDOVER_TIMEOUT_HOURS}h timeout")
                return False
        except Exception:
            pass
    
    return True


async def pause_sandwich_chat(phone_number: str, admin_phone: str, reason: str = "human_handover"):
    """Pause bot for a specific chat"""
    await db.sandwich_paused.update_one(
        {"phone_number": phone_number},
        {"$set": {
            "phone_number": phone_number,
            "paused_by": admin_phone,
            "reason": reason,
            "paused_at": datetime.now(timezone.utc).isoformat(),
            "auto_resume_at": (datetime.now(timezone.utc) + timedelta(hours=HANDOVER_TIMEOUT_HOURS)).isoformat()
        }},
        upsert=True
    )


async def resume_sandwich_chat(phone_number: str):
    """Resume bot for a specific chat"""
    await db.sandwich_paused.delete_one({"phone_number": phone_number})


async def get_sandwich_paused_chats():
    """Get list of all paused chats"""
    paused = await db.sandwich_paused.find({}, {"_id": 0}).to_list(100)
    return paused


# ============ CLIENT LOCATION HANDLING ============

async def save_client_location(phone_number: str, latitude: float, longitude: float):
    """Save client's shared location"""
    await db.sandwich_client_data.update_one(
        {"phone_number": phone_number},
        {"$set": {
            "phone_number": phone_number,
            "location": {
                "latitude": latitude,
                "longitude": longitude,
                "shared_at": datetime.now(timezone.utc).isoformat()
            },
            "updated_at": datetime.now(timezone.utc).isoformat()
        }},
        upsert=True
    )
    print(f"[Sandwich Bot] Saved location for {phone_number}: {latitude}, {longitude}")


async def get_client_location(phone_number: str):
    """Get client's saved location"""
    client_data = await db.sandwich_client_data.find_one({"phone_number": phone_number})
    if client_data and "location" in client_data:
        return client_data["location"]
    return None


async def save_client_whatsapp_number(phone_number: str, whatsapp_number: str):
    """Save client's actual WhatsApp number for delivery contact"""
    await db.sandwich_client_data.update_one(
        {"phone_number": phone_number},
        {"$set": {
            "phone_number": phone_number,
            "whatsapp_contact": whatsapp_number,
            "updated_at": datetime.now(timezone.utc).isoformat()
        }},
        upsert=True
    )


async def get_client_whatsapp_number(phone_number: str):
    """Get client's WhatsApp contact number"""
    client_data = await db.sandwich_client_data.find_one({"phone_number": phone_number})
    if client_data:
        return client_data.get("whatsapp_contact")
    return None


# ============ STATUS QUERY HANDLING ============

async def create_status_query(phone_number: str, numero_pedido: str):
    """Create a status query from client to admin"""
    await db.sandwich_status_queries.insert_one({
        "phone_number": phone_number,
        "numero_pedido": numero_pedido,
        "status": "pending",  # pending, answered
        "created_at": datetime.now(timezone.utc).isoformat()
    })
    
    # Notify admin
    config = await get_sandwich_config()
    admin_msg = f"""🔔 *CONSULTA DE ESTADO*

Un cliente pregunta por su pedido:
📋 Pedido: #{numero_pedido}
📱 Cliente: {phone_number}

Para responder, escribí:
*ESTADO {numero_pedido} [tu respuesta]*

Ejemplo: ESTADO {numero_pedido} Ya casi sale, 5 minutos más"""
    
    admin_lid = config.get('admin_lid', '')
    admin_phone = config.get('admin_phone', '')
    
    try:
        if admin_lid:
            await send_sandwich_message_to_jid(f"{admin_lid}@lid", admin_msg)
        elif admin_phone:
            await send_sandwich_message(admin_phone, admin_msg)
    except Exception as e:
        print(f"[Sandwich Bot] Error notifying admin about status query: {e}")


async def answer_status_query(numero_pedido: str, response: str, phone_number: str):
    """Admin answers a status query"""
    # Find pending query
    query = await db.sandwich_status_queries.find_one({
        "numero_pedido": numero_pedido,
        "status": "pending"
    })
    
    if not query:
        # Try to find the order directly
        order = await db.sandwich_pedidos.find_one({"numero_pedido": numero_pedido})
        if order:
            client_phone = order.get("telefono") or order.get("whatsapp_phone")
            if client_phone:
                client_msg = f"""📋 *Estado de tu pedido #{numero_pedido}*

{response}"""
                await send_sandwich_message(client_phone, client_msg)
                return "✅ Respuesta enviada al cliente"
        return f"❌ No encontré consulta pendiente para el pedido #{numero_pedido}"
    
    # Mark as answered
    await db.sandwich_status_queries.update_one(
        {"_id": query["_id"]},
        {"$set": {"status": "answered", "response": response, "answered_at": datetime.now(timezone.utc).isoformat()}}
    )
    
    # Send response to client
    client_msg = f"""📋 *Estado de tu pedido #{numero_pedido}*

{response}"""
    
    await send_sandwich_message(query["phone_number"], client_msg)
    return "✅ Respuesta enviada al cliente"


# ============ ORDER MANAGEMENT ============

async def notify_sandwich_admin(order_data: dict):
    """Notify ALL admins about new order"""
    location_info = ""
    if order_data.get('has_location'):
        location_info = "\n📍 *Ubicación compartida:* ✅ Disponible"
    
    modificaciones = order_data.get('modificaciones', 'Ninguna')
    if modificaciones and modificaciones.lower() != 'ninguna':
        modificaciones_text = f"\n✏️ *Modificaciones:* {modificaciones}"
    else:
        modificaciones_text = ""
    
    notification = f"""🔔 *NUEVO PEDIDO #{order_data['numero_pedido']}*

👤 *Cliente:* {order_data['nombre']}
📱 *WhatsApp:* {order_data.get('whatsapp_contact', 'Pendiente')}
📍 *Entrega:* {order_data['tipo_entrega'].upper()}
{f"🏠 *Dirección:* {order_data['direccion']}" if order_data['tipo_entrega'] == 'delivery' else '🏪 *Retira en local*'}{location_info}{modificaciones_text}

🛒 *PEDIDO:*
{order_data['items_formatted']}

💰 *Subtotal:* ${order_data['subtotal']:,}
🛵 *Delivery:* ${order_data['costo_delivery']:,}
💵 *TOTAL:* ${order_data['total']:,}

⏰ {datetime.now().strftime('%H:%M')}

Para confirmar: *CONFIRMAR {order_data['numero_pedido']}*
Para rechazar: *RECHAZAR {order_data['numero_pedido']}*"""
    
    # Notify ALL active admins
    notified = await notify_all_admins(notification)
    print(f"[Sandwich Bot] Notified about order {order_data['numero_pedido']}: {notified}")


async def get_sandwich_conversation_history(phone_number: str, limit: int = 10):
    """Get recent conversation history for a phone number"""
    messages = await db.sandwich_messages.find(
        {"phone_number": phone_number}
    ).sort("timestamp", -1).limit(limit).to_list(limit)
    
    return list(reversed(messages))


async def save_sandwich_message(phone_number: str, message: str, role: str, push_name: str = ""):
    """Save a message to the database"""
    doc = {
        "phone_number": phone_number,
        "message": message,
        "role": role,
        "push_name": push_name,
        "timestamp": datetime.now(timezone.utc).isoformat()
    }
    await db.sandwich_messages.insert_one(doc)
    return doc


def parse_price(value) -> int:
    """Parse a price string like '$23,000' or '23000' to integer"""
    if isinstance(value, int):
        return value
    if isinstance(value, float):
        return int(value)
    if not value:
        return 0
    # Remove $, dots, commas, spaces
    cleaned = str(value).replace('$', '').replace('.', '').replace(',', '').replace(' ', '').strip()
    try:
        return int(cleaned)
    except ValueError:
        return 0


async def create_sandwich_order(phone_number: str, data: dict):
    """Create a new order from WhatsApp with sequential number"""
    # Get sequential order number
    seq_number = await get_next_order_number()
    numero_pedido = str(seq_number)  # Just the number: 1, 2, 3...
    
    # Check if client has location saved
    location = await get_client_location(phone_number)
    has_location = location is not None
    
    # Get client's WhatsApp contact if saved
    whatsapp_contact = await get_client_whatsapp_number(phone_number)
    
    order_doc = {
        "numero_pedido": numero_pedido,
        "sequence_number": seq_number,
        "nombre": data.get('nombre', ''),
        "telefono": phone_number,
        "whatsapp_contact": whatsapp_contact,  # Actual contact number
        "direccion": data.get('direccion', ''),
        "tipo_entrega": data.get('tipo_entrega', 'retiro'),
        "items": data.get('items', ''),
        "cantidades": data.get('cantidades', ''),
        "items_formatted": data.get('items_formatted', ''),
        "modificaciones": data.get('modificaciones', ''),
        "subtotal": int(data.get('subtotal', 0)),
        "costo_delivery": int(data.get('delivery', 0)),
        "total": int(data.get('total', 0)),
        "estado": "pendiente",  # pendiente, confirmado, preparando, listo, en_camino, entregado, cancelado
        "whatsapp_phone": phone_number,  # LID or phone for bot communication
        "has_location": has_location,
        "location": location,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "pending_whatsapp_request": not whatsapp_contact  # Flag to request WhatsApp number
    }
    
    await db.sandwich_pedidos.insert_one(order_doc)
    print(f"[Sandwich Bot] Order created: #{numero_pedido}")
    return order_doc


async def admin_confirm_order(numero_pedido: str, admin_phone: str):
    """Admin confirms an order"""
    order = await db.sandwich_pedidos.find_one({"numero_pedido": numero_pedido})
    
    if not order:
        return f"❌ No encontré el pedido #{numero_pedido}"
    
    if order.get('estado') != 'pendiente':
        return f"⚠️ El pedido #{numero_pedido} ya está en estado: {order.get('estado')}"
    
    await db.sandwich_pedidos.update_one(
        {"numero_pedido": numero_pedido},
        {"$set": {
            "estado": "confirmado",
            "confirmado_por": admin_phone,
            "confirmado_at": datetime.now(timezone.utc).isoformat()
        }}
    )
    
    # Notify client
    config = await get_sandwich_config()
    tiempo = config.get('tiempo_preparacion', '20-30 minutos')
    
    client_msg = f"""✅ *¡PEDIDO CONFIRMADO!*

📋 Pedido #{numero_pedido}
⏱️ Tiempo estimado: {tiempo}

{'🛵 Te lo llevamos a tu dirección' if order['tipo_entrega'] == 'delivery' else '🏪 Te avisamos cuando esté listo para retirar'}

¡Gracias por tu pedido! 🙌"""
    
    try:
        await send_sandwich_message(order['telefono'], client_msg)
    except Exception as e:
        print(f"[Sandwich Bot] Error notifying client: {e}")
    
    # Admin confirmation message (without "needs approval" - they ARE the approver)
    return f"""✅ *PEDIDO #{numero_pedido} CONFIRMADO*

👤 {order['nombre']}
💰 ${order['total']:,}

Cliente notificado ✓

Para marcar como LISTO: *LISTO {numero_pedido}*"""


async def admin_reject_order(numero_pedido: str, admin_phone: str, motivo: str = ""):
    """Admin rejects an order"""
    order = await db.sandwich_pedidos.find_one({"numero_pedido": numero_pedido})
    
    if not order:
        return f"❌ No encontré el pedido #{numero_pedido}"
    
    await db.sandwich_pedidos.update_one(
        {"numero_pedido": numero_pedido},
        {"$set": {
            "estado": "cancelado",
            "cancelado_por": admin_phone,
            "motivo_cancelacion": motivo,
            "cancelado_at": datetime.now(timezone.utc).isoformat()
        }}
    )
    
    client_msg = f"""❌ *PEDIDO CANCELADO*

Lamentablemente no podemos procesar tu pedido #{numero_pedido} en este momento.
{f'Motivo: {motivo}' if motivo else ''}

Disculpá las molestias. ¿Querés hacer otro pedido?"""
    
    try:
        await send_sandwich_message(order['telefono'], client_msg)
    except Exception as e:
        print(f"[Sandwich Bot] Error notifying client: {e}")
    
    return f"✅ Pedido #{numero_pedido} cancelado. Se notificó al cliente."


async def admin_order_ready(numero_pedido: str, admin_phone: str):
    """Admin or delivery marks order as ready"""
    order = await db.sandwich_pedidos.find_one({"numero_pedido": numero_pedido})
    
    if not order:
        return f"❌ No encontré el pedido #{numero_pedido}"
    
    await db.sandwich_pedidos.update_one(
        {"numero_pedido": numero_pedido},
        {"$set": {
            "estado": "listo",
            "listo_at": datetime.now(timezone.utc).isoformat(),
            "listo_por": admin_phone
        }}
    )
    
    if order['tipo_entrega'] == 'delivery':
        client_msg = f"""🛵 *¡TU PEDIDO ESTÁ LISTO!*

Pedido #{numero_pedido}

Ya está preparado y pronto saldrá para entrega.
¡En unos minutos lo tenés! 🙌"""
        
        # Notify all deliveries about ready order
        delivery_msg = f"""📦 *PEDIDO LISTO PARA ENTREGA*

📋 Pedido #{numero_pedido}
👤 {order.get('nombre', 'Cliente')}
📍 {order.get('direccion', 'Sin dirección')}
💰 ${order.get('total', 0):,}

Para ver detalles: *PEDIDO {numero_pedido}*
Para marcar en camino: *ENCAMINO {numero_pedido}*"""
        
        await notify_all_deliveries(delivery_msg)
    else:
        client_msg = f"""🏪 *¡TU PEDIDO ESTÁ LISTO!*

Pedido #{numero_pedido}

Ya podés pasar a retirarlo.
¡Te esperamos! 🙌"""
    
    try:
        await send_sandwich_message(order['telefono'], client_msg)
    except Exception as e:
        print(f"[Sandwich Bot] Error notifying client: {e}")
    
    return f"✅ Pedido #{numero_pedido} marcado como LISTO. Se notificó al cliente{' y deliveries' if order['tipo_entrega'] == 'delivery' else ''}."


async def client_cancel_order(phone_number: str):
    """Client cancels their pending order"""
    # Find the most recent pending or confirmed order for this client
    order = await db.sandwich_pedidos.find_one(
        {"telefono": phone_number, "estado": {"$in": ["pendiente", "confirmado"]}},
        sort=[("created_at", -1)]
    )
    
    if not order:
        return None, "No tenés pedidos activos para cancelar."
    
    await db.sandwich_pedidos.update_one(
        {"numero_pedido": order['numero_pedido']},
        {"$set": {
            "estado": "cancelado",
            "cancelado_por": "cliente",
            "cancelado_at": datetime.now(timezone.utc).isoformat()
        }}
    )
    
    # Notify all admins
    admin_msg = f"""⚠️ *PEDIDO CANCELADO POR CLIENTE*

📋 Pedido #{order['numero_pedido']}
👤 {order['nombre']}
💰 ${order['total']:,}

El cliente canceló su pedido."""
    
    await notify_all_admins(admin_msg)
    
    return order, f"✅ Tu pedido #{order['numero_pedido']} ha sido cancelado."


async def get_client_active_order(phone_number: str):
    """Get client's active order if any"""
    order = await db.sandwich_pedidos.find_one(
        {"telefono": phone_number, "estado": {"$in": ["pendiente", "confirmado", "preparando", "listo"]}},
        sort=[("created_at", -1)]
    )
    return order


# ============ DELIVERY ROLE ============

async def is_delivery_person(phone_number: str) -> bool:
    """Check if phone number belongs to a delivery person"""
    config = await get_sandwich_config()
    delivery_phones = config.get('delivery_phones', [])
    
    # Normalize phone number for comparison
    phone_digits = ''.join(filter(str.isdigit, str(phone_number)))[-10:]
    
    for dp in delivery_phones:
        dp_digits = ''.join(filter(str.isdigit, str(dp)))[-10:]
        if phone_digits == dp_digits or phone_digits.endswith(dp_digits) or dp_digits.endswith(phone_digits):
            return True
    
    return False


async def get_order_for_delivery(numero_pedido: str):
    """Get order details for delivery person"""
    order = await db.sandwich_pedidos.find_one({"numero_pedido": numero_pedido})
    
    if not order:
        return None, f"❌ No encontré el pedido #{numero_pedido}"
    
    # Get client location if available
    location_info = ""
    if order.get('has_location') and order.get('location'):
        lat = order['location'].get('latitude')
        lng = order['location'].get('longitude')
        location_info = f"\n📍 *Ubicación:* https://maps.google.com/?q={lat},{lng}"
    
    whatsapp_contact = order.get('whatsapp_contact', 'No disponible')
    
    response = f"""🛵 *DETALLES PEDIDO #{numero_pedido}*

👤 *Cliente:* {order['nombre']}
📱 *WhatsApp:* {whatsapp_contact}
🏠 *Dirección:* {order['direccion']}{location_info}

🛒 *Pedido:*
{order['items_formatted']}

{'✏️ *Modificaciones:* ' + order.get('modificaciones', '') if order.get('modificaciones') and order.get('modificaciones').lower() != 'ninguna' else ''}

💰 *Total:* ${order['total']:,}
📊 *Estado:* {order['estado'].upper()}

---
Para marcar en camino: *ENCAMINO {numero_pedido}*
Para marcar entregado: *ENTREGADO {numero_pedido}*"""
    
    return order, response


async def delivery_mark_on_way(numero_pedido: str, delivery_phone: str):
    """Delivery marks order as on the way"""
    order = await db.sandwich_pedidos.find_one({"numero_pedido": numero_pedido})
    
    if not order:
        return f"❌ No encontré el pedido #{numero_pedido}"
    
    await db.sandwich_pedidos.update_one(
        {"numero_pedido": numero_pedido},
        {"$set": {
            "estado": "en_camino",
            "delivery_phone": delivery_phone,
            "en_camino_at": datetime.now(timezone.utc).isoformat()
        }}
    )
    
    # Notify client
    client_msg = f"""🛵 *¡TU PEDIDO ESTÁ EN CAMINO!*

Pedido #{numero_pedido}

El delivery ya salió a entregarte.
¡En unos minutos llega! 🙌"""
    
    try:
        await send_sandwich_message(order['telefono'], client_msg)
    except Exception as e:
        print(f"[Sandwich Bot] Error notifying client: {e}")
    
    return f"✅ Pedido #{numero_pedido} marcado EN CAMINO. Cliente notificado."


async def delivery_mark_delivered(numero_pedido: str, delivery_phone: str):
    """Delivery marks order as delivered"""
    order = await db.sandwich_pedidos.find_one({"numero_pedido": numero_pedido})
    
    if not order:
        return f"❌ No encontré el pedido #{numero_pedido}"
    
    await db.sandwich_pedidos.update_one(
        {"numero_pedido": numero_pedido},
        {"$set": {
            "estado": "entregado",
            "entregado_at": datetime.now(timezone.utc).isoformat()
        }}
    )
    
    # Notify client
    client_msg = f"""✅ *¡PEDIDO ENTREGADO!*

Pedido #{numero_pedido}

¡Gracias por elegirnos! 🙌
Esperamos que lo disfrutes.

¿Qué tal estuvo? Tu opinión nos ayuda a mejorar."""
    
    try:
        await send_sandwich_message(order['telefono'], client_msg)
    except Exception as e:
        print(f"[Sandwich Bot] Error notifying client: {e}")
    
    return f"✅ Pedido #{numero_pedido} marcado como ENTREGADO."


# ============ MAIN MESSAGE PROCESSOR ============

async def process_sandwich_message_with_ai(phone_number: str, message: str, push_name: str = "", location: dict = None):
    """Process incoming message with ChatGPT and return response"""
    import re
    
    config = await get_sandwich_config()
    
    if not config.get("bot_activo", True):
        return None
    
    # Handle location message
    if location:
        lat = location.get('latitude') or location.get('degreesLatitude')
        lng = location.get('longitude') or location.get('degreesLongitude')
        if lat and lng:
            await save_client_location(phone_number, lat, lng)
            return "¡Perfecto! Ya guardé tu ubicación 📍 Así el delivery te encuentra más fácil."
    
    # Check if message contains location data (some formats)
    if 'latitude' in message.lower() or 'degreeslatitude' in message.lower():
        try:
            import json
            loc_data = json.loads(message)
            lat = loc_data.get('latitude') or loc_data.get('degreesLatitude')
            lng = loc_data.get('longitude') or loc_data.get('degreesLongitude')
            if lat and lng:
                await save_client_location(phone_number, lat, lng)
                return "¡Perfecto! Ya guardé tu ubicación 📍 Así el delivery te encuentra más fácil."
        except Exception:
            pass
    
    # Normalize phone for comparison
    def normalize_phone(phone):
        if not phone:
            return ""
        return ''.join(filter(str.isdigit, str(phone)))[-10:]
    
    admin_phone = config.get('admin_phone', '')
    admin_lid = config.get('admin_lid', '')
    phone_digits = ''.join(filter(str.isdigit, str(phone_number)))
    
    # ============ LOGIN/LOGOUT DETECTION ============
    message_lower = message.lower().strip()
    
    # Check for logout command first
    if message_lower in ['cerrar sesion', 'cerrar sesión', 'logout', 'salir']:
        session = await get_session(phone_number)
        if session:
            await close_session(phone_number)
            return f"✅ Sesión cerrada. ¡Hasta luego, {session.get('username')}!"
        return "No tenés una sesión activa."
    
    # Check for login attempt: "soy admin1 clave 1234" or "soy delivery1 clave 1234"
    login_match = re.match(r'soy\s+(\w+)\s+clave\s+(\S+)', message_lower)
    if login_match:
        username = login_match.group(1)
        password = login_match.group(2)
        
        user = await authenticate_user(username, password)
        if user:
            await create_session(phone_number, username, user['role'])
            role_emoji = "👤" if user['role'] == 'admin' else "🛵"
            pending_count = await db.sandwich_pedidos.count_documents({"estado": "pendiente"})
            
            welcome_msg = f"""{role_emoji} *¡Bienvenido, {username}!*

Sesión iniciada como *{user['role'].upper()}*
📊 Pedidos pendientes: {pending_count}

Para cerrar sesión: *cerrar sesión*"""
            
            if user['role'] == 'admin':
                welcome_msg += """

📋 *Comandos Admin:*
• *PEDIDOS* - Ver pendientes
• *CONFIRMAR X* / *RECHAZAR X*
• *LISTO X* / *ENCAMINO X* / *ENTREGADO X*"""
            else:
                welcome_msg += """

📋 *Comandos Delivery:*
• *PEDIDO #X* - Ver detalles
• *LISTO X* - Marcar listo
• *ENCAMINO X* - En camino
• *ENTREGADO X* - Entregado"""
            
            return welcome_msg
        else:
            return "❌ Usuario o clave incorrectos. Intentá de nuevo.\n\nFormato: *soy [usuario] clave [clave]*"
    
    # ============ DETERMINE USER ROLE ============
    
    # Check if master admin (from config)
    is_master_admin_user = False
    if admin_lid and (phone_digits == admin_lid or phone_number == admin_lid):
        is_master_admin_user = True
    elif admin_phone:
        normalized_admin = normalize_phone(admin_phone)
        normalized_phone = normalize_phone(phone_number)
        if normalized_phone == normalized_admin or normalized_phone.endswith(normalized_admin) or normalized_admin.endswith(normalized_phone):
            is_master_admin_user = True
            if len(phone_digits) > 12 and not admin_lid:
                await db.sandwich_config.update_one(
                    {"_id": "bot_config"},
                    {"$set": {"admin_lid": phone_digits}}
                )
    
    # Check if logged in as admin or delivery
    session = await get_session(phone_number)
    is_logged_admin = session and session.get('role') == 'admin'
    is_logged_delivery = session and session.get('role') == 'delivery'
    
    # Check old-style delivery (from config list)
    is_config_delivery = await is_delivery_person(phone_number)
    
    # Determine effective role
    is_admin = is_master_admin_user or is_logged_admin
    is_delivery = is_logged_delivery or is_config_delivery
    
    # ============ MASTER ADMIN ONLY COMMANDS ============
    if is_master_admin_user:
        # CREAR ADMIN/DELIVERY command
        crear_match = re.match(r'(?:CREAR|crear)\s+(ADMIN|admin|DELIVERY|delivery)\s+(\w+)\s+(\S+)', message.strip())
        if crear_match:
            role = crear_match.group(1).lower()
            username = crear_match.group(2)
            password = crear_match.group(3)
            user, msg = await create_bot_user(username, password, role, phone_number)
            return msg
        
        # ELIMINAR command
        eliminar_match = re.match(r'(?:ELIMINAR|eliminar)\s+(\w+)', message.strip())
        if eliminar_match:
            username = eliminar_match.group(1)
            success, msg = await delete_bot_user(username)
            return msg
        
        # USUARIOS command
        if message_lower == 'usuarios':
            users = await get_all_bot_users()
            if not users:
                return "No hay usuarios creados.\n\nPara crear: *CREAR ADMIN usuario clave*\no *CREAR DELIVERY usuario clave*"
            
            msg = "👥 *USUARIOS REGISTRADOS:*\n\n"
            for u in users:
                role_emoji = "👤" if u['role'] == 'admin' else "🛵"
                status = "✅" if u.get('activo', True) else "❌"
                msg += f"{role_emoji} *{u['username']}* - {u['role'].upper()} {status}\n"
            
            # Show active sessions
            sessions = await db.sandwich_bot_sessions.find({}).to_list(100)
            if sessions:
                msg += "\n📱 *Sesiones activas:*\n"
                for s in sessions:
                    msg += f"• {s.get('username')} en {s.get('phone_number')}\n"
            
            msg += "\nPara eliminar: *ELIMINAR usuario*\nPara cerrar sesión: *KICKEAR usuario*"
            return msg
        
        # KICKEAR command (close someone's session)
        kickear_match = re.match(r'(?:KICKEAR|kickear|KICK|kick)\s+(\w+)', message.strip())
        if kickear_match:
            username = kickear_match.group(1)
            count = await close_session_by_username(username)
            if count > 0:
                return f"✅ Sesión de *{username}* cerrada."
            return f"❌ *{username}* no tiene sesión activa."
    
    # ============ ADMIN COMMANDS ============
    if is_admin:
        logged_as = f" ({session.get('username')})" if session else ""
        print(f"[Sandwich Bot] ✅ ADMIN DETECTED{logged_as}! Message: {message[:50]}")
        
        # CONFIRMAR command
        confirm_match = re.match(r'(?:CONFIRMAR|confirmar|Confirmar)\s+(\d+)', message.strip())
        if confirm_match:
            numero = confirm_match.group(1)
            return await admin_confirm_order(numero, phone_number)
        
        # RECHAZAR command
        reject_match = re.match(r'(?:RECHAZAR|rechazar|Rechazar)\s+(\d+)\s*(.*)?', message.strip())
        if reject_match:
            numero = reject_match.group(1)
            motivo = reject_match.group(2) or ""
            return await admin_reject_order(numero, phone_number, motivo)
        
        # LISTO command
        listo_match = re.match(r'(?:LISTO|listo|Listo)\s+(\d+)', message.strip())
        if listo_match:
            numero = listo_match.group(1)
            return await admin_order_ready(numero, phone_number)
        
        # ESTADO command (answer status query)
        estado_match = re.match(r'(?:ESTADO|estado|Estado)\s+(\d+)\s+(.+)', message.strip())
        if estado_match:
            numero = estado_match.group(1)
            respuesta = estado_match.group(2)
            return await answer_status_query(numero, respuesta, phone_number)
        
        # PAUSAR command
        pausar_match = re.match(r'(?:PAUSAR|pausar|Pausar)\s+(\d+)', message.strip())
        if pausar_match:
            client_phone = pausar_match.group(1)
            await pause_sandwich_chat(client_phone, phone_number)
            return f"✅ Chat pausado para {client_phone}. Ahora podés atenderlo manualmente.\n\nPara reanudar: *REANUDAR {client_phone}*\n\n⚠️ El bot se reanudará automáticamente en {HANDOVER_TIMEOUT_HOURS} horas."
        
        # REANUDAR command
        reanudar_match = re.match(r'(?:REANUDAR|reanudar|Reanudar)\s+(\d+)', message.strip())
        if reanudar_match:
            client_phone = reanudar_match.group(1)
            await resume_sandwich_chat(client_phone)
            return f"✅ Bot reanudado para {client_phone}."
        
        # ENCAMINO command (admin can also use)
        encamino_match = re.match(r'(?:ENCAMINO|encamino|Encamino|EN CAMINO|en camino)\s+(\d+)', message.strip())
        if encamino_match:
            numero = encamino_match.group(1)
            return await delivery_mark_on_way(numero, phone_number)
        
        # ENTREGADO command
        entregado_match = re.match(r'(?:ENTREGADO|entregado|Entregado)\s+(\d+)', message.strip())
        if entregado_match:
            numero = entregado_match.group(1)
            return await delivery_mark_delivered(numero, phone_number)
        
        # DELIVERY command - register delivery person (old style)
        delivery_add_match = re.match(r'(?:DELIVERY|delivery)\s+(\d+)', message.strip())
        if delivery_add_match:
            new_delivery_phone = delivery_add_match.group(1)
            current_deliveries = config.get('delivery_phones', [])
            if new_delivery_phone not in current_deliveries:
                current_deliveries.append(new_delivery_phone)
                await update_sandwich_config({"delivery_phones": current_deliveries})
            return f"✅ {new_delivery_phone} agregado como delivery.\n\nDeliveries registrados: {', '.join(current_deliveries)}"
        
        # PEDIDOS command
        if message_lower == 'pedidos':
            pending = await db.sandwich_pedidos.find({"estado": "pendiente"}).to_list(10)
            if pending:
                msg = "📋 *PEDIDOS PENDIENTES:*\n\n"
                for p in pending:
                    msg += f"• *#{p['numero_pedido']}* - {p.get('nombre', 'Sin nombre')} - ${p.get('total', 0):,}\n"
                msg += "\nPara confirmar: *CONFIRMAR [N°]*"
                return msg
            return "✅ No hay pedidos pendientes"
        
        # PEDIDO #X command - view order details
        pedido_match = re.match(r'(?:PEDIDO|pedido|Pedido)\s*#?(\d+)', message.strip())
        if pedido_match:
            numero = pedido_match.group(1)
            order, response = await get_order_for_delivery(numero)
            return response
        
        # Admin greeting
        if message_lower in ['hola', 'hi', 'hey', 'buenas']:
            pending_count = await db.sandwich_pedidos.count_documents({"estado": "pendiente"})
            admin_greeting = f"""👋 *¡Hola Admin{logged_as}!*

📊 *Pedidos pendientes:* {pending_count}

📋 *Comandos:*
• *PEDIDOS* - Ver pendientes
• *PEDIDO #X* - Ver detalles
• *CONFIRMAR X* - Confirmar pedido
• *RECHAZAR X [motivo]* - Rechazar pedido
• *LISTO X* - Marcar como listo
• *ENCAMINO X* - Marcar en camino
• *ENTREGADO X* - Marcar entregado
• *ESTADO X [resp]* - Responder consulta"""
            
            if is_master_admin_user:
                admin_greeting += """

👑 *Comandos Admin Principal:*
• *CREAR ADMIN user clave*
• *CREAR DELIVERY user clave*
• *USUARIOS* - Ver usuarios
• *ELIMINAR user* - Eliminar usuario
• *KICKEAR user* - Cerrar sesión"""
            
            return admin_greeting
        
        return """👋 Comandos disponibles:

• *PEDIDOS* - Ver pendientes
• *CONFIRMAR X* / *RECHAZAR X*
• *LISTO X* / *ENCAMINO X* / *ENTREGADO X*"""
    
    # ============ DELIVERY COMMANDS ============
    if is_delivery:
        print(f"[Sandwich Bot] 🛵 DELIVERY DETECTED! Message: {message[:50]}")
        
        # PEDIDO #X command
        pedido_match = re.match(r'(?:PEDIDO|pedido|Pedido)\s*#?(\d+)', message.strip())
        if pedido_match:
            numero = pedido_match.group(1)
            order, response = await get_order_for_delivery(numero)
            return response
        
        # LISTO command (delivery can also mark as ready)
        listo_match = re.match(r'(?:LISTO|listo|Listo)\s+(\d+)', message.strip())
        if listo_match:
            numero = listo_match.group(1)
            return await admin_order_ready(numero, phone_number)
        
        # ENCAMINO command
        encamino_match = re.match(r'(?:ENCAMINO|encamino|Encamino|EN CAMINO|en camino)\s+(\d+)', message.strip())
        if encamino_match:
            numero = encamino_match.group(1)
            return await delivery_mark_on_way(numero, phone_number)
        
        # ENTREGADO command
        entregado_match = re.match(r'(?:ENTREGADO|entregado|Entregado)\s+(\d+)', message.strip())
        if entregado_match:
            numero = entregado_match.group(1)
            return await delivery_mark_delivered(numero, phone_number)
        
        # Delivery greeting
        logged_as = f" ({session.get('username')})" if session else ""
        if message_lower in ['hola', 'hi', 'hey', 'buenas']:
            # Show pending deliveries
            ready_orders = await db.sandwich_pedidos.find(
                {"estado": {"$in": ["confirmado", "preparando", "listo", "en_camino"]}, "tipo_entrega": "delivery"}
            ).to_list(10)
            
            if ready_orders:
                msg = f"🛵 *¡Hola Delivery{logged_as}!*\n\n📦 *Pedidos activos:*\n\n"
                for o in ready_orders:
                    msg += f"• *#{o['numero_pedido']}* - {o.get('nombre', 'Sin nombre')} - {o['estado'].upper()}\n"
                msg += "\nPara ver detalles: *PEDIDO #X*"
                return msg
            return f"🛵 *¡Hola Delivery{logged_as}!*\n\nNo hay pedidos activos para entrega.\n\nPara ver un pedido: *PEDIDO #X*"
        
        return """🛵 *Comandos Delivery:*

• *PEDIDO #X* - Ver detalles del pedido
• *LISTO X* - Marcar pedido como listo
• *ENCAMINO X* - Marcar en camino
• *ENTREGADO X* - Marcar entregado
• *cerrar sesión* - Salir"""
    
    # ============ CLIENT FLOW ============
    
    # Check if paused (human handover)
    if await is_sandwich_chat_paused(phone_number):
        print(f"[Sandwich Bot] Chat {phone_number} is paused")
        return None
    
    # Save incoming message
    await save_sandwich_message(phone_number, message, "user", push_name)
    
    # Check if client is providing their WhatsApp number after order
    import re as regex_module
    phone_in_message = regex_module.search(r'\b(\d{10,12})\b', message)
    if phone_in_message:
        # Check if there's a pending WhatsApp request for this client
        pending_order = await db.sandwich_pedidos.find_one(
            {"telefono": phone_number, "pending_whatsapp_request": True},
            sort=[("created_at", -1)]
        )
        if pending_order:
            whatsapp_number = phone_in_message.group(1)
            await save_client_whatsapp_number(phone_number, whatsapp_number)
            await db.sandwich_pedidos.update_one(
                {"numero_pedido": pending_order['numero_pedido']},
                {"$set": {
                    "whatsapp_contact": whatsapp_number,
                    "pending_whatsapp_request": False
                }}
            )
            
            # Notify admin
            config = await get_sandwich_config()
            admin_msg = f"📱 Pedido #{pending_order['numero_pedido']} - WhatsApp del cliente: {whatsapp_number}"
            admin_lid = config.get('admin_lid', '')
            admin_phone_cfg = config.get('admin_phone', '')
            try:
                if admin_lid:
                    await send_sandwich_message_to_jid(f"{admin_lid}@lid", admin_msg)
                elif admin_phone_cfg:
                    await send_sandwich_message(admin_phone_cfg, admin_msg)
            except Exception:
                pass
            
            response = f"✅ ¡Perfecto! Guardé tu número {whatsapp_number}. El delivery podrá contactarte si es necesario. 👍"
            await save_sandwich_message(phone_number, response, "assistant")
            return response
    
    # Check for client commands first
    message_lower = message.lower().strip()
    
    # CANCELAR command
    if 'cancelar' in message_lower or message_lower == 'cancelo':
        order, response = await client_cancel_order(phone_number)
        if order:
            await save_sandwich_message(phone_number, response, "assistant")
            return response
    
    # Status query - "cómo va mi pedido"
    if any(phrase in message_lower for phrase in ['cómo va', 'como va', 'estado de mi pedido', 'mi pedido', 'dónde está', 'donde esta']):
        active_order = await get_client_active_order(phone_number)
        if active_order:
            await create_status_query(phone_number, active_order['numero_pedido'])
            response = f"🔍 Dejame consultar el estado de tu pedido #{active_order['numero_pedido']}...\n\nTe respondo en un momento."
            await save_sandwich_message(phone_number, response, "assistant")
            return response
    
    # Human handover request
    if any(phrase in message_lower for phrase in ['hablar con', 'encargado', 'humano', 'persona', 'gerente', 'manager', 'alguien']):
        await pause_sandwich_chat(phone_number, "client_request", "human_handover")
        
        # Notify admin
        config = await get_sandwich_config()
        admin_msg = f"""👤 *SOLICITUD DE ATENCIÓN HUMANA*

Un cliente quiere hablar con alguien:
📱 {phone_number}
💬 Mensaje: "{message}"

Para atenderlo manualmente y luego reanudar el bot:
*REANUDAR {phone_number}*

⚠️ El bot se reanudará automáticamente en {HANDOVER_TIMEOUT_HOURS} horas."""
        
        admin_lid = config.get('admin_lid', '')
        admin_phone_conf = config.get('admin_phone', '')
        
        try:
            if admin_lid:
                await send_sandwich_message_to_jid(f"{admin_lid}@lid", admin_msg)
            elif admin_phone_conf:
                await send_sandwich_message(admin_phone_conf, admin_msg)
        except Exception as e:
            print(f"[Sandwich Bot] Error notifying admin: {e}")
        
        response = "Un momento, te comunico con el encargado 👤\n\nAlguien te va a atender en breve."
        await save_sandwich_message(phone_number, response, "assistant")
        return response
    
    # Get conversation history
    history = await get_sandwich_conversation_history(phone_number, limit=10)
    
    # Build system prompt
    instrucciones = config.get("instrucciones_bot", DEFAULT_SANDWICH_CONFIG["instrucciones_bot"])
    menu_formateado = await format_menu_for_bot()
    
    system_prompt = instrucciones.format(
        nombre_negocio=config.get('nombre_negocio', 'Modo Cocina'),
        menu_formateado=menu_formateado,
        costo_delivery=config.get('costo_delivery', 500),
        pedido_minimo=config.get('pedido_minimo_delivery', 2000),
        tiempo_preparacion=config.get('tiempo_preparacion', '20-30 minutos'),
        horario_apertura=config.get('horario_apertura', '10:00'),
        horario_cierre=config.get('horario_cierre', '22:00'),
        dias_abierto=', '.join(config.get('dias_abierto', ['lunes', 'martes', 'miércoles', 'jueves', 'viernes', 'sábado'])),
        direccion_local=config.get('direccion_local', 'Av. Principal 123'),
        zona_restringida=config.get('zona_restringida', 'Valle Viejo')
    )
    
    is_new_conversation = len(history) <= 1
    
    try:
        llm_key = os.environ.get('EMERGENT_LLM_KEY')
        if not llm_key:
            raise ValueError("EMERGENT_LLM_KEY not configured")
        
        initial_messages = [{"role": "system", "content": system_prompt}]
        
        if is_new_conversation:
            welcome_msg = config.get("mensaje_bienvenida", DEFAULT_SANDWICH_CONFIG["mensaje_bienvenida"])
            initial_messages.append({"role": "assistant", "content": welcome_msg})
        
        for msg in history:
            role = msg.get("role", "user")
            content = msg.get("message", "")
            if content:
                initial_messages.append({"role": role, "content": content})
        
        llm = LlmChat(
            api_key=llm_key,
            session_id=f"sandwich-{phone_number}",
            system_message="",
            initial_messages=initial_messages
        )
        
        llm = llm.with_model('openai', 'gpt-4o')
        
        ai_response = await llm.send_message(UserMessage(text=message))
        
        # Process commands in response
        ai_response = await process_sandwich_bot_commands(phone_number, ai_response)
        
        await save_sandwich_message(phone_number, ai_response, "assistant")
        
        return ai_response
        
    except Exception as e:
        print(f"[Sandwich Bot] Error processing message: {e}")
        import traceback
        traceback.print_exc()
        fallback = "Disculpa, estoy teniendo dificultades técnicas. Un encargado se comunicará contigo pronto. 🙏"
        await save_sandwich_message(phone_number, fallback, "assistant")
        return fallback


async def process_sandwich_bot_commands(phone_number: str, ai_response: str):
    """Process special commands in bot response"""
    import re
    
    # Check for CREAR_PEDIDO command
    crear_match = re.search(r'\[CREAR_PEDIDO\](.*?)\[/CREAR_PEDIDO\]', ai_response, re.DOTALL)
    if crear_match:
        try:
            data_text = crear_match.group(1)
            data = {}
            for line in data_text.strip().split('\n'):
                if ':' in line:
                    key, value = line.split(':', 1)
                    data[key.strip().lower()] = value.strip()
            
            # Format items for display
            items = data.get('items', '').split(',')
            cantidades = data.get('cantidades', '').split(',')
            items_formatted = ""
            for i, item in enumerate(items):
                cant = cantidades[i].strip() if i < len(cantidades) else "1"
                items_formatted += f"• {cant}x {item.strip()}\n"
            data['items_formatted'] = items_formatted
            
            # Check if within operating hours
            config = await get_sandwich_config()
            hora_apertura = config.get('horario_apertura', '20:00')
            hora_cierre = config.get('horario_cierre', '01:00')
            
            is_open = is_within_operating_hours(hora_apertura, hora_cierre)
            
            if is_open:
                # Normal order during operating hours
                order = await create_sandwich_order(phone_number, data)
                
                # Notify admin
                await notify_sandwich_admin(order)
                
                success_msg = f"""✅ *¡PEDIDO REGISTRADO!*

📋 *N° de Pedido:* #{order['numero_pedido']}

⏳ Tu pedido fue enviado al local y está *PENDIENTE DE CONFIRMACIÓN*.
Te avisamos apenas el local lo confirme.

📱 *IMPORTANTE:* ¿Me pasás tu número de WhatsApp para que el delivery pueda contactarte? 
(Escribí solo el número, ej: 3834123456)"""
            else:
                # Create reservation for when store opens
                order = await create_reservation(phone_number, data)
                
                success_msg = f"""📅 *¡RESERVA REGISTRADA!*

📋 *N° de Reserva:* #{order['numero_pedido']}

⏰ Estamos cerrados ahora (abrimos de {hora_apertura} a {hora_cierre}).

Tu pedido quedó guardado como *RESERVA* y lo enviaremos al local apenas abramos. 
Te avisaremos cuando se confirme. 🙌

📱 *IMPORTANTE:* ¿Me pasás tu número de WhatsApp para que el delivery pueda contactarte? 
(Escribí solo el número, ej: 3834123456)"""
            
            ai_response = re.sub(r'\[CREAR_PEDIDO\].*?\[/CREAR_PEDIDO\]', '', ai_response, flags=re.DOTALL)
            ai_response = ai_response.replace('Procesando tu pedido... ⏳', success_msg)
            
            # Remove any extra text that GPT might have added
            if success_msg in ai_response:
                ai_response = success_msg
            
        except Exception as e:
            print(f"[Sandwich Bot] Error creating order: {e}")
            import traceback
            traceback.print_exc()
            ai_response = re.sub(r'\[CREAR_PEDIDO\].*?\[/CREAR_PEDIDO\]', '', ai_response, flags=re.DOTALL)
            ai_response = ai_response.replace('Procesando tu pedido... ⏳', '❌ Hubo un error al crear el pedido. Por favor, intentá de nuevo.')
    
    # Check for PAUSAR_BOT command
    if '[PAUSAR_BOT]' in ai_response:
        await pause_sandwich_chat(phone_number, "bot_request", "human_handover")
        ai_response = ai_response.replace('[PAUSAR_BOT]', '')
        
        # Notify admin
        config = await get_sandwich_config()
        admin_msg = f"""👤 *SOLICITUD DE ATENCIÓN HUMANA*

📱 Cliente: {phone_number}

Para atenderlo y luego reanudar:
*REANUDAR {phone_number}*"""
        
        admin_lid = config.get('admin_lid', '')
        admin_phone = config.get('admin_phone', '')
        
        try:
            if admin_lid:
                await send_sandwich_message_to_jid(f"{admin_lid}@lid", admin_msg)
            elif admin_phone:
                await send_sandwich_message(admin_phone, admin_msg)
        except Exception:
            pass
    
    # Check for CONSULTAR_ESTADO command
    if '[CONSULTAR_ESTADO]' in ai_response:
        ai_response = ai_response.replace('[CONSULTAR_ESTADO]', '')
        active_order = await get_client_active_order(phone_number)
        if active_order:
            await create_status_query(phone_number, active_order['numero_pedido'])
    
    # Check for CANCELAR_PEDIDO command
    if '[CANCELAR_PEDIDO]' in ai_response:
        ai_response = ai_response.replace('[CANCELAR_PEDIDO]', '')
        order, msg = await client_cancel_order(phone_number)
        if order:
            ai_response += f"\n\n{msg}"
    
    # Check if client provided WhatsApp number after order
    # Look for phone number pattern in recent orders
    recent_order = await db.sandwich_pedidos.find_one(
        {"telefono": phone_number, "pending_whatsapp_request": True},
        sort=[("created_at", -1)]
    )
    if recent_order:
        # Try to extract phone number from message
        phone_match = re.search(r'\b(\d{10,12})\b', ai_response)
        if not phone_match:
            # Check original message (we don't have it here, but the bot might echo it)
            pass
    
    ai_response = re.sub(r'\[/?CREAR_PEDIDO\]', '', ai_response)
    ai_response = ai_response.strip()
    
    return ai_response


async def save_client_phone_from_message(phone_number: str, message: str):
    """Try to extract and save WhatsApp number from client message"""
    import re
    
    # Check if there's a pending request
    order = await db.sandwich_pedidos.find_one(
        {"telefono": phone_number, "pending_whatsapp_request": True},
        sort=[("created_at", -1)]
    )
    
    if not order:
        return None
    
    # Try to extract phone number
    phone_match = re.search(r'\b(\d{10,12})\b', message)
    if phone_match:
        whatsapp_number = phone_match.group(1)
        await save_client_whatsapp_number(phone_number, whatsapp_number)
        
        # Update order
        await db.sandwich_pedidos.update_one(
            {"numero_pedido": order['numero_pedido']},
            {"$set": {
                "whatsapp_contact": whatsapp_number,
                "pending_whatsapp_request": False
            }}
        )
        
        # Notify admin about updated contact
        config = await get_sandwich_config()
        admin_msg = f"📱 Pedido #{order['numero_pedido']} - WhatsApp del cliente: {whatsapp_number}"
        
        admin_lid = config.get('admin_lid', '')
        admin_phone = config.get('admin_phone', '')
        
        try:
            if admin_lid:
                await send_sandwich_message_to_jid(f"{admin_lid}@lid", admin_msg)
            elif admin_phone:
                await send_sandwich_message(admin_phone, admin_msg)
        except Exception:
            pass
        
        return whatsapp_number
    
    return None


# ============ WHATSAPP COMMUNICATION ============

async def send_sandwich_message(phone_number: str, message: str):
    """Send a message via WhatsApp sandwich service"""
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{WHATSAPP_SANDWICH_URL}/send",
                json={"phone_number": phone_number, "message": message},
                timeout=30.0
            )
            return response.json()
    except Exception as e:
        print(f"[Sandwich Bot] Error sending message: {e}")
        return {"success": False, "error": str(e)}


async def send_sandwich_message_to_jid(jid: str, message: str):
    """Send a message via WhatsApp sandwich service using JID"""
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{WHATSAPP_SANDWICH_URL}/send-jid",
                json={"jid": jid, "message": message},
                timeout=30.0
            )
            return response.json()
    except Exception as e:
        print(f"[Sandwich Bot] Error sending message to JID: {e}")
        return {"success": False, "error": str(e)}


async def get_sandwich_whatsapp_status():
    """Get WhatsApp connection status for sandwich service"""
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{WHATSAPP_SANDWICH_URL}/status", timeout=10.0)
            return response.json()
    except Exception as e:
        return {"status": "error", "connected": False, "error": str(e)}


async def get_sandwich_whatsapp_qr():
    """Get WhatsApp QR code for sandwich service"""
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{WHATSAPP_SANDWICH_URL}/qr", timeout=10.0)
            return response.json()
    except Exception as e:
        return {"qr": None, "qr_data_url": None, "error": str(e)}


async def connect_sandwich_whatsapp():
    """Initiate WhatsApp connection for sandwich service"""
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(f"{WHATSAPP_SANDWICH_URL}/connect", timeout=10.0)
            return response.json()
    except Exception as e:
        return {"success": False, "error": str(e)}


async def disconnect_sandwich_whatsapp():
    """Disconnect WhatsApp for sandwich service"""
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(f"{WHATSAPP_SANDWICH_URL}/disconnect", timeout=10.0)
            return response.json()
    except Exception as e:
        return {"success": False, "error": str(e)}


async def get_sandwich_conversations():
    """Get all conversations from sandwich WhatsApp service"""
    conversations = {}
    
    try:
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
        
        results = await db.sandwich_messages.aggregate(pipeline).to_list(100)
        
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
        print(f"[Sandwich Bot] Error getting conversations: {e}")
    
    conv_list = list(conversations.values())
    conv_list.sort(key=lambda x: x.get("last_message_time", ""), reverse=True)
    
    return {"conversations": conv_list, "paused_chats": []}


async def get_sandwich_chat_history(phone_number: str, limit: int = 50):
    """Get chat history for a specific number"""
    messages = await db.sandwich_messages.find(
        {"phone_number": phone_number},
        {"_id": 0}
    ).sort("timestamp", -1).limit(limit).to_list(limit)
    
    return list(reversed(messages))

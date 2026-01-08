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

=== FLUJO DE PEDIDO ===

PASO 1 - MOSTRAR MENÚ:
Si el cliente pide ver el menú o no sabe qué pedir, mostrá las opciones disponibles organizadas por categoría.

PASO 2 - TOMAR PEDIDO:
Cuando el cliente elija, confirmá:
- Qué producto quiere
- Cantidad
- Si quiere agregar extras/adicionales

PASO 3 - PREGUNTAR MODIFICACIONES:
IMPORTANTE: Antes de confirmar el pedido, SIEMPRE preguntá:
"¿Querés alguna modificación? Por ejemplo: sin mayonesa, extra queso, bien cocido, etc. 🍔"

PASO 4 - DELIVERY O RETIRO:
Preguntá: "¿Lo querés para delivery o lo retirás por el local?"

PASO 5 - DATOS DEL CLIENTE:
Si es DELIVERY, pedí:
- Nombre
- Dirección completa
- Referencias (opcional)
- Si comparte ubicación, agradecele y guardala

ZONA RESTRINGIDA: Si la dirección incluye "{zona_restringida}", informá amablemente que no hacemos delivery a esa zona pero puede retirar en el local.

Si es RETIRO, pedí:
- Nombre (para el pedido)

PASO 6 - CONFIRMAR PEDIDO:
Mostrá un resumen completo:
"📋 *RESUMEN DE TU PEDIDO*
👤 Nombre: [nombre]
📍 Entrega: [delivery/retiro]
[Dirección si es delivery]
[Modificaciones si las hay]

🛒 *Pedido:*
[lista de items con precios]

💰 Subtotal: $[subtotal]
🛵 Delivery: $[costo_delivery o GRATIS]
💵 *TOTAL: $[total]*

¿Confirmás el pedido? Respondé *SÍ* para confirmar o *MODIFICAR* si querés cambiar algo."

PASO 7 - CREAR PEDIDO:
Cuando confirme, respondé con:

[CREAR_PEDIDO]
nombre: [nombre]
telefono: [telefono del chat]
direccion: [dirección o "Retira en local"]
tipo_entrega: [delivery/retiro]
items: [lista de items separados por coma]
cantidades: [cantidades separadas por coma]
modificaciones: [modificaciones solicitadas o "ninguna"]
subtotal: [subtotal sin delivery]
delivery: [costo delivery o 0]
total: [total final]
[/CREAR_PEDIDO]

Procesando tu pedido... ⏳

=== COMANDOS DEL CLIENTE ===
Si el cliente dice:
- "CANCELAR" o quiere cancelar su pedido → Preguntá si está seguro y luego usa [CANCELAR_PEDIDO]
- "MODIFICAR" o quiere modificar → Preguntá qué quiere cambiar
- "HABLAR CON ALGUIEN" / "ENCARGADO" / "HUMANO" → Respondé: "Un momento, te comunico con el encargado 👤" y usá [PAUSAR_BOT]
- "¿Cómo va mi pedido?" / "Estado de mi pedido" → Respondé: "Déjame consultar con el equipo... 🔍" y usá [CONSULTAR_ESTADO]

=== REGLAS ===
- NUNCA inventes productos que no están en el menú
- NUNCA cambies los precios
- Si algo no está disponible, sugerí alternativas
- El costo de delivery es ${costo_delivery}
- Pedido mínimo para delivery: ${pedido_minimo}
- Tiempo estimado: {tiempo_preparacion}

=== HORARIOS ===
Abierto: {horario_apertura} a {horario_cierre}
Días: {dias_abierto}
Dirección: {direccion_local}

=== PROMOCIONES ===
- Si el cliente pide 3 o más items del mismo producto, ofrecé un 10% de descuento
- Mencioná las promos de forma natural

=== UBICACIÓN COMPARTIDA ===
Si el cliente comparte su ubicación (verás un mensaje con coordenadas), agradecele y confirma que la guardaste:
"¡Perfecto! Ya guardé tu ubicación 📍 Así el delivery te encuentra más fácil."
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
        except:
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
    """Notify admin about new order"""
    config = await get_sandwich_config()
    admin_phone = config.get('admin_phone', '')
    admin_lid = config.get('admin_lid', '')
    
    if not admin_phone and not admin_lid:
        print("[Sandwich Bot] No admin configured for notifications")
        return
    
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
    
    try:
        if admin_lid:
            await send_sandwich_message_to_jid(f"{admin_lid}@lid", notification)
        elif admin_phone:
            await send_sandwich_message(admin_phone, notification)
        print(f"[Sandwich Bot] Notified admin about order {order_data['numero_pedido']}")
    except Exception as e:
        print(f"[Sandwich Bot] Error notifying admin: {e}")


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
    """Admin marks order as ready"""
    order = await db.sandwich_pedidos.find_one({"numero_pedido": numero_pedido})
    
    if not order:
        return f"❌ No encontré el pedido #{numero_pedido}"
    
    await db.sandwich_pedidos.update_one(
        {"numero_pedido": numero_pedido},
        {"$set": {
            "estado": "listo",
            "listo_at": datetime.now(timezone.utc).isoformat()
        }}
    )
    
    if order['tipo_entrega'] == 'delivery':
        client_msg = f"""🛵 *¡TU PEDIDO ESTÁ EN CAMINO!*

Pedido #{numero_pedido}

Nuestro delivery ya salió con tu pedido.
¡En unos minutos lo tenés! 🙌"""
    else:
        client_msg = f"""🏪 *¡TU PEDIDO ESTÁ LISTO!*

Pedido #{numero_pedido}

Ya podés pasar a retirarlo.
¡Te esperamos! 🙌"""
    
    try:
        await send_sandwich_message(order['telefono'], client_msg)
    except Exception as e:
        print(f"[Sandwich Bot] Error notifying client: {e}")
    
    return f"✅ Pedido #{numero_pedido} marcado como LISTO. Se notificó al cliente."


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
    
    # Notify admin
    config = await get_sandwich_config()
    admin_msg = f"""⚠️ *PEDIDO CANCELADO POR CLIENTE*

📋 Pedido #{order['numero_pedido']}
👤 {order['nombre']}
💰 ${order['total']:,}

El cliente canceló su pedido."""
    
    admin_lid = config.get('admin_lid', '')
    admin_phone = config.get('admin_phone', '')
    
    try:
        if admin_lid:
            await send_sandwich_message_to_jid(f"{admin_lid}@lid", admin_msg)
        elif admin_phone:
            await send_sandwich_message(admin_phone, admin_msg)
    except Exception as e:
        print(f"[Sandwich Bot] Error notifying admin: {e}")
    
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
        except:
            pass
    
    # Normalize phone for comparison
    def normalize_phone(phone):
        if not phone:
            return ""
        return ''.join(filter(str.isdigit, str(phone)))[-10:]
    
    admin_phone = config.get('admin_phone', '')
    admin_lid = config.get('admin_lid', '')
    phone_digits = ''.join(filter(str.isdigit, str(phone_number)))
    
    # Check if admin
    is_admin = False
    if admin_lid and (phone_digits == admin_lid or phone_number == admin_lid):
        is_admin = True
    elif admin_phone:
        normalized_admin = normalize_phone(admin_phone)
        normalized_phone = normalize_phone(phone_number)
        if normalized_phone == normalized_admin or normalized_phone.endswith(normalized_admin) or normalized_admin.endswith(normalized_phone):
            is_admin = True
            if len(phone_digits) > 12 and not admin_lid:
                await db.sandwich_config.update_one(
                    {"_id": "bot_config"},
                    {"$set": {"admin_lid": phone_digits}}
                )
    
    # Check if delivery person
    is_delivery = await is_delivery_person(phone_number)
    
    # ============ ADMIN COMMANDS ============
    if is_admin:
        print(f"[Sandwich Bot] ✅ ADMIN DETECTED! Message: {message[:50]}")
        
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
        
        # DELIVERY command - register delivery person
        delivery_add_match = re.match(r'(?:DELIVERY|delivery)\s+(\d+)', message.strip())
        if delivery_add_match:
            new_delivery_phone = delivery_add_match.group(1)
            current_deliveries = config.get('delivery_phones', [])
            if new_delivery_phone not in current_deliveries:
                current_deliveries.append(new_delivery_phone)
                await update_sandwich_config({"delivery_phones": current_deliveries})
            return f"✅ {new_delivery_phone} agregado como delivery.\n\nDeliveries registrados: {', '.join(current_deliveries)}"
        
        # PEDIDOS command
        if message.lower().strip() == 'pedidos':
            pending = await db.sandwich_pedidos.find({"estado": "pendiente"}).to_list(10)
            if pending:
                msg = "📋 *PEDIDOS PENDIENTES:*\n\n"
                for p in pending:
                    msg += f"• *#{p['numero_pedido']}* - {p['nombre']} - ${p['total']:,}\n"
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
        message_lower = message.lower().strip()
        if message_lower in ['hola', 'hi', 'hey', 'buenas']:
            pending_count = await db.sandwich_pedidos.count_documents({"estado": "pendiente"})
            return f"""👋 *¡Hola Admin!*

📊 *Pedidos pendientes:* {pending_count}

📋 *Comandos:*
• *PEDIDOS* - Ver pendientes
• *PEDIDO #X* - Ver detalles
• *CONFIRMAR X* - Confirmar pedido
• *RECHAZAR X* - Rechazar pedido
• *LISTO X* - Marcar como listo
• *ENCAMINO X* - Marcar en camino
• *ENTREGADO X* - Marcar entregado
• *ESTADO X [resp]* - Responder consulta
• *PAUSAR TEL* - Atender manualmente
• *REANUDAR TEL* - Reactivar bot
• *DELIVERY TEL* - Agregar delivery"""
        
        return """👋 Comandos disponibles:

• *PEDIDOS* - Ver pendientes
• *PEDIDO #X* - Ver detalles
• *CONFIRMAR X* - Confirmar
• *RECHAZAR X* - Rechazar
• *LISTO X* - Listo para entrega
• *ENCAMINO X* - En camino
• *ENTREGADO X* - Entregado
• *ESTADO X [resp]* - Responder cliente
• *PAUSAR TEL* - Atender manual
• *REANUDAR TEL* - Reactivar bot"""
    
    # ============ DELIVERY COMMANDS ============
    if is_delivery:
        print(f"[Sandwich Bot] 🛵 DELIVERY DETECTED! Message: {message[:50]}")
        
        # PEDIDO #X command
        pedido_match = re.match(r'(?:PEDIDO|pedido|Pedido)\s*#?(\d+)', message.strip())
        if pedido_match:
            numero = pedido_match.group(1)
            order, response = await get_order_for_delivery(numero)
            return response
        
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
        message_lower = message.lower().strip()
        if message_lower in ['hola', 'hi', 'hey', 'buenas']:
            # Show pending deliveries
            ready_orders = await db.sandwich_pedidos.find(
                {"estado": {"$in": ["listo", "en_camino"]}, "tipo_entrega": "delivery"}
            ).to_list(10)
            
            if ready_orders:
                msg = "🛵 *¡Hola Delivery!*\n\n📦 *Pedidos listos:*\n\n"
                for o in ready_orders:
                    msg += f"• *#{o['numero_pedido']}* - {o['nombre']} - {o['estado'].upper()}\n"
                msg += "\nPara ver detalles: *PEDIDO #X*"
                return msg
            return "🛵 *¡Hola Delivery!*\n\nNo hay pedidos listos para entrega.\n\nPara ver un pedido: *PEDIDO #X*"
        
        return """🛵 *Comandos Delivery:*

• *PEDIDO #X* - Ver detalles del pedido
• *ENCAMINO X* - Marcar en camino
• *ENTREGADO X* - Marcar entregado"""
    
    # ============ CLIENT FLOW ============
    
    # Check if paused (human handover)
    if await is_sandwich_chat_paused(phone_number):
        print(f"[Sandwich Bot] Chat {phone_number} is paused")
        return None
    
    # Save incoming message
    await save_sandwich_message(phone_number, message, "user", push_name)
    
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
            
            order = await create_sandwich_order(phone_number, data)
            
            # Notify admin
            await notify_sandwich_admin(order)
            
            # Ask for WhatsApp number after order creation
            whatsapp_request = ""
            if order.get('pending_whatsapp_request'):
                whatsapp_request = "\n\n📱 Por último, ¿me pasás tu número de WhatsApp para que el delivery pueda contactarte si es necesario? (Ej: 3834123456)"
            
            success_msg = f"""✅ *¡PEDIDO REGISTRADO!*

📋 *N° de Pedido:* #{order['numero_pedido']}

Tu pedido fue enviado al local.
Te avisamos cuando esté confirmado. 🙌

_Tiempo estimado de preparación: 20-30 min_{whatsapp_request}"""
            
            ai_response = re.sub(r'\[CREAR_PEDIDO\].*?\[/CREAR_PEDIDO\]', '', ai_response, flags=re.DOTALL)
            ai_response = ai_response.replace('Procesando tu pedido... ⏳', success_msg)
            
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
        except:
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
        except:
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

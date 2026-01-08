"""
WhatsApp AI Bot Service for Sandwichería
Handles message processing with ChatGPT integration for food orders
"""

import os
import httpx
from datetime import datetime, timezone, timedelta
from pathlib import Path
from dotenv import load_dotenv
from uuid import uuid4

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

# Default bot configuration for Sandwich
DEFAULT_SANDWICH_CONFIG = {
    "nombre_negocio": "Sandwichería",
    "mensaje_bienvenida": """¡Hola! 👋 Bienvenido a *Sandwichería*

🥪 Hacemos los mejores sándwiches de la zona

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
    "admin_phone": "",
    "admin_lid": "",
    "bot_activo": True,
    
    "instrucciones_bot": """Sos el asistente de pedidos de {nombre_negocio}. Tu objetivo es tomar pedidos de comida de forma amable y eficiente.

=== MENÚ DISPONIBLE ===
{menu_formateado}

=== TU PERSONALIDAD ===
- Sos argentino, usá "vos" en lugar de "tú"
- Sé amable y servicial
- Usá emojis con moderación (1-2 por mensaje)
- Respuestas cortas y claras

=== FLUJO DE PEDIDO ===

PASO 1 - MOSTRAR MENÚ:
Si el cliente pide ver el menú o no sabe qué pedir, mostrá las opciones disponibles organizadas por categoría.

PASO 2 - TOMAR PEDIDO:
Cuando el cliente elija, confirmá:
- Qué producto quiere
- Cantidad
- Si quiere agregar extras/adicionales

PASO 3 - DELIVERY O RETIRO:
Preguntá: "¿Lo querés para delivery o lo retirás por el local?"

PASO 4 - DATOS DEL CLIENTE:
Si es DELIVERY, pedí:
- Nombre
- Dirección completa
- Referencias (opcional)

Si es RETIRO, pedí:
- Nombre (para el pedido)

PASO 5 - CONFIRMAR PEDIDO:
Mostrá un resumen completo:
"📋 *RESUMEN DE TU PEDIDO*
👤 Nombre: [nombre]
📍 Entrega: [delivery/retiro]
[Dirección si es delivery]

🛒 *Pedido:*
[lista de items con precios]

💰 Subtotal: $[subtotal]
🛵 Delivery: $[costo_delivery o GRATIS]
💵 *TOTAL: $[total]*

¿Confirmás el pedido? Respondé *SÍ* para confirmar."

PASO 6 - CREAR PEDIDO:
Cuando confirme, respondé con:

[CREAR_PEDIDO]
nombre: [nombre]
telefono: [telefono del chat]
direccion: [dirección o "Retira en local"]
tipo_entrega: [delivery/retiro]
items: [lista de items separados por coma]
cantidades: [cantidades separadas por coma]
subtotal: [subtotal sin delivery]
delivery: [costo delivery o 0]
total: [total final]
[/CREAR_PEDIDO]

Procesando tu pedido... ⏳

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

=== DERIVACIÓN A HUMANO ===
Si el cliente tiene un problema o quiere hablar con alguien:
- Respondé: "Un momento, te comunico con el encargado 👤"
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


async def is_sandwich_chat_paused(phone_number: str) -> bool:
    """Check if a chat is paused for human attention"""
    paused = await db.sandwich_paused.find_one({"phone_number": phone_number})
    return paused is not None


async def pause_sandwich_chat(phone_number: str, admin_phone: str):
    """Pause bot for a specific chat"""
    await db.sandwich_paused.update_one(
        {"phone_number": phone_number},
        {"$set": {
            "phone_number": phone_number,
            "paused_by": admin_phone,
            "paused_at": datetime.now(timezone.utc).isoformat()
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


async def notify_sandwich_admin(order_data: dict):
    """Notify admin about new order"""
    config = await get_sandwich_config()
    admin_phone = config.get('admin_phone', '')
    admin_lid = config.get('admin_lid', '')
    
    if not admin_phone and not admin_lid:
        print("[Sandwich Bot] No admin configured for notifications")
        return
    
    notification = f"""🔔 *NUEVO PEDIDO #{order_data['numero_pedido']}*

👤 *Cliente:* {order_data['nombre']}
📱 *Tel:* {order_data['telefono']}
📍 *Entrega:* {order_data['tipo_entrega'].upper()}
{f"🏠 *Dirección:* {order_data['direccion']}" if order_data['tipo_entrega'] == 'delivery' else '🏪 *Retira en local*'}

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
    """Create a new order from WhatsApp"""
    order_id = str(uuid4())
    numero_pedido = str(uuid4())[:6].upper()
    
    order_doc = {
        "_id": order_id,
        "numero_pedido": numero_pedido,
        "nombre": data.get('nombre', ''),
        "telefono": phone_number,
        "direccion": data.get('direccion', ''),
        "tipo_entrega": data.get('tipo_entrega', 'retiro'),
        "items": data.get('items', ''),
        "cantidades": data.get('cantidades', ''),
        "items_formatted": data.get('items_formatted', ''),
        "subtotal": int(data.get('subtotal', 0)),
        "costo_delivery": int(data.get('delivery', 0)),
        "total": int(data.get('total', 0)),
        "estado": "pendiente",  # pendiente, confirmado, preparando, listo, entregado, cancelado
        "whatsapp_phone": phone_number,
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    
    await db.sandwich_pedidos.insert_one(order_doc)
    print(f"[Sandwich Bot] Order created: {numero_pedido}")
    return order_doc


async def admin_confirm_order(numero_pedido: str, admin_phone: str):
    """Admin confirms an order"""
    order = await db.sandwich_pedidos.find_one({"numero_pedido": numero_pedido})
    
    if not order:
        return f"❌ No encontré el pedido {numero_pedido}"
    
    if order.get('estado') != 'pendiente':
        return f"⚠️ El pedido {numero_pedido} ya está en estado: {order.get('estado')}"
    
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
    
    return f"""✅ *PEDIDO CONFIRMADO*

Pedido #{numero_pedido} confirmado.
Se notificó al cliente.

👤 {order['nombre']}
💰 ${order['total']:,}

Para marcar como LISTO: *LISTO {numero_pedido}*"""


async def admin_reject_order(numero_pedido: str, admin_phone: str, motivo: str = ""):
    """Admin rejects an order"""
    order = await db.sandwich_pedidos.find_one({"numero_pedido": numero_pedido})
    
    if not order:
        return f"❌ No encontré el pedido {numero_pedido}"
    
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
        return f"❌ No encontré el pedido {numero_pedido}"
    
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


async def process_sandwich_message_with_ai(phone_number: str, message: str, push_name: str = ""):
    """Process incoming message with ChatGPT and return response"""
    import re
    
    config = await get_sandwich_config()
    
    if not config.get("bot_activo", True):
        return None
    
    # Check if admin
    def normalize_phone(phone):
        if not phone:
            return ""
        return ''.join(filter(str.isdigit, str(phone)))[-10:]
    
    admin_phone = config.get('admin_phone', '')
    admin_lid = config.get('admin_lid', '')
    phone_digits = ''.join(filter(str.isdigit, str(phone_number)))
    
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
    
    if is_admin:
        print(f"[Sandwich Bot] ✅ ADMIN DETECTED! Message: {message[:50]}")
        
        # CONFIRMAR command
        confirm_match = re.match(r'(?:CONFIRMAR|confirmar|Confirmar)\s+([A-Za-z0-9]+)', message.strip())
        if confirm_match:
            numero = confirm_match.group(1).upper()
            return await admin_confirm_order(numero, phone_number)
        
        # RECHAZAR command
        reject_match = re.match(r'(?:RECHAZAR|rechazar|Rechazar)\s+([A-Za-z0-9]+)\s*(.*)?', message.strip())
        if reject_match:
            numero = reject_match.group(1).upper()
            motivo = reject_match.group(2) or ""
            return await admin_reject_order(numero, phone_number, motivo)
        
        # LISTO command
        listo_match = re.match(r'(?:LISTO|listo|Listo)\s+([A-Za-z0-9]+)', message.strip())
        if listo_match:
            numero = listo_match.group(1).upper()
            return await admin_order_ready(numero, phone_number)
        
        # PAUSAR command
        pausar_match = re.match(r'(?:PAUSAR|pausar|Pausar)\s+(\d+)', message.strip())
        if pausar_match:
            client_phone = pausar_match.group(1)
            await pause_sandwich_chat(client_phone, phone_number)
            return f"✅ Chat pausado para {client_phone}. Ahora podés atenderlo manualmente.\n\nPara reanudar: *REANUDAR {client_phone}*"
        
        # REANUDAR command
        reanudar_match = re.match(r'(?:REANUDAR|reanudar|Reanudar)\s+(\d+)', message.strip())
        if reanudar_match:
            client_phone = reanudar_match.group(1)
            await resume_sandwich_chat(client_phone)
            return f"✅ Bot reanudado para {client_phone}."
        
        # PEDIDOS command
        if message.lower().strip() == 'pedidos':
            pending = await db.sandwich_pedidos.find({"estado": "pendiente"}).to_list(10)
            if pending:
                msg = "📋 *PEDIDOS PENDIENTES:*\n\n"
                for p in pending:
                    msg += f"• *{p['numero_pedido']}* - {p['nombre']} - ${p['total']:,}\n"
                msg += "\nPara confirmar: *CONFIRMAR [NÚMERO]*"
                return msg
            return "✅ No hay pedidos pendientes"
        
        # Admin greeting
        message_lower = message.lower().strip()
        if message_lower in ['hola', 'hi', 'hey', 'buenas']:
            pending_count = await db.sandwich_pedidos.count_documents({"estado": "pendiente"})
            return f"""👋 *¡Hola Admin!*

📊 *Pedidos pendientes:* {pending_count}

📋 *Comandos:*
• *PEDIDOS* - Ver pendientes
• *CONFIRMAR [N°]* - Confirmar pedido
• *RECHAZAR [N°]* - Rechazar pedido
• *LISTO [N°]* - Marcar como listo
• *PAUSAR [TEL]* - Atender manualmente
• *REANUDAR [TEL]* - Reactivar bot"""
        
        return f"""👋 Comandos disponibles:

• *PEDIDOS* - Ver pendientes
• *CONFIRMAR [N°]* - Confirmar
• *RECHAZAR [N°]* - Rechazar
• *LISTO [N°]* - Listo para entrega
• *PAUSAR [TEL]* - Atender manual
• *REANUDAR [TEL]* - Reactivar bot"""
    
    # Check if paused
    if await is_sandwich_chat_paused(phone_number):
        print(f"[Sandwich Bot] Chat {phone_number} is paused")
        return None
    
    # Save incoming message
    await save_sandwich_message(phone_number, message, "user", push_name)
    
    # Get conversation history
    history = await get_sandwich_conversation_history(phone_number, limit=10)
    
    # Build system prompt
    instrucciones = config.get("instrucciones_bot", DEFAULT_SANDWICH_CONFIG["instrucciones_bot"])
    menu_formateado = await format_menu_for_bot()
    
    system_prompt = instrucciones.format(
        nombre_negocio=config.get('nombre_negocio', 'Sandwichería'),
        menu_formateado=menu_formateado,
        costo_delivery=config.get('costo_delivery', 500),
        pedido_minimo=config.get('pedido_minimo_delivery', 2000),
        tiempo_preparacion=config.get('tiempo_preparacion', '20-30 minutos'),
        horario_apertura=config.get('horario_apertura', '10:00'),
        horario_cierre=config.get('horario_cierre', '22:00'),
        dias_abierto=', '.join(config.get('dias_abierto', ['lunes', 'martes', 'miércoles', 'jueves', 'viernes', 'sábado'])),
        direccion_local=config.get('direccion_local', 'Av. Principal 123')
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
            
            success_msg = f"""✅ *¡PEDIDO REGISTRADO!*

📋 *N° de Pedido:* {order['numero_pedido']}

Tu pedido fue enviado al local.
Te avisamos cuando esté confirmado. 🙌

_Tiempo estimado de preparación: 20-30 min_"""
            
            ai_response = re.sub(r'\[CREAR_PEDIDO\].*?\[/CREAR_PEDIDO\]', '', ai_response, flags=re.DOTALL)
            ai_response = ai_response.replace('Procesando tu pedido... ⏳', success_msg)
            
        except Exception as e:
            print(f"[Sandwich Bot] Error creating order: {e}")
            import traceback
            traceback.print_exc()
            ai_response = re.sub(r'\[CREAR_PEDIDO\].*?\[/CREAR_PEDIDO\]', '', ai_response, flags=re.DOTALL)
            ai_response = ai_response.replace('Procesando tu pedido... ⏳', '❌ Hubo un error al crear el pedido. Por favor, intentá de nuevo.')
    
    ai_response = re.sub(r'\[/?CREAR_PEDIDO\]', '', ai_response)
    ai_response = ai_response.strip()
    
    return ai_response


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

"""
GastroBot SaaS - Multi-tenant WhatsApp Bot Service
Handles multiple restaurant clients, each with their own WhatsApp bot
"""

import os
import re
from datetime import datetime, timezone, timedelta
from motor.motor_asyncio import AsyncIOMotorClient
from emergentintegrations.llm.chat import LlmChat, UserMessage

# MongoDB connection
mongo_url = os.environ.get('MONGO_URL', 'mongodb://localhost:27017')
db_name = os.environ.get('DB_NAME', 'estonia_seguros')

client = AsyncIOMotorClient(mongo_url)
db = client[db_name]

# Collections prefix for GastroBot
GB_PREFIX = "gb_"

# ============ TENANT (BUSINESS) MANAGEMENT ============

async def create_tenant(data: dict) -> dict:
    """Create a new tenant (restaurant client)"""
    import uuid
    
    tenant_id = str(uuid.uuid4())[:8]
    
    tenant_doc = {
        "_id": tenant_id,
        "nombre_negocio": data.get("nombre_negocio", ""),
        "slug": data.get("slug", "").lower().replace(" ", "-"),
        "email": data.get("email", ""),
        "telefono": data.get("telefono", ""),
        "direccion": data.get("direccion", ""),
        "link_ubicacion": data.get("link_ubicacion", ""),
        "logo_url": data.get("logo_url", ""),
        
        # Plan & subscription
        "plan": data.get("plan", "basico"),  # basico, pro, enterprise
        "max_bots": 1 if data.get("plan", "basico") == "basico" else 5,
        "estado_suscripcion": "activo",  # activo, pausado, cancelado
        "fecha_vencimiento": (datetime.now(timezone.utc) + timedelta(days=30)).isoformat(),
        
        # WhatsApp config
        "whatsapp_connected": False,
        "whatsapp_number": "",
        "bot_activo": True,
        
        # Business hours
        "horario_apertura": data.get("horario_apertura", "10:00"),
        "horario_cierre": data.get("horario_cierre", "22:00"),
        "dias_abierto": data.get("dias_abierto", ["lunes", "martes", "miércoles", "jueves", "viernes", "sábado"]),
        
        # Delivery config
        "costo_delivery": data.get("costo_delivery", 0),
        "tiempo_preparacion": data.get("tiempo_preparacion", "30-45 minutos"),
        "zonas_sin_delivery": data.get("zonas_sin_delivery", []),
        
        # Admin credentials (for client login)
        "admin_username": data.get("admin_username", ""),
        "admin_password": data.get("admin_password", ""),
        
        # Timestamps
        "created_at": datetime.now(timezone.utc).isoformat(),
        "updated_at": datetime.now(timezone.utc).isoformat()
    }
    
    await db[f"{GB_PREFIX}tenants"].insert_one(tenant_doc)
    
    # Create default menu for tenant
    await create_default_menu(tenant_id)
    
    # Create default bot config
    await create_default_bot_config(tenant_id, tenant_doc["nombre_negocio"])
    
    return {k: v for k, v in tenant_doc.items() if k != "_id" and k != "admin_password"}


async def get_tenant(tenant_id: str) -> dict:
    """Get tenant by ID"""
    tenant = await db[f"{GB_PREFIX}tenants"].find_one({"_id": tenant_id})
    if tenant:
        tenant["id"] = tenant["_id"]
        del tenant["_id"]
        if "admin_password" in tenant:
            del tenant["admin_password"]
    return tenant


async def get_all_tenants() -> list:
    """Get all tenants for super admin"""
    tenants = await db[f"{GB_PREFIX}tenants"].find({}).to_list(1000)
    result = []
    for t in tenants:
        t["id"] = t["_id"]
        del t["_id"]
        if "admin_password" in t:
            del t["admin_password"]
        
        # Get stats
        pedidos_count = await db[f"{GB_PREFIX}pedidos"].count_documents({"tenant_id": t["id"]})
        pedidos_hoy = await db[f"{GB_PREFIX}pedidos"].count_documents({
            "tenant_id": t["id"],
            "created_at": {"$gte": datetime.now(timezone.utc).replace(hour=0, minute=0, second=0).isoformat()}
        })
        
        t["stats"] = {
            "total_pedidos": pedidos_count,
            "pedidos_hoy": pedidos_hoy
        }
        result.append(t)
    
    return result


async def update_tenant(tenant_id: str, data: dict) -> dict:
    """Update tenant"""
    data["updated_at"] = datetime.now(timezone.utc).isoformat()
    
    # Don't allow updating certain fields
    protected_fields = ["_id", "created_at"]
    for field in protected_fields:
        data.pop(field, None)
    
    await db[f"{GB_PREFIX}tenants"].update_one(
        {"_id": tenant_id},
        {"$set": data}
    )
    return await get_tenant(tenant_id)


async def delete_tenant(tenant_id: str) -> bool:
    """Delete tenant and all related data"""
    # Delete tenant
    result = await db[f"{GB_PREFIX}tenants"].delete_one({"_id": tenant_id})
    
    # Delete related data
    await db[f"{GB_PREFIX}pedidos"].delete_many({"tenant_id": tenant_id})
    await db[f"{GB_PREFIX}menu"].delete_many({"tenant_id": tenant_id})
    await db[f"{GB_PREFIX}config"].delete_many({"tenant_id": tenant_id})
    await db[f"{GB_PREFIX}messages"].delete_many({"tenant_id": tenant_id})
    
    return result.deleted_count > 0


async def authenticate_tenant(username: str, password: str) -> dict:
    """Authenticate tenant admin"""
    tenant = await db[f"{GB_PREFIX}tenants"].find_one({
        "admin_username": username,
        "admin_password": password,
        "estado_suscripcion": "activo"
    })
    
    if tenant:
        return {
            "id": tenant["_id"],
            "nombre_negocio": tenant["nombre_negocio"],
            "plan": tenant["plan"]
        }
    return None


# ============ MENU MANAGEMENT ============

async def create_default_menu(tenant_id: str):
    """Create default menu categories for a new tenant"""
    default_categories = [
        {
            "tenant_id": tenant_id,
            "categoria": "Platos Principales",
            "emoji": "🍽️",
            "orden": 1,
            "productos": []
        },
        {
            "tenant_id": tenant_id,
            "categoria": "Bebidas",
            "emoji": "🥤",
            "orden": 2,
            "productos": []
        },
        {
            "tenant_id": tenant_id,
            "categoria": "Postres",
            "emoji": "🍰",
            "orden": 3,
            "productos": []
        }
    ]
    
    await db[f"{GB_PREFIX}menu"].insert_many(default_categories)


async def get_menu(tenant_id: str) -> list:
    """Get menu for a tenant"""
    menu = await db[f"{GB_PREFIX}menu"].find(
        {"tenant_id": tenant_id},
        {"_id": 0}
    ).sort("orden", 1).to_list(100)
    return menu


async def update_menu(tenant_id: str, menu_data: list) -> list:
    """Update entire menu for a tenant"""
    # Delete old menu
    await db[f"{GB_PREFIX}menu"].delete_many({"tenant_id": tenant_id})
    
    # Insert new menu
    for i, cat in enumerate(menu_data):
        cat["tenant_id"] = tenant_id
        cat["orden"] = i + 1
    
    if menu_data:
        await db[f"{GB_PREFIX}menu"].insert_many(menu_data)
    
    return await get_menu(tenant_id)


async def add_product(tenant_id: str, categoria: str, producto: dict) -> bool:
    """Add a product to a category"""
    result = await db[f"{GB_PREFIX}menu"].update_one(
        {"tenant_id": tenant_id, "categoria": categoria},
        {"$push": {"productos": producto}}
    )
    return result.modified_count > 0


# ============ BOT CONFIG ============

async def create_default_bot_config(tenant_id: str, nombre_negocio: str):
    """Create default bot config for a tenant"""
    config = {
        "tenant_id": tenant_id,
        "nombre_negocio": nombre_negocio,
        "mensaje_bienvenida": f"¡Hola! 🍔 Bienvenido a *{nombre_negocio}*\n\n¿Qué te gustaría pedir hoy?",
        "instrucciones_bot": None,  # Will use default
        "admin_phones": [],
        "delivery_phones": [],
        "bot_activo": True
    }
    
    await db[f"{GB_PREFIX}config"].insert_one(config)


async def get_bot_config(tenant_id: str) -> dict:
    """Get bot config for a tenant"""
    config = await db[f"{GB_PREFIX}config"].find_one(
        {"tenant_id": tenant_id},
        {"_id": 0}
    )
    return config or {}


async def update_bot_config(tenant_id: str, data: dict) -> dict:
    """Update bot config for a tenant"""
    await db[f"{GB_PREFIX}config"].update_one(
        {"tenant_id": tenant_id},
        {"$set": data},
        upsert=True
    )
    return await get_bot_config(tenant_id)


# ============ ORDER MANAGEMENT ============

async def get_next_order_number(tenant_id: str) -> int:
    """Get next sequential order number for a tenant"""
    counter = await db[f"{GB_PREFIX}order_counters"].find_one_and_update(
        {"tenant_id": tenant_id},
        {"$inc": {"sequence": 1}},
        upsert=True,
        return_document=True
    )
    return counter.get("sequence", 1)


async def create_order(tenant_id: str, phone_number: str, data: dict) -> dict:
    """Create a new order"""
    import uuid
    
    seq_number = await get_next_order_number(tenant_id)
    
    order_doc = {
        "_id": str(uuid.uuid4()),
        "tenant_id": tenant_id,
        "numero_pedido": str(seq_number),
        "nombre": data.get("nombre", ""),
        "telefono": phone_number,
        "whatsapp_contact": data.get("whatsapp_contact", ""),
        "direccion": data.get("direccion", ""),
        "tipo_entrega": data.get("tipo_entrega", "delivery"),
        "items": data.get("items", ""),
        "items_formatted": data.get("items_formatted", ""),
        "modificaciones": data.get("modificaciones", ""),
        "subtotal": data.get("subtotal", 0),
        "costo_delivery": data.get("delivery", 0),
        "total": data.get("total", 0),
        "estado": "pendiente",
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    
    await db[f"{GB_PREFIX}pedidos"].insert_one(order_doc)
    
    return order_doc


async def get_orders(tenant_id: str, estado: str = None, limit: int = 50) -> list:
    """Get orders for a tenant"""
    query = {"tenant_id": tenant_id}
    if estado:
        query["estado"] = estado
    
    orders = await db[f"{GB_PREFIX}pedidos"].find(
        query,
        {"_id": 0}
    ).sort("created_at", -1).limit(limit).to_list(limit)
    
    return orders


async def update_order_status(tenant_id: str, numero_pedido: str, nuevo_estado: str) -> dict:
    """Update order status"""
    result = await db[f"{GB_PREFIX}pedidos"].find_one_and_update(
        {"tenant_id": tenant_id, "numero_pedido": numero_pedido},
        {"$set": {
            "estado": nuevo_estado,
            "updated_at": datetime.now(timezone.utc).isoformat()
        }},
        return_document=True
    )
    
    if result:
        result["id"] = result["_id"]
        del result["_id"]
    
    return result


# ============ STATISTICS ============

async def get_tenant_stats(tenant_id: str) -> dict:
    """Get statistics for a tenant"""
    today_start = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)
    
    # Total orders
    total_pedidos = await db[f"{GB_PREFIX}pedidos"].count_documents({"tenant_id": tenant_id})
    
    # Orders today
    pedidos_hoy = await db[f"{GB_PREFIX}pedidos"].count_documents({
        "tenant_id": tenant_id,
        "created_at": {"$gte": today_start.isoformat()}
    })
    
    # Pending orders
    pedidos_pendientes = await db[f"{GB_PREFIX}pedidos"].count_documents({
        "tenant_id": tenant_id,
        "estado": "pendiente"
    })
    
    # Revenue today
    orders_today = await db[f"{GB_PREFIX}pedidos"].find({
        "tenant_id": tenant_id,
        "created_at": {"$gte": today_start.isoformat()},
        "estado": {"$in": ["confirmado", "listo", "en_camino", "entregado"]}
    }).to_list(1000)
    
    ventas_hoy = sum([o.get("total", 0) for o in orders_today])
    
    return {
        "total_pedidos": total_pedidos,
        "pedidos_hoy": pedidos_hoy,
        "pedidos_pendientes": pedidos_pendientes,
        "ventas_hoy": ventas_hoy
    }


# ============ SUPER ADMIN STATS ============

async def get_super_admin_stats() -> dict:
    """Get global statistics for super admin"""
    total_tenants = await db[f"{GB_PREFIX}tenants"].count_documents({})
    tenants_activos = await db[f"{GB_PREFIX}tenants"].count_documents({"estado_suscripcion": "activo"})
    
    today_start = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)
    
    total_pedidos = await db[f"{GB_PREFIX}pedidos"].count_documents({})
    pedidos_hoy = await db[f"{GB_PREFIX}pedidos"].count_documents({
        "created_at": {"$gte": today_start.isoformat()}
    })
    
    # Revenue by plan
    tenants = await db[f"{GB_PREFIX}tenants"].find({}).to_list(1000)
    plan_counts = {"basico": 0, "pro": 0, "enterprise": 0}
    for t in tenants:
        plan = t.get("plan", "basico")
        plan_counts[plan] = plan_counts.get(plan, 0) + 1
    
    return {
        "total_negocios": total_tenants,
        "negocios_activos": tenants_activos,
        "total_pedidos": total_pedidos,
        "pedidos_hoy": pedidos_hoy,
        "por_plan": plan_counts
    }


# ============ MESSAGE HISTORY ============

async def save_message(tenant_id: str, phone_number: str, message: str, role: str, push_name: str = ""):
    """Save a message to history"""
    doc = {
        "tenant_id": tenant_id,
        "phone_number": phone_number,
        "message": message,
        "role": role,
        "push_name": push_name,
        "timestamp": datetime.now(timezone.utc).isoformat()
    }
    await db[f"{GB_PREFIX}messages"].insert_one(doc)


async def get_conversation_history(tenant_id: str, phone_number: str, limit: int = 10) -> list:
    """Get conversation history"""
    messages = await db[f"{GB_PREFIX}messages"].find(
        {"tenant_id": tenant_id, "phone_number": phone_number},
        {"_id": 0}
    ).sort("timestamp", -1).limit(limit).to_list(limit)
    
    return list(reversed(messages))


async def get_all_conversations(tenant_id: str) -> list:
    """Get all unique conversations for a tenant"""
    pipeline = [
        {"$match": {"tenant_id": tenant_id}},
        {"$sort": {"timestamp": -1}},
        {"$group": {
            "_id": "$phone_number",
            "push_name": {"$first": "$push_name"},
            "last_message": {"$first": "$message"},
            "last_timestamp": {"$first": "$timestamp"},
            "message_count": {"$sum": 1}
        }},
        {"$sort": {"last_timestamp": -1}},
        {"$limit": 50}
    ]
    
    result = await db[f"{GB_PREFIX}messages"].aggregate(pipeline).to_list(50)
    
    conversations = []
    for r in result:
        conversations.append({
            "phone_number": r["_id"],
            "push_name": r.get("push_name", ""),
            "last_message": r.get("last_message", ""),
            "last_timestamp": r.get("last_timestamp", ""),
            "message_count": r.get("message_count", 0)
        })
    
    return conversations


# ============ AI MESSAGE PROCESSING ============

def format_menu_for_bot(menu: list) -> str:
    """Format menu for bot instructions"""
    formatted = ""
    for cat in menu:
        formatted += f"\n{cat.get('emoji', '📍')} *{cat['categoria']}*\n"
        for prod in cat.get('productos', []):
            if prod.get('activo', True):
                formatted += f"  • {prod['nombre']}: ${prod['precio']:,}"
                if prod.get('descripcion'):
                    formatted += f" - {prod['descripcion']}"
                formatted += "\n"
    return formatted if formatted else "No hay productos configurados aún."


DEFAULT_BOT_INSTRUCTIONS = """Sos el asistente de pedidos de {nombre_negocio}. Tu objetivo es tomar pedidos RÁPIDO y SIN VUELTAS.

=== MENÚ ===
{menu_formateado}

=== TU ESTILO ===
- Argentino, usá "vos"
- Amable pero DIRECTO
- Respuestas CORTAS (máximo 3-4 líneas)
- Usá emojis con moderación (1-2 por mensaje)

=== FLUJO RÁPIDO (MÁXIMO 5 MENSAJES) ===

1. Saludá y preguntá qué quiere pedir
2. Después del pedido, preguntá: "¿Es para delivery o retirás en local?"
3. Si es delivery: "Enviame tu ubicación 📍"
   Si es retiro: Dá la dirección del local
4. Pedí nombre y celular
5. Mostrá resumen y decí: "Dame un minuto que paso tu pedido a cocina 👨‍🍳"

Luego usá:
[CREAR_PEDIDO]
nombre: [nombre]
telefono: [celular]
direccion: [dirección o "Retira en local"]
tipo_entrega: [delivery/retiro]
items: [items]
cantidades: [cantidades]
modificaciones: [modificaciones o "ninguna"]
subtotal: [subtotal]
delivery: [costo o 0]
total: [total]
[/CREAR_PEDIDO]

=== REGLAS ===
- NUNCA digas "confirmado" vos - solo el sistema
- NUNCA inventes productos
- Costo delivery: ${costo_delivery}
- Tiempo: {tiempo_preparacion}
"""


async def process_message(tenant_id: str, phone_number: str, message: str, push_name: str = "") -> str:
    """Process incoming message with AI for a specific tenant"""
    
    # Get tenant config
    tenant = await get_tenant(tenant_id)
    if not tenant or not tenant.get("bot_activo", True):
        return None
    
    bot_config = await get_bot_config(tenant_id)
    menu = await get_menu(tenant_id)
    
    # Save incoming message
    await save_message(tenant_id, phone_number, message, "user", push_name)
    
    # Build system prompt
    menu_formatted = format_menu_for_bot(menu)
    instructions = bot_config.get("instrucciones_bot") or DEFAULT_BOT_INSTRUCTIONS
    
    system_prompt = instructions.format(
        nombre_negocio=tenant.get("nombre_negocio", "Restaurante"),
        menu_formateado=menu_formatted,
        costo_delivery=tenant.get("costo_delivery", 0),
        tiempo_preparacion=tenant.get("tiempo_preparacion", "30-45 minutos"),
        direccion_local=tenant.get("direccion", ""),
        link_ubicacion=tenant.get("link_ubicacion", "")
    )
    
    # Get conversation history
    history = await get_conversation_history(tenant_id, phone_number, limit=10)
    
    # Build messages for AI
    try:
        llm_key = os.environ.get('EMERGENT_LLM_KEY')
        if not llm_key:
            return "Lo siento, el bot no está disponible en este momento."
        
        chat = LlmChat(
            api_key=llm_key,
            system_message=system_prompt
        )
        
        # Add history
        for msg in history[:-1]:  # Exclude current message
            if msg["role"] == "user":
                chat.add_message(UserMessage(content=msg["message"]))
            else:
                chat.messages.append({"role": "assistant", "content": msg["message"]})
        
        # Get response
        response = await chat.send_message_async(UserMessage(content=message))
        reply = response.content if hasattr(response, 'content') else str(response)
        
        # Check for order creation
        if "[CREAR_PEDIDO]" in reply and "[/CREAR_PEDIDO]" in reply:
            order_data = parse_order_from_response(reply)
            if order_data:
                order = await create_order(tenant_id, phone_number, order_data)
                
                # Notify admins
                await notify_tenant_admins(tenant_id, order)
                
                # Clean response
                reply = reply.split("[CREAR_PEDIDO]")[0].strip()
        
        # Save bot response
        await save_message(tenant_id, phone_number, reply, "assistant")
        
        return reply
        
    except Exception as e:
        print(f"[GastroBot] Error processing message: {e}")
        return "Disculpá, hubo un error. ¿Podés repetir tu pedido?"


def parse_order_from_response(response: str) -> dict:
    """Parse order data from bot response"""
    try:
        start = response.find("[CREAR_PEDIDO]") + len("[CREAR_PEDIDO]")
        end = response.find("[/CREAR_PEDIDO]")
        order_text = response[start:end].strip()
        
        data = {}
        for line in order_text.split("\n"):
            if ":" in line:
                key, value = line.split(":", 1)
                data[key.strip().lower()] = value.strip()
        
        # Parse numeric values
        for field in ["subtotal", "delivery", "total"]:
            if field in data:
                cleaned = data[field].replace("$", "").replace(".", "").replace(",", "").strip()
                try:
                    data[field] = int(cleaned)
                except:
                    data[field] = 0
        
        return data
    except:
        return None


async def notify_tenant_admins(tenant_id: str, order: dict):
    """Notify tenant admins about new order"""
    # This would integrate with the WhatsApp service
    # For now, just log it
    print(f"[GastroBot] New order #{order['numero_pedido']} for tenant {tenant_id}")
    
    # TODO: Send WhatsApp notification to admin phones

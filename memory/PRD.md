# Estonia Cobertura + Modo Cocina + GastroBot SaaS - Multi-Business Platform

## Problema Original
Sistema multi-negocio para gestión de:
1. **Estonia Cobertura Colaborativa** - Sistema de coberturas de vehículos con bot de WhatsApp para ventas
2. **Modo Cocina (V1)** - Sandwichería con bot de WhatsApp para toma de pedidos
3. **GastroBot SaaS (V2)** - Sistema multi-tenant para múltiples restaurantes con WhatsApp bots

## Arquitectura

### Stack Tecnológico
- **Frontend:** React + TailwindCSS + Shadcn/UI
- **Backend:** FastAPI (Python)
- **Database:** MongoDB
- **WhatsApp:** Servicios Baileys (Node.js)
- **AI:** OpenAI GPT-4o via Emergent LLM Key

### Estructura de Archivos Clave
```
/app/
├── backend/
│   ├── server.py                    # API principal FastAPI
│   ├── whatsapp_service.py          # Bot de seguros
│   ├── whatsapp_sandwich_service.py # Bot V1 Modo Cocina
│   └── gastrobot_service.py         # 🆕 Servicio SaaS multi-tenant
├── frontend/
│   └── src/
│       ├── pages/
│       │   ├── AdminSelector.jsx    # Selector de negocio
│       │   ├── AdminSandwich.jsx    # Panel admin V1
│       │   ├── AdminPanel.jsx       # Panel admin seguros
│       │   ├── GastrobotLogin.jsx   # 🆕 Login GastroBot
│       │   ├── GastrobotSuperAdmin.jsx # 🆕 Panel Super Admin
│       │   └── GastrobotClientPanel.jsx # 🆕 Panel clientes
│       └── components/
└── whatsapp-service/
    ├── index.js                     # WhatsApp seguros
    └── index_sandwich.js            # WhatsApp V1
```

## URLs de la Aplicación
| URL | Descripción |
|-----|-------------|
| `/` | Landing Estonia Cobertura |
| `/admin-selector` | Selector negocio (Estonia/Modo Cocina) |
| `/admin-sandwich` | Panel V1 Modo Cocina |
| `/admin` | Panel Estonia Seguros |
| `/gastrobot` | 🆕 Login GastroBot SaaS |
| `/gastrobot/super` | 🆕 Super Admin Panel |
| `/gastrobot/panel` | 🆕 Panel del Cliente |

## Credenciales
| Sistema | Usuario | Contraseña |
|---------|---------|------------|
| Admin V1 | admin | Estonia2025! |
| GastroBot Super | superadmin | GastroBot2025! |

## Implementado

### 2025-01-09 - GastroBot SaaS V2 (Fase 1 + Fase 2)

**Backend:**
- ✅ Servicio `gastrobot_service.py` con arquitectura multi-tenant
- ✅ Modelo de tenants con planes (básico, pro, enterprise)
- ✅ CRUD completo para negocios
- ✅ Sistema de pedidos por tenant
- ✅ Autenticación separada (super admin + tenant admin)
- ✅ Estadísticas por tenant y globales
- ✅ Endpoints proxy para WhatsApp multi-tenant

**Frontend:**
- ✅ Página de login con tabs (Mi Negocio / Super Admin)
- ✅ Super Admin Panel con:
  - Dashboard de estadísticas
  - Lista de negocios con gestión
  - Crear/editar/eliminar negocios
  - Activar/pausar suscripciones
- ✅ Panel del Cliente con:
  - Vista de pedidos con gestión de estados
  - Gestión de menú por categorías
  - Chat con clientes
  - **📱 Tab WhatsApp con conexión QR**
  - Configuración del bot

**WhatsApp Multi-Tenant (Fase 2):**
- ✅ Servicio Node.js `index_gastrobot.js` multi-tenant
- ✅ Sistema de QR codes individuales por tenant
- ✅ Conexión/desconexión dinámica
- ✅ Auto-reconexión de tenants activos al iniciar
- ✅ Polling de estado desde el frontend
- ✅ Supervisor config para servicio en puerto 3004

**Colecciones MongoDB GastroBot:**
- `gb_tenants` - Negocios clientes
- `gb_pedidos` - Pedidos por tenant
- `gb_menu` - Menú por tenant
- `gb_config` - Configuración bot por tenant
- `gb_messages` - Historial de conversaciones
- `gb_order_counters` - Numeración secuencial

### 2025-01-09 - Optimización Flujo Bot V1

- ✅ Prompt del bot simplificado (máximo 5 mensajes)
- ✅ Flujo directo: Saludo → Pedido → ¿Delivery/Retiro? → Datos → "Dame un minuto..."
- ✅ Campo `link_ubicacion_local` para retiros
- ✅ Campo `mensaje_retiro_local` personalizable

### 2025-01-08 - Sistema de Usuarios y Recordatorios

**Sistema de Gestión de Usuarios (vía WhatsApp):**
- ✅ **Crear usuarios:** `CREAR ADMIN/DELIVERY usuario clave` (solo master admin)
- ✅ **Login:** `soy [usuario] clave [clave]` desde cualquier número
- ✅ **Logout:** `cerrar sesión`
- ✅ **Kick usuarios:** `KICKEAR usuario` (cierra sesión remota)
- ✅ **Eliminar usuarios:** `ELIMINAR usuario`
- ✅ **Listar usuarios:** `USUARIOS` (muestra usuarios y sesiones activas)

**Notificaciones Múltiples:**
- ✅ Todos los admins activos reciben notificaciones de nuevos pedidos
- ✅ Todos los deliveries reciben notificación cuando pedido está listo

**Recordatorios Automáticos:**
- ✅ Cada 5 minutos se verifican pedidos pendientes sin confirmar
- ✅ Recordatorio se envía a TODOS los admins activos
- ✅ Se repite cada 5 min hasta confirmar o rechazar

**Delivery puede marcar LISTO:**
- ✅ Los deliveries logueados pueden usar `LISTO X` además de `ENCAMINO X` y `ENTREGADO X`

### 2025-01-08 - Bot Modo Cocina V2 (10 mejoras anteriores)

1. ✅ **Solicitar WhatsApp del cliente** - Después de crear pedido, pide número para que delivery contacte
2. ✅ **Mensaje de admin corregido** - Ya no muestra "necesita aprobación del gerente"
3. ✅ **Números secuenciales** - Pedidos ahora usan #1, #2, #3... 
4. ✅ **Ubicación compartida** - Detecta y guarda ubicación, muestra link a Google Maps en panel
5. ✅ **Preguntar modificaciones** - Bot pregunta "¿sin mayo?, ¿extra queso?" antes de confirmar
6. ✅ **Controles del cliente** - Puede cancelar pedido y pedir hablar con humano
7. ✅ **Handover con auto-resume** - Pausa 2h automáticamente, luego se reanuda
8. ✅ **Rol de Delivery** - Nuevo rol con comandos PEDIDO #X, ENCAMINO, ENTREGADO
9. ✅ **Comando "Listo"** - Admin marca listo, notifica al cliente
10. ✅ **Consulta de estado** - Cliente pregunta estado, admin responde y bot retransmite

### Comandos WhatsApp Implementados

**Master Admin (número en config):**
- Todo lo de Admin +
- `CREAR ADMIN user clave` / `CREAR DELIVERY user clave`
- `USUARIOS` - Listar usuarios y sesiones
- `ELIMINAR user` - Eliminar usuario
- `KICKEAR user` - Cerrar sesión de usuario

**Admin (logueado):**
- `PEDIDOS`, `PEDIDO #X`, `CONFIRMAR X`, `RECHAZAR X [motivo]`
- `LISTO X`, `ENCAMINO X`, `ENTREGADO X`
- `ESTADO X [respuesta]`, `PAUSAR TEL`, `REANUDAR TEL`
- `cerrar sesión` - Logout

**Delivery (logueado):**
- `PEDIDO #X` (ver detalles con dirección, WhatsApp, ubicación)
- `LISTO X`, `ENCAMINO X`, `ENTREGADO X`
- `cerrar sesión` - Logout

**Cliente:**
- "cancelar" - cancela pedido activo
- "hablar con alguien" - pausa bot
- "¿cómo va mi pedido?" - consulta estado

## Credenciales
- **Admin Panel:** `/admin` → user: `admin`, password: `Estonia2025!`
- **Selector de negocio:** `/admin-selector`

## Tareas Pendientes

### P2 - Diferido
- [ ] Rebranding global de "seguro" → "cobertura" en todo el sistema

## Notas Técnicas
- WhatsApp Sandwich service corre en puerto 3003
- WhatsApp Seguros service corre en puerto 3002
- Master admin = número configurado en `admin_phone` del config
- Los recordatorios se disparan automáticamente cada 5 min desde el servicio Node.js
- Zona restringida (sin delivery): "Valle Viejo" configurable en admin

## Colecciones MongoDB (Sandwich)
- `sandwich_config` - Configuración del bot
- `sandwich_pedidos` - Pedidos
- `sandwich_messages` - Historial de mensajes
- `sandwich_bot_users` - Usuarios creados (admins/deliveries)
- `sandwich_bot_sessions` - Sesiones activas
- `sandwich_order_counter` - Contador secuencial de pedidos
- `sandwich_client_data` - Ubicaciones y datos de clientes

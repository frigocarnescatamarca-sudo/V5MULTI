# 🚗🥪 Sistema Multi-Negocio - Proyecto Finalizado

## 📋 Resumen del Proyecto

Sistema completo de gestión con dos negocios integrados:
1. **Estonia Cobertura** - Coberturas vehiculares con bot de WhatsApp
2. **Sandwichería** - Sistema de pedidos con bot de WhatsApp

**URL de Producción:** https://brand-hub-app.preview.emergentagent.com

---

## 🆕 NUEVO: Sistema Híbrido Multi-Negocio

### Selector de Sistema (`/admin-selector`)
Después del login, el admin puede elegir qué sistema gestionar:
- 🚗 **Estonia Cobertura** → `/admin`
- 🥪 **Sandwichería** → `/admin-sandwich`

### Panel Sandwichería (`/admin-sandwich`)
- **📋 Pedidos:** Lista de pedidos con estados (pendiente, confirmado, preparando, listo, entregado)
- **🍽️ Menú:** Visualización de categorías y productos
- **💬 WhatsApp Bot:** Conexión QR independiente para el número de la sandwichería
- **⚙️ Configuración:** Horarios, delivery, mensaje de bienvenida

### Bot de WhatsApp para Sandwichería
- **Puerto:** 3003 (independiente del bot de coberturas en puerto 3002)
- **Funcionalidades:**
  - Muestra menú completo con precios
  - Toma pedidos paso a paso
  - Pregunta delivery o retiro
  - Recopila datos del cliente
  - Notifica al admin con cada pedido nuevo
  - Comandos del admin: `PEDIDOS`, `CONFIRMAR`, `RECHAZAR`, `LISTO`, `PAUSAR`, `REANUDAR`

### Menú por Defecto
| Categoría | Productos |
|-----------|-----------|
| 🥪 Sándwiches | Milanesa ($2,500), Milanesa Completo ($3,000), Lomito ($3,500), Lomito Completo ($4,000) |
| 🍔 Hamburguesas | Simple ($2,000), Completa ($2,800), Doble ($3,500) |
| 🥤 Bebidas | Coca/Sprite ($800), Agua ($500), Cerveza ($1,500) |
| ➕ Extras | Papas ($1,000), Huevo ($300), Queso ($400), Panceta ($500) |

---

## 🔐 Credenciales de Acceso

### Panel Administrativo (`/admin`)
- **Usuario:** `admin`
- **Contraseña:** `Estonia2025!`

### Panel de Agentes (`/agente`)
- **Usuario de prueba:** `agentetest`
- **Contraseña:** (configurar en base de datos)

---

## ✅ Funcionalidades Implementadas

### 1. Landing Page (CRO Optimizada)
- ✅ Hero con frase de urgencia/miedo controlado
- ✅ Sección de tipos de vehículos (Auto, Moto, Taxi, Uber)
- ✅ Beneficios destacados (Activación inmediata, Certificado QR, 100% Digital)
- ✅ Prueba social ("Más de 500 conductores...")
- ✅ **Cobertura Solidaria para Pasajeros** - Sección completa con:
  - Reintegros hasta $80,000 (medicamentos)
  - Reintegros hasta $200,000 (lesiones mayores)
  - CTA agresivo "Activar por $11.000 ahora"
- ✅ Planes y precios dinámicos
- ✅ CTA final con WhatsApp
- ✅ Footer con enlaces legales

### 2. Páginas Legales
- ✅ `/terminos` - Términos y Condiciones
- ✅ `/privacidad` - Política de Privacidad

### 3. Portal de Clientes
- ✅ `/mis-coberturas` - Consulta de coberturas por DNI
- ✅ `/verificar/:recibo` - Verificación de cobertura con QR

### 4. Panel Administrativo (`/admin`)
- ✅ **Seguros:** CRUD completo de coberturas
- ✅ **Agentes:** Gestión de agentes con estadísticas de ventas
- ✅ **Premios:** Sistema de códigos promocionales
- ✅ **Vencimientos:** Control de coberturas por vencer
- ✅ **Códigos:** Gestión de códigos de descuento
- ✅ **WhatsApp Bot:** Panel completo con:
  - **Conexión:** QR para vincular WhatsApp
  - **Conversaciones:** Historial de chats
  - **Precios:** Editor dinámico de precios por tipo de vehículo
  - **Guía:** Documentación de comandos del bot
  - **Configuración:** Mensaje de bienvenida, datos bancarios, admin LID

### 5. Bot de WhatsApp con IA (GPT-4o)
- ✅ **Flujo de ventas automatizado:**
  - Detecta tipo de vehículo
  - Ofrece opciones según tipo (2 opciones para auto/moto, 3 para taxi/apps)
  - Recopila datos del cliente
  - Crea cobertura en sistema
  - Envía instrucciones de pago
  - Notifica al admin para confirmar pago
- ✅ **Cobertura Solidaria Pasajeros:** Ofrecida automáticamente para Taxi/Uber
- ✅ **Memoria de clientes:** Recuerda datos en futuras conversaciones
- ✅ **Seguimiento por inactividad:** Mensaje de despedida tras 10 min sin respuesta
- ✅ **Derivación a humano:** Cliente puede pedir hablar con persona
- ✅ **Comandos de admin vía WhatsApp:**
  - `CONFIRMAR [RECIBO]` - Confirma un pago
  - `ESTADO` - Ver coberturas pendientes
  - `PAUSAR [NÚMERO]` - Atender cliente manualmente
  - `REANUDAR [NÚMERO]` - Reactivar bot
  - `PAUSADOS` - Ver chats pausados
- ✅ **Agente Virtual:** Todas las ventas del bot quedan asignadas a "🤖 Bot WhatsApp"

### 6. Precios Dinámicos (desde Admin Panel)
| Vehículo | RC | Completo | RC + Pasajeros |
|----------|-----|----------|----------------|
| 🚗 Auto | $6,000 | $9,000 | - |
| 🏍️ Moto | $3,500 | $5,500 | - |
| 🚕 Taxi/Remis | $10,000 | $18,000 | $11,000 |
| 📱 App (Uber/Didi) | $6,000 | $9,000 | $11,000 |

---

## 🛠 Stack Tecnológico

- **Frontend:** React + TailwindCSS + Shadcn UI
- **Backend:** FastAPI (Python)
- **Base de Datos:** MongoDB
- **IA:** OpenAI GPT-4o (via Emergent LLM Key)
- **WhatsApp:** Baileys (Node.js) + FastAPI Bridge
- **Pagos:** MercadoPago (configurar link en admin)

---

## 📁 Estructura de Archivos Clave

```
/app/
├── backend/
│   ├── server.py              # API principal
│   └── whatsapp_service.py    # Lógica del bot de WhatsApp
├── frontend/src/
│   ├── pages/
│   │   ├── Home.jsx           # Landing CRO
│   │   ├── MisCoberturas.jsx  # Portal cliente
│   │   ├── Terminos.jsx       # Legal
│   │   └── Privacidad.jsx     # Legal
│   └── components/
│       └── WhatsAppBotPanel.jsx # Panel admin del bot
└── whatsapp-service/
    └── index.js               # Servicio Node.js para WhatsApp
```

---

## 📊 Colecciones MongoDB

- `seguros` - Coberturas/pólizas
- `agentes` - Agentes de ventas (incluye Bot WhatsApp)
- `whatsapp_config` - Configuración del bot
- `whatsapp_messages` - Historial de mensajes
- `whatsapp_clients` - Memoria de clientes
- `whatsapp_paused` - Chats pausados para atención humana
- `codigos_promocionales` - Descuentos

---

## 🔧 Configuración Pendiente para Producción

1. **Datos bancarios:** Configurar CBU/Alias en Admin → WhatsApp Bot → Configuración
2. **WhatsApp:** Escanear QR con el número de ventas
3. **Admin LID:** Se captura automáticamente al primer mensaje del admin
4. **Número de ventas:** Configurar en Admin para el botón "Contratar Ahora"

---

## 📝 Tarea Pendiente (P2)

- **Rebranding global:** Reemplazar "seguro/seguros" por "cobertura/coberturas" en código y UI

---

## 🎉 Estado Final

✅ **PROYECTO COMPLETADO Y FUNCIONANDO**

Todas las funcionalidades de coberturas vehiculares están implementadas y probadas.

# Estonia Cobertura + Modo Cocina - Multi-Business Platform

## Problema Original
Sistema multi-negocio para gestión de:
1. **Estonia Cobertura Colaborativa** - Sistema de coberturas de vehículos con bot de WhatsApp para ventas
2. **Modo Cocina** - Sandwichería con bot de WhatsApp para toma de pedidos

## Arquitectura

### Stack Tecnológico
- **Frontend:** React + TailwindCSS + Shadcn/UI
- **Backend:** FastAPI (Python)
- **Database:** MongoDB
- **WhatsApp:** 2x servicios Baileys (Node.js) - uno por cada negocio
- **AI:** OpenAI GPT-4o via Emergent LLM Key

### Estructura de Archivos Clave
```
/app/
├── backend/
│   ├── server.py                   # API principal FastAPI
│   ├── whatsapp_service.py         # Bot de seguros
│   └── whatsapp_sandwich_service.py # Bot de sandwiches
├── frontend/
│   └── src/
│       ├── pages/
│       │   ├── AdminSelector.jsx   # Selector de negocio
│       │   ├── AdminSandwich.jsx   # Panel admin sandwiches
│       │   └── AdminPanel.jsx      # Panel admin seguros
│       └── components/
└── whatsapp-service/
    ├── index.js                    # WhatsApp seguros
    └── index_sandwich.js           # WhatsApp sandwiches
```

## Implementado

### 2025-01-08 - Bot Modo Cocina V2 (10 mejoras)

1. ✅ **Solicitar número de WhatsApp** - Bot pide número después de crear pedido para que delivery contacte
2. ✅ **Corregir mensaje admin** - Admin ya no ve "necesita aprobación" al confirmar
3. ✅ **Números secuenciales** - Pedidos usan #1, #2, #3... en lugar de IDs aleatorios
4. ✅ **Ubicación compartida** - Detecta y guarda ubicación del cliente, muestra link a Google Maps
5. ✅ **Preguntar modificaciones** - Bot pregunta "¿sin mayo? ¿extra queso?" antes de confirmar
6. ✅ **Controles del cliente** - Puede cancelar pedido y pedir hablar con humano
7. ✅ **Handover humano** - Pausa bot por 2 horas cuando cliente pide humano, auto-resume
8. ✅ **Rol de Delivery** - Nuevo rol con comandos: PEDIDO #X, ENCAMINO X, ENTREGADO X
9. ✅ **Comando "Listo"** - Admin marca pedido listo, notifica al cliente
10. ✅ **Consulta de estado** - Cliente pregunta "¿cómo va mi pedido?", admin responde

### Comandos WhatsApp Implementados

**Admin:**
- PEDIDOS, PEDIDO #X, CONFIRMAR X, RECHAZAR X
- LISTO X, ENCAMINO X, ENTREGADO X
- ESTADO X [respuesta], PAUSAR TEL, REANUDAR TEL
- DELIVERY TEL (agregar delivery)

**Delivery:**
- PEDIDO #X (ver detalles con dirección, WhatsApp, ubicación)
- ENCAMINO X, ENTREGADO X

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
- Los números de delivery se configuran en `/admin-sandwich` → Configuración
- Zona restringida (sin delivery): "Valle Viejo" configurable en admin

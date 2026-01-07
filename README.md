# Estonia Seguros - Plataforma de Seguros Express

Sistema completo de generación de seguros automotor express para controles viales en Argentina.

## 🚗 Características Principales

- **Generación Instantánea**: Comprobante de seguro en minutos
- **Múltiples Tipos**: Autos, Motos, Taxis/Remises, Apps (Uber/Didi)
- **Coberturas**: Responsabilidad Civil y Terceros Completo
- **Vigencia**: 30 días desde emisión
- **QR Verificable**: Para agentes viales
- **Códigos Promocionales**: Sistema de descuentos y código MASTER (gratis)
- **Portal Cliente**: Autogestión con DNI
- **Panel Admin**: Gestión de seguros y códigos promo

## 💰 Precios

| Tipo Vehículo | Resp. Civil | Terceros Completo |
|---------------|-------------|-------------------|
| Autos | $6.000 | $9.000 |
| Motos | $5.000 | $7.500 |
| Taxis/Remises | $10.000 | $18.000 |
| Apps (Uber/Didi) | $6.000 | $9.000 |

## 🛠️ Stack Tecnológico

- **Backend**: FastAPI + MongoDB
- **Frontend**: React + TailwindCSS + Shadcn/UI
- **Pago**: MercadoPago (Argentina)
- **PDF**: ReportLab
- **QR**: qrcode + pillow

## 🚀 Configuración

### Variables de Entorno Backend (.env)

```env
MONGO_URL="mongodb://localhost:27017"
DB_NAME="estonia_seguros"
MP_ACCESS_TOKEN="TU_ACCESS_TOKEN_MERCADOPAGO"
REACT_APP_BACKEND_URL="https://tu-dominio.com"
BACKEND_WEBHOOK_URL="https://tu-dominio.com"
```

### Variables de Entorno Frontend (.env)

```env
REACT_APP_BACKEND_URL=https://tu-dominio.com
```

## 📋 Código Promocional MASTER

El código **MASTER** está pre-configurado en el sistema y genera seguros gratuitos. Úsalo para generar seguros sin pago cuando cobres manualmente.

## 🔑 Configurar MercadoPago

1. Crear cuenta en [MercadoPago Argentina](https://www.mercadopago.com.ar)
2. Ir a [Credenciales](https://www.mercadopago.com/mla/account/credentials)
3. Copiar el **Access Token** (TEST para pruebas, PRODUCTION para producción)
4. Agregar en `/app/backend/.env` como `MP_ACCESS_TOKEN`
5. Configurar Webhook URL en MercadoPago: `https://tu-dominio.com/api/webhook/mercadopago`

## 📱 Rutas de la Aplicación

### Públicas
- `/` - Landing page
- `/verificar/:numero_recibo` - Verificación QR (para agentes viales)

### Cliente
- `/cliente` - Portal cliente (buscar por DNI)
- `/pago-exitoso` - Confirmación de pago exitoso
- `/pago-fallido` - Error en el pago

### Admin
- `/admin` - Panel administrativo (gestión seguros y códigos promo)

## 🔄 Flujo de Uso

### Para Clientes:
1. Ingresar datos personales y del vehículo
2. Subir 4 fotos del vehículo (frente, lados, trasera)
3. Opcionalmente ingresar código promocional
4. Pagar con MercadoPago
5. Descargar comprobante PDF/Imagen con QR

### Con Código MASTER:
1. Seguir pasos 1-2
2. Ingresar "MASTER" en código promocional
3. Generar seguro gratis (sin pago)
4. Descargar comprobante

### Portal Cliente:
1. Ingresar DNI
2. Ver todos los seguros
3. Descargar comprobantes
4. Renovar seguros vencidos

### Panel Admin:
1. Ver listado de seguros vendidos
2. Marcar como "procesado" cuando se cargue en sistema oficial
3. Crear/gestionar códigos promocionales

## 📞 Contacto

**Atención al Cliente:**
- 0800 555 3543
- 0810 362 0700

## 🏗️ Estructura del Proyecto

```
/app/
├── backend/
│   ├── server.py          # API FastAPI
│   ├── requirements.txt   # Dependencias Python
│   └── .env              # Variables de entorno
├── frontend/
│   ├── src/
│   │   ├── pages/        # Páginas principales
│   │   ├── components/   # Componentes React
│   │   ├── services/     # API clients
│   │   └── store/        # Estado global
│   └── package.json
└── uploads/              # Fotos de vehículos
```

## 📝 Notas Importantes

- **MercadoPago TEST**: Actualmente configurado en modo TEST
- **Fotos**: Guardadas localmente en `/app/uploads` (usar S3 en producción)
- **Webhook**: Configurar URL pública en MercadoPago dashboard
- **MongoDB**: Base de datos `estonia_seguros` creada automáticamente
- **Código MASTER**: Pre-configurado al iniciar el backend

## 🔐 Colecciones MongoDB

- `seguros` - Seguros generados
- `promo_codes` - Códigos promocionales
- `status_checks` - (legacy, puede eliminarse)

## 🎨 Diseño

- **Colores**: Verde Estonia (#064E3B) + Verde Lima (#D9F99D)
- **Tipografía**: Manrope (headings), Inter (body), Space Grotesk (números)
- **Componentes**: Shadcn/UI con TailwindCSS

---

**Estonia Seguros** - Seguros Express para circular sin preocupaciones 🛡️

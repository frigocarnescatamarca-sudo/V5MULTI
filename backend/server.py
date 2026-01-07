from fastapi import FastAPI, APIRouter, HTTPException, status, Request, UploadFile, File, Form
from fastapi.responses import FileResponse, Response
from fastapi.staticfiles import StaticFiles
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import os
import logging
from pathlib import Path
from pydantic import BaseModel, Field, ConfigDict, EmailStr
from typing import List, Optional
import uuid
from datetime import datetime, timezone, timedelta
import mercadopago
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from reportlab.lib.utils import ImageReader
from reportlab.lib.colors import HexColor
import qrcode
from io import BytesIO
from PIL import Image
import base64

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# MongoDB connection
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

# MercadoPago SDK (TEST mode)
mp_access_token = os.environ.get('MP_ACCESS_TOKEN', 'TEST-ACCESS-TOKEN')
sdk = mercadopago.SDK(mp_access_token)

# Create the main app
app = FastAPI(title="Estonia Seguros API")
api_router = APIRouter(prefix="/api")

# Servir archivos estáticos de uploads
app.mount("/uploads", StaticFiles(directory="/app/uploads"), name="uploads")

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# ============ MODELS ============

class VehicleType(str):
    AUTO = "auto"
    MOTO = "moto"
    TAXI = "taxi"
    APP = "app"

class CoverageType(str):
    RC = "rc"
    COMPLETO = "completo"

# Pricing configuration
PRICING = {
    "auto": {"rc": 6000, "completo": 9000},
    "moto": {"rc": 5000, "completo": 7500},
    "taxi": {"rc": 10000, "completo": 18000},
    "app": {"rc": 6000, "completo": 9000}
}

class InsuranceRequest(BaseModel):
    dni: str
    nombre: str
    email: EmailStr
    telefono: str
    patente: str
    marca: str
    modelo: str
    ano: int
    tipo_vehiculo: str
    cobertura: str
    codigo_promocional: Optional[str] = None

class PromoCode(BaseModel):
    codigo: str
    descuento_porcentaje: int = Field(ge=0, le=100)
    activo: bool = True
    es_master: bool = False

class PromoCodeCreate(BaseModel):
    codigo: str
    descuento_porcentaje: int = Field(ge=0, le=100)
    es_master: bool = False

class AgenteCreate(BaseModel):
    nombre: str
    email: EmailStr
    telefono: str
    username: str
    password: str
    comision_porcentaje: int = Field(ge=0, le=100, default=10)
    activo: bool = True

class AgenteUpdate(BaseModel):
    nombre: str
    email: EmailStr
    telefono: str
    comision_porcentaje: int = Field(ge=0, le=100)
    activo: bool
    password: Optional[str] = None  # Password opcional para actualización

class AgregarSaldoAgente(BaseModel):
    monto: float = Field(gt=0)
    observacion: str = ""

class RegistrarCobroAgente(BaseModel):
    monto: float = Field(gt=0)
    observacion: str = ""

class PremioCreate(BaseModel):
    nombre: str
    cantidad_seguros: int = Field(ge=1)
    monto_premio: float = Field(ge=0)
    activo: bool = True

class InsuranceResponse(BaseModel):
    id: str
    numero_recibo: str
    precio_original: float
    precio_final: float
    estado: str
    vigencia_desde: str
    vigencia_hasta: str

class PreferenceResponse(BaseModel):
    preference_id: str
    init_point: str
    seguro_id: str

# ============ HELPER FUNCTIONS ============

def generar_numero_recibo():
    """Genera un número de recibo único"""
    return str(uuid.uuid4())[:8].upper()

def calcular_precio(tipo_vehiculo: str, cobertura: str) -> float:
    """Calcula el precio base del seguro"""
    return PRICING.get(tipo_vehiculo, {}).get(cobertura, 6000)

async def aplicar_codigo_promocional(precio: float, codigo: str) -> tuple[float, bool]:
    """Aplica código promocional y retorna (precio_final, es_gratis)"""
    if not codigo:
        return precio, False
    
    promo = await db.promo_codes.find_one({"codigo": codigo.upper(), "activo": True})
    if not promo:
        return precio, False
    
    if promo.get("es_master", False):
        return 0, True
    
    descuento = promo.get("descuento_porcentaje", 0)
    precio_final = precio * (1 - descuento / 100)
    return precio_final, False

def generar_qr_code(data: str) -> BytesIO:
    """Genera un código QR"""
    qr = qrcode.QRCode(version=1, box_size=10, border=2)
    qr.add_data(data)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")
    buffer = BytesIO()
    img.save(buffer, format='PNG')
    buffer.seek(0)
    return buffer

def generar_pdf_comprobante(seguro: dict) -> BytesIO:
    """Genera el PDF del comprobante de cobertura - Diseño profesional"""
    buffer = BytesIO()
    c = canvas.Canvas(buffer, pagesize=letter)
    width, height = letter
    
    # Colores
    verde_oscuro = HexColor(0x064E3B)
    amarillo_resaltado = HexColor(0xFEF08A)
    gris = HexColor(0x64748B)
    negro = HexColor(0x000000)
    rojo = HexColor(0xDC2626)
    verde_aprobado = HexColor(0x10B981)
    azul_cobertura = HexColor(0x3B82F6)
    
    # Mapeo de tipos de cobertura
    tipos_cobertura = {
        'rc': 'RESPONSABILIDAD CIVIL',
        'terceros': 'TERCEROS COMPLETO',
        'completo': 'TODO RIESGO'
    }
    tipo_cobertura_texto = tipos_cobertura.get(seguro.get('cobertura', 'rc'), 'RESPONSABILIDAD CIVIL')
    
    # === HEADER CON LOGO ===
    try:
        logo_path = os.path.join(os.path.dirname(__file__), "logo_estonia.png")
        if os.path.exists(logo_path):
            logo = ImageReader(logo_path)
            c.drawImage(logo, 40, height - 120, width=100, height=100, mask='auto', preserveAspectRatio=True)
    except Exception as e:
        # Fallback: cuadrado con iniciales
        c.setFillColor(verde_oscuro)
        c.rect(40, height - 110, 80, 80, fill=1)
        c.setFillColor(HexColor(0xD9F99D))
        c.setFont("Helvetica-Bold", 28)
        c.drawCentredString(80, height - 80, "EC")
    
    # Título
    c.setFillColor(verde_oscuro)
    c.setFont("Helvetica-Bold", 22)
    c.drawString(160, height - 55, "ESTONIA")
    c.setFont("Helvetica-Bold", 18)
    c.drawString(160, height - 78, "COBERTURA COLABORATIVA")
    
    # Contacto
    c.setFillColor(gris)
    c.setFont("Helvetica", 9)
    c.drawRightString(width - 40, height - 50, "ATENCIÓN AL CLIENTE")
    c.setFillColor(negro)
    c.setFont("Helvetica-Bold", 11)
    c.drawRightString(width - 40, height - 65, "0800 555 3543")
    c.drawRightString(width - 40, height - 80, "0810 362 0700")
    
    # Línea separadora
    c.setStrokeColor(verde_oscuro)
    c.setLineWidth(2)
    c.line(40, height - 130, width - 40, height - 130)
    
    # === SECCIÓN DATOS PRINCIPALES ===
    y_pos = height - 165
    
    # Número de recibo grande
    c.setFillColor(verde_oscuro)
    c.setFont("Helvetica-Bold", 14)
    c.drawString(40, y_pos, "COMPROBANTE DE COBERTURA")
    c.setFont("Helvetica-Bold", 12)
    c.drawRightString(width - 40, y_pos, f"Nº {seguro['numero_recibo']}")
    
    # Tipo de Cobertura (badge azul)
    y_pos -= 35
    c.setFillColor(azul_cobertura)
    c.roundRect(40, y_pos - 5, 200, 28, 5, fill=1)
    c.setFillColor(HexColor(0xFFFFFF))
    c.setFont("Helvetica-Bold", 12)
    c.drawString(50, y_pos + 3, tipo_cobertura_texto)
    
    # Sello APROBADO
    c.setFillColor(verde_aprobado)
    c.roundRect(width - 140, y_pos - 5, 100, 28, 5, fill=1)
    c.setFillColor(HexColor(0xFFFFFF))
    c.setFont("Helvetica-Bold", 14)
    c.drawCentredString(width - 90, y_pos + 3, "APROBADO")
    
    # === DATOS DEL ASEGURADO ===
    y_pos -= 50
    c.setFillColor(verde_oscuro)
    c.setFont("Helvetica-Bold", 11)
    c.drawString(40, y_pos, "DATOS DEL TITULAR")
    c.setStrokeColor(gris)
    c.setLineWidth(0.5)
    c.line(40, y_pos - 5, 280, y_pos - 5)
    
    y_pos -= 25
    c.setFillColor(gris)
    c.setFont("Helvetica", 9)
    c.drawString(40, y_pos, "Nombre completo")
    c.setFillColor(negro)
    c.setFont("Helvetica-Bold", 11)
    c.drawString(40, y_pos - 15, seguro['nombre'].upper())
    
    y_pos -= 40
    c.setFillColor(gris)
    c.setFont("Helvetica", 9)
    c.drawString(40, y_pos, "DNI")
    c.drawString(150, y_pos, "Email")
    c.setFillColor(negro)
    c.setFont("Helvetica", 11)
    c.drawString(40, y_pos - 15, seguro['dni'])
    c.drawString(150, y_pos - 15, seguro.get('email', '-'))
    
    # === DATOS DEL VEHÍCULO ===
    y_pos -= 55
    c.setFillColor(verde_oscuro)
    c.setFont("Helvetica-Bold", 11)
    c.drawString(40, y_pos, "DATOS DEL VEHÍCULO")
    c.setStrokeColor(gris)
    c.line(40, y_pos - 5, 280, y_pos - 5)
    
    y_pos -= 25
    c.setFillColor(gris)
    c.setFont("Helvetica", 9)
    c.drawString(40, y_pos, "Dominio (Patente)")
    c.setFillColor(negro)
    c.setFont("Helvetica-Bold", 16)
    c.drawString(40, y_pos - 18, seguro['patente'])
    
    y_pos -= 45
    c.setFillColor(gris)
    c.setFont("Helvetica", 9)
    c.drawString(40, y_pos, "Marca / Modelo")
    c.drawString(200, y_pos, "Año")
    c.setFillColor(negro)
    c.setFont("Helvetica", 11)
    c.drawString(40, y_pos - 15, f"{seguro['marca']} {seguro['modelo']}")
    c.drawString(200, y_pos - 15, str(seguro.get('ano', '-')))
    
    # === VIGENCIA CON RESALTADO AMARILLO ===
    y_pos -= 55
    c.setFillColor(verde_oscuro)
    c.setFont("Helvetica-Bold", 11)
    c.drawString(40, y_pos, "VIGENCIA DE LA COBERTURA")
    c.setStrokeColor(gris)
    c.line(40, y_pos - 5, 350, y_pos - 5)
    
    y_pos -= 30
    c.setFillColor(gris)
    c.setFont("Helvetica", 9)
    c.drawString(40, y_pos, "Desde")
    c.drawString(180, y_pos, "Hasta (VENCIMIENTO)")
    
    y_pos -= 18
    c.setFillColor(negro)
    c.setFont("Helvetica", 11)
    c.drawString(40, y_pos, seguro['vigencia_desde'][:10])
    
    # RESALTADO AMARILLO PARA VENCIMIENTO
    c.setFillColor(amarillo_resaltado)
    c.roundRect(175, y_pos - 5, 130, 22, 3, fill=1, stroke=0)
    c.setFillColor(negro)
    c.setFont("Helvetica-Bold", 12)
    c.drawString(180, y_pos, seguro['vigencia_hasta'][:10])
    
    # === IMPORTE ===
    y_pos -= 50
    c.setFillColor(verde_oscuro)
    c.setFont("Helvetica-Bold", 11)
    c.drawString(40, y_pos, "IMPORTE ABONADO")
    y_pos -= 20
    c.setFont("Helvetica-Bold", 18)
    c.drawString(40, y_pos, f"$ {seguro['precio_final']:,.0f}")
    
    # === QR CODE ===
    qr_url = f"{os.environ.get('REACT_APP_BACKEND_URL', 'http://localhost:3000')}/verificar/{seguro['numero_recibo']}"
    qr_buffer = generar_qr_code(qr_url)
    qr_image = ImageReader(qr_buffer)
    c.drawImage(qr_image, width - 180, 120, width=140, height=140, mask='auto')
    
    c.setFillColor(gris)
    c.setFont("Helvetica", 9)
    c.drawCentredString(width - 110, 105, "Escanea para verificar")
    c.drawCentredString(width - 110, 92, "la cobertura")
    
    # === FOOTER ===
    c.setFillColor(gris)
    c.setFont("Helvetica", 8)
    c.drawString(40, 60, "RECIBO VÁLIDO PARA PRESENTAR DE MANERA DIGITAL O IMPRESO.")
    c.drawString(40, 47, "POR DUDAS O CONSULTAS LLAME A LOS NÚMEROS DE ATENCIÓN AL CLIENTE.")
    c.drawString(40, 34, f"Generado el: {datetime.now().strftime('%d/%m/%Y %H:%M')}")
    
    c.save()
    buffer.seek(0)
    return buffer

# ============ ROUTES ============

@api_router.get("/")
async def root():
    return {"message": "Estonia Seguros API", "version": "1.0"}

@api_router.post("/seguros/cotizar")
async def cotizar_seguro(data: dict):
    """Cotiza un seguro y retorna el precio"""
    tipo_vehiculo = data.get("tipo_vehiculo")
    cobertura = data.get("cobertura")
    codigo = data.get("codigo_promocional")
    
    precio_base = calcular_precio(tipo_vehiculo, cobertura)
    precio_final, es_gratis = await aplicar_codigo_promocional(precio_base, codigo)
    
    return {
        "precio_base": precio_base,
        "precio_final": precio_final,
        "es_gratis": es_gratis,
        "cobertura_nombre": "Responsabilidad Civil" if cobertura == "rc" else "Terceros Completo"
    }

@api_router.post("/seguros/crear", response_model=InsuranceResponse)
async def crear_seguro(request: InsuranceRequest):
    """Crea un nuevo seguro"""
    
    precio_base = calcular_precio(request.tipo_vehiculo, request.cobertura)
    precio_final, es_gratis = await aplicar_codigo_promocional(
        precio_base, 
        request.codigo_promocional
    )
    
    seguro_id = str(uuid.uuid4())
    numero_recibo = generar_numero_recibo()
    fecha_inicio = datetime.now(timezone.utc)
    fecha_fin = fecha_inicio + timedelta(days=30)
    
    seguro_doc = {
        "_id": seguro_id,
        "numero_recibo": numero_recibo,
        "dni": request.dni,
        "nombre": request.nombre,
        "email": request.email,
        "telefono": request.telefono,
        "patente": request.patente,
        "marca": request.marca,
        "modelo": request.modelo,
        "ano": request.ano,
        "tipo_vehiculo": request.tipo_vehiculo,
        "cobertura": request.cobertura,
        "precio_original": precio_base,
        "precio_final": precio_final,
        "estado": "gratis" if es_gratis else "pendiente_pago",
        "vigencia_desde": fecha_inicio.isoformat(),
        "vigencia_hasta": fecha_fin.isoformat(),
        "codigo_promocional_usado": request.codigo_promocional,
        "fotos": [],
        "procesado": False,
        "created_at": fecha_inicio.isoformat()
    }
    
    await db.seguros.insert_one(seguro_doc)
    
    return InsuranceResponse(
        id=seguro_id,
        numero_recibo=numero_recibo,
        precio_original=precio_base,
        precio_final=precio_final,
        estado=seguro_doc["estado"],
        vigencia_desde=fecha_inicio.isoformat(),
        vigencia_hasta=fecha_fin.isoformat()
    )

@api_router.post("/seguros/{seguro_id}/upload-foto")
async def upload_foto(seguro_id: str, foto: UploadFile = File(...), tipo: str = Form(...)):
    """Sube una foto del vehículo"""
    
    # Guardar foto en filesystem (en producción usar S3)
    upload_dir = Path("/app/uploads")
    upload_dir.mkdir(exist_ok=True)
    
    file_ext = foto.filename.split(".")[-1]
    filename = f"{seguro_id}_{tipo}.{file_ext}"
    file_path = upload_dir / filename
    
    contents = await foto.read()
    with open(file_path, "wb") as f:
        f.write(contents)
    
    # Actualizar base de datos
    await db.seguros.update_one(
        {"_id": seguro_id},
        {"$push": {"fotos": {"tipo": tipo, "filename": filename, "path": str(file_path)}}}
    )
    
    return {"success": True, "filename": filename}

@api_router.post("/pagos/crear-preferencia", response_model=PreferenceResponse)
async def crear_preferencia_pago(data: dict):
    """Crea una preferencia de pago en MercadoPago"""
    
    seguro_id = data.get("seguro_id")
    seguro = await db.seguros.find_one({"_id": seguro_id})
    
    if not seguro:
        raise HTTPException(status_code=404, detail="Seguro no encontrado")
    
    if seguro["estado"] == "pagado":
        raise HTTPException(status_code=400, detail="Este seguro ya está pagado")
    
    # Crear preferencia en MercadoPago
    preference_data = {
        "items": [
            {
                "title": f"Seguro {seguro['tipo_vehiculo'].upper()} - {seguro['patente']}",
                "quantity": 1,
                "currency_id": "ARS",
                "unit_price": float(seguro["precio_final"])
            }
        ],
        "payer": {
            "name": seguro["nombre"],
            "email": seguro["email"],
            "phone": {
                "number": seguro["telefono"]
            }
        },
        "external_reference": seguro_id,
        "auto_return": "approved",
        "back_urls": {
            "success": f"{os.environ.get('REACT_APP_BACKEND_URL', 'http://localhost:3000')}/pago-exitoso",
            "failure": f"{os.environ.get('REACT_APP_BACKEND_URL', 'http://localhost:3000')}/pago-fallido",
            "pending": f"{os.environ.get('REACT_APP_BACKEND_URL', 'http://localhost:3000')}/pago-pendiente"
        },
        "notification_url": f"{os.environ.get('BACKEND_WEBHOOK_URL', 'http://localhost:8001')}/api/webhook/mercadopago"
    }
    
    try:
        result = sdk.preference().create(preference_data)
        response = result["response"]
        
        # Guardar preferencia en BD
        await db.seguros.update_one(
            {"_id": seguro_id},
            {"$set": {"preference_id": response["id"], "estado": "pendiente_pago"}}
        )
        
        return PreferenceResponse(
            preference_id=response["id"],
            init_point=response["init_point"],
            seguro_id=seguro_id
        )
    except Exception as e:
        logger.error(f"Error creating preference: {e}")
        raise HTTPException(status_code=500, detail="Error al crear preferencia de pago")

@api_router.post("/webhook/mercadopago")
async def webhook_mercadopago(request: Request):
    """Webhook para notificaciones de MercadoPago"""
    
    body = await request.json()
    logger.info(f"Webhook received: {body}")
    
    if body.get("type") == "payment":
        payment_id = body["data"]["id"]
        
        try:
            # Obtener información del pago
            payment_info = sdk.payment().get(payment_id)
            payment_data = payment_info["response"]
            
            if payment_data["status"] == "approved":
                external_reference = payment_data.get("external_reference")
                
                # Actualizar estado del seguro
                await db.seguros.update_one(
                    {"_id": external_reference},
                    {"$set": {
                        "estado": "pagado",
                        "payment_id": payment_id,
                        "fecha_pago": datetime.now(timezone.utc).isoformat()
                    }}
                )
                
                logger.info(f"Payment approved for seguro {external_reference}")
        except Exception as e:
            logger.error(f"Error processing webhook: {e}")
    
    return {"status": "ok"}

@api_router.get("/seguros/{seguro_id}/comprobante/pdf")
async def descargar_comprobante_pdf(seguro_id: str):
    """Descarga el comprobante en PDF"""
    
    seguro = await db.seguros.find_one({"_id": seguro_id})
    if not seguro:
        raise HTTPException(status_code=404, detail="Seguro no encontrado")
    
    if seguro["estado"] not in ["pagado", "gratis"]:
        raise HTTPException(status_code=400, detail="El seguro debe estar pagado para descargar el comprobante")
    
    pdf_buffer = generar_pdf_comprobante(seguro)
    
    return Response(
        content=pdf_buffer.getvalue(),
        media_type="application/pdf",
        headers={
            "Content-Disposition": f"attachment; filename=comprobante_{seguro['numero_recibo']}.pdf"
        }
    )

@api_router.get("/seguros/{seguro_id}/comprobante/imagen")
async def descargar_comprobante_imagen(seguro_id: str):
    """Genera y descarga el comprobante como imagen - Diseño profesional"""
    from PIL import Image, ImageDraw, ImageFont
    
    seguro = await db.seguros.find_one({"_id": seguro_id})
    if not seguro:
        raise HTTPException(status_code=404, detail="Seguro no encontrado")
    
    if seguro["estado"] not in ["pagado", "gratis"]:
        raise HTTPException(status_code=400, detail="El seguro debe estar pagado")
    
    # Mapeo de tipos de cobertura
    tipos_cobertura = {
        'rc': 'RESPONSABILIDAD CIVIL',
        'terceros': 'TERCEROS COMPLETO',
        'completo': 'TODO RIESGO'
    }
    tipo_cobertura_texto = tipos_cobertura.get(seguro.get('cobertura', 'rc'), 'RESPONSABILIDAD CIVIL')
    
    # Crear imagen
    img = Image.new('RGB', (800, 1050), color='white')
    draw = ImageDraw.Draw(img)
    
    # Colores
    verde_oscuro = (6, 78, 59)
    amarillo_resaltado = (254, 240, 138)
    negro = (0, 0, 0)
    gris = (100, 116, 139)
    verde_aprobado = (16, 185, 129)
    azul_cobertura = (59, 130, 246)
    blanco = (255, 255, 255)
    
    # Fuentes
    try:
        font_title = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 24)
        font_large = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 18)
        font_medium = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 14)
        font_normal = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 14)
        font_small = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 11)
        font_patente = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 22)
    except:
        font_title = font_large = font_medium = font_normal = font_small = font_patente = ImageFont.load_default()
    
    # === HEADER CON LOGO ===
    try:
        logo_path = os.path.join(os.path.dirname(__file__), "logo_estonia.png")
        if os.path.exists(logo_path):
            logo = Image.open(logo_path)
            logo = logo.resize((90, 90), Image.Resampling.LANCZOS)
            # Si tiene transparencia, crear fondo blanco
            if logo.mode == 'RGBA':
                bg = Image.new('RGB', logo.size, 'white')
                bg.paste(logo, mask=logo.split()[3])
                logo = bg
            img.paste(logo, (30, 20))
    except Exception as e:
        # Fallback: cuadrado con iniciales
        draw.rectangle([30, 20, 110, 100], fill=verde_oscuro)
        draw.text((70, 60), "EC", fill=(217, 249, 157), font=font_large, anchor="mm")
    
    # Título
    draw.text((140, 35), "ESTONIA", fill=verde_oscuro, font=font_title)
    draw.text((140, 65), "COBERTURA COLABORATIVA", fill=verde_oscuro, font=font_medium)
    
    # Contacto
    draw.text((620, 25), "ATENCIÓN AL CLIENTE", fill=gris, font=font_small)
    draw.text((620, 42), "0800 555 3543", fill=negro, font=font_normal)
    draw.text((620, 60), "0810 362 0700", fill=negro, font=font_normal)
    
    # Línea separadora
    draw.line([(30, 120), (770, 120)], fill=verde_oscuro, width=2)
    
    # === NÚMERO DE RECIBO Y SELLO ===
    y_pos = 145
    draw.text((30, y_pos), "COMPROBANTE DE COBERTURA", fill=verde_oscuro, font=font_medium)
    draw.text((500, y_pos), f"Nº {seguro['numero_recibo']}", fill=verde_oscuro, font=font_medium)
    
    # Tipo de Cobertura (badge azul)
    y_pos += 35
    draw.rounded_rectangle([30, y_pos - 5, 250, y_pos + 25], radius=5, fill=azul_cobertura)
    draw.text((40, y_pos + 2), tipo_cobertura_texto, fill=blanco, font=font_medium)
    
    # Sello APROBADO
    draw.rounded_rectangle([660, y_pos - 5, 770, y_pos + 25], radius=5, fill=verde_aprobado)
    draw.text((715, y_pos + 10), "APROBADO", fill=blanco, font=font_medium, anchor="mm")
    
    # === DATOS DEL TITULAR ===
    y_pos += 50
    draw.text((30, y_pos), "DATOS DEL TITULAR", fill=verde_oscuro, font=font_medium)
    draw.line([(30, y_pos + 20), (300, y_pos + 20)], fill=gris, width=1)
    
    y_pos += 35
    draw.text((30, y_pos), "Nombre completo", fill=gris, font=font_small)
    draw.text((30, y_pos + 18), seguro['nombre'].upper(), fill=negro, font=font_large)
    
    y_pos += 55
    draw.text((30, y_pos), "DNI", fill=gris, font=font_small)
    draw.text((180, y_pos), "Email", fill=gris, font=font_small)
    draw.text((30, y_pos + 18), seguro['dni'], fill=negro, font=font_normal)
    draw.text((180, y_pos + 18), seguro.get('email', '-'), fill=negro, font=font_normal)
    
    # === DATOS DEL VEHÍCULO ===
    y_pos += 60
    draw.text((30, y_pos), "DATOS DEL VEHÍCULO", fill=verde_oscuro, font=font_medium)
    draw.line([(30, y_pos + 20), (300, y_pos + 20)], fill=gris, width=1)
    
    y_pos += 35
    draw.text((30, y_pos), "Dominio (Patente)", fill=gris, font=font_small)
    draw.text((30, y_pos + 18), seguro['patente'], fill=negro, font=font_patente)
    
    y_pos += 55
    draw.text((30, y_pos), "Marca / Modelo", fill=gris, font=font_small)
    draw.text((280, y_pos), "Año", fill=gris, font=font_small)
    draw.text((30, y_pos + 18), f"{seguro['marca']} {seguro['modelo']}", fill=negro, font=font_normal)
    draw.text((280, y_pos + 18), str(seguro.get('ano', '-')), fill=negro, font=font_normal)
    
    # === VIGENCIA CON RESALTADO AMARILLO ===
    y_pos += 60
    draw.text((30, y_pos), "VIGENCIA DE LA COBERTURA", fill=verde_oscuro, font=font_medium)
    draw.line([(30, y_pos + 20), (400, y_pos + 20)], fill=gris, width=1)
    
    y_pos += 35
    draw.text((30, y_pos), "Desde", fill=gris, font=font_small)
    draw.text((200, y_pos), "Hasta (VENCIMIENTO)", fill=gris, font=font_small)
    
    y_pos += 18
    draw.text((30, y_pos), seguro['vigencia_desde'][:10], fill=negro, font=font_normal)
    
    # RESALTADO AMARILLO PARA VENCIMIENTO
    draw.rounded_rectangle([195, y_pos - 5, 340, y_pos + 22], radius=5, fill=amarillo_resaltado)
    draw.text((200, y_pos), seguro['vigencia_hasta'][:10], fill=negro, font=font_large)
    
    # === IMPORTE ===
    y_pos += 50
    draw.text((30, y_pos), "IMPORTE ABONADO", fill=verde_oscuro, font=font_medium)
    draw.text((30, y_pos + 25), f"$ {seguro['precio_final']:,.0f}", fill=verde_oscuro, font=font_title)
    
    # === QR CODE ===
    qr_url = f"{os.environ.get('REACT_APP_BACKEND_URL', 'http://localhost:3000')}/verificar/{seguro['numero_recibo']}"
    qr_buffer = generar_qr_code(qr_url)
    qr_img = Image.open(qr_buffer)
    qr_img = qr_img.resize((150, 150))
    img.paste(qr_img, (600, 750))
    
    draw.text((675, 910), "Escanea para verificar", fill=gris, font=font_small, anchor="mm")
    draw.text((675, 928), "la cobertura", fill=gris, font=font_small, anchor="mm")
    
    # === FOOTER ===
    draw.text((30, 970), "RECIBO VÁLIDO PARA PRESENTAR DE MANERA DIGITAL O IMPRESO.", fill=gris, font=font_small)
    draw.text((30, 990), "POR DUDAS O CONSULTAS LLAME A LOS NÚMEROS DE ATENCIÓN AL CLIENTE.", fill=gris, font=font_small)
    draw.text((30, 1010), f"Generado el: {datetime.now().strftime('%d/%m/%Y %H:%M')}", fill=gris, font=font_small)
    
    buffer = BytesIO()
    img.save(buffer, format='PNG', quality=95)
    buffer.seek(0)
    
    return Response(
        content=buffer.getvalue(),
        media_type="image/png",
        headers={
            "Content-Disposition": f"attachment; filename=comprobante_{seguro['numero_recibo']}.png"
        }
    )

@api_router.get("/verificar/{numero_recibo}")
async def verificar_seguro(numero_recibo: str):
    """Verifica un seguro por QR (para agentes viales)"""
    
    seguro = await db.seguros.find_one({"numero_recibo": numero_recibo})
    
    if not seguro:
        return {"valido": False, "mensaje": "Seguro no encontrado"}
    
    # Verificar vigencia
    fecha_fin = datetime.fromisoformat(seguro["vigencia_hasta"])
    ahora = datetime.now(timezone.utc)
    
    if ahora > fecha_fin:
        return {
            "valido": False,
            "mensaje": "Seguro vencido",
            "datos": {
                "patente": seguro["patente"],
                "nombre": seguro["nombre"],
                "vigencia_hasta": seguro["vigencia_hasta"][:10]
            }
        }
    
    if seguro["estado"] not in ["pagado", "gratis"]:
        return {
            "valido": False,
            "mensaje": "Seguro pendiente de pago"
        }
    
    return {
        "valido": True,
        "mensaje": "COBERTURA VIGENTE",
        "datos": {
            "numero_recibo": seguro["numero_recibo"],
            "patente": seguro["patente"],
            "nombre": seguro["nombre"],
            "dni": seguro["dni"],
            "marca": seguro["marca"],
            "modelo": seguro["modelo"],
            "ano": seguro["ano"],
            "cobertura": "Responsabilidad Civil" if seguro["cobertura"] == "rc" else "Terceros Completo",
            "vigencia_desde": seguro["vigencia_desde"][:10],
            "vigencia_hasta": seguro["vigencia_hasta"][:10]
        }
    }

@api_router.get("/cliente/{dni}/seguros")
async def obtener_seguros_cliente(dni: str):
    """Obtiene todos los seguros de un cliente por DNI"""
    
    seguros = await db.seguros.find(
        {"dni": dni},
        {"_id": 0}
    ).sort("created_at", -1).to_list(100)
    
    return {"seguros": seguros}

@api_router.get("/coberturas/dni/{dni}")
async def consultar_coberturas_por_dni(dni: str):
    """Endpoint público para consultar coberturas por DNI - Portal Web"""
    
    # Clean DNI - remove dots, spaces and hyphens
    dni_clean = dni.replace('.', '').replace(' ', '').replace('-', '').strip()
    
    if not dni_clean.isdigit() or len(dni_clean) < 7 or len(dni_clean) > 8:
        raise HTTPException(status_code=400, detail="DNI inválido. Debe contener entre 7 y 8 dígitos.")
    
    coberturas = await db.seguros.find(
        {"dni": dni_clean},
        {"_id": 0, "email": 0, "telefono": 0}  # Exclude sensitive data
    ).sort("created_at", -1).to_list(100)
    
    # Add status check for each coverage
    ahora = datetime.now(timezone.utc)
    for cob in coberturas:
        vigencia_hasta = cob.get('vigencia_hasta', '')
        if vigencia_hasta:
            try:
                fecha_fin = datetime.fromisoformat(vigencia_hasta)
                cob['vigente'] = fecha_fin > ahora and cob.get('estado') in ['pagado', 'gratis']
                cob['vencida'] = fecha_fin <= ahora
            except:
                cob['vigente'] = False
                cob['vencida'] = False
        else:
            cob['vigente'] = False
            cob['vencida'] = False
    
    return {
        "dni": dni_clean,
        "total": len(coberturas),
        "coberturas": coberturas
    }

@api_router.get("/whatsapp/ventas")
async def obtener_whatsapp_ventas():
    """Endpoint público para obtener el número de WhatsApp de ventas"""
    config = await get_bot_config()
    whatsapp_ventas = config.get('whatsapp_ventas', '')
    
    return {
        "whatsapp_ventas": whatsapp_ventas,
        "tiene_whatsapp": bool(whatsapp_ventas)
    }

@api_router.post("/seguros/{seguro_id}/renovar")
async def renovar_seguro(seguro_id: str):
    """Renueva un seguro existente"""
    
    seguro_original = await db.seguros.find_one({"_id": seguro_id})
    
    if not seguro_original:
        raise HTTPException(status_code=404, detail="Seguro no encontrado")
    
    # Crear nuevo seguro con los mismos datos
    nuevo_seguro_id = str(uuid.uuid4())
    numero_recibo = generar_numero_recibo()
    fecha_inicio = datetime.now(timezone.utc)
    fecha_fin = fecha_inicio + timedelta(days=30)
    
    nuevo_seguro = {
        "_id": nuevo_seguro_id,
        "numero_recibo": numero_recibo,
        "dni": seguro_original["dni"],
        "nombre": seguro_original["nombre"],
        "email": seguro_original["email"],
        "telefono": seguro_original["telefono"],
        "patente": seguro_original["patente"],
        "marca": seguro_original["marca"],
        "modelo": seguro_original["modelo"],
        "ano": seguro_original["ano"],
        "tipo_vehiculo": seguro_original["tipo_vehiculo"],
        "cobertura": seguro_original["cobertura"],
        "precio_original": seguro_original["precio_original"],
        "precio_final": seguro_original["precio_original"],  # Sin descuento en renovación
        "estado": "pendiente_pago",
        "vigencia_desde": fecha_inicio.isoformat(),
        "vigencia_hasta": fecha_fin.isoformat(),
        "seguro_renovado_de": seguro_id,
        "fotos": seguro_original.get("fotos", []),
        "procesado": False,
        "created_at": fecha_inicio.isoformat()
    }
    
    await db.seguros.insert_one(nuevo_seguro)
    
    return InsuranceResponse(
        id=nuevo_seguro_id,
        numero_recibo=numero_recibo,
        precio_original=nuevo_seguro["precio_original"],
        precio_final=nuevo_seguro["precio_final"],
        estado=nuevo_seguro["estado"],
        vigencia_desde=fecha_inicio.isoformat(),
        vigencia_hasta=fecha_fin.isoformat()
    )

# ============ ADMIN ROUTES ============

@api_router.post("/admin/login")
async def admin_login(data: dict):
    """Login de administrador"""
    username = data.get("username")
    password = data.get("password")
    
    # Credenciales hardcodeadas (en producción usar hash y BD)
    ADMIN_USERNAME = os.environ.get("ADMIN_USERNAME", "admin")
    ADMIN_PASSWORD = os.environ.get("ADMIN_PASSWORD", "Estonia2025!")
    
    if username == ADMIN_USERNAME and password == ADMIN_PASSWORD:
        # Generar token simple (en producción usar JWT)
        import secrets
        token = secrets.token_urlsafe(32)
        
        # Guardar token en base de datos (expira en 24h)
        await db.admin_sessions.insert_one({
            "token": token,
            "username": username,
            "created_at": datetime.now(timezone.utc),
            "expires_at": datetime.now(timezone.utc) + timedelta(hours=24)
        })
        
        return {
            "success": True,
            "token": token,
            "username": username
        }
    
    raise HTTPException(status_code=401, detail="Credenciales inválidas")

@api_router.post("/admin/logout")
async def admin_logout(data: dict):
    """Logout de administrador"""
    token = data.get("token")
    if token:
        await db.admin_sessions.delete_one({"token": token})
    return {"success": True}

@api_router.get("/admin/verify")
async def verify_admin_token(token: str):
    """Verifica si un token de admin es válido"""
    session = await db.admin_sessions.find_one({
        "token": token,
        "expires_at": {"$gt": datetime.now(timezone.utc)}
    })
    
    if session:
        return {"valid": True, "username": session["username"]}
    
    return {"valid": False}

# ============ AGENTES ROUTES ============

@api_router.post("/agente/login")
async def agente_login(data: dict):
    """Login de agente"""
    username = data.get("username")
    password = data.get("password")
    
    # Buscar agente en base de datos
    agente = await db.agentes.find_one({"username": username, "activo": True})
    
    if not agente:
        raise HTTPException(status_code=401, detail="Credenciales inválidas")
    
    # Verificar password (en producción usar hash)
    if agente.get("password") != password:
        raise HTTPException(status_code=401, detail="Credenciales inválidas")
    
    # Generar token
    import secrets
    token = secrets.token_urlsafe(32)
    
    # Guardar sesión
    await db.agente_sessions.insert_one({
        "token": token,
        "agente_id": agente["_id"],
        "username": username,
        "created_at": datetime.now(timezone.utc),
        "expires_at": datetime.now(timezone.utc) + timedelta(hours=24)
    })
    
    return {
        "success": True,
        "token": token,
        "agente": {
            "id": agente["_id"],
            "nombre": agente["nombre"],
            "email": agente["email"],
            "comision_porcentaje": agente.get("comision_porcentaje", 10)
        }
    }

@api_router.post("/agente/logout")
async def agente_logout(data: dict):
    """Logout de agente"""
    token = data.get("token")
    if token:
        await db.agente_sessions.delete_one({"token": token})
    return {"success": True}

@api_router.get("/agente/verify")
async def verify_agente_token(token: str):
    """Verifica si un token de agente es válido"""
    session = await db.agente_sessions.find_one({
        "token": token,
        "expires_at": {"$gt": datetime.now(timezone.utc)}
    })
    
    if session:
        agente = await db.agentes.find_one({"_id": session["agente_id"]})
        if agente:
            return {
                "valid": True,
                "agente": {
                    "id": agente["_id"],
                    "nombre": agente["nombre"],
                    "username": session["username"]
                }
            }
    
    return {"valid": False}

@api_router.get("/agente/mis-seguros")
async def obtener_seguros_agente(token: str):
    """Obtiene los seguros del agente autenticado"""
    session = await db.agente_sessions.find_one({
        "token": token,
        "expires_at": {"$gt": datetime.now(timezone.utc)}
    })
    
    if not session:
        raise HTTPException(status_code=401, detail="Token inválido")
    
    agente_id = session["agente_id"]
    
    # Obtener datos del agente
    agente = await db.agentes.find_one({"_id": agente_id})
    
    # Obtener seguros asignados al agente
    seguros = await db.seguros.find(
        {"agente_id": agente_id}
    ).sort("created_at", -1).to_list(1000)
    
    # Convertir _id a id
    for seguro in seguros:
        if '_id' in seguro:
            seguro['id'] = seguro['_id']
            del seguro['_id']
    
    # Calcular estadísticas
    total_seguros = len(seguros)
    seguros_pagados_list = [s for s in seguros if s.get('estado') in ['pagado', 'gratis']]
    seguros_pagados = len(seguros_pagados_list)
    
    # Total ventas y comisiones
    total_ventas = sum([s.get('precio_final', 0) for s in seguros_pagados_list])
    total_comisiones = sum([
        s.get('precio_final', 0) * (s.get('comision_porcentaje', agente.get('comision_porcentaje', 10) if agente else 10) / 100)
        for s in seguros_pagados_list
    ])
    
    # Calcular deuda al admin
    deuda_bruta = total_ventas - total_comisiones
    
    # Obtener cobros realizados
    cobros = await db.cobros_agentes.find({"agente_id": agente_id}).to_list(1000)
    total_cobrado = sum([c.get('monto', 0) for c in cobros])
    
    # Deuda actual
    deuda_actual = deuda_bruta - total_cobrado
    
    # Verificar premios ganados
    premios_activos = await db.premios.find({"activo": True}).to_list(100)
    premios_ganados = []
    
    for premio in premios_activos:
        if seguros_pagados >= premio.get('cantidad_seguros', 0):
            premios_ganados.append({
                "nombre": premio.get('nombre'),
                "monto": premio.get('monto_premio'),
                "cantidad_requerida": premio.get('cantidad_seguros')
            })
    
    return {
        "seguros": seguros,
        "estadisticas": {
            "total_seguros": total_seguros,
            "seguros_pagados": seguros_pagados,
            "seguros_pendientes": total_seguros - seguros_pagados,
            "total_ventas": total_ventas,
            "total_comisiones": total_comisiones,
            "deuda_bruta": deuda_bruta,
            "total_cobrado": total_cobrado,
            "deuda_actual": deuda_actual,
            "premios_ganados": premios_ganados
        },
        "cobros": [{
            "id": c["_id"],
            "monto": c["monto"],
            "observacion": c.get("observacion", ""),
            "fecha": c["fecha"]
        } for c in cobros]
    }

@api_router.get("/agente/vencimientos")
async def obtener_vencimientos_agente(token: str):
    """Obtiene próximos vencimientos del agente"""
    session = await db.agente_sessions.find_one({
        "token": token,
        "expires_at": {"$gt": datetime.now(timezone.utc)}
    })
    
    if not session:
        raise HTTPException(status_code=401, detail="Token inválido")
    
    agente_id = session["agente_id"]
    ahora = datetime.now(timezone.utc)
    
    # Seguros del agente
    seguros = await db.seguros.find(
        {"agente_id": agente_id, "estado": {"$in": ["pagado", "gratis"]}}
    ).to_list(1000)
    
    # Clasificar por vencimiento
    vencidos = []
    proximos_7_dias = []
    proximos_15_dias = []
    proximos_30_dias = []
    vigentes = []
    
    for seguro in seguros:
        vigencia_hasta = datetime.fromisoformat(seguro['vigencia_hasta'])
        dias_restantes = (vigencia_hasta - ahora).days
        
        seguro['id'] = seguro['_id']
        del seguro['_id']
        seguro['dias_restantes'] = dias_restantes
        
        if dias_restantes < 0:
            vencidos.append(seguro)
        elif dias_restantes <= 7:
            proximos_7_dias.append(seguro)
        elif dias_restantes <= 15:
            proximos_15_dias.append(seguro)
        elif dias_restantes <= 30:
            proximos_30_dias.append(seguro)
        else:
            vigentes.append(seguro)
    
    return {
        "vencidos": vencidos,
        "proximos_7_dias": proximos_7_dias,
        "proximos_15_dias": proximos_15_dias,
        "proximos_30_dias": proximos_30_dias,
        "vigentes": vigentes
    }

@api_router.post("/agente/crear-seguro")
async def crear_seguro_agente(data: dict):
    """Crea un seguro asignado al agente"""
    
    token = data.get('token')
    if not token:
        raise HTTPException(status_code=401, detail="Token requerido")
    
    session = await db.agente_sessions.find_one({
        "token": token,
        "expires_at": {"$gt": datetime.now(timezone.utc)}
    })
    
    if not session:
        raise HTTPException(status_code=401, detail="Token inválido")
    
    agente_id = session["agente_id"]
    
    # Obtener datos del agente
    agente = await db.agentes.find_one({"_id": agente_id})
    if not agente:
        raise HTTPException(status_code=404, detail="Agente no encontrado")
    
    # Validar campos requeridos
    required_fields = ['dni', 'nombre', 'email', 'patente', 'marca', 'modelo']
    for field in required_fields:
        if not data.get(field):
            raise HTTPException(status_code=400, detail=f"Campo {field} es requerido")
    
    # Generar número de recibo único
    numero_recibo = f"EC-{datetime.now().strftime('%Y%m%d')}-{str(uuid.uuid4())[:8].upper()}"
    
    # Calcular precio según tipo de cobertura
    precios_cobertura = {
        'rc': 15000,
        'terceros': 25000,
        'completo': 45000
    }
    cobertura = data.get('cobertura', 'rc')
    precio = precios_cobertura.get(cobertura, 15000)
    
    # Crear el seguro - APROBADO DIRECTAMENTE cuando lo crea un agente
    seguro_doc = {
        "_id": str(uuid.uuid4()),
        "numero_recibo": numero_recibo,
        "dni": data['dni'],
        "nombre": data['nombre'],
        "email": data['email'],
        "telefono": data.get('telefono', ''),
        "patente": data['patente'].upper(),
        "marca": data['marca'],
        "modelo": data['modelo'],
        "ano": data.get('ano', datetime.now().year),
        "tipo_vehiculo": data.get('tipo_vehiculo', 'auto'),
        "cobertura": cobertura,
        "precio_original": precio,
        "precio_final": precio,
        "estado": "pagado",  # Aprobado directamente
        "procesado": True,
        "vigencia_desde": datetime.now(timezone.utc).isoformat(),
        "vigencia_hasta": (datetime.now(timezone.utc) + timedelta(days=30)).isoformat(),
        "fotos": {},
        "agente_id": agente_id,
        "agente_nombre": agente['nombre'],
        "comision_porcentaje": agente.get('comision_porcentaje', 10),
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    
    await db.seguros.insert_one(seguro_doc)
    
    seguro_doc['id'] = seguro_doc['_id']
    del seguro_doc['_id']
    
    return {"success": True, "seguro": seguro_doc}

@api_router.get("/admin/seguros")
async def listar_seguros_admin(skip: int = 0, limit: int = 50, token: str = None):
    """Lista todos los seguros (admin)"""
    
    # Verificar token (opcional por ahora para no romper frontend)
    if token:
        session = await db.admin_sessions.find_one({
            "token": token,
            "expires_at": {"$gt": datetime.now(timezone.utc)}
        })
        if not session:
            raise HTTPException(status_code=401, detail="Token inválido o expirado")
    
    seguros = await db.seguros.find(
        {}
    ).sort("created_at", -1).skip(skip).limit(limit).to_list(limit)
    
    # Convertir _id a string para serialización
    for seguro in seguros:
        if '_id' in seguro:
            seguro['id'] = seguro['_id']
            del seguro['_id']
    
    total = await db.seguros.count_documents({})
    
    return {
        "seguros": seguros,
        "total": total,
        "skip": skip,
        "limit": limit
    }

@api_router.post("/admin/seguros/{seguro_id}/marcar-procesado")
async def marcar_seguro_procesado(seguro_id: str):
    """Marca un seguro como procesado en el sistema oficial"""
    
    result = await db.seguros.update_one(
        {"_id": seguro_id},
        {"$set": {
            "procesado": True,
            "fecha_procesado": datetime.now(timezone.utc).isoformat()
        }}
    )
    
    if result.modified_count == 0:
        raise HTTPException(status_code=404, detail="Seguro no encontrado")
    
    return {"success": True}

@api_router.put("/admin/seguros/{seguro_id}")
async def actualizar_seguro(seguro_id: str, data: InsuranceRequest):
    """Actualiza un seguro existente (admin)"""
    
    seguro_existente = await db.seguros.find_one({"_id": seguro_id})
    if not seguro_existente:
        raise HTTPException(status_code=404, detail="Seguro no encontrado")
    
    # Calcular nuevo precio si cambió tipo o cobertura
    precio_base = calcular_precio(data.tipo_vehiculo, data.cobertura)
    
    update_data = {
        "dni": data.dni,
        "nombre": data.nombre,
        "email": data.email,
        "telefono": data.telefono,
        "patente": data.patente,
        "marca": data.marca,
        "modelo": data.modelo,
        "ano": data.ano,
        "tipo_vehiculo": data.tipo_vehiculo,
        "cobertura": data.cobertura,
        "precio_original": precio_base,
        "updated_at": datetime.now(timezone.utc).isoformat()
    }
    
    result = await db.seguros.update_one(
        {"_id": seguro_id},
        {"$set": update_data}
    )
    
    if result.modified_count == 0:
        raise HTTPException(status_code=404, detail="Seguro no encontrado")
    
    return {"success": True, "message": "Seguro actualizado correctamente"}

@api_router.delete("/admin/seguros/{seguro_id}")
async def eliminar_seguro(seguro_id: str):
    """Elimina un seguro (admin)"""
    
    result = await db.seguros.delete_one({"_id": seguro_id})
    
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Seguro no encontrado")
    
    return {"success": True, "message": "Seguro eliminado correctamente"}

@api_router.post("/admin/seguros/crear-manual")
async def crear_seguro_manual(data: InsuranceRequest):
    """Crea un seguro manualmente desde admin (sin pago)"""
    
    precio_base = calcular_precio(data.tipo_vehiculo, data.cobertura)
    
    seguro_id = str(uuid.uuid4())
    numero_recibo = generar_numero_recibo()
    fecha_inicio = datetime.now(timezone.utc)
    fecha_fin = fecha_inicio + timedelta(days=30)
    
    seguro_doc = {
        "_id": seguro_id,
        "numero_recibo": numero_recibo,
        "dni": data.dni,
        "nombre": data.nombre,
        "email": data.email,
        "telefono": data.telefono,
        "patente": data.patente,
        "marca": data.marca,
        "modelo": data.modelo,
        "ano": data.ano,
        "tipo_vehiculo": data.tipo_vehiculo,
        "cobertura": data.cobertura,
        "precio_original": precio_base,
        "precio_final": precio_base,
        "estado": "pagado",  # Admin lo crea como pagado
        "vigencia_desde": fecha_inicio.isoformat(),
        "vigencia_hasta": fecha_fin.isoformat(),
        "fotos": [],
        "procesado": False,
        "creado_por_admin": True,
        "created_at": fecha_inicio.isoformat()
    }
    
    await db.seguros.insert_one(seguro_doc)
    
    return {
        "success": True,
        "seguro": {
            "id": seguro_id,
            "numero_recibo": numero_recibo,
            "estado": "pagado"
        }
    }

@api_router.post("/admin/promo-codes", response_model=PromoCode)
async def crear_codigo_promocional(promo: PromoCodeCreate):
    """Crea un nuevo código promocional"""
    
    # Verificar si ya existe
    existente = await db.promo_codes.find_one({"codigo": promo.codigo.upper()})
    if existente:
        raise HTTPException(status_code=400, detail="El código ya existe")
    
    promo_doc = {
        "codigo": promo.codigo.upper(),
        "descuento_porcentaje": promo.descuento_porcentaje,
        "es_master": promo.es_master,
        "activo": True,
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    
    await db.promo_codes.insert_one(promo_doc)
    
    return PromoCode(
        codigo=promo_doc["codigo"],
        descuento_porcentaje=promo_doc["descuento_porcentaje"],
        activo=promo_doc["activo"],
        es_master=promo_doc["es_master"]
    )

@api_router.get("/admin/promo-codes")
async def listar_codigos_promocionales():
    """Lista todos los códigos promocionales"""
    
    codigos = await db.promo_codes.find({}, {"_id": 0}).to_list(100)
    return {"codigos": codigos}

@api_router.delete("/admin/promo-codes/{codigo}")
async def eliminar_codigo_promocional(codigo: str):
    """Desactiva un código promocional"""
    
    result = await db.promo_codes.update_one(
        {"codigo": codigo.upper()},
        {"$set": {"activo": False}}
    )
    
    if result.modified_count == 0:
        raise HTTPException(status_code=404, detail="Código no encontrado")
    
    return {"success": True}

# ============ ADMIN AGENTES ROUTES ============

@api_router.post("/admin/agentes")
async def crear_agente(agente: AgenteCreate):
    """Crea un nuevo agente"""
    
    # Verificar si ya existe el username
    existente = await db.agentes.find_one({"username": agente.username})
    if existente:
        raise HTTPException(status_code=400, detail="El username ya existe")
    
    agente_doc = {
        "_id": str(uuid.uuid4()),
        "nombre": agente.nombre,
        "email": agente.email,
        "telefono": agente.telefono,
        "username": agente.username,
        "password": agente.password,  # En producción usar hash
        "comision_porcentaje": agente.comision_porcentaje,
        "activo": agente.activo,
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    
    await db.agentes.insert_one(agente_doc)
    
    agente_doc['id'] = agente_doc['_id']
    del agente_doc['_id']
    del agente_doc['password']  # No devolver password
    
    return {"success": True, "agente": agente_doc}

@api_router.get("/admin/agentes")
async def listar_agentes():
    """Lista todos los agentes con estadísticas y deuda"""
    
    agentes = await db.agentes.find({}).to_list(1000)
    
    # Calcular estadísticas para cada agente
    for agente in agentes:
        agente_id = agente['_id']
        agente['id'] = agente_id
        del agente['_id']
        if 'password' in agente:
            del agente['password']  # No exponer passwords
        
        # Contar seguros del agente
        total_seguros = await db.seguros.count_documents({"agente_id": agente_id})
        seguros_pagados = await db.seguros.count_documents({
            "agente_id": agente_id,
            "estado": {"$in": ["pagado", "gratis"]}
        })
        
        # Obtener seguros pagados para calcular
        seguros = await db.seguros.find({
            "agente_id": agente_id,
            "estado": {"$in": ["pagado", "gratis"]}
        }).to_list(1000)
        
        # Calcular totales
        total_ventas = sum([s.get('precio_final', 0) for s in seguros])
        total_comisiones = sum([
            s.get('precio_final', 0) * (s.get('comision_porcentaje', agente.get('comision_porcentaje', 10)) / 100)
            for s in seguros
        ])
        
        # Deuda bruta = ventas - comisiones
        deuda_bruta = total_ventas - total_comisiones
        
        # Obtener total de cobros realizados
        cobros = await db.cobros_agentes.find({"agente_id": agente_id}).to_list(1000)
        total_cobrado = sum([c.get('monto', 0) for c in cobros])
        
        # Deuda actual = deuda bruta - cobros realizados
        deuda_actual = deuda_bruta - total_cobrado
        
        # Saldo actual (dinero que admin le debe al agente, si es positivo)
        saldo_actual = agente.get('saldo', 0)
        
        agente['estadisticas'] = {
            "total_seguros": total_seguros,
            "seguros_pagados": seguros_pagados,
            "total_ventas": total_ventas,
            "total_comisiones": total_comisiones,
            "deuda_bruta": deuda_bruta,
            "total_cobrado": total_cobrado,
            "deuda_actual": deuda_actual,
            "saldo_actual": saldo_actual
        }
    
    return {"agentes": agentes}

@api_router.put("/admin/agentes/{agente_id}")
async def actualizar_agente(agente_id: str, agente: AgenteUpdate):
    """Actualiza un agente"""
    
    update_data = {
        "nombre": agente.nombre,
        "email": agente.email,
        "telefono": agente.telefono,
        "comision_porcentaje": agente.comision_porcentaje,
        "activo": agente.activo,
        "updated_at": datetime.now(timezone.utc).isoformat()
    }
    
    # Solo actualizar password si se proporciona
    if agente.password:
        update_data["password"] = agente.password
    
    result = await db.agentes.update_one(
        {"_id": agente_id},
        {"$set": update_data}
    )
    
    if result.modified_count == 0:
        raise HTTPException(status_code=404, detail="Agente no encontrado")
    
    return {"success": True}

@api_router.delete("/admin/agentes/{agente_id}")
async def eliminar_agente(agente_id: str):
    """Elimina un agente (lo desactiva)"""
    
    result = await db.agentes.update_one(
        {"_id": agente_id},
        {"$set": {"activo": False}}
    )
    
    if result.modified_count == 0:
        raise HTTPException(status_code=404, detail="Agente no encontrado")
    
    return {"success": True}

@api_router.post("/admin/agentes/{agente_id}/agregar-saldo")
async def agregar_saldo_agente(agente_id: str, data: AgregarSaldoAgente):
    """Agrega saldo a un agente con observación"""
    
    # Verificar que el agente existe
    agente = await db.agentes.find_one({"_id": agente_id})
    if not agente:
        raise HTTPException(status_code=404, detail="Agente no encontrado")
    
    # Crear registro de movimiento
    movimiento = {
        "_id": str(uuid.uuid4()),
        "agente_id": agente_id,
        "tipo": "ingreso",
        "monto": data.monto,
        "observacion": data.observacion,
        "fecha": datetime.now(timezone.utc).isoformat(),
        "saldo_anterior": agente.get("saldo", 0),
        "saldo_nuevo": agente.get("saldo", 0) + data.monto
    }
    
    await db.movimientos_agentes.insert_one(movimiento)
    
    # Actualizar saldo del agente
    nuevo_saldo = agente.get("saldo", 0) + data.monto
    await db.agentes.update_one(
        {"_id": agente_id},
        {"$set": {"saldo": nuevo_saldo}}
    )
    
    return {
        "success": True,
        "saldo_anterior": movimiento["saldo_anterior"],
        "saldo_nuevo": nuevo_saldo,
        "movimiento_id": movimiento["_id"]
    }

@api_router.get("/admin/agentes/{agente_id}/movimientos")
async def obtener_movimientos_agente(agente_id: str):
    """Obtiene el historial de movimientos de un agente"""
    
    movimientos = await db.movimientos_agentes.find(
        {"agente_id": agente_id}
    ).sort("fecha", -1).to_list(100)
    
    for mov in movimientos:
        mov["id"] = mov["_id"]
        del mov["_id"]
    
    return {"movimientos": movimientos}

@api_router.post("/admin/agentes/{agente_id}/registrar-cobro")
async def registrar_cobro_agente(agente_id: str, data: RegistrarCobroAgente):
    """Registra un cobro realizado al agente (el agente pagó al admin)"""
    
    # Verificar que el agente existe
    agente = await db.agentes.find_one({"_id": agente_id})
    if not agente:
        raise HTTPException(status_code=404, detail="Agente no encontrado")
    
    # Calcular deuda actual para validar
    seguros = await db.seguros.find({
        "agente_id": agente_id,
        "estado": {"$in": ["pagado", "gratis"]}
    }).to_list(1000)
    
    total_ventas = sum([s.get('precio_final', 0) for s in seguros])
    total_comisiones = sum([
        s.get('precio_final', 0) * (s.get('comision_porcentaje', agente.get('comision_porcentaje', 10)) / 100)
        for s in seguros
    ])
    deuda_bruta = total_ventas - total_comisiones
    
    cobros_previos = await db.cobros_agentes.find({"agente_id": agente_id}).to_list(1000)
    total_cobrado_previo = sum([c.get('monto', 0) for c in cobros_previos])
    deuda_actual = deuda_bruta - total_cobrado_previo
    
    # Crear registro de cobro
    cobro = {
        "_id": str(uuid.uuid4()),
        "agente_id": agente_id,
        "agente_nombre": agente['nombre'],
        "monto": data.monto,
        "observacion": data.observacion,
        "fecha": datetime.now(timezone.utc).isoformat(),
        "deuda_antes": deuda_actual,
        "deuda_despues": deuda_actual - data.monto
    }
    
    await db.cobros_agentes.insert_one(cobro)
    
    cobro['id'] = cobro['_id']
    del cobro['_id']
    
    return {
        "success": True,
        "cobro": cobro,
        "deuda_anterior": deuda_actual,
        "deuda_nueva": deuda_actual - data.monto
    }

@api_router.get("/admin/agentes/{agente_id}/cobros")
async def obtener_cobros_agente(agente_id: str):
    """Obtiene el historial de cobros de un agente"""
    
    cobros = await db.cobros_agentes.find(
        {"agente_id": agente_id}
    ).sort("fecha", -1).to_list(100)
    
    for cobro in cobros:
        cobro["id"] = cobro["_id"]
        del cobro["_id"]
    
    return {"cobros": cobros}

@api_router.post("/admin/seguros/{seguro_id}/asignar-agente")
async def asignar_agente_a_seguro(seguro_id: str, data: dict):
    """Asigna un agente a un seguro"""
    
    agente_id = data.get("agente_id")
    
    # Verificar que el agente existe
    agente = await db.agentes.find_one({"_id": agente_id})
    if not agente:
        raise HTTPException(status_code=404, detail="Agente no encontrado")
    
    result = await db.seguros.update_one(
        {"_id": seguro_id},
        {"$set": {
            "agente_id": agente_id,
            "agente_nombre": agente['nombre'],
            "comision_aplicada": agente.get('comision_porcentaje', 10)
        }}
    )
    
    if result.modified_count == 0:
        raise HTTPException(status_code=404, detail="Seguro no encontrado")
    
    return {"success": True}

# ============ ADMIN PREMIOS ROUTES ============

@api_router.post("/admin/premios")
async def crear_premio(premio: PremioCreate):
    """Crea un nuevo premio"""
    
    premio_doc = {
        "_id": str(uuid.uuid4()),
        "nombre": premio.nombre,
        "cantidad_seguros": premio.cantidad_seguros,
        "monto_premio": premio.monto_premio,
        "activo": premio.activo,
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    
    await db.premios.insert_one(premio_doc)
    
    premio_doc['id'] = premio_doc['_id']
    del premio_doc['_id']
    
    return {"success": True, "premio": premio_doc}

@api_router.get("/admin/premios")
async def listar_premios():
    """Lista todos los premios"""
    
    premios = await db.premios.find({}).to_list(100)
    
    for premio in premios:
        premio['id'] = premio['_id']
        del premio['_id']
    
    return {"premios": premios}

@api_router.delete("/admin/premios/{premio_id}")
async def eliminar_premio(premio_id: str):
    """Desactiva un premio"""
    
    result = await db.premios.update_one(
        {"_id": premio_id},
        {"$set": {"activo": False}}
    )
    
    if result.modified_count == 0:
        raise HTTPException(status_code=404, detail="Premio no encontrado")
    
    return {"success": True}

@api_router.get("/admin/vencimientos")
async def obtener_vencimientos_admin():
    """Obtiene todos los vencimientos para el admin"""
    
    ahora = datetime.now(timezone.utc)
    
    # Todos los seguros pagados/gratis
    seguros = await db.seguros.find(
        {"estado": {"$in": ["pagado", "gratis"]}}
    ).to_list(10000)
    
    # Clasificar por vencimiento
    vencidos = []
    proximos_7_dias = []
    proximos_15_dias = []
    proximos_30_dias = []
    vigentes = []
    
    for seguro in seguros:
        vigencia_hasta = datetime.fromisoformat(seguro['vigencia_hasta'])
        dias_restantes = (vigencia_hasta - ahora).days
        
        seguro['id'] = seguro['_id']
        del seguro['_id']
        seguro['dias_restantes'] = dias_restantes
        
        if dias_restantes < 0:
            vencidos.append(seguro)
        elif dias_restantes <= 7:
            proximos_7_dias.append(seguro)
        elif dias_restantes <= 15:
            proximos_15_dias.append(seguro)
        elif dias_restantes <= 30:
            proximos_30_dias.append(seguro)
        else:
            vigentes.append(seguro)
    
    return {
        "vencidos": vencidos,
        "proximos_7_dias": proximos_7_dias,
        "proximos_15_dias": proximos_15_dias,
        "proximos_30_dias": proximos_30_dias,
        "vigentes": vigentes
    }

# ============ WHATSAPP BOT ROUTES ============

from whatsapp_service import (
    process_message_with_ai,
    get_bot_config,
    update_bot_config,
    get_whatsapp_status,
    get_whatsapp_qr,
    connect_whatsapp,
    disconnect_whatsapp,
    get_conversations,
    pause_chat,
    resume_chat,
    send_whatsapp_message,
    get_chat_history,
    simulate_conversation_flow,
    get_coverage_by_id,
    mark_coverage_paid
)

class WhatsAppConfigUpdate(BaseModel):
    mensaje_bienvenida: Optional[str] = None
    instrucciones_bot: Optional[str] = None
    datos_bancarios: Optional[str] = None
    numero_admin: Optional[str] = None
    admin_lid: Optional[str] = None
    whatsapp_ventas: Optional[str] = None
    bot_activo: Optional[bool] = None

@api_router.post("/whatsapp/message")
async def receive_whatsapp_message(data: dict):
    """Receive message from WhatsApp service and process with AI"""
    phone_number = data.get("phone_number")
    message = data.get("message")
    push_name = data.get("push_name", "")
    reply_jid = data.get("reply_jid", "")  # JID for replying to this user
    
    if not phone_number or not message:
        raise HTTPException(status_code=400, detail="phone_number and message required")
    
    # Store the JID mapping for this phone
    if reply_jid:
        await store_jid_mapping(phone_number, reply_jid)
    
    # Process with AI
    reply = await process_message_with_ai(phone_number, message, push_name)
    
    return {"reply": reply}

async def store_jid_mapping(phone_number: str, jid: str):
    """Store the JID mapping for a phone number"""
    from whatsapp_service import db
    await db.whatsapp_jid_mapping.update_one(
        {"phone_number": phone_number},
        {"$set": {"jid": jid, "updated_at": datetime.now(timezone.utc).isoformat()}},
        upsert=True
    )

@api_router.get("/admin/whatsapp/status")
async def admin_get_whatsapp_status():
    """Get WhatsApp connection status"""
    return await get_whatsapp_status()

@api_router.get("/admin/whatsapp/qr")
async def admin_get_whatsapp_qr():
    """Get QR code for WhatsApp connection"""
    return await get_whatsapp_qr()

@api_router.post("/admin/whatsapp/connect")
async def admin_connect_whatsapp():
    """Initiate WhatsApp connection"""
    return await connect_whatsapp()

@api_router.post("/admin/whatsapp/disconnect")
async def admin_disconnect_whatsapp():
    """Disconnect WhatsApp"""
    return await disconnect_whatsapp()

@api_router.get("/admin/whatsapp/config")
async def admin_get_whatsapp_config():
    """Get bot configuration"""
    return await get_bot_config()

@api_router.put("/admin/whatsapp/config")
async def admin_update_whatsapp_config(data: WhatsAppConfigUpdate):
    """Update bot configuration"""
    update_data = {k: v for k, v in data.dict().items() if v is not None}
    return await update_bot_config(update_data)

@api_router.get("/admin/whatsapp/conversations")
async def admin_get_conversations():
    """Get all conversations"""
    return await get_conversations()

@api_router.post("/admin/whatsapp/pause-chat")
async def admin_pause_chat(data: dict):
    """Pause bot for a specific chat"""
    phone_number = data.get("phone_number")
    if not phone_number:
        raise HTTPException(status_code=400, detail="phone_number required")
    return await pause_chat(phone_number)

@api_router.post("/admin/whatsapp/resume-chat")
async def admin_resume_chat(data: dict):
    """Resume bot for a specific chat"""
    phone_number = data.get("phone_number")
    if not phone_number:
        raise HTTPException(status_code=400, detail="phone_number required")
    return await resume_chat(phone_number)

@api_router.post("/admin/whatsapp/send")
async def admin_send_message(data: dict):
    """Send a message manually"""
    phone_number = data.get("phone_number")
    message = data.get("message")
    if not phone_number or not message:
        raise HTTPException(status_code=400, detail="phone_number and message required")
    return await send_whatsapp_message(phone_number, message)

@api_router.get("/admin/whatsapp/chat/{phone_number}")
async def admin_get_chat_history(phone_number: str, limit: int = 50):
    """Get chat history for a specific number"""
    messages = await get_chat_history(phone_number, limit)
    return {"messages": messages, "phone_number": phone_number}

@api_router.post("/admin/whatsapp/simulate")
async def admin_simulate_conversation(data: dict):
    """
    Simulate a complete WhatsApp conversation flow for testing.
    Creates a coverage, simulates payment, and generates receipt.
    """
    phone_number = data.get("phone_number", "5491112345678")
    client_data = {
        "nombre": data.get("nombre", "Carlos García"),
        "dni": data.get("dni", "30456789"),
        "email": data.get("email", "carlos.garcia@email.com"),
        "patente": data.get("patente", "AD456FG"),
        "marca": data.get("marca", "Volkswagen"),
        "modelo": data.get("modelo", "Golf"),
        "ano": data.get("ano", 2021),
        "tipo_vehiculo": data.get("tipo_vehiculo", "auto"),
        "cobertura": data.get("cobertura", "rc")
    }
    
    result = await simulate_conversation_flow(phone_number, client_data)
    return result

# Include router
app.include_router(api_router)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=os.environ.get('CORS_ORIGINS', '*').split(','),
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
async def startup_event():
    """Inicializa la base de datos con código MASTER si no existe"""
    master_code = await db.promo_codes.find_one({"codigo": "MASTER"})
    if not master_code:
        await db.promo_codes.insert_one({
            "codigo": "MASTER",
            "descuento_porcentaje": 100,
            "es_master": True,
            "activo": True,
            "created_at": datetime.now(timezone.utc).isoformat()
        })
        logger.info("Código MASTER creado")

@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()
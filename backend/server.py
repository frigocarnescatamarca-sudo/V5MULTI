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
    """Genera el PDF del comprobante de seguro"""
    buffer = BytesIO()
    c = canvas.Canvas(buffer, pagesize=letter)
    width, height = letter
    
    # Colores Estonia
    verde_estonia = HexColor(0x064E3B)
    verde_lima = HexColor(0xD9F99D)
    
    # Logo (Escudo simple con iniciales ES)
    c.setFillColor(verde_estonia)
    c.rect(50, height - 100, 60, 60, fill=1)
    c.setFillColor(verde_lima)
    c.setFont("Helvetica-Bold", 28)
    c.drawCentredString(80, height - 80, "ES")
    
    # Header
    c.setFillColor(verde_estonia)
    c.setFont("Helvetica-Bold", 24)
    c.drawString(120, height - 70, "ESTONIA")
    c.setFont("Helvetica-Bold", 20)
    c.drawString(120, height - 90, "SEGUROS")
    
    # Teléfonos
    c.setFont("Helvetica", 10)
    c.setFillColor(HexColor(0x000000))
    c.drawString(400, height - 60, "ATENCION AL CLIENTE")
    c.setFont("Helvetica-Bold", 12)
    c.drawString(400, height - 75, "0800 555 3543")
    c.drawString(400, height - 90, "0810 362 0700")
    
    # Sello PAGADO
    c.setStrokeColor(HexColor(0xFF0000))
    c.setLineWidth(3)
    c.rect(450, height - 150, 100, 40, fill=0)
    c.setFillColor(HexColor(0xFF0000))
    c.setFont("Helvetica-Bold", 20)
    c.drawCentredString(500, height - 140, "PAGADO")
    
    # Información principal
    c.setFillColor(HexColor(0x000000))
    c.setFont("Helvetica", 11)
    y_pos = height - 180
    
    c.drawString(50, y_pos, f"Pagado el: {seguro['vigencia_desde'][:10]}")
    c.drawString(350, y_pos, f"Recibo Nro: {seguro['numero_recibo']}")
    
    y_pos -= 40
    c.drawString(50, y_pos, f"DNI: {seguro['dni']}")
    
    y_pos -= 30
    c.drawString(50, y_pos, f"Asegurado: {seguro['nombre']}")
    c.drawString(350, y_pos, "Cuota: 1")
    
    y_pos -= 30
    c.drawString(50, y_pos, f"Marca/Modelo: {seguro['marca']} {seguro['modelo']}")
    c.drawString(350, y_pos, "Tipo de Pago: DEB. AUTOMATICO")
    
    y_pos -= 30
    c.drawString(50, y_pos, f"Año: {seguro['ano']}")
    
    y_pos -= 40
    c.drawString(50, y_pos, f"Dominio: {seguro['patente']}")
    c.drawString(350, y_pos, f"Próx Vto: {seguro['vigencia_hasta'][:10]}")
    
    y_pos -= 40
    c.setFont("Helvetica-Bold", 14)
    c.drawString(350, y_pos, f"Importe: ${seguro['precio_final']:,.0f}")
    
    # QR Code
    qr_buffer = generar_qr_code(f"{os.environ.get('REACT_APP_BACKEND_URL', 'http://localhost:3000')}/verificar/{seguro['numero_recibo']}")
    qr_image = ImageReader(qr_buffer)
    c.drawImage(qr_image, 50, 100, width=120, height=120, mask='auto')
    
    # Footer
    c.setFont("Helvetica", 8)
    c.drawString(50, 50, "RECIBO VALIDO PARA PRESENTAR DE MANERA DIGITAL O IMPRESO.")
    c.drawString(50, 35, "POR DUDAS O CONSULTAS LLAME A LOS NUMEROS DE ATENCION AL CLIENTE")
    
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
    """Genera y descarga el comprobante como imagen"""
    from PIL import Image, ImageDraw, ImageFont
    
    seguro = await db.seguros.find_one({"_id": seguro_id})
    if not seguro:
        raise HTTPException(status_code=404, detail="Seguro no encontrado")
    
    if seguro["estado"] not in ["pagado", "gratis"]:
        raise HTTPException(status_code=400, detail="El seguro debe estar pagado")
    
    # Crear imagen con información del comprobante
    img = Image.new('RGB', (800, 1100), color='white')
    draw = ImageDraw.Draw(img)
    
    # Colores
    verde_oscuro = (6, 78, 59)
    verde_lima = (217, 249, 157)
    negro = (0, 0, 0)
    rojo = (255, 0, 0)
    gris = (100, 116, 139)
    
    # Fuentes por defecto (sin archivo de fuente)
    try:
        from PIL import ImageFont
        # Intentar cargar fuentes del sistema
        font_title = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 32)
        font_large = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 24)
        font_normal = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 18)
        font_small = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 14)
    except:
        font_title = ImageFont.load_default()
        font_large = ImageFont.load_default()
        font_normal = ImageFont.load_default()
        font_small = ImageFont.load_default()
    
    # Logo/Header - Cuadrado verde con ES
    draw.rectangle([20, 20, 100, 100], fill=verde_oscuro)
    draw.text((60, 60), "ES", fill=verde_lima, font=font_large, anchor="mm")
    
    # Texto ESTONIA SEGUROS
    draw.text((120, 40), "ESTONIA", fill=verde_oscuro, font=font_title)
    draw.text((120, 75), "SEGUROS", fill=verde_oscuro, font=font_large)
    
    # Teléfonos
    draw.text((580, 30), "ATENCION AL CLIENTE", fill=gris, font=font_small)
    draw.text((580, 50), "0800 555 3543", fill=negro, font=font_normal)
    draw.text((580, 70), "0810 362 0700", fill=negro, font=font_normal)
    
    # Sello PAGADO
    draw.rectangle([650, 110, 770, 160], outline=rojo, width=4)
    draw.text((710, 135), "PAGADO", fill=rojo, font=font_large, anchor="mm")
    
    # Información principal
    y_pos = 180
    draw.text((20, y_pos), f"Pagado el: {seguro['vigencia_desde'][:10]}", fill=negro, font=font_normal)
    draw.text((500, y_pos), f"Recibo Nro: {seguro['numero_recibo']}", fill=negro, font=font_normal)
    
    y_pos += 50
    draw.text((20, y_pos), f"DNI: {seguro['dni']}", fill=negro, font=font_normal)
    
    y_pos += 40
    draw.text((20, y_pos), f"Asegurado: {seguro['nombre']}", fill=negro, font=font_normal)
    draw.text((500, y_pos), "Cuota: 1", fill=negro, font=font_normal)
    
    y_pos += 40
    draw.text((20, y_pos), f"Marca/Modelo: {seguro['marca']} {seguro['modelo']}", fill=negro, font=font_normal)
    draw.text((500, y_pos), "Tipo de Pago:", fill=negro, font=font_normal)
    
    y_pos += 40
    draw.text((20, y_pos), f"Año: {seguro['ano']}", fill=negro, font=font_normal)
    draw.text((500, y_pos), "DEB. AUTOMATICO", fill=negro, font=font_normal)
    
    y_pos += 50
    draw.text((20, y_pos), f"Dominio: {seguro['patente']}", fill=negro, font=font_large)
    draw.text((500, y_pos), f"Próx Vto: {seguro['vigencia_hasta'][:10]}", fill=negro, font=font_normal)
    
    y_pos += 60
    draw.text((500, y_pos), f"Importe: ${seguro['precio_final']:,.0f}", fill=negro, font=font_large)
    
    # QR Code
    qr_buffer = generar_qr_code(f"{os.environ.get('REACT_APP_BACKEND_URL', 'http://localhost:3000')}/verificar/{seguro['numero_recibo']}")
    qr_img = Image.open(qr_buffer)
    qr_img = qr_img.resize((180, 180))
    img.paste(qr_img, (20, 550))
    
    # Texto junto al QR
    draw.text((220, 570), "Escanea el código QR", fill=gris, font=font_normal)
    draw.text((220, 595), "para verificar la", fill=gris, font=font_normal)
    draw.text((220, 620), "cobertura", fill=gris, font=font_normal)
    
    # Footer
    draw.text((20, 950), "RECIBO VALIDO PARA PRESENTAR DE MANERA", fill=gris, font=font_normal)
    draw.text((20, 975), "DIGITAL O IMPRESO.", fill=gris, font=font_normal)
    draw.text((20, 1005), "POR DUDAS O CONSULTAS LLAME A LOS NUMEROS", fill=gris, font=font_small)
    draw.text((20, 1025), "DE ATENCION AL CLIENTE", fill=gris, font=font_small)
    
    buffer = BytesIO()
    img.save(buffer, format='PNG')
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
    seguros_pagados = len([s for s in seguros if s.get('estado') in ['pagado', 'gratis']])
    total_comisiones = sum([
        s.get('precio_final', 0) * (session.get('comision_porcentaje', 10) / 100)
        for s in seguros if s.get('estado') in ['pagado', 'gratis']
    ])
    
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
            "total_comisiones": total_comisiones,
            "premios_ganados": premios_ganados
        }
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
    
    # Crear el seguro
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
        "estado": "pendiente",
        "vigencia_desde": datetime.now(timezone.utc).isoformat(),
        "vigencia_hasta": (datetime.now(timezone.utc) + timedelta(days=30)).isoformat(),
        "fotos": {},
        "agente_id": agente_id,
        "agente_nombre": agente['nombre'],
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
    """Lista todos los agentes"""
    
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
        
        # Calcular comisiones
        seguros = await db.seguros.find({
            "agente_id": agente_id,
            "estado": {"$in": ["pagado", "gratis"]}
        }).to_list(1000)
        
        total_comisiones = sum([
            s.get('precio_final', 0) * (agente.get('comision_porcentaje', 10) / 100)
            for s in seguros
        ])
        
        # Incluir saldo actual
        saldo_actual = agente.get('saldo', 0)
        
        agente['estadisticas'] = {
            "total_seguros": total_seguros,
            "seguros_pagados": seguros_pagados,
            "total_comisiones": total_comisiones,
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
import { useState } from 'react';
import { X, Upload, CheckCircle2, Loader2 } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { useDropzone } from 'react-dropzone';
import { segurosAPI, pagosAPI } from '@/services/api';
import { toast } from 'sonner';
import { useSeguroStore } from '@/store/useSeguroStore';

export default function FormularioSeguro({ onClose }) {
  const [step, setStep] = useState(1);
  const [formData, setFormData] = useState({
    dni: '',
    nombre: '',
    email: '',
    telefono: '',
    patente: '',
    marca: '',
    modelo: '',
    ano: new Date().getFullYear(),
    tipo_vehiculo: 'auto',
    cobertura: 'rc',
    codigo_promocional: ''
  });
  const [fotos, setFotos] = useState({ 
    frente: null, 
    lado_izq: null, 
    lado_der: null, 
    trasera: null,
    cedula_vehiculo: null,
    carnet_conductor: null
  });
  const [cotizacion, setCotizacion] = useState(null);
  const [loading, setLoading] = useState(false);
  const { setSeguroActual } = useSeguroStore();

  const handleChange = (field, value) => {
    setFormData(prev => ({ ...prev, [field]: value }));
  };

  const handleCotizar = async () => {
    setLoading(true);
    try {
      const result = await segurosAPI.cotizar({
        tipo_vehiculo: formData.tipo_vehiculo,
        cobertura: formData.cobertura,
        codigo_promocional: formData.codigo_promocional
      });
      setCotizacion(result);
      toast.success('Cotización generada exitosamente');
    } catch (error) {
      toast.error('Error al cotizar');
    } finally {
      setLoading(false);
    }
  };

  const handleSubmit = async () => {
    // Validaciones
    if (!formData.dni || !formData.nombre || !formData.email || !formData.telefono || !formData.patente) {
      toast.error('Por favor complete todos los campos obligatorios');
      return;
    }

    const fotosRequeridas = ['frente', 'lado_izq', 'lado_der', 'trasera', 'cedula_vehiculo', 'carnet_conductor'];
    const faltanFotos = fotosRequeridas.some(tipo => !fotos[tipo]);
    
    if (faltanFotos) {
      toast.error('Por favor suba todas las fotos y documentos requeridos');
      return;
    }

    setLoading(true);
    try {
      // Crear seguro
      const seguro = await segurosAPI.crear(formData);
      setSeguroActual(seguro);

      // Subir fotos
      const fotoPromises = Object.entries(fotos).map(([tipo, archivo]) => {
        if (archivo) {
          return segurosAPI.uploadFoto(seguro.id, archivo, tipo);
        }
      });
      await Promise.all(fotoPromises);

      // Si es gratis (código MASTER), mostrar descarga directa
      if (seguro.estado === 'gratis') {
        toast.success('¡Seguro generado exitosamente! (Gratis con código promocional)');
        setStep(4); // Paso de descarga
      } else {
        // Crear preferencia de pago
        const preferencia = await pagosAPI.crearPreferencia(seguro.id);
        // Redirigir a MercadoPago
        window.location.href = preferencia.init_point;
      }
    } catch (error) {
      toast.error('Error al crear el seguro: ' + (error.response?.data?.detail || error.message));
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="fixed inset-0 bg-black/50 backdrop-blur-sm z-50 flex items-center justify-center p-4">
      <div className="bg-white rounded-3xl shadow-2xl max-w-3xl w-full max-h-[90vh] overflow-y-auto">
        {/* Header */}
        <div className="sticky top-0 bg-[#064E3B] text-white p-6 rounded-t-3xl flex justify-between items-center">
          <div>
            <h2 className="text-2xl font-bold" style={{ fontFamily: 'Manrope, sans-serif' }}>
              Generar Seguro Express
            </h2>
            <p className="text-[#D9F99D] text-sm">Paso {step} de 3</p>
          </div>
          <button onClick={onClose} className="text-white hover:text-[#D9F99D]">
            <X className="w-6 h-6" />
          </button>
        </div>

        {/* Progress Bar */}
        <div className="px-6 pt-4">
          <div className="flex gap-2">
            {[1, 2, 3].map(s => (
              <div key={s} className={`flex-1 h-2 rounded-full ${
                s <= step ? 'bg-[#10B981]' : 'bg-slate-200'
              }`} />
            ))}
          </div>
        </div>

        {/* Content */}
        <div className="p-6">
          {step === 1 && (
            <Step1 
              formData={formData} 
              onChange={handleChange}
              cotizacion={cotizacion}
              onCotizar={handleCotizar}
              loading={loading}
              onNext={() => setStep(2)}
            />
          )}

          {step === 2 && (
            <Step2 
              fotos={fotos}
              setFotos={setFotos}
              onNext={() => setStep(3)}
              onBack={() => setStep(1)}
            />
          )}

          {step === 3 && (
            <Step3 
              formData={formData}
              cotizacion={cotizacion}
              loading={loading}
              onSubmit={handleSubmit}
              onBack={() => setStep(2)}
            />
          )}

          {step === 4 && (
            <StepDescarga seguro={useSeguroStore.getState().seguroActual} />
          )}
        </div>
      </div>
    </div>
  );
}

function Step1({ formData, onChange, cotizacion, onCotizar, loading, onNext }) {
  return (
    <div className="space-y-6">
      <h3 className="text-xl font-bold text-[#064E3B]">Información Personal y del Vehículo</h3>
      
      <div className="grid md:grid-cols-2 gap-4">
        <div>
          <Label htmlFor="dni">DNI *</Label>
          <Input
            id="dni"
            value={formData.dni}
            onChange={(e) => onChange('dni', e.target.value)}
            placeholder="12345678"
            data-testid="dni-input"
          />
        </div>
        <div>
          <Label htmlFor="nombre">Nombre Completo *</Label>
          <Input
            id="nombre"
            value={formData.nombre}
            onChange={(e) => onChange('nombre', e.target.value)}
            placeholder="Juan Pérez"
            data-testid="nombre-input"
          />
        </div>
        <div>
          <Label htmlFor="email">Email *</Label>
          <Input
            id="email"
            type="email"
            value={formData.email}
            onChange={(e) => onChange('email', e.target.value)}
            placeholder="juan@email.com"
            data-testid="email-input"
          />
        </div>
        <div>
          <Label htmlFor="telefono">Teléfono *</Label>
          <Input
            id="telefono"
            value={formData.telefono}
            onChange={(e) => onChange('telefono', e.target.value)}
            placeholder="+54 9 11 1234-5678"
            data-testid="telefono-input"
          />
        </div>
      </div>

      <div className="border-t border-slate-200 pt-6">
        <h4 className="font-bold text-[#064E3B] mb-4">Datos del Vehículo</h4>
        <div className="grid md:grid-cols-2 gap-4">
          <div>
            <Label htmlFor="patente">Patente/Dominio *</Label>
            <Input
              id="patente"
              value={formData.patente}
              onChange={(e) => onChange('patente', e.target.value.toUpperCase())}
              placeholder="ABC123"
              data-testid="patente-input"
            />
          </div>
          <div>
            <Label htmlFor="marca">Marca *</Label>
            <Input
              id="marca"
              value={formData.marca}
              onChange={(e) => onChange('marca', e.target.value)}
              placeholder="Ford"
              data-testid="marca-input"
            />
          </div>
          <div>
            <Label htmlFor="modelo">Modelo *</Label>
            <Input
              id="modelo"
              value={formData.modelo}
              onChange={(e) => onChange('modelo', e.target.value)}
              placeholder="Focus"
              data-testid="modelo-input"
            />
          </div>
          <div>
            <Label htmlFor="ano">Año *</Label>
            <Input
              id="ano"
              type="number"
              value={formData.ano}
              onChange={(e) => onChange('ano', parseInt(e.target.value))}
              data-testid="ano-input"
            />
          </div>
        </div>
      </div>

      <div className="border-t border-slate-200 pt-6">
        <h4 className="font-bold text-[#064E3B] mb-4">Tipo y Cobertura</h4>
        <div className="grid md:grid-cols-2 gap-4">
          <div>
            <Label htmlFor="tipo_vehiculo">Tipo de Vehículo</Label>
            <Select value={formData.tipo_vehiculo} onValueChange={(v) => onChange('tipo_vehiculo', v)}>
              <SelectTrigger data-testid="tipo-vehiculo-select">
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="auto">Auto</SelectItem>
                <SelectItem value="moto">Moto</SelectItem>
                <SelectItem value="taxi">Taxi/Remis</SelectItem>
                <SelectItem value="app">App (Uber/Didi)</SelectItem>
              </SelectContent>
            </Select>
          </div>
          <div>
            <Label htmlFor="cobertura">Cobertura</Label>
            <Select value={formData.cobertura} onValueChange={(v) => onChange('cobertura', v)}>
              <SelectTrigger data-testid="cobertura-select">
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="rc">Responsabilidad Civil</SelectItem>
                <SelectItem value="completo">Terceros Completo</SelectItem>
              </SelectContent>
            </Select>
          </div>
        </div>
      </div>

      <div>
        <Label htmlFor="codigo">Código Promocional (opcional)</Label>
        <Input
          id="codigo"
          value={formData.codigo_promocional}
          onChange={(e) => onChange('codigo_promocional', e.target.value.toUpperCase())}
          placeholder="MASTER"
          data-testid="codigo-promo-input"
        />
      </div>

      <div className="flex gap-4">
        <Button
          onClick={onCotizar}
          disabled={loading}
          variant="outline"
          className="flex-1"
          data-testid="cotizar-btn"
        >
          {loading ? <Loader2 className="w-4 h-4 animate-spin mr-2" /> : null}
          Cotizar
        </Button>
        <Button
          onClick={onNext}
          className="flex-1 bg-[#064E3B] hover:bg-[#064E3B]/90"
          data-testid="siguiente-step1-btn"
        >
          Siguiente
        </Button>
      </div>

      {cotizacion && (
        <div className="bg-[#F0FDF4] border border-[#10B981] rounded-xl p-4">
          <h4 className="font-bold text-[#064E3B] mb-2">{cotizacion.cobertura_nombre}</h4>
          {cotizacion.es_gratis ? (
            <p className="text-2xl font-bold text-[#10B981]">GRATIS (Código promocional aplicado)</p>
          ) : (
            <div>
              {cotizacion.precio_base !== cotizacion.precio_final && (
                <p className="text-sm text-[#64748B] line-through">Precio base: ${cotizacion.precio_base.toLocaleString('es-AR')}</p>
              )}
              <p className="text-3xl font-bold text-[#064E3B]" style={{ fontFamily: 'Space Grotesk, monospace' }}>
                ${cotizacion.precio_final.toLocaleString('es-AR')}
              </p>
            </div>
          )}
        </div>
      )}
    </div>
  );
}

function Step2({ fotos, setFotos, onNext, onBack }) {
  const FotoDropzone = ({ tipo, label }) => {
    const { getRootProps, getInputProps, isDragActive } = useDropzone({
      accept: { 'image/*': ['.jpg', '.jpeg', '.png'] },
      maxFiles: 1,
      onDrop: (acceptedFiles) => {
        if (acceptedFiles.length > 0) {
          setFotos(prev => ({ ...prev, [tipo]: acceptedFiles[0] }));
          toast.success(`Foto ${label} cargada`);
        }
      }
    });

    return (
      <div
        {...getRootProps()}
        className={`border-2 border-dashed rounded-xl p-6 text-center cursor-pointer transition-all ${
          isDragActive ? 'border-[#10B981] bg-[#F0FDF4]' : 'border-slate-300 hover:border-[#10B981]'
        } ${fotos[tipo] ? 'bg-[#F0FDF4] border-[#10B981]' : ''}`}
        data-testid={`dropzone-${tipo}`}
      >
        <input {...getInputProps()} />
        {fotos[tipo] ? (
          <div className="space-y-2">
            <CheckCircle2 className="w-8 h-8 text-[#10B981] mx-auto" />
            <p className="text-sm font-semibold text-[#064E3B]">{label}</p>
            <p className="text-xs text-[#64748B]">{fotos[tipo].name}</p>
          </div>
        ) : (
          <div className="space-y-2">
            <Upload className="w-8 h-8 text-slate-400 mx-auto" />
            <p className="text-sm font-semibold text-[#064E3B]">{label}</p>
            <p className="text-xs text-[#64748B]">Arrastra o haz clic</p>
          </div>
        )}
      </div>
    );
  };

  const todasLasFotos = Object.values(fotos).every(f => f !== null);

  return (
    <div className="space-y-6">
      <h3 className="text-xl font-bold text-[#064E3B]">Fotos del Vehículo</h3>
      <p className="text-[#64748B]">Sube 4 fotos del vehículo (frente, lados y trasera)</p>
      
      <div className="grid grid-cols-2 gap-4">
        <FotoDropzone tipo="frente" label="Frente" />
        <FotoDropzone tipo="lado_izq" label="Lado Izquierdo" />
        <FotoDropzone tipo="lado_der" label="Lado Derecho" />
        <FotoDropzone tipo="trasera" label="Trasera" />
      </div>

      <div className="flex gap-4">
        <Button onClick={onBack} variant="outline" className="flex-1" data-testid="volver-step2-btn">
          Volver
        </Button>
        <Button
          onClick={onNext}
          disabled={!todasLasFotos}
          className="flex-1 bg-[#064E3B] hover:bg-[#064E3B]/90"
          data-testid="siguiente-step2-btn"
        >
          Siguiente
        </Button>
      </div>
    </div>
  );
}

function Step3({ formData, cotizacion, loading, onSubmit, onBack }) {
  return (
    <div className="space-y-6">
      <h3 className="text-xl font-bold text-[#064E3B]">Confirmación</h3>
      
      <div className="bg-slate-50 rounded-xl p-6 space-y-4">
        <div className="grid grid-cols-2 gap-4 text-sm">
          <div>
            <p className="text-[#64748B]">Nombre</p>
            <p className="font-semibold text-[#064E3B]">{formData.nombre}</p>
          </div>
          <div>
            <p className="text-[#64748B]">DNI</p>
            <p className="font-semibold text-[#064E3B]">{formData.dni}</p>
          </div>
          <div>
            <p className="text-[#64748B]">Patente</p>
            <p className="font-semibold text-[#064E3B]">{formData.patente}</p>
          </div>
          <div>
            <p className="text-[#64748B]">Vehículo</p>
            <p className="font-semibold text-[#064E3B]">{formData.marca} {formData.modelo} {formData.ano}</p>
          </div>
        </div>
      </div>

      {cotizacion && (
        <div className="bg-[#F0FDF4] border border-[#10B981] rounded-xl p-6">
          <h4 className="font-bold text-[#064E3B] mb-2">Total a Pagar</h4>
          {cotizacion.es_gratis ? (
            <p className="text-3xl font-bold text-[#10B981]">GRATIS</p>
          ) : (
            <p className="text-4xl font-bold text-[#064E3B]" style={{ fontFamily: 'Space Grotesk, monospace' }}>
              ${cotizacion.precio_final.toLocaleString('es-AR')}
            </p>
          )}
          <p className="text-sm text-[#64748B] mt-2">Vigencia: 30 días</p>
        </div>
      )}

      <div className="flex gap-4">
        <Button onClick={onBack} variant="outline" className="flex-1" data-testid="volver-step3-btn">
          Volver
        </Button>
        <Button
          onClick={onSubmit}
          disabled={loading}
          className="flex-1 bg-[#D9F99D] text-[#064E3B] hover:bg-[#BEF264] font-bold"
          data-testid="confirmar-pago-btn"
        >
          {loading ? (
            <><Loader2 className="w-4 h-4 animate-spin mr-2" /> Procesando...</>
          ) : (
            cotizacion?.es_gratis ? 'Generar Seguro' : 'Proceder al Pago'
          )}
        </Button>
      </div>
    </div>
  );
}

function StepDescarga({ seguro }) {
  if (!seguro) return null;

  return (
    <div className="space-y-6 text-center">
      <div className="w-20 h-20 bg-[#10B981] rounded-full flex items-center justify-center mx-auto">
        <CheckCircle2 className="w-12 h-12 text-white" />
      </div>
      <h3 className="text-2xl font-bold text-[#064E3B]">¡Seguro Generado!</h3>
      <p className="text-[#64748B]">Descarga tu comprobante</p>
      
      <div className="bg-slate-50 rounded-xl p-6">
        <p className="text-sm text-[#64748B] mb-1">Número de Recibo</p>
        <p className="text-3xl font-bold text-[#064E3B]" style={{ fontFamily: 'Space Grotesk, monospace' }}>
          {seguro.numero_recibo}
        </p>
      </div>

      <div className="flex flex-col gap-3">
        <Button
          onClick={() => window.open(segurosAPI.descargarPDF(seguro.id), '_blank')}
          className="w-full bg-[#064E3B] hover:bg-[#064E3B]/90"
          data-testid="descargar-pdf-btn"
        >
          Descargar PDF
        </Button>
        <Button
          onClick={() => window.open(segurosAPI.descargarImagen(seguro.id), '_blank')}
          variant="outline"
          className="w-full"
          data-testid="descargar-imagen-btn"
        >
          Descargar Imagen
        </Button>
      </div>
    </div>
  );
}
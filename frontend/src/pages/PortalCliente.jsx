import { useState } from 'react';
import { Search, Download, RefreshCw, Shield, Calendar, CreditCard } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { segurosAPI } from '@/services/api';
import { toast } from 'sonner';

export default function PortalCliente() {
  const [dni, setDni] = useState('');
  const [seguros, setSeguros] = useState([]);
  const [loading, setLoading] = useState(false);
  const [buscado, setBuscado] = useState(false);

  const buscarSeguros = async () => {
    if (!dni) {
      toast.error('Por favor ingresa tu DNI');
      return;
    }

    setLoading(true);
    try {
      const data = await segurosAPI.obtenerPorDNI(dni);
      setSeguros(data.seguros || []);
      setBuscado(true);
      if (data.seguros.length === 0) {
        toast.info('No se encontraron seguros para este DNI');
      }
    } catch (error) {
      toast.error('Error al buscar seguros');
    } finally {
      setLoading(false);
    }
  };

  const renovarSeguro = async (seguroId) => {
    try {
      const nuevoSeguro = await segurosAPI.renovar(seguroId);
      toast.success('Seguro renovado exitosamente');
      // Redirigir a pago si es necesario
      if (nuevoSeguro.estado === 'pendiente_pago') {
        const preferencia = await pagosAPI.crearPreferencia(nuevoSeguro.id);
        window.location.href = preferencia.init_point;
      }
    } catch (error) {
      toast.error('Error al renovar seguro');
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-[#F8FAFC] to-white">
      {/* Header */}
      <header className="bg-white/80 backdrop-blur-xl border-b border-white/20 shadow-sm sticky top-0 z-50">
        <div className="container mx-auto px-6 py-4 flex justify-between items-center">
          <div className="flex items-center gap-3">
            <div className="w-12 h-12 bg-[#064E3B] rounded-xl flex items-center justify-center">
              <Shield className="w-6 h-6 text-[#D9F99D]" />
            </div>
            <div>
              <h1 className="text-2xl font-bold text-[#064E3B]" style={{ fontFamily: 'Manrope, sans-serif' }}>
                Portal Cliente
              </h1>
            </div>
          </div>
          <Button 
            variant="ghost" 
            onClick={() => window.location.href = '/'}
            className="text-[#064E3B]"
          >
            Volver al Inicio
          </Button>
        </div>
      </header>

      {/* Content */}
      <div className="container mx-auto px-6 py-12">
        {/* Search Section */}
        <Card className="max-w-xl mx-auto mb-12">
          <CardHeader>
            <CardTitle className="text-2xl font-bold text-[#064E3B]" style={{ fontFamily: 'Manrope, sans-serif' }}>
              Consultar Mis Seguros
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div>
              <Label htmlFor="dni-search">Ingresa tu DNI</Label>
              <div className="flex gap-2">
                <Input
                  id="dni-search"
                  value={dni}
                  onChange={(e) => setDni(e.target.value)}
                  placeholder="12345678"
                  onKeyPress={(e) => e.key === 'Enter' && buscarSeguros()}
                  data-testid="dni-search-input"
                  className="flex-1"
                />
                <Button
                  onClick={buscarSeguros}
                  disabled={loading}
                  className="bg-[#064E3B] hover:bg-[#064E3B]/90"
                  data-testid="buscar-seguros-btn"
                >
                  <Search className="w-4 h-4 mr-2" />
                  Buscar
                </Button>
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Results */}
        {buscado && seguros.length === 0 && (
          <div className="text-center py-12">
            <Shield className="w-16 h-16 text-slate-300 mx-auto mb-4" />
            <p className="text-[#64748B]">No se encontraron seguros para este DNI</p>
          </div>
        )}

        {seguros.length > 0 && (
          <div className="space-y-6">
            <h2 className="text-2xl font-bold text-[#064E3B]" style={{ fontFamily: 'Manrope, sans-serif' }}>
              Tus Seguros
            </h2>
            
            <div className="grid md:grid-cols-2 gap-6">
              {seguros.map((seguro) => (
                <SeguroCard key={seguro.numero_recibo} seguro={seguro} onRenovar={renovarSeguro} />
              ))}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

function SeguroCard({ seguro, onRenovar }) {
  const vigente = new Date(seguro.vigencia_hasta) > new Date();
  const pagado = seguro.estado === 'pagado' || seguro.estado === 'gratis';

  return (
    <Card className={`${
      vigente && pagado ? 'border-[#10B981]' : 'border-slate-200'
    }`} data-testid="seguro-card">
      <CardHeader>
        <div className="flex justify-between items-start">
          <div>
            <CardTitle className="text-lg font-bold text-[#064E3B]">
              {seguro.patente}
            </CardTitle>
            <p className="text-sm text-[#64748B]">
              {seguro.marca} {seguro.modelo} {seguro.ano}
            </p>
          </div>
          <span className={`px-3 py-1 rounded-full text-xs font-semibold ${
            vigente && pagado
              ? 'bg-[#10B981] text-white'
              : 'bg-slate-200 text-slate-600'
          }`}>
            {vigente && pagado ? 'VIGENTE' : seguro.estado === 'pendiente_pago' ? 'PENDIENTE' : 'VENCIDO'}
          </span>
        </div>
      </CardHeader>
      <CardContent className="space-y-4">
        <div className="grid grid-cols-2 gap-4 text-sm">
          <div>
            <p className="text-[#64748B]">N° Recibo</p>
            <p className="font-mono font-semibold text-[#064E3B]">{seguro.numero_recibo}</p>
          </div>
          <div>
            <p className="text-[#64748B]">Cobertura</p>
            <p className="font-semibold text-[#064E3B]">
              {seguro.cobertura === 'rc' ? 'R.C.' : 'Completo'}
            </p>
          </div>
          <div>
            <p className="text-[#64748B]">Vigencia hasta</p>
            <p className="font-semibold text-[#064E3B]">
              <Calendar className="w-3 h-3 inline mr-1" />
              {new Date(seguro.vigencia_hasta).toLocaleDateString('es-AR')}
            </p>
          </div>
          <div>
            <p className="text-[#64748B]">Precio</p>
            <p className="font-bold text-[#064E3B]" style={{ fontFamily: 'Space Grotesk, monospace' }}>
              ${seguro.precio_final.toLocaleString('es-AR')}
            </p>
          </div>
        </div>

        {pagado && (
          <div className="flex gap-2">
            <Button
              onClick={() => window.open(segurosAPI.descargarPDF(seguro._id || seguro.id), '_blank')}
              variant="outline"
              size="sm"
              className="flex-1"
              data-testid="descargar-pdf-card-btn"
            >
              <Download className="w-3 h-3 mr-1" />
              PDF
            </Button>
            <Button
              onClick={() => window.open(segurosAPI.descargarImagen(seguro._id || seguro.id), '_blank')}
              variant="outline"
              size="sm"
              className="flex-1"
            >
              <Download className="w-3 h-3 mr-1" />
              Imagen
            </Button>
          </div>
        )}

        {!vigente && pagado && (
          <Button
            onClick={() => onRenovar(seguro._id || seguro.id)}
            className="w-full bg-[#10B981] hover:bg-[#10B981]/90"
            data-testid="renovar-seguro-btn"
          >
            <RefreshCw className="w-4 h-4 mr-2" />
            Renovar Seguro
          </Button>
        )}

        {seguro.estado === 'pendiente_pago' && (
          <Button
            onClick={() => {
              // Redirigir a pago
              toast.info('Redirigiendo a pago...');
            }}
            className="w-full bg-[#064E3B] hover:bg-[#064E3B]/90"
          >
            <CreditCard className="w-4 h-4 mr-2" />
            Completar Pago
          </Button>
        )}
      </CardContent>
    </Card>
  );
}
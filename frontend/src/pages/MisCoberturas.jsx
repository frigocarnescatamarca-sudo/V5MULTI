import { useState } from 'react';
import { Shield, Search, Car, Calendar, CheckCircle, XCircle, Clock, AlertTriangle, ExternalLink, ArrowLeft } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';

const API_URL = process.env.REACT_APP_BACKEND_URL;

export default function MisCoberturas() {
  const [dni, setDni] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [resultado, setResultado] = useState(null);

  const handleBuscar = async (e) => {
    e.preventDefault();
    setError('');
    setResultado(null);

    // Validate DNI
    const dniClean = dni.replace(/\D/g, '');
    if (dniClean.length < 7 || dniClean.length > 8) {
      setError('Por favor, ingresa un DNI válido (7-8 dígitos)');
      return;
    }

    setLoading(true);
    try {
      const response = await fetch(`${API_URL}/api/coberturas/dni/${dniClean}`);
      if (!response.ok) {
        const data = await response.json();
        throw new Error(data.detail || 'Error al consultar coberturas');
      }
      const data = await response.json();
      setResultado(data);
    } catch (err) {
      setError(err.message || 'Error al consultar. Intentá de nuevo.');
    } finally {
      setLoading(false);
    }
  };

  const getStatusBadge = (cobertura) => {
    if (cobertura.vencida) {
      return (
        <span className="inline-flex items-center gap-1 px-3 py-1 rounded-full text-sm font-medium bg-gray-100 text-gray-700">
          <XCircle className="w-4 h-4" />
          Vencida
        </span>
      );
    }
    if (cobertura.vigente) {
      return (
        <span className="inline-flex items-center gap-1 px-3 py-1 rounded-full text-sm font-medium bg-green-100 text-green-700">
          <CheckCircle className="w-4 h-4" />
          Vigente
        </span>
      );
    }
    if (cobertura.estado === 'pendiente_pago') {
      return (
        <span className="inline-flex items-center gap-1 px-3 py-1 rounded-full text-sm font-medium bg-yellow-100 text-yellow-700">
          <Clock className="w-4 h-4" />
          Pendiente de Pago
        </span>
      );
    }
    return (
      <span className="inline-flex items-center gap-1 px-3 py-1 rounded-full text-sm font-medium bg-gray-100 text-gray-700">
        <AlertTriangle className="w-4 h-4" />
        {cobertura.estado || 'Desconocido'}
      </span>
    );
  };

  const getCoberturaName = (tipo) => {
    const tipos = {
      'rc': 'Responsabilidad Civil',
      'completo': 'Terceros Completo',
      'terceros': 'Terceros Completo'
    };
    return tipos[tipo] || tipo;
  };

  return (
    <div className="min-h-screen bg-gradient-to-b from-[#F8FAFC] to-white">
      {/* Header */}
      <header className="bg-white/80 backdrop-blur-xl border-b border-white/20 shadow-sm sticky top-0 z-50">
        <div className="container mx-auto px-6 py-4 flex justify-between items-center">
          <div className="flex items-center gap-3">
            <a href="/" className="flex items-center gap-3">
              <div className="w-12 h-12 bg-[#064E3B] rounded-xl flex items-center justify-center">
                <Shield className="w-6 h-6 text-[#D9F99D]" />
              </div>
              <div>
                <h1 className="text-2xl font-bold text-[#064E3B]" style={{ fontFamily: 'Manrope, sans-serif' }}>
                  ESTONIA COBERTURA
                </h1>
              </div>
            </a>
          </div>
          <Button 
            variant="ghost" 
            onClick={() => window.location.href = '/'}
            className="text-[#064E3B]"
          >
            <ArrowLeft className="w-4 h-4 mr-2" />
            Volver al Inicio
          </Button>
        </div>
      </header>

      {/* Main Content */}
      <main className="container mx-auto px-6 py-12">
        <div className="max-w-3xl mx-auto">
          {/* Title */}
          <div className="text-center mb-10">
            <h1 className="text-3xl md:text-4xl font-bold text-[#064E3B] mb-4" style={{ fontFamily: 'Manrope, sans-serif' }}>
              Consultá tus Coberturas
            </h1>
            <p className="text-lg text-[#64748B]">
              Ingresá tu DNI para ver el estado de tus coberturas vigentes
            </p>
          </div>

          {/* Search Form */}
          <Card className="mb-8">
            <CardContent className="p-6">
              <form onSubmit={handleBuscar} className="flex flex-col sm:flex-row gap-4">
                <div className="flex-1">
                  <Input
                    type="text"
                    placeholder="Ingresá tu DNI (sin puntos)"
                    value={dni}
                    onChange={(e) => setDni(e.target.value.replace(/[^\d.]/g, ''))}
                    className="text-lg h-12"
                    maxLength={10}
                  />
                </div>
                <Button 
                  type="submit" 
                  disabled={loading}
                  className="bg-[#064E3B] hover:bg-[#064E3B]/90 h-12 px-8"
                >
                  {loading ? (
                    <span className="flex items-center gap-2">
                      <div className="w-5 h-5 border-2 border-white border-t-transparent rounded-full animate-spin" />
                      Buscando...
                    </span>
                  ) : (
                    <span className="flex items-center gap-2">
                      <Search className="w-5 h-5" />
                      Consultar
                    </span>
                  )}
                </Button>
              </form>

              {error && (
                <div className="mt-4 p-4 bg-red-50 border border-red-200 rounded-lg text-red-700">
                  {error}
                </div>
              )}
            </CardContent>
          </Card>

          {/* Results */}
          {resultado && (
            <div className="space-y-6">
              {/* Summary */}
              <div className="text-center p-6 bg-[#064E3B] text-white rounded-2xl">
                <p className="text-lg mb-2">Coberturas encontradas para DNI</p>
                <p className="text-3xl font-bold font-mono">{resultado.dni}</p>
                <p className="text-[#D9F99D] mt-2">
                  {resultado.total} cobertura(s) registrada(s)
                </p>
              </div>

              {/* No results */}
              {resultado.total === 0 && (
                <Card>
                  <CardContent className="p-8 text-center">
                    <div className="w-20 h-20 bg-gray-100 rounded-full flex items-center justify-center mx-auto mb-4">
                      <Search className="w-10 h-10 text-gray-400" />
                    </div>
                    <h3 className="text-xl font-semibold text-gray-700 mb-2">
                      No se encontraron coberturas
                    </h3>
                    <p className="text-gray-500 mb-4">
                      No hay coberturas registradas para este DNI
                    </p>
                    <Button 
                      onClick={() => window.location.href = '/'}
                      className="bg-[#064E3B] hover:bg-[#064E3B]/90"
                    >
                      Contratar una Cobertura
                    </Button>
                  </CardContent>
                </Card>
              )}

              {/* Coverage Cards */}
              {resultado.coberturas?.map((cob, index) => (
                <Card key={index} className={`overflow-hidden ${cob.vigente ? 'border-2 border-green-500' : ''}`}>
                  <CardHeader className="bg-gray-50 border-b">
                    <div className="flex items-center justify-between">
                      <CardTitle className="flex items-center gap-3">
                        <Car className="w-6 h-6 text-[#064E3B]" />
                        <span className="font-mono text-xl">{cob.patente}</span>
                      </CardTitle>
                      {getStatusBadge(cob)}
                    </div>
                  </CardHeader>
                  <CardContent className="p-6">
                    <div className="grid md:grid-cols-2 gap-6">
                      {/* Vehicle Info */}
                      <div className="space-y-3">
                        <h4 className="font-semibold text-[#064E3B] border-b pb-2">Vehículo</h4>
                        <div className="space-y-2 text-sm">
                          <div className="flex justify-between">
                            <span className="text-gray-500">Marca/Modelo:</span>
                            <span className="font-medium">{cob.marca} {cob.modelo}</span>
                          </div>
                          <div className="flex justify-between">
                            <span className="text-gray-500">Año:</span>
                            <span className="font-medium">{cob.ano}</span>
                          </div>
                          <div className="flex justify-between">
                            <span className="text-gray-500">Tipo:</span>
                            <span className="font-medium capitalize">{cob.tipo_vehiculo}</span>
                          </div>
                        </div>
                      </div>

                      {/* Coverage Info */}
                      <div className="space-y-3">
                        <h4 className="font-semibold text-[#064E3B] border-b pb-2">Cobertura</h4>
                        <div className="space-y-2 text-sm">
                          <div className="flex justify-between">
                            <span className="text-gray-500">Tipo:</span>
                            <span className="font-medium">{getCoberturaName(cob.cobertura)}</span>
                          </div>
                          <div className="flex justify-between">
                            <span className="text-gray-500">Recibo:</span>
                            <span className="font-medium font-mono">{cob.numero_recibo}</span>
                          </div>
                          <div className="flex justify-between">
                            <span className="text-gray-500">Precio:</span>
                            <span className="font-medium">${cob.precio_final?.toLocaleString('es-AR')}</span>
                          </div>
                        </div>
                      </div>
                    </div>

                    {/* Validity */}
                    <div className="mt-6 p-4 bg-gray-50 rounded-lg">
                      <div className="flex items-center gap-2 mb-2">
                        <Calendar className="w-5 h-5 text-[#064E3B]" />
                        <span className="font-semibold text-[#064E3B]">Vigencia</span>
                      </div>
                      <div className="flex justify-between text-sm">
                        <span>
                          <span className="text-gray-500">Desde: </span>
                          <span className="font-medium">{cob.vigencia_desde?.split('T')[0]}</span>
                        </span>
                        <span>
                          <span className="text-gray-500">Hasta: </span>
                          <span className={`font-medium ${cob.vencida ? 'text-red-500' : ''}`}>
                            {cob.vigencia_hasta?.split('T')[0]}
                          </span>
                        </span>
                      </div>
                    </div>

                    {/* Actions for paid coverages */}
                    {(cob.estado === 'pagado' || cob.estado === 'gratis') && (
                      <div className="mt-6 flex flex-wrap gap-3">
                        <Button
                          variant="outline"
                          onClick={() => window.open(`${API_URL}/api/seguros/${cob.numero_recibo}/comprobante/pdf`, '_blank')}
                          className="flex-1"
                        >
                          Descargar PDF
                        </Button>
                        <Button
                          variant="outline"
                          onClick={() => window.open(`${API_URL}/api/seguros/${cob.numero_recibo}/comprobante/imagen`, '_blank')}
                          className="flex-1"
                        >
                          Descargar Imagen
                        </Button>
                        <Button
                          onClick={() => window.open(`/verificar/${cob.numero_recibo}`, '_blank')}
                          className="flex-1 bg-[#064E3B] hover:bg-[#064E3B]/90"
                        >
                          <ExternalLink className="w-4 h-4 mr-2" />
                          Verificar Online
                        </Button>
                      </div>
                    )}
                  </CardContent>
                </Card>
              ))}
            </div>
          )}
        </div>
      </main>

      {/* Footer */}
      <footer className="bg-[#0F172A] text-white py-8 mt-12">
        <div className="container mx-auto px-6 text-center">
          <p className="text-white/50">
            © 2025 Estonia Cobertura Colaborativa. Todos los derechos reservados.
          </p>
        </div>
      </footer>
    </div>
  );
}

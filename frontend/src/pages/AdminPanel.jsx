import { useState, useEffect } from 'react';
import { Shield, Check, Plus, Trash2, Tag } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger } from '@/components/ui/dialog';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { adminAPI } from '@/services/api';
import { toast } from 'sonner';

export default function AdminPanel() {
  const [seguros, setSeguros] = useState([]);
  const [promoCodes, setPromoCodes] = useState([]);
  const [loading, setLoading] = useState(false);
  const [nuevoPromo, setNuevoPromo] = useState({ codigo: '', descuento_porcentaje: 0, es_master: false });

  useEffect(() => {
    cargarDatos();
  }, []);

  const cargarDatos = async () => {
    setLoading(true);
    try {
      const [segurosData, codigosData] = await Promise.all([
        adminAPI.listarSeguros(0, 100),
        adminAPI.listarPromoCodes()
      ]);
      setSeguros(segurosData.seguros || []);
      setPromoCodes(codigosData.codigos || []);
    } catch (error) {
      toast.error('Error al cargar datos');
    } finally {
      setLoading(false);
    }
  };

  const marcarProcesado = async (seguroId) => {
    try {
      await adminAPI.marcarProcesado(seguroId);
      toast.success('Seguro marcado como procesado');
      cargarDatos();
    } catch (error) {
      toast.error('Error al marcar seguro');
    }
  };

  const crearCodigoPromo = async () => {
    if (!nuevoPromo.codigo) {
      toast.error('El código es requerido');
      return;
    }

    try {
      await adminAPI.crearPromoCode(nuevoPromo);
      toast.success('Código creado exitosamente');
      setNuevoPromo({ codigo: '', descuento_porcentaje: 0, es_master: false });
      cargarDatos();
    } catch (error) {
      toast.error('Error al crear código: ' + (error.response?.data?.detail || ''));
    }
  };

  const eliminarCodigo = async (codigo) => {
    if (!window.confirm(`¿Desactivar el código ${codigo}?`)) return;
    
    try {
      await adminAPI.eliminarPromoCode(codigo);
      toast.success('Código desactivado');
      cargarDatos();
    } catch (error) {
      toast.error('Error al eliminar código');
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
                Panel Admin
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
        <Tabs defaultValue="seguros" className="space-y-6">
          <TabsList className="grid w-full max-w-md grid-cols-2">
            <TabsTrigger value="seguros">Seguros</TabsTrigger>
            <TabsTrigger value="promos">Códigos Promo</TabsTrigger>
          </TabsList>

          {/* Tab Seguros */}
          <TabsContent value="seguros" className="space-y-6" data-testid="tab-seguros">
            <div className="flex justify-between items-center">
              <h2 className="text-2xl font-bold text-[#064E3B]" style={{ fontFamily: 'Manrope, sans-serif' }}>
                Listado de Seguros
              </h2>
              <Button onClick={cargarDatos} disabled={loading} variant="outline">
                Recargar
              </Button>
            </div>

            <div className="grid gap-4">
              {seguros.map((seguro) => (
                <Card key={seguro.numero_recibo} data-testid="seguro-admin-card">
                  <CardContent className="p-6">
                    <div className="grid md:grid-cols-5 gap-4 items-center">
                      <div>
                        <p className="text-sm text-[#64748B]">Recibo</p>
                        <p className="font-mono font-bold text-[#064E3B]">{seguro.numero_recibo}</p>
                      </div>
                      <div>
                        <p className="text-sm text-[#64748B]">Cliente</p>
                        <p className="font-semibold text-[#064E3B]">{seguro.nombre}</p>
                        <p className="text-xs text-[#64748B]">DNI: {seguro.dni}</p>
                      </div>
                      <div>
                        <p className="text-sm text-[#64748B]">Vehículo</p>
                        <p className="font-semibold text-[#064E3B]">{seguro.patente}</p>
                        <p className="text-xs text-[#64748B]">{seguro.marca} {seguro.modelo}</p>
                      </div>
                      <div>
                        <p className="text-sm text-[#64748B]">Estado</p>
                        <span className={`inline-block px-2 py-1 rounded-full text-xs font-semibold ${
                          seguro.estado === 'pagado' || seguro.estado === 'gratis'
                            ? 'bg-[#10B981] text-white'
                            : 'bg-yellow-500 text-white'
                        }`}>
                          {seguro.estado}
                        </span>
                        {seguro.procesado && (
                          <span className="ml-2 inline-block px-2 py-1 rounded-full text-xs font-semibold bg-blue-500 text-white">
                            Procesado
                          </span>
                        )}
                      </div>
                      <div className="flex justify-end">
                        {!seguro.procesado && (seguro.estado === 'pagado' || seguro.estado === 'gratis') && (
                          <Button
                            onClick={() => marcarProcesado(seguro._id || seguro.numero_recibo)}
                            size="sm"
                            className="bg-[#064E3B] hover:bg-[#064E3B]/90"
                            data-testid="marcar-procesado-btn"
                          >
                            <Check className="w-4 h-4 mr-1" />
                            Marcar Procesado
                          </Button>
                        )}
                      </div>
                    </div>
                  </CardContent>
                </Card>
              ))}
            </div>

            {seguros.length === 0 && (
              <div className="text-center py-12">
                <Shield className="w-16 h-16 text-slate-300 mx-auto mb-4" />
                <p className="text-[#64748B]">No hay seguros registrados</p>
              </div>
            )}
          </TabsContent>

          {/* Tab Códigos Promo */}
          <TabsContent value="promos" className="space-y-6" data-testid="tab-promos">
            <div className="flex justify-between items-center">
              <h2 className="text-2xl font-bold text-[#064E3B]" style={{ fontFamily: 'Manrope, sans-serif' }}>
                Códigos Promocionales
              </h2>
              <Dialog>
                <DialogTrigger asChild>
                  <Button className="bg-[#064E3B] hover:bg-[#064E3B]/90" data-testid="crear-promo-btn">
                    <Plus className="w-4 h-4 mr-2" />
                    Nuevo Código
                  </Button>
                </DialogTrigger>
                <DialogContent>
                  <DialogHeader>
                    <DialogTitle>Crear Código Promocional</DialogTitle>
                  </DialogHeader>
                  <div className="space-y-4">
                    <div>
                      <Label htmlFor="codigo">Código</Label>
                      <Input
                        id="codigo"
                        value={nuevoPromo.codigo}
                        onChange={(e) => setNuevoPromo({ ...nuevoPromo, codigo: e.target.value.toUpperCase() })}
                        placeholder="VERANO2025"
                        data-testid="nuevo-codigo-input"
                      />
                    </div>
                    <div>
                      <Label htmlFor="descuento">Descuento (%)</Label>
                      <Input
                        id="descuento"
                        type="number"
                        min="0"
                        max="100"
                        value={nuevoPromo.descuento_porcentaje}
                        onChange={(e) => setNuevoPromo({ ...nuevoPromo, descuento_porcentaje: parseInt(e.target.value) })}
                        data-testid="descuento-input"
                      />
                    </div>
                    <div className="flex items-center gap-2">
                      <input
                        type="checkbox"
                        id="es-master"
                        checked={nuevoPromo.es_master}
                        onChange={(e) => setNuevoPromo({ ...nuevoPromo, es_master: e.target.checked })}
                        className="w-4 h-4"
                      />
                      <Label htmlFor="es-master">Es código MASTER (100% gratis)</Label>
                    </div>
                    <Button
                      onClick={crearCodigoPromo}
                      className="w-full bg-[#064E3B] hover:bg-[#064E3B]/90"
                      data-testid="guardar-promo-btn"
                    >
                      Crear Código
                    </Button>
                  </div>
                </DialogContent>
              </Dialog>
            </div>

            <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-4">
              {promoCodes.map((promo) => (
                <Card key={promo.codigo} className={promo.activo ? '' : 'opacity-50'} data-testid="promo-card">
                  <CardHeader>
                    <div className="flex justify-between items-start">
                      <div>
                        <CardTitle className="flex items-center gap-2 text-lg font-bold text-[#064E3B]">
                          <Tag className="w-4 h-4" />
                          {promo.codigo}
                        </CardTitle>
                        {/* Texto MASTER oculto para usuarios */}
                      </div>
                      {promo.activo && !(promo.codigo === 'MASTER') && (
                        <Button
                          onClick={() => eliminarCodigo(promo.codigo)}
                          size="sm"
                          variant="ghost"
                          className="text-red-500 hover:text-red-700"
                          data-testid="eliminar-promo-btn"
                        >
                          <Trash2 className="w-4 h-4" />
                        </Button>
                      )}
                    </div>
                  </CardHeader>
                  <CardContent>
                    <p className="text-3xl font-bold text-[#064E3B]" style={{ fontFamily: 'Space Grotesk, monospace' }}>
                      {promo.es_master ? '100%' : `${promo.descuento_porcentaje}%`}
                    </p>
                    <p className="text-sm text-[#64748B]">Descuento</p>
                    <p className={`text-xs mt-2 font-semibold ${
                      promo.activo ? 'text-[#10B981]' : 'text-red-500'
                    }`}>
                      {promo.activo ? 'ACTIVO' : 'INACTIVO'}
                    </p>
                  </CardContent>
                </Card>
              ))}
            </div>

            {promoCodes.length === 0 && (
              <div className="text-center py-12">
                <Tag className="w-16 h-16 text-slate-300 mx-auto mb-4" />
                <p className="text-[#64748B]">No hay códigos promocionales</p>
              </div>
            )}
          </TabsContent>
        </Tabs>
      </div>
    </div>
  );
}
import { useState, useEffect } from 'react';
import { Shield, LogOut, TrendingUp, Award, DollarSign, Calendar, AlertCircle, Plus, FileText, Car } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Dialog, DialogContent, DialogHeader, DialogTitle } from '@/components/ui/dialog';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { agenteAPI, segurosAPI } from '@/services/api';
import { toast } from 'sonner';

export default function PanelAgente() {
  const [authenticated, setAuthenticated] = useState(false);
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [token, setToken] = useState(null);
  const [agente, setAgente] = useState(null);
  const [seguros, setSeguros] = useState([]);
  const [estadisticas, setEstadisticas] = useState(null);
  const [vencimientos, setVencimientos] = useState(null);
  const [loading, setLoading] = useState(false);
  
  // Estados para crear seguro
  const [modalCrearOpen, setModalCrearOpen] = useState(false);
  const [formSeguro, setFormSeguro] = useState({
    dni: '',
    nombre: '',
    email: '',
    telefono: '',
    patente: '',
    marca: '',
    modelo: '',
    ano: new Date().getFullYear(),
    tipo_vehiculo: 'auto',
    cobertura: 'rc'
  });

  useEffect(() => {
    const savedToken = localStorage.getItem('agente_token');
    const savedAgente = localStorage.getItem('agente_data');
    
    if (savedToken && savedAgente) {
      verifyToken(savedToken, JSON.parse(savedAgente));
    }
  }, []);

  useEffect(() => {
    if (authenticated && token) {
      cargarDatos();
    }
  }, [authenticated, token]);

  const verifyToken = async (savedToken, savedAgente) => {
    try {
      const result = await agenteAPI.verifyToken(savedToken);
      if (result.valid) {
        setToken(savedToken);
        setAgente(savedAgente);
        setAuthenticated(true);
      } else {
        localStorage.removeItem('agente_token');
        localStorage.removeItem('agente_data');
      }
    } catch (error) {
      localStorage.removeItem('agente_token');
      localStorage.removeItem('agente_data');
    }
  };

  const handleLogin = async (e) => {
    e.preventDefault();
    setLoading(true);
    
    try {
      const result = await agenteAPI.login(username, password);
      setToken(result.token);
      setAgente(result.agente);
      setAuthenticated(true);
      
      localStorage.setItem('agente_token', result.token);
      localStorage.setItem('agente_data', JSON.stringify(result.agente));
      
      toast.success('Sesión iniciada correctamente');
    } catch (error) {
      toast.error('Credenciales incorrectas');
    } finally {
      setLoading(false);
    }
  };

  const handleLogout = async () => {
    try {
      await agenteAPI.logout(token);
      localStorage.removeItem('agente_token');
      localStorage.removeItem('agente_data');
      setAuthenticated(false);
      setToken(null);
      setAgente(null);
      toast.success('Sesión cerrada');
    } catch (error) {
      toast.error('Error al cerrar sesión');
    }
  };

  const cargarDatos = async () => {
    setLoading(true);
    try {
      const [segurosData, vencimientosData] = await Promise.all([
        agenteAPI.misSeguros(token),
        agenteAPI.misVencimientos(token)
      ]);
      
      setSeguros(segurosData.seguros || []);
      setEstadisticas(segurosData.estadisticas);
      setVencimientos(vencimientosData);
    } catch (error) {
      toast.error('Error al cargar datos');
    } finally {
      setLoading(false);
    }
  };

  const abrirModalCrear = () => {
    setFormSeguro({
      dni: '',
      nombre: '',
      email: '',
      telefono: '',
      patente: '',
      marca: '',
      modelo: '',
      ano: new Date().getFullYear(),
      tipo_vehiculo: 'auto',
      cobertura: 'rc'
    });
    setModalCrearOpen(true);
  };

  const crearSeguro = async () => {
    // Validar campos
    if (!formSeguro.dni || !formSeguro.nombre || !formSeguro.email || !formSeguro.patente) {
      toast.error('Complete todos los campos obligatorios');
      return;
    }

    setLoading(true);
    try {
      await agenteAPI.crearSeguro(token, formSeguro);
      toast.success('Cobertura creada correctamente');
      setModalCrearOpen(false);
      cargarDatos();
    } catch (error) {
      toast.error('Error al crear cobertura: ' + (error.response?.data?.detail || error.message));
    } finally {
      setLoading(false);
    }
  };

  // Pantalla de Login
  if (!authenticated) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-[#F8FAFC] to-white flex items-center justify-center p-6">
        <Card className="max-w-md w-full">
          <CardHeader className="text-center">
            <div className="w-16 h-16 bg-[#10B981] rounded-xl flex items-center justify-center mx-auto mb-4">
              <Shield className="w-8 h-8 text-white" />
            </div>
            <CardTitle className="text-2xl font-bold text-[#064E3B]" style={{ fontFamily: 'Manrope, sans-serif' }}>
              Panel de Agentes
            </CardTitle>
            <p className="text-[#64748B]">Estonia Seguros</p>
          </CardHeader>
          <CardContent>
            <form onSubmit={handleLogin} className="space-y-4">
              <div>
                <Label htmlFor="username">Usuario</Label>
                <Input
                  id="username"
                  value={username}
                  onChange={(e) => setUsername(e.target.value)}
                  placeholder="tu_usuario"
                  required
                  data-testid="agente-username-input"
                />
              </div>
              <div>
                <Label htmlFor="password">Contraseña</Label>
                <Input
                  id="password"
                  type="password"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  placeholder="••••••••"
                  required
                  data-testid="agente-password-input"
                />
              </div>
              <Button
                type="submit"
                disabled={loading}
                className="w-full bg-[#10B981] hover:bg-[#10B981]/90"
                data-testid="agente-login-btn"
              >
                {loading ? 'Iniciando sesión...' : 'Iniciar Sesión'}
              </Button>
            </form>
          </CardContent>
        </Card>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-[#F8FAFC] to-white">
      {/* Header */}
      <header className="bg-white/80 backdrop-blur-xl border-b border-white/20 shadow-sm sticky top-0 z-50">
        <div className="container mx-auto px-6 py-4 flex justify-between items-center">
          <div className="flex items-center gap-3">
            <div className="w-12 h-12 bg-[#10B981] rounded-xl flex items-center justify-center">
              <Shield className="w-6 h-6 text-white" />
            </div>
            <div>
              <h1 className="text-2xl font-bold text-[#064E3B]" style={{ fontFamily: 'Manrope, sans-serif' }}>
                Panel de Agente
              </h1>
            </div>
          </div>
          <div className="flex gap-4 items-center">
            <span className="text-sm text-[#64748B]">Hola, {agente?.nombre}</span>
            <Button 
              variant="ghost" 
              onClick={handleLogout}
              className="text-[#064E3B]"
              data-testid="agente-logout-btn"
            >
              <LogOut className="w-4 h-4 mr-2" />
              Cerrar Sesión
            </Button>
          </div>
        </div>
      </header>

      {/* Content */}
      <div className="container mx-auto px-6 py-12">
        {/* Estadísticas Cards */}
        {estadisticas && (
          <div className="grid md:grid-cols-4 gap-6 mb-12">
            <Card>
              <CardContent className="p-6">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-sm text-[#64748B]">Total Seguros</p>
                    <p className="text-3xl font-bold text-[#064E3B]" style={{ fontFamily: 'Space Grotesk, monospace' }}>
                      {estadisticas.total_seguros}
                    </p>
                  </div>
                  <TrendingUp className="w-10 h-10 text-[#10B981]" />
                </div>
              </CardContent>
            </Card>

            <Card>
              <CardContent className="p-6">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-sm text-[#64748B]">Seguros Pagados</p>
                    <p className="text-3xl font-bold text-[#064E3B]" style={{ fontFamily: 'Space Grotesk, monospace' }}>
                      {estadisticas.seguros_pagados}
                    </p>
                  </div>
                  <Shield className="w-10 h-10 text-[#10B981]" />
                </div>
              </CardContent>
            </Card>

            <Card>
              <CardContent className="p-6">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-sm text-[#64748B]">Comisiones Totales</p>
                    <p className="text-3xl font-bold text-[#10B981]" style={{ fontFamily: 'Space Grotesk, monospace' }}>
                      ${estadisticas.total_comisiones.toLocaleString('es-AR', { maximumFractionDigits: 0 })}
                    </p>
                  </div>
                  <DollarSign className="w-10 h-10 text-[#10B981]" />
                </div>
              </CardContent>
            </Card>

            <Card>
              <CardContent className="p-6">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-sm text-[#64748B]">Premios Ganados</p>
                    <p className="text-3xl font-bold text-[#F59E0B]" style={{ fontFamily: 'Space Grotesk, monospace' }}>
                      {estadisticas.premios_ganados?.length || 0}
                    </p>
                  </div>
                  <Award className="w-10 h-10 text-[#F59E0B]" />
                </div>
              </CardContent>
            </Card>
          </div>
        )}

        {/* Premios Ganados */}
        {estadisticas?.premios_ganados?.length > 0 && (
          <Card className="mb-12 border-2 border-[#F59E0B] bg-gradient-to-r from-[#FEF3C7] to-white">
            <CardHeader>
              <CardTitle className="flex items-center gap-2 text-[#F59E0B]">
                <Award className="w-6 h-6" />
                ¡Felicitaciones! Has ganado premios
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="grid md:grid-cols-3 gap-4">
                {estadisticas.premios_ganados.map((premio, idx) => (
                  <div key={idx} className="bg-white rounded-xl p-4 border border-[#F59E0B]/20">
                    <p className="font-bold text-[#064E3B] mb-1">{premio.nombre}</p>
                    <p className="text-2xl font-bold text-[#F59E0B]" style={{ fontFamily: 'Space Grotesk, monospace' }}>
                      ${premio.monto.toLocaleString('es-AR')}
                    </p>
                    <p className="text-xs text-[#64748B]">Por {premio.cantidad_requerida} seguros</p>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        )}

        {/* Tabs */}
        <Tabs defaultValue="seguros" className="space-y-6">
          <TabsList className="grid w-full max-w-md grid-cols-2">
            <TabsTrigger value="seguros">Mis Seguros</TabsTrigger>
            <TabsTrigger value="vencimientos">Vencimientos</TabsTrigger>
          </TabsList>

          {/* Tab Seguros */}
          <TabsContent value="seguros" className="space-y-4">
            <div className="flex justify-between items-center">
              <h2 className="text-2xl font-bold text-[#064E3B]">Mis Coberturas Vendidas</h2>
              <Button 
                onClick={abrirModalCrear}
                className="bg-[#10B981] hover:bg-[#10B981]/90"
                data-testid="crear-cobertura-btn"
              >
                <Plus className="w-4 h-4 mr-2" />
                Nueva Cobertura
              </Button>
            </div>
            
            {seguros.length === 0 ? (
              <Card>
                <CardContent className="p-12 text-center">
                  <Car className="w-16 h-16 text-slate-300 mx-auto mb-4" />
                  <p className="text-[#64748B] mb-4">No tienes coberturas asignadas aún</p>
                  <Button 
                    onClick={abrirModalCrear}
                    className="bg-[#10B981] hover:bg-[#10B981]/90"
                  >
                    <Plus className="w-4 h-4 mr-2" />
                    Crear tu primera cobertura
                  </Button>
                </CardContent>
              </Card>
            ) : (
              <div className="grid gap-4">
                {seguros.map((seguro) => (
                  <Card key={seguro.id}>
                    <CardContent className="p-6">
                      <div className="grid md:grid-cols-5 gap-4 items-center">
                        <div>
                          <p className="text-sm text-[#64748B]">Recibo</p>
                          <p className="font-mono font-bold text-[#064E3B]">{seguro.numero_recibo}</p>
                        </div>
                        <div>
                          <p className="text-sm text-[#64748B]">Cliente</p>
                          <p className="font-semibold text-[#064E3B]">{seguro.nombre}</p>
                          <p className="text-xs text-[#64748B]">{seguro.patente}</p>
                        </div>
                        <div>
                          <p className="text-sm text-[#64748B]">Vencimiento</p>
                          <p className="font-semibold text-[#064E3B]">
                            {new Date(seguro.vigencia_hasta).toLocaleDateString('es-AR')}
                          </p>
                        </div>
                        <div>
                          <p className="text-sm text-[#64748B]">Tu Comisión</p>
                          <p className="text-xl font-bold text-[#10B981]" style={{ fontFamily: 'Space Grotesk, monospace' }}>
                            ${(seguro.precio_final * (seguro.comision_aplicada || agente?.comision_porcentaje || 10) / 100).toLocaleString('es-AR')}
                          </p>
                        </div>
                        <div>
                          <span className={`px-3 py-1 rounded-full text-xs font-semibold ${
                            seguro.estado === 'pagado' || seguro.estado === 'gratis'
                              ? 'bg-[#10B981] text-white'
                              : 'bg-yellow-500 text-white'
                          }`}>
                            {seguro.estado}
                          </span>
                        </div>
                      </div>
                    </CardContent>
                  </Card>
                ))}
              </div>
            )}
          </TabsContent>

          {/* Tab Vencimientos */}
          <TabsContent value="vencimientos" className="space-y-6">
            <h2 className="text-2xl font-bold text-[#064E3B]">Control de Vencimientos</h2>
            
            {vencimientos && (
              <>
                {/* Vencidos */}
                {vencimientos.vencidos?.length > 0 && (
                  <div>
                    <div className="flex items-center gap-2 mb-4">
                      <AlertCircle className="w-5 h-5 text-red-500" />
                      <h3 className="text-xl font-bold text-red-500">Vencidos ({vencimientos.vencidos.length})</h3>
                    </div>
                    <div className="grid gap-4">
                      {vencimientos.vencidos.map((seguro) => (
                        <VencimientoCard key={seguro.id} seguro={seguro} color="red" />
                      ))}
                    </div>
                  </div>
                )}

                {/* Próximos 7 días */}
                {vencimientos.proximos_7_dias?.length > 0 && (
                  <div>
                    <div className="flex items-center gap-2 mb-4">
                      <Calendar className="w-5 h-5 text-red-600" />
                      <h3 className="text-xl font-bold text-red-600">Próximos 7 días ({vencimientos.proximos_7_dias.length})</h3>
                    </div>
                    <div className="grid md:grid-cols-2 gap-4">
                      {vencimientos.proximos_7_dias.map((seguro) => (
                        <VencimientoCard key={seguro.id} seguro={seguro} color="red" />
                      ))}
                    </div>
                  </div>
                )}

                {/* Próximos 15 días */}
                {vencimientos.proximos_15_dias?.length > 0 && (
                  <div>
                    <div className="flex items-center gap-2 mb-4">
                      <Calendar className="w-5 h-5 text-yellow-600" />
                      <h3 className="text-xl font-bold text-yellow-600">Próximos 15 días ({vencimientos.proximos_15_dias.length})</h3>
                    </div>
                    <div className="grid md:grid-cols-2 gap-4">
                      {vencimientos.proximos_15_dias.map((seguro) => (
                        <VencimientoCard key={seguro.id} seguro={seguro} color="yellow" />
                      ))}
                    </div>
                  </div>
                )}

                {/* Próximos 30 días */}
                {vencimientos.proximos_30_dias?.length > 0 && (
                  <div>
                    <div className="flex items-center gap-2 mb-4">
                      <Calendar className="w-5 h-5 text-orange-600" />
                      <h3 className="text-xl font-bold text-orange-600">Próximos 30 días ({vencimientos.proximos_30_dias.length})</h3>
                    </div>
                    <div className="grid md:grid-cols-2 gap-4">
                      {vencimientos.proximos_30_dias.map((seguro) => (
                        <VencimientoCard key={seguro.id} seguro={seguro} color="orange" />
                      ))}
                    </div>
                  </div>
                )}
              </>
            )}
          </TabsContent>
        </Tabs>
      </div>

      {/* Modal Crear Cobertura */}
      <Dialog open={modalCrearOpen} onOpenChange={setModalCrearOpen}>
        <DialogContent className="max-w-2xl max-h-[90vh] overflow-y-auto">
          <DialogHeader>
            <DialogTitle className="text-2xl font-bold text-[#064E3B] flex items-center gap-2">
              <Car className="w-6 h-6" />
              Nueva Cobertura
            </DialogTitle>
          </DialogHeader>
          
          <div className="space-y-6">
            {/* Datos del Cliente */}
            <div>
              <h4 className="font-bold text-[#064E3B] mb-4">Datos del Cliente</h4>
              <div className="grid md:grid-cols-2 gap-4">
                <div>
                  <Label>DNI *</Label>
                  <Input
                    value={formSeguro.dni}
                    onChange={(e) => setFormSeguro({...formSeguro, dni: e.target.value})}
                    placeholder="12345678"
                    data-testid="seguro-dni-input"
                  />
                </div>
                <div>
                  <Label>Nombre Completo *</Label>
                  <Input
                    value={formSeguro.nombre}
                    onChange={(e) => setFormSeguro({...formSeguro, nombre: e.target.value})}
                    placeholder="Juan Pérez"
                    data-testid="seguro-nombre-input"
                  />
                </div>
                <div>
                  <Label>Email *</Label>
                  <Input
                    type="email"
                    value={formSeguro.email}
                    onChange={(e) => setFormSeguro({...formSeguro, email: e.target.value})}
                    placeholder="juan@email.com"
                    data-testid="seguro-email-input"
                  />
                </div>
                <div>
                  <Label>Teléfono</Label>
                  <Input
                    value={formSeguro.telefono}
                    onChange={(e) => setFormSeguro({...formSeguro, telefono: e.target.value})}
                    placeholder="1122334455"
                    data-testid="seguro-telefono-input"
                  />
                </div>
              </div>
            </div>

            {/* Datos del Vehículo */}
            <div className="border-t pt-4">
              <h4 className="font-bold text-[#064E3B] mb-4">Datos del Vehículo</h4>
              <div className="grid md:grid-cols-2 gap-4">
                <div>
                  <Label>Patente *</Label>
                  <Input
                    value={formSeguro.patente}
                    onChange={(e) => setFormSeguro({...formSeguro, patente: e.target.value.toUpperCase()})}
                    placeholder="AA123BB"
                    data-testid="seguro-patente-input"
                  />
                </div>
                <div>
                  <Label>Marca *</Label>
                  <Input
                    value={formSeguro.marca}
                    onChange={(e) => setFormSeguro({...formSeguro, marca: e.target.value})}
                    placeholder="Toyota"
                    data-testid="seguro-marca-input"
                  />
                </div>
                <div>
                  <Label>Modelo *</Label>
                  <Input
                    value={formSeguro.modelo}
                    onChange={(e) => setFormSeguro({...formSeguro, modelo: e.target.value})}
                    placeholder="Corolla"
                    data-testid="seguro-modelo-input"
                  />
                </div>
                <div>
                  <Label>Año</Label>
                  <Input
                    type="number"
                    value={formSeguro.ano}
                    onChange={(e) => setFormSeguro({...formSeguro, ano: parseInt(e.target.value)})}
                    data-testid="seguro-ano-input"
                  />
                </div>
                <div>
                  <Label>Tipo de Vehículo</Label>
                  <Select 
                    value={formSeguro.tipo_vehiculo}
                    onValueChange={(v) => setFormSeguro({...formSeguro, tipo_vehiculo: v})}
                  >
                    <SelectTrigger data-testid="seguro-tipo-input">
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="auto">Auto</SelectItem>
                      <SelectItem value="moto">Moto</SelectItem>
                      <SelectItem value="camioneta">Camioneta</SelectItem>
                      <SelectItem value="camion">Camión</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
                <div>
                  <Label>Tipo de Cobertura</Label>
                  <Select 
                    value={formSeguro.cobertura}
                    onValueChange={(v) => setFormSeguro({...formSeguro, cobertura: v})}
                  >
                    <SelectTrigger data-testid="seguro-cobertura-input">
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="rc">Responsabilidad Civil ($15.000)</SelectItem>
                      <SelectItem value="terceros">Terceros Completo ($25.000)</SelectItem>
                      <SelectItem value="completo">Todo Riesgo ($45.000)</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
              </div>
            </div>

            {/* Botones */}
            <div className="flex gap-4 pt-4 border-t">
              <Button
                onClick={() => setModalCrearOpen(false)}
                variant="outline"
                className="flex-1"
              >
                Cancelar
              </Button>
              <Button
                onClick={crearSeguro}
                disabled={loading}
                className="flex-1 bg-[#10B981] hover:bg-[#10B981]/90"
                data-testid="guardar-cobertura-btn"
              >
                {loading ? 'Creando...' : 'Crear Cobertura'}
              </Button>
            </div>
          </div>
        </DialogContent>
      </Dialog>
    </div>
  );
}

function VencimientoCard({ seguro, color }) {
  const colorClasses = {
    red: 'border-red-500 bg-red-50',
    yellow: 'border-yellow-500 bg-yellow-50',
    orange: 'border-orange-500 bg-orange-50',
    green: 'border-green-500 bg-green-50'
  };

  return (
    <Card className={`border-2 ${colorClasses[color]}`}>
      <CardContent className="p-4">
        <div className="flex justify-between items-start mb-2">
          <div>
            <p className="font-bold text-[#064E3B]">{seguro.patente}</p>
            <p className="text-sm text-[#64748B]">{seguro.nombre}</p>
          </div>
          <div className="text-right">
            <p className="text-xs text-[#64748B]">Vence en</p>
            <p className="text-xl font-bold text-[#064E3B]">{seguro.dias_restantes} días</p>
          </div>
        </div>
        <p className="text-xs text-[#64748B]">
          Vencimiento: {new Date(seguro.vigencia_hasta).toLocaleDateString('es-AR')}
        </p>
      </CardContent>
    </Card>
  );
}

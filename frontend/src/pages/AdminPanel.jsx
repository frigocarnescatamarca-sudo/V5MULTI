import { useState, useEffect } from 'react';
import { Shield, Check, Plus, Trash2, Tag, Download, LogOut, Edit, X, Image as ImageIcon, Users, Award, Calendar, TrendingUp, DollarSign, History } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger } from '@/components/ui/dialog';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Textarea } from '@/components/ui/textarea';
import { adminAPI, segurosAPI } from '@/services/api';
import { toast } from 'sonner';
import VisorDocumentos from '@/components/VisorDocumentos';

export default function AdminPanel() {
  const [authenticated, setAuthenticated] = useState(false);
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [token, setToken] = useState(null);
  const [adminUsername, setAdminUsername] = useState('');
  const [seguros, setSeguros] = useState([]);
  const [promoCodes, setPromoCodes] = useState([]);
  const [agentes, setAgentes] = useState([]);
  const [premios, setPremios] = useState([]);
  const [vencimientos, setVencimientos] = useState(null);
  const [loading, setLoading] = useState(false);
  const [nuevoPromo, setNuevoPromo] = useState({ codigo: '', descuento_porcentaje: 0, es_master: false });
  const [nuevoAgente, setNuevoAgente] = useState({ 
    nombre: '', 
    email: '', 
    telefono: '', 
    username: '', 
    password: '', 
    comision_porcentaje: 10 
  });
  const [nuevoPremio, setNuevoPremio] = useState({ 
    nombre: '', 
    cantidad_seguros: 50, 
    monto_premio: 10000 
  });
  const [modalAgenteOpen, setModalAgenteOpen] = useState(false);
  const [agenteEditando, setAgenteEditando] = useState(null);
  const [modalSeguroOpen, setModalSeguroOpen] = useState(false);
  const [seguroEditando, setSeguroEditando] = useState(null);
  const [seguroVerDocs, setSeguroVerDocs] = useState(null);
  // Estados para modal de saldo
  const [modalSaldoOpen, setModalSaldoOpen] = useState(false);
  const [agenteParaSaldo, setAgenteParaSaldo] = useState(null);
  const [nuevoSaldo, setNuevoSaldo] = useState({ monto: '', observacion: '' });
  const [movimientosAgente, setMovimientosAgente] = useState([]);
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
    cobertura: 'rc',
    agente_id: ''
  });

  useEffect(() => {
    // Verificar si hay token guardado
    const savedToken = localStorage.getItem('admin_token');
    const savedUsername = localStorage.getItem('admin_username');
    
    if (savedToken && savedUsername) {
      verifyToken(savedToken, savedUsername);
    }
  }, []);

  useEffect(() => {
    if (authenticated) {
      cargarDatos();
    }
  }, [authenticated]);

  const verifyToken = async (savedToken, savedUsername) => {
    try {
      const result = await adminAPI.verifyToken(savedToken);
      if (result.valid) {
        setToken(savedToken);
        setAdminUsername(savedUsername);
        setAuthenticated(true);
      } else {
        // Token inválido, limpiar
        localStorage.removeItem('admin_token');
        localStorage.removeItem('admin_username');
      }
    } catch (error) {
      localStorage.removeItem('admin_token');
      localStorage.removeItem('admin_username');
    }
  };

  const handleLogin = async (e) => {
    e.preventDefault();
    setLoading(true);
    
    try {
      const result = await adminAPI.login(username, password);
      setToken(result.token);
      setAdminUsername(result.username);
      setAuthenticated(true);
      
      // Guardar token
      localStorage.setItem('admin_token', result.token);
      localStorage.setItem('admin_username', result.username);
      
      toast.success('Sesión iniciada correctamente');
    } catch (error) {
      toast.error('Credenciales incorrectas');
    } finally {
      setLoading(false);
    }
  };

  const handleLogout = async () => {
    try {
      await adminAPI.logout(token);
      localStorage.removeItem('admin_token');
      localStorage.removeItem('admin_username');
      setAuthenticated(false);
      setToken(null);
      setAdminUsername('');
      toast.success('Sesión cerrada');
    } catch (error) {
      toast.error('Error al cerrar sesión');
    }
  };

  const cargarDatos = async () => {
    setLoading(true);
    try {
      const [segurosData, codigosData, agentesData, premiosData, vencimientosData] = await Promise.all([
        adminAPI.listarSeguros(0, 100, token),
        adminAPI.listarPromoCodes(),
        adminAPI.listarAgentes(),
        adminAPI.listarPremios(),
        adminAPI.obtenerVencimientos()
      ]);
      setSeguros(segurosData.seguros || []);
      setPromoCodes(codigosData.codigos || []);
      setAgentes(agentesData.agentes || []);
      setPremios(premiosData.premios || []);
      setVencimientos(vencimientosData);
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

  const abrirModalCrearSeguro = () => {
    setSeguroEditando(null);
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
      cobertura: 'rc',
      agente_id: ''
    });
    setModalSeguroOpen(true);
  };

  const abrirModalEditarSeguro = (seguro) => {
    setSeguroEditando(seguro);
    setFormSeguro({
      dni: seguro.dni,
      nombre: seguro.nombre,
      email: seguro.email,
      telefono: seguro.telefono,
      patente: seguro.patente,
      marca: seguro.marca,
      modelo: seguro.modelo,
      ano: seguro.ano,
      tipo_vehiculo: seguro.tipo_vehiculo,
      cobertura: seguro.cobertura,
      agente_id: seguro.agente_id || ''
    });
    setModalSeguroOpen(true);
  };

  const guardarSeguro = async () => {
    // Validar campos
    if (!formSeguro.dni || !formSeguro.nombre || !formSeguro.email || !formSeguro.patente) {
      toast.error('Por favor complete todos los campos obligatorios');
      return;
    }

    setLoading(true);
    try {
      if (seguroEditando) {
        // Editar
        await adminAPI.actualizarSeguro(seguroEditando.id, formSeguro);
        
        // Si se asignó un agente, actualizar la asignación
        if (formSeguro.agente_id && formSeguro.agente_id !== seguroEditando.agente_id) {
          await adminAPI.asignarAgente(seguroEditando.id, formSeguro.agente_id);
        }
        
        toast.success('Seguro actualizado correctamente');
      } else {
        // Crear
        await adminAPI.crearSeguroManual(formSeguro);
        toast.success('Seguro creado correctamente');
      }
      
      setModalSeguroOpen(false);
      cargarDatos();
    } catch (error) {
      toast.error('Error al guardar seguro: ' + (error.response?.data?.detail || error.message));
    } finally {
      setLoading(false);
    }
  };

  const eliminarSeguro = async (seguroId, numeroRecibo) => {
    if (!window.confirm(`¿Está seguro de eliminar el seguro ${numeroRecibo}?`)) return;
    
    try {
      await adminAPI.eliminarSeguro(seguroId);
      toast.success('Seguro eliminado correctamente');
      cargarDatos();
    } catch (error) {
      toast.error('Error al eliminar seguro');
    }
  };

  // Funciones Agentes
  const abrirModalCrearAgente = () => {
    setAgenteEditando(null);
    setNuevoAgente({ nombre: '', email: '', telefono: '', username: '', password: '', comision_porcentaje: 10 });
    setModalAgenteOpen(true);
  };

  const abrirModalEditarAgente = (agente) => {
    setAgenteEditando(agente);
    setNuevoAgente({
      nombre: agente.nombre,
      email: agente.email,
      telefono: agente.telefono,
      username: agente.username,
      password: '',
      comision_porcentaje: agente.comision_porcentaje
    });
    setModalAgenteOpen(true);
  };

  const guardarAgente = async () => {
    if (!nuevoAgente.nombre || !nuevoAgente.email || !nuevoAgente.username) {
      toast.error('Complete los campos obligatorios');
      return;
    }

    if (!agenteEditando && !nuevoAgente.password) {
      toast.error('La contraseña es requerida para nuevos agentes');
      return;
    }

    setLoading(true);
    try {
      if (agenteEditando) {
        await adminAPI.actualizarAgente(agenteEditando.id, nuevoAgente);
        toast.success('Agente actualizado');
      } else {
        await adminAPI.crearAgente(nuevoAgente);
        toast.success('Agente creado');
      }
      setModalAgenteOpen(false);
      cargarDatos();
    } catch (error) {
      toast.error('Error: ' + (error.response?.data?.detail || error.message));
    } finally {
      setLoading(false);
    }
  };

  const eliminarAgente = async (agenteId, nombre) => {
    if (!window.confirm(`¿Desactivar agente ${nombre}?`)) return;
    
    try {
      await adminAPI.eliminarAgente(agenteId);
      toast.success('Agente desactivado');
      cargarDatos();
    } catch (error) {
      toast.error('Error al desactivar agente');
    }
  };

  // Funciones Premios
  const crearPremio = async () => {
    if (!nuevoPremio.nombre || nuevoPremio.cantidad_seguros < 1) {
      toast.error('Complete los campos correctamente');
      return;
    }

    try {
      await adminAPI.crearPremio(nuevoPremio);
      toast.success('Premio creado');
      setNuevoPremio({ nombre: '', cantidad_seguros: 50, monto_premio: 10000 });
      cargarDatos();
    } catch (error) {
      toast.error('Error al crear premio');
    }
  };

  const eliminarPremio = async (premioId, nombre) => {
    if (!window.confirm(`¿Desactivar premio "${nombre}"?`)) return;
    
    try {
      await adminAPI.eliminarPremio(premioId);
      toast.success('Premio desactivado');
      cargarDatos();
    } catch (error) {
      toast.error('Error al desactivar premio');
    }
  };

  // Funciones de Saldo de Agentes
  const abrirModalSaldo = async (agente) => {
    setAgenteParaSaldo(agente);
    setNuevoSaldo({ monto: '', observacion: '' });
    setModalSaldoOpen(true);
    
    // Cargar historial de movimientos
    try {
      const data = await adminAPI.obtenerMovimientosAgente(agente.id);
      setMovimientosAgente(data.movimientos || []);
    } catch (error) {
      setMovimientosAgente([]);
    }
  };

  const agregarSaldo = async () => {
    if (!nuevoSaldo.monto || parseFloat(nuevoSaldo.monto) <= 0) {
      toast.error('Ingrese un monto válido mayor a 0');
      return;
    }

    setLoading(true);
    try {
      await adminAPI.agregarSaldoAgente(
        agenteParaSaldo.id, 
        parseFloat(nuevoSaldo.monto), 
        nuevoSaldo.observacion
      );
      toast.success(`Se agregaron $${parseFloat(nuevoSaldo.monto).toLocaleString('es-AR')} al saldo de ${agenteParaSaldo.nombre}`);
      setNuevoSaldo({ monto: '', observacion: '' });
      
      // Recargar movimientos
      const data = await adminAPI.obtenerMovimientosAgente(agenteParaSaldo.id);
      setMovimientosAgente(data.movimientos || []);
      
      // Recargar agentes para actualizar saldo
      cargarDatos();
    } catch (error) {
      toast.error('Error al agregar saldo');
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
            <div className="w-16 h-16 bg-[#064E3B] rounded-xl flex items-center justify-center mx-auto mb-4">
              <Shield className="w-8 h-8 text-[#D9F99D]" />
            </div>
            <CardTitle className="text-2xl font-bold text-[#064E3B]" style={{ fontFamily: 'Manrope, sans-serif' }}>
              Panel Administrativo
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
                  placeholder="admin"
                  required
                  data-testid="admin-username-input"
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
                  data-testid="admin-password-input"
                />
              </div>
              <Button
                type="submit"
                disabled={loading}
                className="w-full bg-[#064E3B] hover:bg-[#064E3B]/90"
                data-testid="admin-login-btn"
              >
                {loading ? 'Iniciando sesión...' : 'Iniciar Sesión'}
              </Button>
              <div className="text-center text-sm text-[#64748B] mt-4">
                <p>Credenciales por defecto:</p>
                <p className="font-mono text-xs">Usuario: admin</p>
                <p className="font-mono text-xs">Contraseña: Estonia2025!</p>
              </div>
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
            <div className="w-12 h-12 bg-[#064E3B] rounded-xl flex items-center justify-center">
              <Shield className="w-6 h-6 text-[#D9F99D]" />
            </div>
            <div>
              <h1 className="text-2xl font-bold text-[#064E3B]" style={{ fontFamily: 'Manrope, sans-serif' }}>
                Panel Admin
              </h1>
            </div>
          </div>
          <div className="flex gap-4 items-center">
            <span className="text-sm text-[#64748B]">Hola, {adminUsername}</span>
            <Button 
              variant="ghost" 
              onClick={handleLogout}
              className="text-[#064E3B]"
              data-testid="admin-logout-btn"
            >
              <LogOut className="w-4 h-4 mr-2" />
              Cerrar Sesión
            </Button>
            <Button 
              variant="ghost" 
              onClick={() => window.location.href = '/'}
              className="text-[#064E3B]"
            >
              Volver al Inicio
            </Button>
          </div>
        </div>
      </header>

      {/* Content */}
      <div className="container mx-auto px-6 py-12">
        <Tabs defaultValue="seguros" className="space-y-6">
          <TabsList className="grid w-full max-w-4xl grid-cols-5">
            <TabsTrigger value="seguros">Seguros</TabsTrigger>
            <TabsTrigger value="agentes">Agentes</TabsTrigger>
            <TabsTrigger value="premios">Premios</TabsTrigger>
            <TabsTrigger value="vencimientos">Vencimientos</TabsTrigger>
            <TabsTrigger value="promos">Códigos</TabsTrigger>
          </TabsList>

          {/* Tab Seguros */}
          <TabsContent value="seguros" className="space-y-6" data-testid="tab-seguros">
            <div className="flex justify-between items-center">
              <h2 className="text-2xl font-bold text-[#064E3B]" style={{ fontFamily: 'Manrope, sans-serif' }}>
                Listado de Seguros
              </h2>
              <div className="flex gap-2">
                <Button
                  onClick={abrirModalCrearSeguro}
                  className="bg-[#10B981] hover:bg-[#10B981]/90"
                  data-testid="crear-seguro-btn"
                >
                  <Plus className="w-4 h-4 mr-2" />
                  Crear Seguro
                </Button>
                <Button onClick={cargarDatos} disabled={loading} variant="outline">
                  Recargar
                </Button>
              </div>
            </div>

            <div className="grid gap-4">
              {seguros.map((seguro) => (
                <Card key={seguro.numero_recibo} data-testid="seguro-admin-card">
                  <CardContent className="p-6">
                    <div className="grid md:grid-cols-6 gap-4 items-center">
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
                        <p className="text-sm text-[#64748B]">Agente</p>
                        {seguro.agente_nombre ? (
                          <p className="font-semibold text-[#10B981]">{seguro.agente_nombre}</p>
                        ) : (
                          <p className="text-xs text-[#64748B] italic">Sin agente</p>
                        )}
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
                      <div className="flex justify-end gap-2 flex-wrap">
                        <Button
                          onClick={() => setSeguroVerDocs(seguro)}
                          size="sm"
                          variant="outline"
                          className="text-[#064E3B]"
                          data-testid="ver-docs-btn"
                        >
                          <ImageIcon className="w-4 h-4 mr-1" />
                          Docs
                        </Button>
                        <Button
                          onClick={() => abrirModalEditarSeguro(seguro)}
                          size="sm"
                          variant="ghost"
                          className="text-blue-600 hover:text-blue-700"
                          data-testid="editar-seguro-btn"
                        >
                          <Edit className="w-4 h-4" />
                        </Button>
                        <Button
                          onClick={() => eliminarSeguro(seguro.id, seguro.numero_recibo)}
                          size="sm"
                          variant="ghost"
                          className="text-red-600 hover:text-red-700"
                          data-testid="eliminar-seguro-btn"
                        >
                          <Trash2 className="w-4 h-4" />
                        </Button>
                        <Button
                          onClick={() => window.open(segurosAPI.descargarPDF(seguro.id || seguro.numero_recibo), '_blank')}
                          size="sm"
                          variant="outline"
                          className="text-[#064E3B]"
                          data-testid="admin-download-pdf-btn"
                        >
                          <Download className="w-4 h-4 mr-1" />
                          PDF
                        </Button>
                        <Button
                          onClick={() => window.open(segurosAPI.descargarImagen(seguro.id || seguro.numero_recibo), '_blank')}
                          size="sm"
                          variant="outline"
                          className="text-[#064E3B]"
                          data-testid="admin-download-img-btn"
                        >
                          <Download className="w-4 h-4 mr-1" />
                          IMG
                        </Button>
                        {!seguro.procesado && (seguro.estado === 'pagado' || seguro.estado === 'gratis') && (
                          <Button
                            onClick={() => marcarProcesado(seguro.id || seguro.numero_recibo)}
                            size="sm"
                            className="bg-[#064E3B] hover:bg-[#064E3B]/90"
                            data-testid="marcar-procesado-btn"
                          >
                            <Check className="w-4 h-4 mr-1" />
                            Procesado
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

          {/* Tab Agentes */}
          <TabsContent value="agentes" className="space-y-6" data-testid="tab-agentes">
            <div className="flex justify-between items-center">
              <h2 className="text-2xl font-bold text-[#064E3B]" style={{ fontFamily: 'Manrope, sans-serif' }}>
                Gestión de Agentes
              </h2>
              <Button
                onClick={abrirModalCrearAgente}
                className="bg-[#10B981] hover:bg-[#10B981]/90"
                data-testid="crear-agente-btn"
              >
                <Plus className="w-4 h-4 mr-2" />
                Crear Agente
              </Button>
            </div>

            <div className="grid gap-4">
              {agentes.map((agente) => (
                <Card key={agente.id} className={!agente.activo ? 'opacity-50' : ''}>
                  <CardContent className="p-6">
                    <div className="grid md:grid-cols-5 gap-4 items-center">
                      <div>
                        <p className="text-sm text-[#64748B]">Agente</p>
                        <p className="font-bold text-[#064E3B]">{agente.nombre}</p>
                        <p className="text-xs text-[#64748B]">@{agente.username}</p>
                      </div>
                      <div>
                        <p className="text-sm text-[#64748B]">Contacto</p>
                        <p className="text-sm text-[#064E3B]">{agente.email}</p>
                        <p className="text-xs text-[#64748B]">{agente.telefono}</p>
                      </div>
                      <div>
                        <p className="text-sm text-[#64748B]">Comisión</p>
                        <p className="text-2xl font-bold text-[#10B981]">{agente.comision_porcentaje}%</p>
                      </div>
                      <div>
                        <p className="text-sm text-[#64748B]">Estadísticas</p>
                        <p className="text-sm text-[#064E3B]">
                          {agente.estadisticas?.seguros_pagados || 0} vendidos
                        </p>
                        <p className="text-xs text-[#10B981]">
                          ${(agente.estadisticas?.total_comisiones || 0).toLocaleString('es-AR')} comisiones
                        </p>
                      </div>
                      <div className="flex gap-2 justify-end">
                        <Button
                          onClick={() => abrirModalEditarAgente(agente)}
                          size="sm"
                          variant="outline"
                          data-testid="editar-agente-btn"
                        >
                          <Edit className="w-4 h-4" />
                        </Button>
                        {agente.activo && (
                          <Button
                            onClick={() => eliminarAgente(agente.id, agente.nombre)}
                            size="sm"
                            variant="ghost"
                            className="text-red-500"
                            data-testid="desactivar-agente-btn"
                          >
                            <Trash2 className="w-4 h-4" />
                          </Button>
                        )}
                      </div>
                    </div>
                  </CardContent>
                </Card>
              ))}
            </div>

            {agentes.length === 0 && (
              <Card>
                <CardContent className="p-12 text-center">
                  <Users className="w-16 h-16 text-slate-300 mx-auto mb-4" />
                  <p className="text-[#64748B]">No hay agentes registrados</p>
                </CardContent>
              </Card>
            )}
          </TabsContent>

          {/* Tab Premios */}
          <TabsContent value="premios" className="space-y-6" data-testid="tab-premios">
            <div className="flex justify-between items-center">
              <h2 className="text-2xl font-bold text-[#064E3B]" style={{ fontFamily: 'Manrope, sans-serif' }}>
                Premios por Ventas
              </h2>
            </div>

            <Card className="bg-[#F0FDF4]">
              <CardHeader>
                <CardTitle>Crear Nuevo Premio</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="grid md:grid-cols-4 gap-4 items-end">
                  <div>
                    <Label>Nombre del Premio</Label>
                    <Input
                      value={nuevoPremio.nombre}
                      onChange={(e) => setNuevoPremio({...nuevoPremio, nombre: e.target.value})}
                      placeholder="Ej: Premio 50 Ventas"
                      data-testid="premio-nombre-input"
                    />
                  </div>
                  <div>
                    <Label>Cantidad de Seguros</Label>
                    <Input
                      type="number"
                      value={nuevoPremio.cantidad_seguros}
                      onChange={(e) => setNuevoPremio({...nuevoPremio, cantidad_seguros: parseInt(e.target.value)})}
                      data-testid="premio-cantidad-input"
                    />
                  </div>
                  <div>
                    <Label>Monto del Premio ($)</Label>
                    <Input
                      type="number"
                      value={nuevoPremio.monto_premio}
                      onChange={(e) => setNuevoPremio({...nuevoPremio, monto_premio: parseFloat(e.target.value)})}
                      data-testid="premio-monto-input"
                    />
                  </div>
                  <Button
                    onClick={crearPremio}
                    className="bg-[#10B981] hover:bg-[#10B981]/90"
                    data-testid="crear-premio-btn"
                  >
                    <Plus className="w-4 h-4 mr-2" />
                    Crear
                  </Button>
                </div>
              </CardContent>
            </Card>

            <div className="grid md:grid-cols-3 gap-4">
              {premios.map((premio) => (
                <Card key={premio.id} className={!premio.activo ? 'opacity-50' : 'border-[#F59E0B] border-2'}>
                  <CardHeader>
                    <div className="flex justify-between items-start">
                      <div>
                        <CardTitle className="flex items-center gap-2 text-[#064E3B]">
                          <Award className="w-5 h-5 text-[#F59E0B]" />
                          {premio.nombre}
                        </CardTitle>
                      </div>
                      {premio.activo && (
                        <Button
                          onClick={() => eliminarPremio(premio.id, premio.nombre)}
                          size="sm"
                          variant="ghost"
                          className="text-red-500"
                        >
                          <Trash2 className="w-4 h-4" />
                        </Button>
                      )}
                    </div>
                  </CardHeader>
                  <CardContent>
                    <p className="text-3xl font-bold text-[#F59E0B]" style={{ fontFamily: 'Space Grotesk, monospace' }}>
                      ${premio.monto_premio.toLocaleString('es-AR')}
                    </p>
                    <p className="text-sm text-[#64748B] mt-2">
                      Por vender {premio.cantidad_seguros} seguros
                    </p>
                    <p className={`text-xs mt-2 font-semibold ${premio.activo ? 'text-[#10B981]' : 'text-red-500'}`}>
                      {premio.activo ? 'ACTIVO' : 'INACTIVO'}
                    </p>
                  </CardContent>
                </Card>
              ))}
            </div>

            {premios.length === 0 && (
              <Card>
                <CardContent className="p-12 text-center">
                  <Award className="w-16 h-16 text-slate-300 mx-auto mb-4" />
                  <p className="text-[#64748B]">No hay premios configurados</p>
                </CardContent>
              </Card>
            )}
          </TabsContent>

          {/* Tab Vencimientos */}
          <TabsContent value="vencimientos" className="space-y-6" data-testid="tab-vencimientos">
            <h2 className="text-2xl font-bold text-[#064E3B]" style={{ fontFamily: 'Manrope, sans-serif' }}>
              Control de Vencimientos
            </h2>

            {vencimientos && (
              <>
                {/* Vencidos */}
                {vencimientos.vencidos?.length > 0 && (
                  <div>
                    <div className="flex items-center gap-2 mb-4">
                      <div className="w-4 h-4 bg-red-500 rounded-full"></div>
                      <h3 className="text-xl font-bold text-red-500">
                        Vencidos ({vencimientos.vencidos.length})
                      </h3>
                    </div>
                    <div className="grid md:grid-cols-3 gap-4">
                      {vencimientos.vencidos.slice(0, 9).map((seguro) => (
                        <VencimientoCard key={seguro.id} seguro={seguro} color="red" />
                      ))}
                    </div>
                  </div>
                )}

                {/* Próximos 7 días */}
                {vencimientos.proximos_7_dias?.length > 0 && (
                  <div>
                    <div className="flex items-center gap-2 mb-4">
                      <div className="w-4 h-4 bg-red-600 rounded-full"></div>
                      <h3 className="text-xl font-bold text-red-600">
                        Próximos 7 días ({vencimientos.proximos_7_dias.length})
                      </h3>
                    </div>
                    <div className="grid md:grid-cols-3 gap-4">
                      {vencimientos.proximos_7_dias.slice(0, 9).map((seguro) => (
                        <VencimientoCard key={seguro.id} seguro={seguro} color="red" />
                      ))}
                    </div>
                  </div>
                )}

                {/* Próximos 15 días */}
                {vencimientos.proximos_15_dias?.length > 0 && (
                  <div>
                    <div className="flex items-center gap-2 mb-4">
                      <div className="w-4 h-4 bg-yellow-500 rounded-full"></div>
                      <h3 className="text-xl font-bold text-yellow-600">
                        Próximos 15 días ({vencimientos.proximos_15_dias.length})
                      </h3>
                    </div>
                    <div className="grid md:grid-cols-3 gap-4">
                      {vencimientos.proximos_15_dias.slice(0, 9).map((seguro) => (
                        <VencimientoCard key={seguro.id} seguro={seguro} color="yellow" />
                      ))}
                    </div>
                  </div>
                )}

                {/* Próximos 30 días */}
                {vencimientos.proximos_30_dias?.length > 0 && (
                  <div>
                    <div className="flex items-center gap-2 mb-4">
                      <div className="w-4 h-4 bg-orange-500 rounded-full"></div>
                      <h3 className="text-xl font-bold text-orange-600">
                        Próximos 30 días ({vencimientos.proximos_30_dias.length})
                      </h3>
                    </div>
                    <div className="grid md:grid-cols-3 gap-4">
                      {vencimientos.proximos_30_dias.slice(0, 9).map((seguro) => (
                        <VencimientoCard key={seguro.id} seguro={seguro} color="orange" />
                      ))}
                    </div>
                  </div>
                )}

                {/* Sin vencimientos próximos */}
                {!vencimientos.vencidos?.length && 
                 !vencimientos.proximos_7_dias?.length && 
                 !vencimientos.proximos_15_dias?.length && 
                 !vencimientos.proximos_30_dias?.length && (
                  <Card>
                    <CardContent className="p-12 text-center">
                      <Calendar className="w-16 h-16 text-[#10B981] mx-auto mb-4" />
                      <p className="text-[#10B981] font-semibold">
                        ¡Todos los seguros tienen vigencia mayor a 30 días!
                      </p>
                    </CardContent>
                  </Card>
                )}
              </>
            )}
          </TabsContent>
        </Tabs>
      </div>

      {/* Modal Crear/Editar Seguro */}
      <Dialog open={modalSeguroOpen} onOpenChange={setModalSeguroOpen}>
        <DialogContent className="max-w-2xl max-h-[90vh] overflow-y-auto">
          <DialogHeader>
            <DialogTitle className="text-2xl font-bold text-[#064E3B]">
              {seguroEditando ? 'Editar Seguro' : 'Crear Nuevo Seguro'}
            </DialogTitle>
          </DialogHeader>
          
          <div className="space-y-4">
            <div className="grid md:grid-cols-2 gap-4">
              <div>
                <Label htmlFor="admin-dni">DNI *</Label>
                <Input
                  id="admin-dni"
                  value={formSeguro.dni}
                  onChange={(e) => setFormSeguro({...formSeguro, dni: e.target.value})}
                  placeholder="12345678"
                  data-testid="admin-seguro-dni"
                />
              </div>
              <div>
                <Label htmlFor="admin-nombre">Nombre Completo *</Label>
                <Input
                  id="admin-nombre"
                  value={formSeguro.nombre}
                  onChange={(e) => setFormSeguro({...formSeguro, nombre: e.target.value})}
                  placeholder="Juan Pérez"
                  data-testid="admin-seguro-nombre"
                />
              </div>
              <div>
                <Label htmlFor="admin-email">Email *</Label>
                <Input
                  id="admin-email"
                  type="email"
                  value={formSeguro.email}
                  onChange={(e) => setFormSeguro({...formSeguro, email: e.target.value})}
                  placeholder="juan@email.com"
                  data-testid="admin-seguro-email"
                />
              </div>
              <div>
                <Label htmlFor="admin-telefono">Teléfono *</Label>
                <Input
                  id="admin-telefono"
                  value={formSeguro.telefono}
                  onChange={(e) => setFormSeguro({...formSeguro, telefono: e.target.value})}
                  placeholder="+54 9 11 1234-5678"
                  data-testid="admin-seguro-telefono"
                />
              </div>
            </div>

            <div className="border-t pt-4">
              <h4 className="font-bold text-[#064E3B] mb-4">Datos del Vehículo</h4>
              <div className="grid md:grid-cols-2 gap-4">
                <div>
                  <Label htmlFor="admin-patente">Patente *</Label>
                  <Input
                    id="admin-patente"
                    value={formSeguro.patente}
                    onChange={(e) => setFormSeguro({...formSeguro, patente: e.target.value.toUpperCase()})}
                    placeholder="ABC123"
                    data-testid="admin-seguro-patente"
                  />
                </div>
                <div>
                  <Label htmlFor="admin-marca">Marca *</Label>
                  <Input
                    id="admin-marca"
                    value={formSeguro.marca}
                    onChange={(e) => setFormSeguro({...formSeguro, marca: e.target.value})}
                    placeholder="Ford"
                    data-testid="admin-seguro-marca"
                  />
                </div>
                <div>
                  <Label htmlFor="admin-modelo">Modelo *</Label>
                  <Input
                    id="admin-modelo"
                    value={formSeguro.modelo}
                    onChange={(e) => setFormSeguro({...formSeguro, modelo: e.target.value})}
                    placeholder="Focus"
                    data-testid="admin-seguro-modelo"
                  />
                </div>
                <div>
                  <Label htmlFor="admin-ano">Año *</Label>
                  <Input
                    id="admin-ano"
                    type="number"
                    value={formSeguro.ano}
                    onChange={(e) => setFormSeguro({...formSeguro, ano: parseInt(e.target.value)})}
                    data-testid="admin-seguro-ano"
                  />
                </div>
              </div>
            </div>

            <div className="border-t pt-4">
              <h4 className="font-bold text-[#064E3B] mb-4">Tipo y Cobertura</h4>
              <div className="grid md:grid-cols-2 gap-4">
                <div>
                  <Label htmlFor="admin-tipo">Tipo de Vehículo</Label>
                  <Select 
                    value={formSeguro.tipo_vehiculo} 
                    onValueChange={(v) => setFormSeguro({...formSeguro, tipo_vehiculo: v})}
                  >
                    <SelectTrigger data-testid="admin-seguro-tipo">
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
                  <Label htmlFor="admin-cobertura">Cobertura</Label>
                  <Select 
                    value={formSeguro.cobertura} 
                    onValueChange={(v) => setFormSeguro({...formSeguro, cobertura: v})}
                  >
                    <SelectTrigger data-testid="admin-seguro-cobertura">
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

            {/* Asignar Agente (solo en edición) */}
            {seguroEditando && (
              <div className="border-t pt-4">
                <h4 className="font-bold text-[#064E3B] mb-4">Asignar Agente</h4>
                <div>
                  <Label>Agente Responsable</Label>
                  <Select 
                    value={formSeguro.agente_id || 'none'} 
                    onValueChange={(v) => setFormSeguro({...formSeguro, agente_id: v === 'none' ? '' : v})}
                  >
                    <SelectTrigger data-testid="admin-seguro-agente">
                      <SelectValue placeholder="Sin agente asignado" />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="none">Sin agente</SelectItem>
                      {agentes.filter(a => a.activo).map((agente) => (
                        <SelectItem key={agente.id} value={agente.id}>
                          {agente.nombre} ({agente.comision_porcentaje}%)
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                  <p className="text-xs text-[#64748B] mt-1">
                    Al asignar un agente, las comisiones se calcularán automáticamente
                  </p>
                </div>
              </div>
            )}

            <div className="flex gap-4 pt-4">
              <Button
                onClick={() => setModalSeguroOpen(false)}
                variant="outline"
                className="flex-1"
              >
                Cancelar
              </Button>
              <Button
                onClick={guardarSeguro}
                disabled={loading}
                className="flex-1 bg-[#064E3B] hover:bg-[#064E3B]/90"
                data-testid="guardar-seguro-btn"
              >
                {loading ? 'Guardando...' : (seguroEditando ? 'Actualizar' : 'Crear Seguro')}
              </Button>
            </div>
          </div>
        </DialogContent>
      </Dialog>

      {/* Modal Ver Documentos */}
      {seguroVerDocs && (
        <VisorDocumentos 
          seguro={seguroVerDocs} 
          onClose={() => setSeguroVerDocs(null)} 
        />
      )}

      {/* Modal Crear/Editar Agente */}
      <Dialog open={modalAgenteOpen} onOpenChange={setModalAgenteOpen}>
        <DialogContent className="max-w-2xl">
          <DialogHeader>
            <DialogTitle className="text-2xl font-bold text-[#064E3B]">
              {agenteEditando ? 'Editar Agente' : 'Crear Nuevo Agente'}
            </DialogTitle>
          </DialogHeader>
          <div className="space-y-4">
            <div className="grid md:grid-cols-2 gap-4">
              <div>
                <Label>Nombre Completo *</Label>
                <Input
                  value={nuevoAgente.nombre}
                  onChange={(e) => setNuevoAgente({...nuevoAgente, nombre: e.target.value})}
                  placeholder="Juan Pérez"
                  data-testid="agente-nombre-input"
                />
              </div>
              <div>
                <Label>Email *</Label>
                <Input
                  type="email"
                  value={nuevoAgente.email}
                  onChange={(e) => setNuevoAgente({...nuevoAgente, email: e.target.value})}
                  placeholder="juan@email.com"
                  data-testid="agente-email-input"
                />
              </div>
              <div>
                <Label>Teléfono *</Label>
                <Input
                  value={nuevoAgente.telefono}
                  onChange={(e) => setNuevoAgente({...nuevoAgente, telefono: e.target.value})}
                  placeholder="+54 9 11 1234-5678"
                  data-testid="agente-telefono-input"
                />
              </div>
              <div>
                <Label>Comisión (%)</Label>
                <Input
                  type="number"
                  min="0"
                  max="100"
                  value={nuevoAgente.comision_porcentaje}
                  onChange={(e) => setNuevoAgente({...nuevoAgente, comision_porcentaje: parseInt(e.target.value)})}
                  data-testid="agente-comision-input"
                />
              </div>
            </div>
            <div className="border-t pt-4">
              <h4 className="font-bold text-[#064E3B] mb-4">Credenciales de Acceso</h4>
              <div className="grid md:grid-cols-2 gap-4">
                <div>
                  <Label>Usuario *</Label>
                  <Input
                    value={nuevoAgente.username}
                    onChange={(e) => setNuevoAgente({...nuevoAgente, username: e.target.value})}
                    placeholder="juanperez"
                    disabled={!!agenteEditando}
                    data-testid="agente-username-input"
                  />
                  {agenteEditando && (
                    <p className="text-xs text-[#64748B] mt-1">El usuario no se puede cambiar</p>
                  )}
                </div>
                <div>
                  <Label>Contraseña {!agenteEditando && '*'}</Label>
                  <Input
                    type="password"
                    value={nuevoAgente.password}
                    onChange={(e) => setNuevoAgente({...nuevoAgente, password: e.target.value})}
                    placeholder={agenteEditando ? "Dejar vacío para no cambiar" : "Contraseña"}
                    data-testid="agente-password-input"
                  />
                </div>
              </div>
            </div>
            <div className="flex gap-4">
              <Button
                onClick={() => setModalAgenteOpen(false)}
                variant="outline"
                className="flex-1"
              >
                Cancelar
              </Button>
              <Button
                onClick={guardarAgente}
                disabled={loading}
                className="flex-1 bg-[#10B981] hover:bg-[#10B981]/90"
                data-testid="guardar-agente-btn"
              >
                {loading ? 'Guardando...' : (agenteEditando ? 'Actualizar' : 'Crear Agente')}
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
    orange: 'border-orange-500 bg-orange-50'
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
            <p className="text-xs text-[#64748B]">
              {seguro.dias_restantes < 0 ? 'Vencido' : `${seguro.dias_restantes} días`}
            </p>
            <p className="text-xs text-[#64748B]">
              {new Date(seguro.vigencia_hasta).toLocaleDateString('es-AR')}
            </p>
          </div>
        </div>
        {seguro.agente_nombre && (
          <p className="text-xs text-[#10B981]">Agente: {seguro.agente_nombre}</p>
        )}
      </CardContent>
    </Card>
  );
}
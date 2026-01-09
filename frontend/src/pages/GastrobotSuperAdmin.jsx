import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Badge } from '@/components/ui/badge';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger } from '@/components/ui/dialog';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { toast } from 'sonner';
import api from '@/services/api';

export default function GastrobotSuperAdmin() {
  const navigate = useNavigate();
  const [loading, setLoading] = useState(true);
  const [stats, setStats] = useState({});
  const [tenants, setTenants] = useState([]);
  const [showNewTenant, setShowNewTenant] = useState(false);
  const [newTenant, setNewTenant] = useState({
    nombre_negocio: '',
    email: '',
    telefono: '',
    direccion: '',
    plan: 'basico',
    admin_username: '',
    admin_password: ''
  });

  useEffect(() => {
    const token = localStorage.getItem('gastrobot_super_token');
    if (!token) {
      navigate('/gastrobot');
      return;
    }
    verifyAndLoad();
  }, []);

  const verifyAndLoad = async () => {
    try {
      const token = localStorage.getItem('gastrobot_super_token');
      const verify = await api.get(`/gastrobot/super/verify?token=${token}`);
      
      if (!verify.data.valid) {
        localStorage.removeItem('gastrobot_super_token');
        navigate('/gastrobot');
        return;
      }
      
      await loadData();
    } catch (error) {
      navigate('/gastrobot');
    }
  };

  const loadData = async () => {
    try {
      const [statsRes, tenantsRes] = await Promise.all([
        api.get('/gastrobot/super/stats'),
        api.get('/gastrobot/tenants')
      ]);
      setStats(statsRes.data);
      setTenants(tenantsRes.data.tenants || []);
    } catch (error) {
      console.error('Error loading data:', error);
      toast.error('Error al cargar datos');
    } finally {
      setLoading(false);
    }
  };

  const createTenant = async () => {
    if (!newTenant.nombre_negocio || !newTenant.admin_username || !newTenant.admin_password) {
      toast.error('Completá los campos obligatorios');
      return;
    }
    
    try {
      await api.post('/gastrobot/tenants', newTenant);
      toast.success('Negocio creado exitosamente');
      setShowNewTenant(false);
      setNewTenant({
        nombre_negocio: '',
        email: '',
        telefono: '',
        direccion: '',
        plan: 'basico',
        admin_username: '',
        admin_password: ''
      });
      loadData();
    } catch (error) {
      toast.error('Error al crear negocio');
    }
  };

  const deleteTenant = async (tenantId) => {
    if (!confirm('¿Estás seguro de eliminar este negocio? Se borrarán todos sus datos.')) {
      return;
    }
    
    try {
      await api.delete(`/gastrobot/tenants/${tenantId}`);
      toast.success('Negocio eliminado');
      loadData();
    } catch (error) {
      toast.error('Error al eliminar negocio');
    }
  };

  const toggleTenantStatus = async (tenant) => {
    const newStatus = tenant.estado_suscripcion === 'activo' ? 'pausado' : 'activo';
    try {
      await api.put(`/gastrobot/tenants/${tenant.id}`, {
        estado_suscripcion: newStatus
      });
      toast.success(`Negocio ${newStatus === 'activo' ? 'activado' : 'pausado'}`);
      loadData();
    } catch (error) {
      toast.error('Error al actualizar estado');
    }
  };

  const logout = () => {
    localStorage.removeItem('gastrobot_super_token');
    navigate('/gastrobot');
  };

  const getPlanBadge = (plan) => {
    const colors = {
      basico: 'bg-gray-100 text-gray-800',
      pro: 'bg-blue-100 text-blue-800',
      enterprise: 'bg-purple-100 text-purple-800'
    };
    return <Badge className={colors[plan] || colors.basico}>{plan?.toUpperCase()}</Badge>;
  };

  const getStatusBadge = (status) => {
    const colors = {
      activo: 'bg-green-100 text-green-800',
      pausado: 'bg-yellow-100 text-yellow-800',
      cancelado: 'bg-red-100 text-red-800'
    };
    return <Badge className={colors[status] || colors.activo}>{status?.toUpperCase()}</Badge>;
  };

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-slate-900">
        <div className="text-center">
          <div className="text-6xl mb-4">🤖</div>
          <p className="text-white">Cargando GastroBot...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-slate-900">
      {/* Header */}
      <header className="bg-gradient-to-r from-emerald-600 to-teal-600 text-white py-4 px-6 shadow-lg">
        <div className="flex justify-between items-center max-w-7xl mx-auto">
          <div className="flex items-center gap-3">
            <span className="text-3xl">🤖</span>
            <div>
              <h1 className="text-2xl font-bold">GastroBot</h1>
              <p className="text-sm text-emerald-100">Super Admin Panel</p>
            </div>
          </div>
          <Button variant="ghost" className="text-white hover:bg-white/20" onClick={logout}>
            Cerrar Sesión
          </Button>
        </div>
      </header>

      <div className="max-w-7xl mx-auto p-6">
        {/* Stats Cards */}
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
          <Card className="bg-slate-800 border-slate-700">
            <CardContent className="p-4 text-center">
              <p className="text-3xl font-bold text-emerald-400">{stats.total_negocios || 0}</p>
              <p className="text-sm text-slate-400">Negocios Totales</p>
            </CardContent>
          </Card>
          <Card className="bg-slate-800 border-slate-700">
            <CardContent className="p-4 text-center">
              <p className="text-3xl font-bold text-green-400">{stats.negocios_activos || 0}</p>
              <p className="text-sm text-slate-400">Activos</p>
            </CardContent>
          </Card>
          <Card className="bg-slate-800 border-slate-700">
            <CardContent className="p-4 text-center">
              <p className="text-3xl font-bold text-blue-400">{stats.total_pedidos || 0}</p>
              <p className="text-sm text-slate-400">Pedidos Totales</p>
            </CardContent>
          </Card>
          <Card className="bg-slate-800 border-slate-700">
            <CardContent className="p-4 text-center">
              <p className="text-3xl font-bold text-yellow-400">{stats.pedidos_hoy || 0}</p>
              <p className="text-sm text-slate-400">Pedidos Hoy</p>
            </CardContent>
          </Card>
        </div>

        {/* Plan Distribution */}
        {stats.por_plan && (
          <Card className="bg-slate-800 border-slate-700 mb-6">
            <CardContent className="p-4">
              <h3 className="text-white font-bold mb-3">Distribución por Plan</h3>
              <div className="flex gap-6">
                <div className="flex items-center gap-2">
                  <Badge className="bg-gray-600">BÁSICO</Badge>
                  <span className="text-white">{stats.por_plan.basico || 0}</span>
                </div>
                <div className="flex items-center gap-2">
                  <Badge className="bg-blue-600">PRO</Badge>
                  <span className="text-white">{stats.por_plan.pro || 0}</span>
                </div>
                <div className="flex items-center gap-2">
                  <Badge className="bg-purple-600">ENTERPRISE</Badge>
                  <span className="text-white">{stats.por_plan.enterprise || 0}</span>
                </div>
              </div>
            </CardContent>
          </Card>
        )}

        {/* Tenants List */}
        <Card className="bg-slate-800 border-slate-700">
          <CardHeader>
            <CardTitle className="flex justify-between items-center text-white">
              <span>🏪 Negocios</span>
              <div className="flex gap-2">
                <Button onClick={loadData} variant="outline" size="sm" className="border-slate-600 text-slate-300">
                  🔄 Actualizar
                </Button>
                <Dialog open={showNewTenant} onOpenChange={setShowNewTenant}>
                  <DialogTrigger asChild>
                    <Button className="bg-emerald-600 hover:bg-emerald-700">
                      ➕ Nuevo Negocio
                    </Button>
                  </DialogTrigger>
                  <DialogContent className="bg-slate-800 border-slate-700">
                    <DialogHeader>
                      <DialogTitle className="text-white">Crear Nuevo Negocio</DialogTitle>
                    </DialogHeader>
                    <div className="space-y-4 mt-4">
                      <div>
                        <Label className="text-slate-300">Nombre del Negocio *</Label>
                        <Input
                          value={newTenant.nombre_negocio}
                          onChange={(e) => setNewTenant({...newTenant, nombre_negocio: e.target.value})}
                          placeholder="Ej: Pizzería Don Juan"
                          className="bg-slate-700 border-slate-600 text-white"
                        />
                      </div>
                      <div className="grid grid-cols-2 gap-4">
                        <div>
                          <Label className="text-slate-300">Email</Label>
                          <Input
                            type="email"
                            value={newTenant.email}
                            onChange={(e) => setNewTenant({...newTenant, email: e.target.value})}
                            className="bg-slate-700 border-slate-600 text-white"
                          />
                        </div>
                        <div>
                          <Label className="text-slate-300">Teléfono</Label>
                          <Input
                            value={newTenant.telefono}
                            onChange={(e) => setNewTenant({...newTenant, telefono: e.target.value})}
                            className="bg-slate-700 border-slate-600 text-white"
                          />
                        </div>
                      </div>
                      <div>
                        <Label className="text-slate-300">Dirección</Label>
                        <Input
                          value={newTenant.direccion}
                          onChange={(e) => setNewTenant({...newTenant, direccion: e.target.value})}
                          className="bg-slate-700 border-slate-600 text-white"
                        />
                      </div>
                      <div>
                        <Label className="text-slate-300">Plan</Label>
                        <Select value={newTenant.plan} onValueChange={(val) => setNewTenant({...newTenant, plan: val})}>
                          <SelectTrigger className="bg-slate-700 border-slate-600 text-white">
                            <SelectValue />
                          </SelectTrigger>
                          <SelectContent>
                            <SelectItem value="basico">Básico (1 bot)</SelectItem>
                            <SelectItem value="pro">Pro (5 bots)</SelectItem>
                            <SelectItem value="enterprise">Enterprise (ilimitado)</SelectItem>
                          </SelectContent>
                        </Select>
                      </div>
                      <div className="border-t border-slate-600 pt-4">
                        <p className="text-slate-400 text-sm mb-2">Credenciales de acceso del cliente:</p>
                        <div className="grid grid-cols-2 gap-4">
                          <div>
                            <Label className="text-slate-300">Usuario *</Label>
                            <Input
                              value={newTenant.admin_username}
                              onChange={(e) => setNewTenant({...newTenant, admin_username: e.target.value})}
                              placeholder="usuario_cliente"
                              className="bg-slate-700 border-slate-600 text-white"
                            />
                          </div>
                          <div>
                            <Label className="text-slate-300">Contraseña *</Label>
                            <Input
                              type="password"
                              value={newTenant.admin_password}
                              onChange={(e) => setNewTenant({...newTenant, admin_password: e.target.value})}
                              className="bg-slate-700 border-slate-600 text-white"
                            />
                          </div>
                        </div>
                      </div>
                      <Button onClick={createTenant} className="w-full bg-emerald-600 hover:bg-emerald-700">
                        Crear Negocio
                      </Button>
                    </div>
                  </DialogContent>
                </Dialog>
              </div>
            </CardTitle>
          </CardHeader>
          <CardContent>
            {tenants.length === 0 ? (
              <div className="text-center py-12 text-slate-400">
                <p className="text-4xl mb-4">🏪</p>
                <p>No hay negocios registrados</p>
                <p className="text-sm">Creá tu primer negocio haciendo click en "Nuevo Negocio"</p>
              </div>
            ) : (
              <div className="space-y-4">
                {tenants.map((tenant) => (
                  <Card key={tenant.id} className="bg-slate-700 border-slate-600">
                    <CardContent className="p-4">
                      <div className="flex justify-between items-start">
                        <div className="flex-1">
                          <div className="flex items-center gap-2 mb-2">
                            <h3 className="text-lg font-bold text-white">{tenant.nombre_negocio}</h3>
                            {getPlanBadge(tenant.plan)}
                            {getStatusBadge(tenant.estado_suscripcion)}
                            {tenant.whatsapp_connected && (
                              <Badge className="bg-green-600">📱 WhatsApp</Badge>
                            )}
                          </div>
                          <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
                            <div>
                              <p className="text-slate-400">ID</p>
                              <p className="text-white font-mono">{tenant.id}</p>
                            </div>
                            <div>
                              <p className="text-slate-400">Usuario</p>
                              <p className="text-white">{tenant.admin_username || '-'}</p>
                            </div>
                            <div>
                              <p className="text-slate-400">Pedidos Hoy</p>
                              <p className="text-white">{tenant.stats?.pedidos_hoy || 0}</p>
                            </div>
                            <div>
                              <p className="text-slate-400">Total Pedidos</p>
                              <p className="text-white">{tenant.stats?.total_pedidos || 0}</p>
                            </div>
                          </div>
                          <p className="text-slate-400 text-sm mt-2">
                            📍 {tenant.direccion || 'Sin dirección'} | 📧 {tenant.email || 'Sin email'}
                          </p>
                        </div>
                        <div className="flex flex-col gap-2 ml-4">
                          <Button 
                            size="sm" 
                            variant="outline" 
                            className="border-slate-500 text-slate-300"
                            onClick={() => navigate(`/gastrobot/tenant/${tenant.id}`)}
                          >
                            👁️ Ver Panel
                          </Button>
                          <Button 
                            size="sm" 
                            variant="outline"
                            className={tenant.estado_suscripcion === 'activo' 
                              ? 'border-yellow-500 text-yellow-400' 
                              : 'border-green-500 text-green-400'}
                            onClick={() => toggleTenantStatus(tenant)}
                          >
                            {tenant.estado_suscripcion === 'activo' ? '⏸️ Pausar' : '▶️ Activar'}
                          </Button>
                          <Button 
                            size="sm" 
                            variant="destructive"
                            onClick={() => deleteTenant(tenant.id)}
                          >
                            🗑️ Eliminar
                          </Button>
                        </div>
                      </div>
                    </CardContent>
                  </Card>
                ))}
              </div>
            )}
          </CardContent>
        </Card>

        {/* Pricing Info */}
        <Card className="bg-slate-800 border-slate-700 mt-6">
          <CardContent className="p-4">
            <h3 className="text-white font-bold mb-3">💰 Planes Disponibles</h3>
            <div className="grid md:grid-cols-3 gap-4">
              <div className="bg-slate-700 p-4 rounded-lg">
                <h4 className="font-bold text-gray-300">BÁSICO</h4>
                <ul className="text-sm text-slate-400 mt-2 space-y-1">
                  <li>• 1 bot WhatsApp</li>
                  <li>• Hasta 500 pedidos/mes</li>
                  <li>• Panel básico</li>
                </ul>
              </div>
              <div className="bg-slate-700 p-4 rounded-lg border-2 border-blue-500">
                <h4 className="font-bold text-blue-400">PRO</h4>
                <ul className="text-sm text-slate-400 mt-2 space-y-1">
                  <li>• Hasta 5 bots (sucursales)</li>
                  <li>• Pedidos ilimitados</li>
                  <li>• Analytics avanzado</li>
                </ul>
              </div>
              <div className="bg-slate-700 p-4 rounded-lg border-2 border-purple-500">
                <h4 className="font-bold text-purple-400">ENTERPRISE</h4>
                <ul className="text-sm text-slate-400 mt-2 space-y-1">
                  <li>• Bots ilimitados</li>
                  <li>• API personalizada</li>
                  <li>• Soporte prioritario</li>
                </ul>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}

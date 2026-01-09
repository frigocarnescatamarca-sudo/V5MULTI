import { useState, useEffect, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Badge } from '@/components/ui/badge';
import { Textarea } from '@/components/ui/textarea';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger } from '@/components/ui/dialog';
import { toast } from 'sonner';
import api from '@/services/api';

export default function GastrobotClientPanel() {
  const navigate = useNavigate();
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState('pedidos');
  const [tenant, setTenant] = useState(null);
  const [stats, setStats] = useState({});
  const [pedidos, setPedidos] = useState([]);
  const [menu, setMenu] = useState([]);
  const [config, setConfig] = useState({});
  const [conversations, setConversations] = useState([]);
  const [selectedChat, setSelectedChat] = useState(null);
  const [chatMessages, setChatMessages] = useState([]);

  // WhatsApp connection
  const [whatsappStatus, setWhatsappStatus] = useState({ status: 'disconnected' });
  const [qrData, setQrData] = useState(null);
  const [connectingWhatsApp, setConnectingWhatsApp] = useState(false);

  // New product dialog
  const [showNewProduct, setShowNewProduct] = useState(false);
  const [selectedCategory, setSelectedCategory] = useState('');
  const [newProduct, setNewProduct] = useState({ nombre: '', precio: '', descripcion: '', activo: true });

  const tenantId = localStorage.getItem('gastrobot_tenant_id');
  const tenantName = localStorage.getItem('gastrobot_tenant_name');

  useEffect(() => {
    const token = localStorage.getItem('gastrobot_tenant_token');
    if (!token || !tenantId) {
      navigate('/gastrobot');
      return;
    }
    verifyAndLoad();
  }, []);

  // Poll WhatsApp status when on config tab
  useEffect(() => {
    let interval;
    if (activeTab === 'whatsapp') {
      checkWhatsAppStatus();
      interval = setInterval(checkWhatsAppStatus, 3000);
    }
    return () => clearInterval(interval);
  }, [activeTab, tenantId]);

  const checkWhatsAppStatus = useCallback(async () => {
    if (!tenantId) return;
    try {
      const [statusRes, qrRes] = await Promise.all([
        api.get(`/gastrobot/tenant/${tenantId}/whatsapp/status`),
        api.get(`/gastrobot/tenant/${tenantId}/whatsapp/qr`)
      ]);
      setWhatsappStatus(statusRes.data);
      setQrData(qrRes.data);
      
      // Update tenant connection status
      if (statusRes.data.connected && tenant && !tenant.whatsapp_connected) {
        setTenant({ ...tenant, whatsapp_connected: true });
      }
    } catch (error) {
      console.error('Error checking WhatsApp status:', error);
    }
  }, [tenantId, tenant]);

  const verifyAndLoad = async () => {
    try {
      const token = localStorage.getItem('gastrobot_tenant_token');
      const verify = await api.get(`/gastrobot/tenant/verify?token=${token}`);
      
      if (!verify.data.valid) {
        localStorage.removeItem('gastrobot_tenant_token');
        navigate('/gastrobot');
        return;
      }
      
      setTenant(verify.data.tenant);
      await loadData();
    } catch (error) {
      navigate('/gastrobot');
    }
  };

  const loadData = async () => {
    try {
      const [statsRes, pedidosRes, menuRes, configRes] = await Promise.all([
        api.get(`/gastrobot/tenant/${tenantId}/stats`),
        api.get(`/gastrobot/tenant/${tenantId}/pedidos`),
        api.get(`/gastrobot/tenant/${tenantId}/menu`),
        api.get(`/gastrobot/tenant/${tenantId}/config`)
      ]);
      setStats(statsRes.data);
      setPedidos(pedidosRes.data.pedidos || []);
      setMenu(menuRes.data.menu || []);
      setConfig(configRes.data || {});
    } catch (error) {
      console.error('Error loading data:', error);
      toast.error('Error al cargar datos');
    } finally {
      setLoading(false);
    }
  };

  const loadConversations = async () => {
    try {
      const res = await api.get(`/gastrobot/tenant/${tenantId}/conversations`);
      setConversations(res.data.conversations || []);
    } catch (error) {
      console.error('Error loading conversations:', error);
    }
  };

  const loadChatMessages = async (phoneNumber) => {
    try {
      const res = await api.get(`/gastrobot/tenant/${tenantId}/chat/${phoneNumber}`);
      setChatMessages(res.data.messages || []);
      setSelectedChat(phoneNumber);
    } catch (error) {
      console.error('Error loading chat:', error);
    }
  };

  const updatePedidoEstado = async (numeroPedido, nuevoEstado) => {
    try {
      await api.put(`/gastrobot/tenant/${tenantId}/pedidos/${numeroPedido}/estado`, {
        estado: nuevoEstado
      });
      toast.success(`Pedido ${numeroPedido} actualizado a ${nuevoEstado}`);
      loadData();
    } catch (error) {
      toast.error('Error al actualizar pedido');
    }
  };

  const addProduct = async () => {
    if (!newProduct.nombre || !newProduct.precio || !selectedCategory) {
      toast.error('Completá nombre, precio y categoría');
      return;
    }

    try {
      await api.post(`/gastrobot/tenant/${tenantId}/menu/product`, {
        categoria: selectedCategory,
        producto: {
          ...newProduct,
          precio: parseInt(newProduct.precio)
        }
      });
      toast.success('Producto agregado');
      setShowNewProduct(false);
      setNewProduct({ nombre: '', precio: '', descripcion: '', activo: true });
      loadData();
    } catch (error) {
      toast.error('Error al agregar producto');
    }
  };

  const saveConfig = async () => {
    try {
      await api.put(`/gastrobot/tenant/${tenantId}/config`, config);
      toast.success('Configuración guardada');
    } catch (error) {
      toast.error('Error al guardar configuración');
    }
  };

  const logout = () => {
    localStorage.removeItem('gastrobot_tenant_token');
    localStorage.removeItem('gastrobot_tenant_id');
    localStorage.removeItem('gastrobot_tenant_name');
    navigate('/gastrobot');
  };

  const getEstadoBadge = (estado) => {
    const colors = {
      pendiente: 'bg-yellow-100 text-yellow-800',
      confirmado: 'bg-blue-100 text-blue-800',
      preparando: 'bg-purple-100 text-purple-800',
      listo: 'bg-green-100 text-green-800',
      en_camino: 'bg-cyan-100 text-cyan-800',
      entregado: 'bg-gray-100 text-gray-800',
      cancelado: 'bg-red-100 text-red-800'
    };
    return <Badge className={colors[estado] || 'bg-gray-100'}>{estado?.toUpperCase().replace('_', ' ')}</Badge>;
  };

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-slate-900">
        <div className="text-center">
          <div className="text-6xl mb-4">🤖</div>
          <p className="text-white">Cargando panel...</p>
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
              <h1 className="text-2xl font-bold">{tenantName || 'Mi Negocio'}</h1>
              <p className="text-sm text-emerald-100">Panel de Administración</p>
            </div>
          </div>
          <div className="flex items-center gap-4">
            <Badge className={tenant?.whatsapp_connected ? 'bg-green-500' : 'bg-red-500'}>
              {tenant?.whatsapp_connected ? '📱 WhatsApp Conectado' : '📱 Sin conexión'}
            </Badge>
            <Button variant="ghost" className="text-white hover:bg-white/20" onClick={logout}>
              Cerrar Sesión
            </Button>
          </div>
        </div>
      </header>

      <div className="max-w-7xl mx-auto p-6">
        {/* Stats */}
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
          <Card className="bg-slate-800 border-slate-700">
            <CardContent className="p-4 text-center">
              <p className="text-3xl font-bold text-yellow-400">{stats.pedidos_pendientes || 0}</p>
              <p className="text-sm text-slate-400">Pendientes</p>
            </CardContent>
          </Card>
          <Card className="bg-slate-800 border-slate-700">
            <CardContent className="p-4 text-center">
              <p className="text-3xl font-bold text-blue-400">{stats.pedidos_hoy || 0}</p>
              <p className="text-sm text-slate-400">Hoy</p>
            </CardContent>
          </Card>
          <Card className="bg-slate-800 border-slate-700">
            <CardContent className="p-4 text-center">
              <p className="text-3xl font-bold text-emerald-400">${(stats.ventas_hoy || 0).toLocaleString()}</p>
              <p className="text-sm text-slate-400">Ventas Hoy</p>
            </CardContent>
          </Card>
          <Card className="bg-slate-800 border-slate-700">
            <CardContent className="p-4 text-center">
              <p className="text-3xl font-bold text-purple-400">{stats.total_pedidos || 0}</p>
              <p className="text-sm text-slate-400">Total Histórico</p>
            </CardContent>
          </Card>
        </div>

        <Tabs value={activeTab} onValueChange={(val) => {
          setActiveTab(val);
          if (val === 'chat') loadConversations();
        }}>
          <TabsList className="bg-slate-800 mb-4">
            <TabsTrigger value="pedidos" className="data-[state=active]:bg-emerald-600">📋 Pedidos</TabsTrigger>
            <TabsTrigger value="menu" className="data-[state=active]:bg-emerald-600">🍽️ Menú</TabsTrigger>
            <TabsTrigger value="chat" className="data-[state=active]:bg-emerald-600">💬 Chat</TabsTrigger>
            <TabsTrigger value="config" className="data-[state=active]:bg-emerald-600">⚙️ Configuración</TabsTrigger>
          </TabsList>

          {/* PEDIDOS TAB */}
          <TabsContent value="pedidos">
            <Card className="bg-slate-800 border-slate-700">
              <CardHeader>
                <CardTitle className="flex justify-between items-center text-white">
                  <span>Pedidos</span>
                  <Button onClick={loadData} variant="outline" size="sm" className="border-slate-600 text-slate-300">
                    🔄 Actualizar
                  </Button>
                </CardTitle>
              </CardHeader>
              <CardContent>
                {pedidos.length === 0 ? (
                  <p className="text-center text-slate-400 py-8">No hay pedidos</p>
                ) : (
                  <div className="space-y-4">
                    {pedidos.map((pedido) => (
                      <Card key={pedido.numero_pedido} className="bg-slate-700 border-slate-600 border-l-4 border-l-emerald-500">
                        <CardContent className="p-4">
                          <div className="flex justify-between items-start">
                            <div className="flex-1">
                              <div className="flex items-center gap-2 mb-2">
                                <span className="font-bold text-lg text-white">#{pedido.numero_pedido}</span>
                                {getEstadoBadge(pedido.estado)}
                                <Badge variant="outline" className="border-slate-500 text-slate-300">
                                  {pedido.tipo_entrega === 'delivery' ? '🛵 Delivery' : '🏪 Retiro'}
                                </Badge>
                              </div>
                              <p className="text-slate-300">👤 {pedido.nombre}</p>
                              <p className="text-slate-400 text-sm">📱 {pedido.whatsapp_contact || pedido.telefono}</p>
                              {pedido.tipo_entrega === 'delivery' && (
                                <p className="text-slate-400 text-sm">📍 {pedido.direccion}</p>
                              )}
                              <div className="mt-2">
                                <p className="text-slate-400 text-sm">Pedido:</p>
                                <p className="text-white">{pedido.items_formatted || pedido.items}</p>
                              </div>
                              <p className="mt-2 font-bold text-lg text-emerald-400">
                                Total: ${pedido.total?.toLocaleString()}
                              </p>
                              <p className="text-xs text-slate-500 mt-1">
                                {new Date(pedido.created_at).toLocaleString('es-AR')}
                              </p>
                            </div>
                            <div className="flex flex-col gap-2 ml-4">
                              {pedido.estado === 'pendiente' && (
                                <>
                                  <Button size="sm" className="bg-green-600 hover:bg-green-700" 
                                    onClick={() => updatePedidoEstado(pedido.numero_pedido, 'confirmado')}>
                                    ✅ Confirmar
                                  </Button>
                                  <Button size="sm" variant="destructive"
                                    onClick={() => updatePedidoEstado(pedido.numero_pedido, 'cancelado')}>
                                    ❌ Rechazar
                                  </Button>
                                </>
                              )}
                              {pedido.estado === 'confirmado' && (
                                <Button size="sm" className="bg-purple-600 hover:bg-purple-700"
                                  onClick={() => updatePedidoEstado(pedido.numero_pedido, 'listo')}>
                                  ✅ Listo
                                </Button>
                              )}
                              {pedido.estado === 'listo' && pedido.tipo_entrega === 'delivery' && (
                                <Button size="sm" className="bg-cyan-600 hover:bg-cyan-700"
                                  onClick={() => updatePedidoEstado(pedido.numero_pedido, 'en_camino')}>
                                  🛵 En Camino
                                </Button>
                              )}
                              {(pedido.estado === 'listo' || pedido.estado === 'en_camino') && (
                                <Button size="sm" className="bg-gray-600 hover:bg-gray-700"
                                  onClick={() => updatePedidoEstado(pedido.numero_pedido, 'entregado')}>
                                  📦 Entregado
                                </Button>
                              )}
                            </div>
                          </div>
                        </CardContent>
                      </Card>
                    ))}
                  </div>
                )}
              </CardContent>
            </Card>
          </TabsContent>

          {/* MENU TAB */}
          <TabsContent value="menu">
            <Card className="bg-slate-800 border-slate-700">
              <CardHeader>
                <CardTitle className="flex justify-between items-center text-white">
                  <span>Menú</span>
                  <Dialog open={showNewProduct} onOpenChange={setShowNewProduct}>
                    <DialogTrigger asChild>
                      <Button className="bg-emerald-600 hover:bg-emerald-700">➕ Agregar Producto</Button>
                    </DialogTrigger>
                    <DialogContent className="bg-slate-800 border-slate-700">
                      <DialogHeader>
                        <DialogTitle className="text-white">Agregar Producto</DialogTitle>
                      </DialogHeader>
                      <div className="space-y-4 mt-4">
                        <div>
                          <Label className="text-slate-300">Categoría</Label>
                          <select 
                            value={selectedCategory}
                            onChange={(e) => setSelectedCategory(e.target.value)}
                            className="w-full bg-slate-700 border border-slate-600 text-white rounded-md p-2"
                          >
                            <option value="">Seleccionar...</option>
                            {menu.map((cat) => (
                              <option key={cat.categoria} value={cat.categoria}>
                                {cat.emoji} {cat.categoria}
                              </option>
                            ))}
                          </select>
                        </div>
                        <div>
                          <Label className="text-slate-300">Nombre</Label>
                          <Input
                            value={newProduct.nombre}
                            onChange={(e) => setNewProduct({...newProduct, nombre: e.target.value})}
                            className="bg-slate-700 border-slate-600 text-white"
                          />
                        </div>
                        <div>
                          <Label className="text-slate-300">Precio</Label>
                          <Input
                            type="number"
                            value={newProduct.precio}
                            onChange={(e) => setNewProduct({...newProduct, precio: e.target.value})}
                            className="bg-slate-700 border-slate-600 text-white"
                          />
                        </div>
                        <div>
                          <Label className="text-slate-300">Descripción (opcional)</Label>
                          <Input
                            value={newProduct.descripcion}
                            onChange={(e) => setNewProduct({...newProduct, descripcion: e.target.value})}
                            className="bg-slate-700 border-slate-600 text-white"
                          />
                        </div>
                        <Button onClick={addProduct} className="w-full bg-emerald-600 hover:bg-emerald-700">
                          Agregar
                        </Button>
                      </div>
                    </DialogContent>
                  </Dialog>
                </CardTitle>
              </CardHeader>
              <CardContent>
                {menu.length === 0 ? (
                  <p className="text-center text-slate-400 py-8">
                    No hay categorías. Agregá productos para comenzar.
                  </p>
                ) : (
                  <div className="space-y-6">
                    {menu.map((categoria) => (
                      <div key={categoria.categoria} className="bg-slate-700 rounded-lg p-4">
                        <h3 className="text-lg font-bold text-white mb-3">
                          {categoria.emoji} {categoria.categoria}
                        </h3>
                        {categoria.productos?.length === 0 ? (
                          <p className="text-slate-400 text-sm">Sin productos</p>
                        ) : (
                          <div className="space-y-2">
                            {categoria.productos?.map((prod, idx) => (
                              <div key={idx} className="flex justify-between items-center bg-slate-600 p-3 rounded">
                                <div>
                                  <span className="text-white font-medium">{prod.nombre}</span>
                                  {prod.descripcion && (
                                    <span className="text-slate-400 text-sm ml-2">- {prod.descripcion}</span>
                                  )}
                                </div>
                                <div className="flex items-center gap-2">
                                  <span className="font-bold text-emerald-400">${prod.precio?.toLocaleString()}</span>
                                  <Badge className={prod.activo ? 'bg-green-600' : 'bg-gray-600'}>
                                    {prod.activo ? 'Activo' : 'Inactivo'}
                                  </Badge>
                                </div>
                              </div>
                            ))}
                          </div>
                        )}
                      </div>
                    ))}
                  </div>
                )}
              </CardContent>
            </Card>
          </TabsContent>

          {/* CHAT TAB */}
          <TabsContent value="chat">
            <div className="grid md:grid-cols-3 gap-4">
              <Card className="bg-slate-800 border-slate-700 md:col-span-1">
                <CardHeader>
                  <CardTitle className="text-white text-lg flex justify-between items-center">
                    <span>Conversaciones</span>
                    <Button onClick={loadConversations} variant="outline" size="sm" className="border-slate-600 text-slate-300">
                      🔄
                    </Button>
                  </CardTitle>
                </CardHeader>
                <CardContent className="p-0">
                  <div className="max-h-[400px] overflow-y-auto">
                    {conversations.length === 0 ? (
                      <p className="text-center text-slate-400 py-8">Sin conversaciones</p>
                    ) : (
                      conversations.map((conv) => (
                        <div
                          key={conv.phone_number}
                          onClick={() => loadChatMessages(conv.phone_number)}
                          className={`p-3 border-b border-slate-700 cursor-pointer hover:bg-slate-700 ${
                            selectedChat === conv.phone_number ? 'bg-slate-700' : ''
                          }`}
                        >
                          <div className="flex justify-between">
                            <span className="text-white font-medium">{conv.push_name || 'Cliente'}</span>
                            <span className="text-xs text-slate-400">{conv.message_count} msgs</span>
                          </div>
                          <p className="text-slate-400 text-sm truncate">{conv.last_message}</p>
                        </div>
                      ))
                    )}
                  </div>
                </CardContent>
              </Card>

              <Card className="bg-slate-800 border-slate-700 md:col-span-2">
                <CardHeader>
                  <CardTitle className="text-white text-lg">
                    {selectedChat ? `Chat: ${selectedChat}` : 'Seleccioná una conversación'}
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  {!selectedChat ? (
                    <p className="text-slate-400 text-center py-8">
                      Seleccioná una conversación para ver los mensajes
                    </p>
                  ) : (
                    <div className="space-y-3 max-h-[400px] overflow-y-auto">
                      {chatMessages.map((msg, idx) => (
                        <div
                          key={idx}
                          className={`p-3 rounded-lg max-w-[80%] ${
                            msg.role === 'assistant'
                              ? 'bg-emerald-900/50 ml-auto'
                              : 'bg-slate-700'
                          }`}
                        >
                          <p className="text-xs text-slate-400 mb-1">
                            {msg.role === 'assistant' ? '🤖 Bot' : `👤 ${msg.push_name || 'Cliente'}`}
                          </p>
                          <p className="text-white text-sm whitespace-pre-wrap">{msg.message}</p>
                        </div>
                      ))}
                    </div>
                  )}
                </CardContent>
              </Card>
            </div>
          </TabsContent>

          {/* CONFIG TAB */}
          <TabsContent value="config">
            <Card className="bg-slate-800 border-slate-700">
              <CardHeader>
                <CardTitle className="text-white">Configuración del Bot</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  <div>
                    <Label className="text-slate-300">Mensaje de Bienvenida</Label>
                    <Textarea
                      value={config.mensaje_bienvenida || ''}
                      onChange={(e) => setConfig({...config, mensaje_bienvenida: e.target.value})}
                      rows={4}
                      className="bg-slate-700 border-slate-600 text-white"
                    />
                  </div>
                  <div className="grid grid-cols-2 gap-4">
                    <div>
                      <Label className="text-slate-300">Teléfonos Admin (notificaciones)</Label>
                      <Input
                        value={(config.admin_phones || []).join(', ')}
                        onChange={(e) => setConfig({
                          ...config, 
                          admin_phones: e.target.value.split(',').map(p => p.trim()).filter(Boolean)
                        })}
                        placeholder="3834111111, 3834222222"
                        className="bg-slate-700 border-slate-600 text-white"
                      />
                    </div>
                    <div>
                      <Label className="text-slate-300">Teléfonos Delivery</Label>
                      <Input
                        value={(config.delivery_phones || []).join(', ')}
                        onChange={(e) => setConfig({
                          ...config,
                          delivery_phones: e.target.value.split(',').map(p => p.trim()).filter(Boolean)
                        })}
                        placeholder="3834333333"
                        className="bg-slate-700 border-slate-600 text-white"
                      />
                    </div>
                  </div>
                  <div className="flex items-center gap-4">
                    <Label className="text-slate-300">Bot Activo</Label>
                    <input
                      type="checkbox"
                      checked={config.bot_activo ?? true}
                      onChange={(e) => setConfig({...config, bot_activo: e.target.checked})}
                      className="w-5 h-5"
                    />
                  </div>
                  <Button onClick={saveConfig} className="bg-emerald-600 hover:bg-emerald-700">
                    💾 Guardar Configuración
                  </Button>
                </div>
              </CardContent>
            </Card>
          </TabsContent>
        </Tabs>
      </div>
    </div>
  );
}

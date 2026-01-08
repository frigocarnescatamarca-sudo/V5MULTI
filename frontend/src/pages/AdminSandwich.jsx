import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Badge } from '@/components/ui/badge';
import { Textarea } from '@/components/ui/textarea';
import { toast } from 'sonner';
import api from '@/services/api';

export default function AdminSandwich() {
  const navigate = useNavigate();
  const [activeTab, setActiveTab] = useState('pedidos');
  const [pedidos, setPedidos] = useState([]);
  const [menu, setMenu] = useState([]);
  const [config, setConfig] = useState({});
  const [stats, setStats] = useState({});
  const [whatsappStatus, setWhatsappStatus] = useState({ connected: false });
  const [qrCode, setQrCode] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const token = localStorage.getItem('admin_token');
    if (!token) {
      navigate('/admin-selector');
      return;
    }
    loadData();
    const interval = setInterval(loadWhatsAppStatus, 5000);
    return () => clearInterval(interval);
  }, []);

  const loadData = async () => {
    try {
      const [pedidosRes, menuRes, configRes, statsRes] = await Promise.all([
        api.get('/sandwich/pedidos'),
        api.get('/sandwich/menu'),
        api.get('/sandwich/whatsapp/config'),
        api.get('/sandwich/estadisticas')
      ]);
      setPedidos(pedidosRes.data.pedidos || []);
      setMenu(menuRes.data.menu || []);
      setConfig(configRes.data || {});
      setStats(statsRes.data || {});
      await loadWhatsAppStatus();
    } catch (error) {
      console.error('Error loading data:', error);
    } finally {
      setLoading(false);
    }
  };

  const loadWhatsAppStatus = async () => {
    try {
      const statusRes = await api.get('/sandwich/whatsapp/status');
      setWhatsappStatus(statusRes.data);
      if (statusRes.data.status === 'awaiting_qr') {
        const qrRes = await api.get('/sandwich/whatsapp/qr');
        setQrCode(qrRes.data.qr_data_url);
      } else {
        setQrCode(null);
      }
    } catch (error) {
      console.error('Error loading WhatsApp status:', error);
    }
  };

  const connectWhatsApp = async () => {
    try {
      await api.post('/sandwich/whatsapp/connect');
      toast.success('Conectando WhatsApp...');
      setTimeout(loadWhatsAppStatus, 2000);
    } catch (error) {
      toast.error('Error al conectar');
    }
  };

  const disconnectWhatsApp = async () => {
    try {
      await api.post('/sandwich/whatsapp/disconnect');
      toast.info('WhatsApp desconectado');
      setWhatsappStatus({ connected: false });
      setQrCode(null);
    } catch (error) {
      toast.error('Error al desconectar');
    }
  };

  const updatePedidoEstado = async (numeroPedido, nuevoEstado) => {
    try {
      await api.put(`/sandwich/pedidos/${numeroPedido}/estado`, { estado: nuevoEstado });
      toast.success(`Pedido ${numeroPedido} actualizado a ${nuevoEstado}`);
      loadData();
    } catch (error) {
      toast.error('Error al actualizar pedido');
    }
  };

  const saveConfig = async () => {
    try {
      await api.post('/sandwich/whatsapp/config', config);
      toast.success('Configuración guardada');
    } catch (error) {
      toast.error('Error al guardar');
    }
  };

  const getEstadoBadge = (estado) => {
    const colors = {
      pendiente: 'bg-yellow-100 text-yellow-800',
      confirmado: 'bg-blue-100 text-blue-800',
      preparando: 'bg-purple-100 text-purple-800',
      listo: 'bg-green-100 text-green-800',
      entregado: 'bg-gray-100 text-gray-800',
      cancelado: 'bg-red-100 text-red-800'
    };
    return <Badge className={colors[estado] || 'bg-gray-100'}>{estado?.toUpperCase()}</Badge>;
  };

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-amber-50">
        <div className="text-center">
          <div className="text-6xl mb-4">🥪</div>
          <p className="text-gray-600">Cargando...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-amber-50">
      {/* Header */}
      <header className="bg-gradient-to-r from-amber-500 to-orange-500 text-white py-4 px-6 shadow-lg">
        <div className="flex justify-between items-center max-w-7xl mx-auto">
          <div className="flex items-center gap-3">
            <span className="text-3xl">🍔</span>
            <h1 className="text-2xl font-bold">Modo Cocina - Panel Admin</h1>
          </div>
          <div className="flex items-center gap-4">
            <div className="text-sm">
              <span className="opacity-75">WhatsApp:</span>
              <Badge className={`ml-2 ${whatsappStatus.connected ? 'bg-green-500' : 'bg-red-500'}`}>
                {whatsappStatus.connected ? '🟢 Conectado' : '🔴 Desconectado'}
              </Badge>
            </div>
            <Button variant="ghost" className="text-white hover:bg-white/20" onClick={() => navigate('/admin-selector')}>
              ← Volver
            </Button>
          </div>
        </div>
      </header>

      {/* Stats Cards */}
      <div className="max-w-7xl mx-auto p-6">
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
          <Card className="bg-white">
            <CardContent className="p-4 text-center">
              <p className="text-3xl font-bold text-amber-600">{stats.pedidos_pendientes || 0}</p>
              <p className="text-sm text-gray-600">Pendientes</p>
            </CardContent>
          </Card>
          <Card className="bg-white">
            <CardContent className="p-4 text-center">
              <p className="text-3xl font-bold text-blue-600">{stats.pedidos_confirmados || 0}</p>
              <p className="text-sm text-gray-600">Confirmados</p>
            </CardContent>
          </Card>
          <Card className="bg-white">
            <CardContent className="p-4 text-center">
              <p className="text-3xl font-bold text-purple-600">{stats.pedidos_hoy || 0}</p>
              <p className="text-sm text-gray-600">Pedidos Hoy</p>
            </CardContent>
          </Card>
          <Card className="bg-white">
            <CardContent className="p-4 text-center">
              <p className="text-3xl font-bold text-green-600">${(stats.total_ventas || 0).toLocaleString()}</p>
              <p className="text-sm text-gray-600">Total Ventas</p>
            </CardContent>
          </Card>
        </div>

        <Tabs value={activeTab} onValueChange={setActiveTab}>
          <TabsList className="bg-white mb-4">
            <TabsTrigger value="pedidos">📋 Pedidos</TabsTrigger>
            <TabsTrigger value="menu">🍽️ Menú</TabsTrigger>
            <TabsTrigger value="whatsapp">💬 WhatsApp Bot</TabsTrigger>
            <TabsTrigger value="config">⚙️ Configuración</TabsTrigger>
          </TabsList>

          {/* PEDIDOS TAB */}
          <TabsContent value="pedidos">
            <Card>
              <CardHeader>
                <CardTitle className="flex justify-between items-center">
                  <span>Pedidos</span>
                  <Button onClick={loadData} variant="outline" size="sm">🔄 Actualizar</Button>
                </CardTitle>
              </CardHeader>
              <CardContent>
                {pedidos.length === 0 ? (
                  <p className="text-center text-gray-500 py-8">No hay pedidos</p>
                ) : (
                  <div className="space-y-4">
                    {pedidos.map((pedido) => (
                      <Card key={pedido.numero_pedido} className="border-l-4 border-l-amber-500">
                        <CardContent className="p-4">
                          <div className="flex justify-between items-start">
                            <div className="flex-1">
                              <div className="flex items-center gap-2 mb-2">
                                <span className="font-bold text-lg">#{pedido.numero_pedido}</span>
                                {getEstadoBadge(pedido.estado)}
                                <Badge variant="outline">
                                  {pedido.tipo_entrega === 'delivery' ? '🛵 Delivery' : '🏪 Retiro'}
                                </Badge>
                                {pedido.has_location && (
                                  <Badge className="bg-blue-100 text-blue-800">📍 Ubicación</Badge>
                                )}
                              </div>
                              <p className="text-gray-600">👤 {pedido.nombre}</p>
                              <p className="text-gray-600">📱 LID: {pedido.telefono}</p>
                              {pedido.whatsapp_contact && (
                                <p className="text-green-600 font-medium">📞 WhatsApp: {pedido.whatsapp_contact}</p>
                              )}
                              {pedido.tipo_entrega === 'delivery' && (
                                <>
                                  <p className="text-gray-600">📍 {pedido.direccion}</p>
                                  {pedido.has_location && pedido.location && (
                                    <a 
                                      href={`https://maps.google.com/?q=${pedido.location.latitude},${pedido.location.longitude}`}
                                      target="_blank"
                                      rel="noopener noreferrer"
                                      className="text-blue-500 hover:underline text-sm"
                                    >
                                      🗺️ Ver en Google Maps
                                    </a>
                                  )}
                                </>
                              )}
                              {pedido.modificaciones && pedido.modificaciones.toLowerCase() !== 'ninguna' && (
                                <p className="text-orange-600 mt-1">✏️ Modificaciones: {pedido.modificaciones}</p>
                              )}
                              <div className="mt-2 text-sm">
                                <p className="font-medium">Pedido:</p>
                                <p className="whitespace-pre-line text-gray-700">{pedido.items_formatted || pedido.items}</p>
                              </div>
                              <p className="mt-2 font-bold text-lg text-amber-600">Total: ${pedido.total?.toLocaleString()}</p>
                              <p className="text-xs text-gray-400 mt-1">
                                {new Date(pedido.created_at).toLocaleString('es-AR')}
                              </p>
                            </div>
                            <div className="flex flex-col gap-2 ml-4">
                              {pedido.estado === 'pendiente' && (
                                <>
                                  <Button size="sm" className="bg-green-500 hover:bg-green-600" onClick={() => updatePedidoEstado(pedido.numero_pedido, 'confirmado')}>
                                    ✅ Confirmar
                                  </Button>
                                  <Button size="sm" variant="destructive" onClick={() => updatePedidoEstado(pedido.numero_pedido, 'cancelado')}>
                                    ❌ Rechazar
                                  </Button>
                                </>
                              )}
                              {pedido.estado === 'confirmado' && (
                                <Button size="sm" className="bg-purple-500 hover:bg-purple-600" onClick={() => updatePedidoEstado(pedido.numero_pedido, 'preparando')}>
                                  👨‍🍳 Preparando
                                </Button>
                              )}
                              {pedido.estado === 'preparando' && (
                                <Button size="sm" className="bg-blue-500 hover:bg-blue-600" onClick={() => updatePedidoEstado(pedido.numero_pedido, 'listo')}>
                                  ✅ Listo
                                </Button>
                              )}
                              {pedido.estado === 'listo' && pedido.tipo_entrega === 'delivery' && (
                                <Button size="sm" className="bg-cyan-500 hover:bg-cyan-600" onClick={() => updatePedidoEstado(pedido.numero_pedido, 'en_camino')}>
                                  🛵 En Camino
                                </Button>
                              )}
                              {(pedido.estado === 'listo' || pedido.estado === 'en_camino') && (
                                <Button size="sm" className="bg-gray-500 hover:bg-gray-600" onClick={() => updatePedidoEstado(pedido.numero_pedido, 'entregado')}>
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
            <Card>
              <CardHeader>
                <CardTitle>Menú</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-6">
                  {menu.map((categoria) => (
                    <div key={categoria.categoria} className="border rounded-lg p-4">
                      <h3 className="text-lg font-bold mb-3">
                        {categoria.emoji} {categoria.categoria}
                      </h3>
                      <div className="grid gap-2">
                        {categoria.productos?.map((producto) => (
                          <div key={producto.nombre} className="flex justify-between items-center p-2 bg-gray-50 rounded">
                            <div>
                              <span className="font-medium">{producto.nombre}</span>
                              {producto.descripcion && (
                                <span className="text-sm text-gray-500 ml-2">- {producto.descripcion}</span>
                              )}
                            </div>
                            <div className="flex items-center gap-2">
                              <span className="font-bold text-amber-600">${producto.precio?.toLocaleString()}</span>
                              <Badge variant={producto.activo ? 'default' : 'secondary'}>
                                {producto.activo ? 'Activo' : 'Inactivo'}
                              </Badge>
                            </div>
                          </div>
                        ))}
                      </div>
                    </div>
                  ))}
                </div>
                <p className="text-sm text-gray-500 mt-4">
                  💡 Para editar el menú, usá los comandos en la base de datos o contactá al desarrollador.
                </p>
              </CardContent>
            </Card>
          </TabsContent>

          {/* WHATSAPP TAB */}
          <TabsContent value="whatsapp">
            <Card>
              <CardHeader>
                <CardTitle>🤖 Cocibot - WhatsApp Bot</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-6">
                  {/* Connection Status */}
                  <div className="p-4 rounded-lg bg-gray-50">
                    <h3 className="font-bold mb-2">Estado de Conexión</h3>
                    <div className="flex items-center gap-4">
                      <Badge className={whatsappStatus.connected ? 'bg-green-500' : 'bg-red-500'}>
                        {whatsappStatus.connected ? '🟢 Conectado' : '🔴 Desconectado'}
                      </Badge>
                      {whatsappStatus.user && (
                        <span className="text-sm text-gray-600">
                          {whatsappStatus.user.name || whatsappStatus.user.id}
                        </span>
                      )}
                    </div>
                    <div className="flex gap-2 mt-4">
                      {!whatsappStatus.connected ? (
                        <Button onClick={connectWhatsApp} className="bg-green-500 hover:bg-green-600">
                          Conectar WhatsApp
                        </Button>
                      ) : (
                        <Button onClick={disconnectWhatsApp} variant="destructive">
                          Desconectar
                        </Button>
                      )}
                    </div>
                  </div>

                  {/* QR Code */}
                  {qrCode && (
                    <div className="p-4 rounded-lg bg-white border text-center">
                      <h3 className="font-bold mb-4">Escaneá el código QR con WhatsApp</h3>
                      <img src={qrCode} alt="QR Code" className="mx-auto max-w-xs" />
                      <p className="text-sm text-gray-500 mt-4">
                        Abrí WhatsApp → Menú → Dispositivos vinculados → Vincular dispositivo
                      </p>
                    </div>
                  )}

                  {/* Admin Commands */}
                  <div className="p-4 rounded-lg bg-amber-50">
                    <h3 className="font-bold mb-2">📋 Comandos del Admin (vía WhatsApp)</h3>
                    <div className="grid md:grid-cols-2 gap-4">
                      <div>
                        <h4 className="font-medium text-sm text-gray-600 mb-1">Gestión de Pedidos</h4>
                        <ul className="text-sm space-y-1">
                          <li><code className="bg-gray-200 px-1">PEDIDOS</code> - Ver pedidos pendientes</li>
                          <li><code className="bg-gray-200 px-1">PEDIDO #X</code> - Ver detalles del pedido</li>
                          <li><code className="bg-gray-200 px-1">CONFIRMAR X</code> - Confirmar un pedido</li>
                          <li><code className="bg-gray-200 px-1">RECHAZAR X</code> - Rechazar un pedido</li>
                          <li><code className="bg-gray-200 px-1">LISTO X</code> - Marcar pedido como listo</li>
                          <li><code className="bg-gray-200 px-1">ENCAMINO X</code> - Marcar en camino</li>
                          <li><code className="bg-gray-200 px-1">ENTREGADO X</code> - Marcar entregado</li>
                        </ul>
                      </div>
                      <div>
                        <h4 className="font-medium text-sm text-gray-600 mb-1">Atención al Cliente</h4>
                        <ul className="text-sm space-y-1">
                          <li><code className="bg-gray-200 px-1">ESTADO X [resp]</code> - Responder consulta de cliente</li>
                          <li><code className="bg-gray-200 px-1">PAUSAR TEL</code> - Atender cliente manualmente</li>
                          <li><code className="bg-gray-200 px-1">REANUDAR TEL</code> - Reactivar bot para cliente</li>
                          <li><code className="bg-gray-200 px-1">DELIVERY TEL</code> - Agregar número de delivery</li>
                        </ul>
                      </div>
                    </div>
                  </div>

                  {/* Delivery Commands */}
                  <div className="p-4 rounded-lg bg-blue-50">
                    <h3 className="font-bold mb-2">🛵 Comandos del Delivery (vía WhatsApp)</h3>
                    <ul className="text-sm space-y-1">
                      <li><code className="bg-gray-200 px-1">PEDIDO #X</code> - Ver detalles del pedido (dirección, WhatsApp, ubicación)</li>
                      <li><code className="bg-gray-200 px-1">ENCAMINO X</code> - Marcar pedido en camino (notifica al cliente)</li>
                      <li><code className="bg-gray-200 px-1">ENTREGADO X</code> - Marcar pedido entregado</li>
                    </ul>
                    <p className="text-xs text-gray-500 mt-2">
                      💡 Para agregar un delivery, el admin debe enviar: <code className="bg-gray-200 px-1">DELIVERY 3834123456</code>
                    </p>
                  </div>

                  {/* Client Features */}
                  <div className="p-4 rounded-lg bg-green-50">
                    <h3 className="font-bold mb-2">👤 Funciones del Cliente</h3>
                    <ul className="text-sm space-y-1">
                      <li>📍 <strong>Compartir ubicación:</strong> El cliente puede enviar su ubicación para facilitar la entrega</li>
                      <li>❓ <strong>Consultar estado:</strong> "¿Cómo va mi pedido?" - Se consulta al admin y se responde</li>
                      <li>👤 <strong>Hablar con humano:</strong> "Quiero hablar con alguien" - Pausa el bot 2 horas</li>
                      <li>❌ <strong>Cancelar pedido:</strong> "Cancelar" - Cancela el pedido activo</li>
                    </ul>
                  </div>

                  {/* Registered Deliveries */}
                  {config.delivery_phones && config.delivery_phones.length > 0 && (
                    <div className="p-4 rounded-lg bg-gray-50">
                      <h3 className="font-bold mb-2">🛵 Deliveries Registrados</h3>
                      <div className="flex flex-wrap gap-2">
                        {config.delivery_phones.map((phone, idx) => (
                          <Badge key={idx} variant="outline">{phone}</Badge>
                        ))}
                      </div>
                    </div>
                  )}
                </div>
              </CardContent>
            </Card>
          </TabsContent>

          {/* CONFIG TAB */}
          <TabsContent value="config">
            <Card>
              <CardHeader>
                <CardTitle>Configuración del Bot</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  <div>
                    <Label>Nombre del Negocio</Label>
                    <Input
                      value={config.nombre_negocio || ''}
                      onChange={(e) => setConfig({...config, nombre_negocio: e.target.value})}
                      placeholder="Sandwichería"
                    />
                  </div>
                  <div>
                    <Label>Mensaje de Bienvenida</Label>
                    <Textarea
                      value={config.mensaje_bienvenida || ''}
                      onChange={(e) => setConfig({...config, mensaje_bienvenida: e.target.value})}
                      rows={4}
                    />
                  </div>
                  <div className="grid grid-cols-2 gap-4">
                    <div>
                      <Label>Horario Apertura</Label>
                      <Input
                        value={config.horario_apertura || ''}
                        onChange={(e) => setConfig({...config, horario_apertura: e.target.value})}
                        placeholder="10:00"
                      />
                    </div>
                    <div>
                      <Label>Horario Cierre</Label>
                      <Input
                        value={config.horario_cierre || ''}
                        onChange={(e) => setConfig({...config, horario_cierre: e.target.value})}
                        placeholder="22:00"
                      />
                    </div>
                  </div>
                  <div className="grid grid-cols-2 gap-4">
                    <div>
                      <Label>Costo Delivery ($)</Label>
                      <Input
                        type="number"
                        value={config.costo_delivery || ''}
                        onChange={(e) => setConfig({...config, costo_delivery: parseInt(e.target.value)})}
                        placeholder="500"
                      />
                    </div>
                    <div>
                      <Label>Pedido Mínimo Delivery ($)</Label>
                      <Input
                        type="number"
                        value={config.pedido_minimo_delivery || ''}
                        onChange={(e) => setConfig({...config, pedido_minimo_delivery: parseInt(e.target.value)})}
                        placeholder="2000"
                      />
                    </div>
                  </div>
                  <div>
                    <Label>Dirección del Local</Label>
                    <Input
                      value={config.direccion_local || ''}
                      onChange={(e) => setConfig({...config, direccion_local: e.target.value})}
                      placeholder="Av. Principal 123"
                    />
                  </div>
                  <div>
                    <Label>Tiempo de Preparación</Label>
                    <Input
                      value={config.tiempo_preparacion || ''}
                      onChange={(e) => setConfig({...config, tiempo_preparacion: e.target.value})}
                      placeholder="20-30 minutos"
                    />
                  </div>
                  <div>
                    <Label>Número de Admin (para notificaciones)</Label>
                    <Input
                      value={config.admin_phone || ''}
                      onChange={(e) => setConfig({...config, admin_phone: e.target.value})}
                      placeholder="5491112345678"
                    />
                  </div>
                  <Button onClick={saveConfig} className="bg-amber-500 hover:bg-amber-600">
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

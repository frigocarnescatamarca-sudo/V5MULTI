import { useState, useEffect, useRef } from 'react';
import { MessageCircle, QrCode, Settings, Send, Pause, Play, RefreshCw, Power, PowerOff, Bot, Save, Loader2, Phone, User, Check, CheckCheck, BookOpen, Command, Zap, Users, Clock, MessageSquare } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Textarea } from '@/components/ui/textarea';
import { Switch } from '@/components/ui/switch';
import { whatsappAPI } from '@/services/api';
import { toast } from 'sonner';

export default function WhatsAppBotPanel() {
  const [activeTab, setActiveTab] = useState('conexion');
  const [loading, setLoading] = useState(false);
  
  // Connection state
  const [connectionStatus, setConnectionStatus] = useState('disconnected');
  const [connectedUser, setConnectedUser] = useState(null);
  const [qrCode, setQrCode] = useState(null);
  const [qrDataUrl, setQrDataUrl] = useState(null);
  
  // Config state
  const [config, setConfig] = useState({
    mensaje_bienvenida: '',
    instrucciones_bot: '',
    datos_bancarios: '',
    numero_admin: '',
    admin_lid: '',
    whatsapp_ventas: '',
    bot_activo: true
  });
  const [configDirty, setConfigDirty] = useState(false);
  
  // Precios state
  const [precios, setPrecios] = useState([]);
  const [preciosDirty, setPreciosDirty] = useState(false);
  const [newTipoVehiculo, setNewTipoVehiculo] = useState({ tipo: '', emoji: '🚗', rc: 0, completo: 0, rc_pasajeros: 0, activo: true });
  
  // Conversations state
  const [conversations, setConversations] = useState([]);
  const [pausedChats, setPausedChats] = useState([]);
  const [selectedChat, setSelectedChat] = useState(null);
  const [chatMessages, setChatMessages] = useState([]);
  const [newMessage, setNewMessage] = useState('');
  
  const messagesEndRef = useRef(null);

  // Auto-scroll to bottom of messages
  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(() => {
    scrollToBottom();
  }, [chatMessages]);

  // Load initial data
  useEffect(() => {
    loadStatus();
    loadConfig();
    const interval = setInterval(() => {
      loadStatus();
      if (selectedChat) {
        loadChatHistory(selectedChat);
      }
    }, 3000);
    return () => clearInterval(interval);
  }, [selectedChat]);

  // Poll for QR when awaiting
  useEffect(() => {
    let qrInterval;
    if (connectionStatus === 'awaiting_qr') {
      qrInterval = setInterval(loadQR, 2000);
    }
    return () => {
      if (qrInterval) clearInterval(qrInterval);
    };
  }, [connectionStatus]);

  const loadStatus = async () => {
    try {
      const data = await whatsappAPI.getStatus();
      setConnectionStatus(data.status || 'disconnected');
      setConnectedUser(data.user);
      setPausedChats(data.paused_chats || []);
      loadConversations();
    } catch (error) {
      console.error('Error loading status:', error);
    }
  };

  const loadQR = async () => {
    try {
      const data = await whatsappAPI.getQR();
      if (data.qr_data_url) {
        setQrDataUrl(data.qr_data_url);
        setQrCode(data.qr);
      }
      if (data.status && data.status !== connectionStatus) {
        setConnectionStatus(data.status);
      }
    } catch (error) {
      console.error('Error loading QR:', error);
    }
  };

  const loadConfig = async () => {
    try {
      const data = await whatsappAPI.getConfig();
      setConfig(data);
      setConfigDirty(false);
      // Also load precios
      if (data.precios) {
        setPrecios(data.precios);
      }
    } catch (error) {
      console.error('Error loading config:', error);
    }
  };

  const loadPrecios = async () => {
    try {
      const data = await whatsappAPI.getPrecios();
      setPrecios(data.precios || []);
      setPreciosDirty(false);
    } catch (error) {
      console.error('Error loading precios:', error);
    }
  };

  const savePrecios = async () => {
    setLoading(true);
    try {
      await whatsappAPI.updatePrecios(precios);
      setPreciosDirty(false);
      toast.success('Precios guardados correctamente');
    } catch (error) {
      console.error('Error saving precios:', error);
      toast.error('Error al guardar precios');
    } finally {
      setLoading(false);
    }
  };

  const updatePrecio = (index, field, value) => {
    const updated = [...precios];
    updated[index] = { ...updated[index], [field]: field === 'rc' || field === 'completo' ? parseInt(value) || 0 : value };
    setPrecios(updated);
    setPreciosDirty(true);
  };

  const addTipoVehiculo = () => {
    if (!newTipoVehiculo.tipo) {
      toast.error('Ingresá el nombre del tipo de vehículo');
      return;
    }
    setPrecios([...precios, { ...newTipoVehiculo }]);
    setNewTipoVehiculo({ tipo: '', emoji: '🚗', rc: 0, completo: 0, rc_pasajeros: 0, activo: true });
    setPreciosDirty(true);
    toast.success('Tipo de vehículo agregado');
  };

  const removeTipoVehiculo = (index) => {
    const updated = precios.filter((_, i) => i !== index);
    setPrecios(updated);
    setPreciosDirty(true);
  };

  const loadConversations = async () => {
    try {
      const data = await whatsappAPI.getConversations();
      setConversations(data.conversations || []);
    } catch (error) {
      console.error('Error loading conversations:', error);
    }
  };

  const handleConnect = async () => {
    setLoading(true);
    try {
      await whatsappAPI.connect();
      toast.info('Iniciando conexión... Espera el código QR');
      setConnectionStatus('awaiting_qr');
      setTimeout(loadQR, 2000);
    } catch (error) {
      toast.error('Error al conectar');
    }
    setLoading(false);
  };

  const handleDisconnect = async () => {
    setLoading(true);
    try {
      await whatsappAPI.disconnect();
      toast.success('Desconectado');
      setConnectionStatus('disconnected');
      setConnectedUser(null);
      setQrCode(null);
      setQrDataUrl(null);
    } catch (error) {
      toast.error('Error al desconectar');
    }
    setLoading(false);
  };

  const handleSaveConfig = async () => {
    setLoading(true);
    try {
      await whatsappAPI.updateConfig(config);
      toast.success('Configuración guardada');
      setConfigDirty(false);
      // Reload to confirm
      await loadConfig();
    } catch (error) {
      toast.error('Error al guardar configuración');
    }
    setLoading(false);
  };

  const handlePauseChat = async (phoneNumber) => {
    try {
      await whatsappAPI.pauseChat(phoneNumber);
      toast.success(`Bot pausado para este chat`);
      loadStatus();
    } catch (error) {
      toast.error('Error al pausar chat');
    }
  };

  const handleResumeChat = async (phoneNumber) => {
    try {
      await whatsappAPI.resumeChat(phoneNumber);
      toast.success(`Bot reactivado`);
      loadStatus();
    } catch (error) {
      toast.error('Error al reactivar chat');
    }
  };

  const loadChatHistory = async (phoneNumber) => {
    try {
      const data = await whatsappAPI.getChatHistory(phoneNumber);
      setChatMessages(data.messages || []);
      setSelectedChat(phoneNumber);
    } catch (error) {
      console.error('Error loading chat:', error);
    }
  };

  const handleSendMessage = async () => {
    if (!newMessage.trim() || !selectedChat) return;
    
    setLoading(true);
    try {
      await whatsappAPI.sendMessage(selectedChat, newMessage);
      toast.success('Mensaje enviado');
      setNewMessage('');
      setTimeout(() => loadChatHistory(selectedChat), 1000);
    } catch (error) {
      toast.error('Error al enviar mensaje');
    }
    setLoading(false);
  };

  const updateConfig = (field, value) => {
    setConfig(prev => ({ ...prev, [field]: value }));
    setConfigDirty(true);
  };

  // Format phone number for display
  const formatPhone = (phone) => {
    if (!phone) return 'Desconocido';
    // Remove @lid suffix
    const cleanPhone = phone.replace('@lid', '').replace('@s.whatsapp.net', '');
    // If it's a long number, format it
    if (cleanPhone.length > 10) {
      return `+${cleanPhone.slice(0, 2)} ${cleanPhone.slice(2, 5)} ${cleanPhone.slice(5, 8)}-${cleanPhone.slice(8)}`;
    }
    return cleanPhone;
  };

  // Format timestamp
  const formatTime = (timestamp) => {
    if (!timestamp) return '';
    const date = new Date(timestamp);
    return date.toLocaleTimeString('es-AR', { hour: '2-digit', minute: '2-digit' });
  };

  const formatDate = (timestamp) => {
    if (!timestamp) return '';
    const date = new Date(timestamp);
    const today = new Date();
    const yesterday = new Date(today);
    yesterday.setDate(yesterday.getDate() - 1);
    
    if (date.toDateString() === today.toDateString()) return 'Hoy';
    if (date.toDateString() === yesterday.toDateString()) return 'Ayer';
    return date.toLocaleDateString('es-AR', { day: '2-digit', month: '2-digit' });
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <Bot className="w-8 h-8 text-[#25D366]" />
          <h2 className="text-2xl font-bold text-[#064E3B]" style={{ fontFamily: 'Manrope, sans-serif' }}>
            Bot de WhatsApp
          </h2>
        </div>
        
        {/* Status Badge */}
        <div className="flex items-center gap-2 bg-white px-4 py-2 rounded-full shadow-sm">
          <div className={`w-3 h-3 rounded-full ${
            connectionStatus === 'connected' ? 'bg-green-500' : 
            connectionStatus === 'awaiting_qr' ? 'bg-yellow-500 animate-pulse' : 
            'bg-red-500'
          }`} />
          <span className="text-sm font-medium">
            {connectionStatus === 'connected' ? 'Conectado' : 
             connectionStatus === 'awaiting_qr' ? 'Esperando QR...' : 
             'Desconectado'}
          </span>
          {connectedUser && (
            <span className="text-xs text-gray-500">
              ({connectedUser.name || connectedUser.id?.split(':')[0]})
            </span>
          )}
        </div>
      </div>

      <Tabs value={activeTab} onValueChange={setActiveTab} className="w-full">
        <TabsList className="grid w-full grid-cols-5 mb-6">
          <TabsTrigger value="conexion" className="flex items-center gap-2">
            <QrCode className="w-4 h-4" />
            Conexión
          </TabsTrigger>
          <TabsTrigger value="precios" className="flex items-center gap-2">
            💰
            Precios
          </TabsTrigger>
          <TabsTrigger value="configuracion" className="flex items-center gap-2">
            <Settings className="w-4 h-4" />
            Configuración
          </TabsTrigger>
          <TabsTrigger value="conversaciones" className="flex items-center gap-2">
            <MessageCircle className="w-4 h-4" />
            Chats
          </TabsTrigger>
          <TabsTrigger value="guia" className="flex items-center gap-2">
            <BookOpen className="w-4 h-4" />
            Guía
          </TabsTrigger>
        </TabsList>

        {/* Tab Conexión */}
        <TabsContent value="conexion" className="space-y-6">
          <div className="grid md:grid-cols-2 gap-6">
            {/* QR Card */}
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <QrCode className="w-5 h-5" />
                  Código QR
                </CardTitle>
              </CardHeader>
              <CardContent className="flex flex-col items-center justify-center min-h-[320px]">
                {connectionStatus === 'connected' ? (
                  <div className="text-center">
                    <div className="w-24 h-24 bg-green-100 rounded-full flex items-center justify-center mx-auto mb-4">
                      <MessageCircle className="w-12 h-12 text-green-600" />
                    </div>
                    <p className="text-green-600 font-semibold text-lg">¡Conectado!</p>
                    {connectedUser && (
                      <p className="text-gray-500 mt-2">{connectedUser.name || connectedUser.id}</p>
                    )}
                    <Button 
                      onClick={handleDisconnect} 
                      variant="outline" 
                      className="mt-4 text-red-500 border-red-500"
                      disabled={loading}
                    >
                      <PowerOff className="w-4 h-4 mr-2" />
                      Desconectar
                    </Button>
                  </div>
                ) : connectionStatus === 'awaiting_qr' && qrDataUrl ? (
                  <div className="text-center">
                    <img 
                      src={qrDataUrl} 
                      alt="QR Code" 
                      className="w-64 h-64 mx-auto border rounded-lg"
                    />
                    <p className="text-gray-500 mt-4 text-sm">
                      Escanea este código con WhatsApp
                    </p>
                    <Button onClick={loadQR} variant="ghost" size="sm" className="mt-2">
                      <RefreshCw className="w-4 h-4 mr-2" />
                      Refrescar QR
                    </Button>
                  </div>
                ) : (
                  <div className="text-center">
                    <div className="w-24 h-24 bg-gray-100 rounded-full flex items-center justify-center mx-auto mb-4">
                      <QrCode className="w-12 h-12 text-gray-400" />
                    </div>
                    <p className="text-gray-500 mb-4">No hay conexión activa</p>
                    <Button onClick={handleConnect} className="bg-[#25D366] hover:bg-[#128C7E]" disabled={loading}>
                      {loading ? <Loader2 className="w-4 h-4 mr-2 animate-spin" /> : <Power className="w-4 h-4 mr-2" />}
                      Conectar WhatsApp
                    </Button>
                  </div>
                )}
              </CardContent>
            </Card>

            {/* Instructions Card */}
            <Card>
              <CardHeader>
                <CardTitle>¿Cómo conectar?</CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="flex items-start gap-3">
                  <div className="w-6 h-6 bg-[#25D366] text-white rounded-full flex items-center justify-center text-sm font-bold shrink-0">1</div>
                  <div>
                    <p className="font-medium">Abre WhatsApp en tu teléfono</p>
                    <p className="text-sm text-gray-500">La aplicación oficial de WhatsApp</p>
                  </div>
                </div>
                <div className="flex items-start gap-3">
                  <div className="w-6 h-6 bg-[#25D366] text-white rounded-full flex items-center justify-center text-sm font-bold shrink-0">2</div>
                  <div>
                    <p className="font-medium">Ve a Configuración</p>
                    <p className="text-sm text-gray-500">Menú ⋮ → Dispositivos vinculados</p>
                  </div>
                </div>
                <div className="flex items-start gap-3">
                  <div className="w-6 h-6 bg-[#25D366] text-white rounded-full flex items-center justify-center text-sm font-bold shrink-0">3</div>
                  <div>
                    <p className="font-medium">Vincular dispositivo</p>
                    <p className="text-sm text-gray-500">Toca "Vincular un dispositivo"</p>
                  </div>
                </div>
                <div className="flex items-start gap-3">
                  <div className="w-6 h-6 bg-[#25D366] text-white rounded-full flex items-center justify-center text-sm font-bold shrink-0">4</div>
                  <div>
                    <p className="font-medium">Escanea el código QR</p>
                    <p className="text-sm text-gray-500">Apunta la cámara al código</p>
                  </div>
                </div>
                <div className="mt-4 p-3 bg-yellow-50 rounded-lg border border-yellow-200">
                  <p className="text-sm text-yellow-800">
                    ⚠️ El teléfono debe permanecer conectado a internet
                  </p>
                </div>
              </CardContent>
            </Card>
          </div>
        </TabsContent>

        {/* Tab Precios */}
        <TabsContent value="precios" className="space-y-6">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center justify-between">
                <span className="flex items-center gap-2">
                  💰 Precios de Coberturas
                </span>
                <Button 
                  onClick={savePrecios} 
                  disabled={!preciosDirty || loading}
                  className="bg-[#25D366] hover:bg-[#128C7E]"
                >
                  {loading ? <Loader2 className="w-4 h-4 animate-spin mr-2" /> : <Save className="w-4 h-4 mr-2" />}
                  Guardar Precios
                </Button>
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-6">
              {/* Lista de precios existentes */}
              <div className="space-y-4">
                {precios.map((precio, index) => (
                  <div key={index} className={`p-4 rounded-lg border ${precio.activo ? 'bg-white border-gray-200' : 'bg-gray-100 border-gray-300 opacity-60'}`}>
                    <div className="grid grid-cols-6 gap-4 items-center">
                      <div className="col-span-2">
                        <Label className="text-xs text-gray-500">Tipo de Vehículo</Label>
                        <div className="flex items-center gap-2">
                          <Input 
                            value={precio.emoji}
                            onChange={(e) => updatePrecio(index, 'emoji', e.target.value)}
                            className="w-16 text-center text-xl"
                            maxLength={2}
                          />
                          <Input 
                            value={precio.tipo}
                            onChange={(e) => updatePrecio(index, 'tipo', e.target.value)}
                            className="flex-1"
                          />
                        </div>
                      </div>
                      <div>
                        <Label className="text-xs text-gray-500">RC ($)</Label>
                        <Input 
                          type="number"
                          value={precio.rc}
                          onChange={(e) => updatePrecio(index, 'rc', e.target.value)}
                          className="font-mono"
                        />
                      </div>
                      <div>
                        <Label className="text-xs text-gray-500">Completo ($)</Label>
                        <Input 
                          type="number"
                          value={precio.completo}
                          onChange={(e) => updatePrecio(index, 'completo', e.target.value)}
                          className="font-mono"
                        />
                      </div>
                      <div className="flex items-center gap-2">
                        <Switch 
                          checked={precio.activo}
                          onCheckedChange={(checked) => updatePrecio(index, 'activo', checked)}
                        />
                        <Label className="text-xs">{precio.activo ? 'Activo' : 'Inactivo'}</Label>
                      </div>
                      <div>
                        <Button 
                          variant="ghost" 
                          size="sm"
                          onClick={() => removeTipoVehiculo(index)}
                          className="text-red-500 hover:text-red-700 hover:bg-red-50"
                        >
                          🗑️ Eliminar
                        </Button>
                      </div>
                    </div>
                  </div>
                ))}
              </div>

              {/* Agregar nuevo tipo */}
              <div className="p-4 bg-green-50 rounded-lg border-2 border-dashed border-green-300">
                <h4 className="font-semibold text-green-800 mb-4">➕ Agregar Nuevo Tipo de Vehículo</h4>
                <div className="grid grid-cols-6 gap-4 items-end">
                  <div className="col-span-2">
                    <Label className="text-xs text-gray-500">Emoji y Nombre</Label>
                    <div className="flex items-center gap-2">
                      <Input 
                        value={newTipoVehiculo.emoji}
                        onChange={(e) => setNewTipoVehiculo({...newTipoVehiculo, emoji: e.target.value})}
                        className="w-16 text-center text-xl"
                        placeholder="🚗"
                        maxLength={2}
                      />
                      <Input 
                        value={newTipoVehiculo.tipo}
                        onChange={(e) => setNewTipoVehiculo({...newTipoVehiculo, tipo: e.target.value})}
                        placeholder="Ej: Camioneta"
                        className="flex-1"
                      />
                    </div>
                  </div>
                  <div>
                    <Label className="text-xs text-gray-500">RC ($)</Label>
                    <Input 
                      type="number"
                      value={newTipoVehiculo.rc || ''}
                      onChange={(e) => setNewTipoVehiculo({...newTipoVehiculo, rc: parseInt(e.target.value) || 0})}
                      placeholder="6000"
                      className="font-mono"
                    />
                  </div>
                  <div>
                    <Label className="text-xs text-gray-500">Completo ($)</Label>
                    <Input 
                      type="number"
                      value={newTipoVehiculo.completo || ''}
                      onChange={(e) => setNewTipoVehiculo({...newTipoVehiculo, completo: parseInt(e.target.value) || 0})}
                      placeholder="9000"
                      className="font-mono"
                    />
                  </div>
                  <div className="col-span-2">
                    <Button 
                      onClick={addTipoVehiculo}
                      className="w-full bg-green-600 hover:bg-green-700"
                    >
                      ➕ Agregar
                    </Button>
                  </div>
                </div>
              </div>

              <div className="p-4 bg-blue-50 rounded-lg border border-blue-200">
                <p className="text-sm text-blue-800">
                  💡 <strong>Tip:</strong> Los precios se actualizan automáticamente en el bot y en la sección Guía.
                  Podés desactivar un tipo de vehículo sin eliminarlo usando el switch.
                </p>
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        {/* Tab Configuración */}
        <TabsContent value="configuracion" className="space-y-6">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center justify-between">
                <span className="flex items-center gap-2">
                  <Settings className="w-5 h-5" />
                  Configuración del Bot
                </span>
                <div className="flex items-center gap-4">
                  <div className="flex items-center gap-2">
                    <Label htmlFor="bot-activo" className="text-sm">Bot Activo</Label>
                    <Switch 
                      id="bot-activo"
                      checked={config.bot_activo}
                      onCheckedChange={(checked) => updateConfig('bot_activo', checked)}
                    />
                  </div>
                  <Button onClick={handleSaveConfig} disabled={!configDirty || loading} className="bg-[#064E3B] hover:bg-[#064E3B]/90">
                    {loading ? <Loader2 className="w-4 h-4 mr-2 animate-spin" /> : <Save className="w-4 h-4 mr-2" />}
                    Guardar
                  </Button>
                </div>
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-6">
              {/* Número del Admin */}
              <div className="p-4 bg-blue-50 rounded-lg border border-blue-200">
                <Label className="text-base font-semibold text-blue-800">📱 Tu número para confirmar pagos</Label>
                <p className="text-sm text-blue-600 mb-2">
                  Cuando un cliente diga que pagó, recibirás un WhatsApp para confirmar.
                </p>
                <Input 
                  value={config.numero_admin || ''}
                  onChange={(e) => updateConfig('numero_admin', e.target.value.replace(/\D/g, ''))}
                  placeholder="Ej: 5491112345678 (con código de país)"
                  className="font-mono bg-white"
                />
              </div>

              {/* Admin LID (identificador interno WhatsApp) */}
              <div className="p-4 bg-purple-50 rounded-lg border border-purple-200">
                <Label className="text-base font-semibold text-purple-800">🔑 Tu LID de WhatsApp (Identificador Interno)</Label>
                <p className="text-sm text-purple-600 mb-2">
                  Este número lo obtiene el bot automáticamente cuando te identifica. Si no te reconoce como admin, 
                  copiá el número largo que aparece en los chats cuando escribís y pegalo acá.
                </p>
                <Input 
                  value={config.admin_lid || ''}
                  onChange={(e) => updateConfig('admin_lid', e.target.value.replace(/\D/g, ''))}
                  placeholder="Ej: 122441598795892 (número largo interno)"
                  className="font-mono bg-white"
                />
                <p className="text-xs text-purple-500 mt-1">
                  💡 Tip: Mirá en la pestaña "Chats" tu conversación y copiá el número que aparece como remitente
                </p>
              </div>

              {/* Número de WhatsApp para Ventas (Homepage) */}
              <div className="p-4 bg-green-50 rounded-lg border border-green-200">
                <Label className="text-base font-semibold text-green-800">📲 Número de WhatsApp para Ventas</Label>
                <p className="text-sm text-green-600 mb-2">
                  Este número aparecerá en el botón "Contratar" de la página principal.
                </p>
                <Input 
                  value={config.whatsapp_ventas || ''}
                  onChange={(e) => updateConfig('whatsapp_ventas', e.target.value.replace(/\D/g, ''))}
                  placeholder="Ej: 5491112345678 (con código de país)"
                  className="font-mono bg-white"
                />
              </div>

              {/* Datos Bancarios */}
              <div>
                <Label className="text-base font-semibold">💳 Datos Bancarios para Transferencias</Label>
                <p className="text-sm text-gray-500 mb-2">
                  El bot usará estos datos cuando un cliente quiera pagar
                </p>
                <Textarea 
                  value={config.datos_bancarios}
                  onChange={(e) => updateConfig('datos_bancarios', e.target.value)}
                  rows={4}
                  placeholder="CBU: 0000000000000000000000&#10;Alias: mi-alias&#10;Titular: Nombre Apellido"
                  className="font-mono text-sm"
                />
              </div>

              {/* Mensaje de Bienvenida */}
              <div>
                <Label className="text-base font-semibold">👋 Mensaje de Bienvenida</Label>
                <p className="text-sm text-gray-500 mb-2">
                  Primer mensaje que ve el cliente
                </p>
                <Textarea 
                  value={config.mensaje_bienvenida}
                  onChange={(e) => updateConfig('mensaje_bienvenida', e.target.value)}
                  rows={5}
                  placeholder="¡Hola! Soy el asistente virtual..."
                  className="font-mono text-sm"
                />
              </div>

              {/* Instrucciones del Bot */}
              <div>
                <Label className="text-base font-semibold">🤖 Instrucciones del Bot</Label>
                <p className="text-sm text-gray-500 mb-2">
                  Cómo debe comportarse el bot (prompt del sistema)
                </p>
                <Textarea 
                  value={config.instrucciones_bot}
                  onChange={(e) => updateConfig('instrucciones_bot', e.target.value)}
                  rows={12}
                  placeholder="Sos el vendedor de..."
                  className="font-mono text-sm"
                />
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        {/* Tab Conversaciones - DISEÑO WHATSAPP */}
        <TabsContent value="conversaciones">
          <div className="flex h-[600px] bg-white rounded-xl shadow-lg overflow-hidden border">
            {/* Lista de Chats - Sidebar */}
            <div className="w-[350px] border-r flex flex-col bg-white">
              {/* Header */}
              <div className="p-4 bg-[#f0f2f5] border-b flex items-center justify-between">
                <h3 className="font-semibold text-[#111b21]">Chats</h3>
                <Button variant="ghost" size="sm" onClick={loadConversations}>
                  <RefreshCw className="w-4 h-4" />
                </Button>
              </div>
              
              {/* Chat List */}
              <div className="flex-1 overflow-y-auto">
                {conversations.length === 0 ? (
                  <div className="flex flex-col items-center justify-center h-full text-gray-400 p-4">
                    <MessageCircle className="w-16 h-16 mb-4 opacity-30" />
                    <p className="text-center">No hay conversaciones aún</p>
                  </div>
                ) : (
                  conversations.map((conv) => (
                    <div 
                      key={conv.phone_number}
                      onClick={() => loadChatHistory(conv.phone_number)}
                      className={`flex items-center gap-3 p-3 cursor-pointer border-b hover:bg-[#f5f6f6] transition-colors ${
                        selectedChat === conv.phone_number ? 'bg-[#f0f2f5]' : ''
                      }`}
                    >
                      {/* Avatar */}
                      <div className="w-12 h-12 rounded-full bg-[#dfe5e7] flex items-center justify-center shrink-0">
                        <User className="w-6 h-6 text-[#8696a0]" />
                      </div>
                      
                      {/* Info */}
                      <div className="flex-1 min-w-0">
                        <div className="flex items-center justify-between">
                          <span className="font-medium text-[#111b21] truncate">
                            {conv.push_name || formatPhone(conv.phone_number)}
                          </span>
                          <span className="text-xs text-[#667781]">
                            {formatDate(conv.last_message_time)}
                          </span>
                        </div>
                        <div className="flex items-center justify-between mt-1">
                          <p className="text-sm text-[#667781] truncate pr-2">
                            {conv.last_message?.substring(0, 40) || 'Sin mensajes'}
                          </p>
                          {conv.message_count > 0 && (
                            <span className="bg-[#25D366] text-white text-xs px-2 py-0.5 rounded-full">
                              {conv.message_count}
                            </span>
                          )}
                        </div>
                      </div>
                    </div>
                  ))
                )}
              </div>
            </div>

            {/* Chat Area */}
            <div className="flex-1 flex flex-col">
              {selectedChat ? (
                <>
                  {/* Chat Header */}
                  <div className="p-3 bg-[#f0f2f5] border-b flex items-center justify-between">
                    <div className="flex items-center gap-3">
                      <div className="w-10 h-10 rounded-full bg-[#dfe5e7] flex items-center justify-center">
                        <User className="w-5 h-5 text-[#8696a0]" />
                      </div>
                      <div>
                        <p className="font-medium text-[#111b21]">
                          {conversations.find(c => c.phone_number === selectedChat)?.push_name || formatPhone(selectedChat)}
                        </p>
                        <p className="text-xs text-[#667781]">
                          {formatPhone(selectedChat)}
                        </p>
                      </div>
                    </div>
                    <div className="flex items-center gap-2">
                      {pausedChats.includes(selectedChat) ? (
                        <Button onClick={() => handleResumeChat(selectedChat)} size="sm" className="bg-[#25D366] hover:bg-[#128C7E]">
                          <Play className="w-4 h-4 mr-1" /> Activar Bot
                        </Button>
                      ) : (
                        <Button onClick={() => handlePauseChat(selectedChat)} size="sm" variant="outline" className="text-orange-500 border-orange-500">
                          <Pause className="w-4 h-4 mr-1" /> Pausar Bot
                        </Button>
                      )}
                    </div>
                  </div>
                  
                  {/* Messages */}
                  <div 
                    className="flex-1 overflow-y-auto p-4 space-y-2"
                    style={{ 
                      backgroundImage: 'url("data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAGQAAABkCAYAAABw4pVUAAAABmJLR0QA/wD/AP+gvaeTAAAACXBIWXMAAAsTAAALEwEAmpwYAAAAB3RJTUUH4QoaDCsoCtO+BAAAAB1pVFh0Q29tbWVudAAAAAAAQ3JlYXRlZCB3aXRoIEdJTVBkLmUHAAAANklEQVR42u3BAQEAAACCIP+vbkhAAQAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAHcGCWAAAT6PJhEAAAAASUVORK5CYII=")',
                      backgroundColor: '#efeae2'
                    }}
                  >
                    {chatMessages.map((msg, idx) => (
                      <div 
                        key={idx}
                        className={`flex ${msg.role === 'assistant' ? 'justify-end' : 'justify-start'}`}
                      >
                        <div className={`max-w-[70%] rounded-lg px-3 py-2 shadow-sm ${
                          msg.role === 'assistant' 
                            ? 'bg-[#d9fdd3] rounded-tr-none' 
                            : 'bg-white rounded-tl-none'
                        }`}>
                          <p className="text-[#111b21] text-sm whitespace-pre-wrap break-words">
                            {msg.message}
                          </p>
                          <div className="flex items-center justify-end gap-1 mt-1">
                            <span className="text-[10px] text-[#667781]">
                              {formatTime(msg.timestamp)}
                            </span>
                            {msg.role === 'assistant' && (
                              <CheckCheck className="w-4 h-4 text-[#53bdeb]" />
                            )}
                          </div>
                        </div>
                      </div>
                    ))}
                    <div ref={messagesEndRef} />
                  </div>

                  {/* Input Area */}
                  <div className="p-3 bg-[#f0f2f5] border-t">
                    {pausedChats.includes(selectedChat) ? (
                      <div className="flex gap-2">
                        <Input 
                          value={newMessage}
                          onChange={(e) => setNewMessage(e.target.value)}
                          placeholder="Escribe un mensaje..."
                          onKeyDown={(e) => e.key === 'Enter' && !e.shiftKey && handleSendMessage()}
                          className="flex-1 rounded-full bg-white border-0"
                        />
                        <Button 
                          onClick={handleSendMessage}
                          disabled={!newMessage.trim() || loading}
                          className="rounded-full w-10 h-10 p-0 bg-[#25D366] hover:bg-[#128C7E]"
                        >
                          <Send className="w-5 h-5" />
                        </Button>
                      </div>
                    ) : (
                      <div className="text-center py-2 text-sm text-[#667781]">
                        🤖 El bot está respondiendo automáticamente · <button onClick={() => handlePauseChat(selectedChat)} className="text-[#25D366] hover:underline">Pausar para escribir</button>
                      </div>
                    )}
                  </div>
                </>
              ) : (
                <div className="flex-1 flex flex-col items-center justify-center bg-[#f0f2f5] text-[#667781]">
                  <div className="w-64 h-64 mb-6">
                    <svg viewBox="0 0 303 172" className="opacity-30">
                      <path fill="currentColor" d="M229.565 160.229c-1.156.622-2.391 1.067-3.662 1.33v6.048c0 2.46-1.99 4.45-4.449 4.45H81.546c-2.46 0-4.449-1.99-4.449-4.45v-6.048a15.27 15.27 0 0 1-3.663-1.33C35.126 139.988 22.554 94.547 52.376 59.07c29.822-35.478 85.063-35.478 114.885 0 29.822 35.477 17.25 80.918-20.058 101.159h-.002c-1.156.622-2.391 1.067-3.662 1.33v6.048c0 2.46-1.99 4.45-4.449 4.45H62.626c-2.46 0-4.449-1.99-4.449-4.45v-6.048c-1.27-.263-2.506-.708-3.662-1.33-37.308-20.241-49.88-65.682-20.058-101.159 29.822-35.478 85.063-35.478 114.885 0 29.822 35.477 17.25 80.918-20.058 101.159z"/>
                    </svg>
                  </div>
                  <h3 className="text-2xl font-light text-[#41525d] mb-2">WhatsApp para Estonia Cobertura</h3>
                  <p className="text-sm">Selecciona un chat para ver la conversación</p>
                </div>
              )}
            </div>
          </div>
        </TabsContent>

        {/* GUÍA TAB */}
        <TabsContent value="guia" className="space-y-6">
          {/* Comandos de Admin */}
          <Card>
            <CardHeader className="bg-gradient-to-r from-purple-500 to-purple-600 text-white rounded-t-lg">
              <CardTitle className="flex items-center gap-2">
                <Command className="w-5 h-5" />
                Comandos de Admin (vía WhatsApp)
              </CardTitle>
            </CardHeader>
            <CardContent className="p-6">
              <div className="space-y-4">
                <div className="grid md:grid-cols-2 gap-4">
                  <div className="p-4 bg-green-50 rounded-lg border border-green-200">
                    <h4 className="font-bold text-green-800 mb-2">CONFIRMAR [RECIBO]</h4>
                    <p className="text-sm text-green-700">Confirma el pago de una cobertura y envía comprobantes al cliente.</p>
                    <code className="text-xs bg-green-100 px-2 py-1 rounded mt-2 block">Ejemplo: CONFIRMAR ABC123</code>
                  </div>
                  <div className="p-4 bg-blue-50 rounded-lg border border-blue-200">
                    <h4 className="font-bold text-blue-800 mb-2">ESTADO</h4>
                    <p className="text-sm text-blue-700">Muestra lista de coberturas pendientes de pago.</p>
                    <code className="text-xs bg-blue-100 px-2 py-1 rounded mt-2 block">Ejemplo: ESTADO</code>
                  </div>
                  <div className="p-4 bg-orange-50 rounded-lg border border-orange-200">
                    <h4 className="font-bold text-orange-800 mb-2">PAUSAR [NÚMERO]</h4>
                    <p className="text-sm text-orange-700">Pausa el bot para ese cliente. Vos lo atendés manualmente.</p>
                    <code className="text-xs bg-orange-100 px-2 py-1 rounded mt-2 block">Ejemplo: PAUSAR 5491112345678</code>
                  </div>
                  <div className="p-4 bg-teal-50 rounded-lg border border-teal-200">
                    <h4 className="font-bold text-teal-800 mb-2">REANUDAR [NÚMERO]</h4>
                    <p className="text-sm text-teal-700">Reactiva el bot para ese cliente.</p>
                    <code className="text-xs bg-teal-100 px-2 py-1 rounded mt-2 block">Ejemplo: REANUDAR 5491112345678</code>
                  </div>
                  <div className="p-4 bg-gray-50 rounded-lg border border-gray-200 md:col-span-2">
                    <h4 className="font-bold text-gray-800 mb-2">PAUSADOS</h4>
                    <p className="text-sm text-gray-700">Muestra lista de todos los chats que están en atención humana.</p>
                    <code className="text-xs bg-gray-100 px-2 py-1 rounded mt-2 block">Ejemplo: PAUSADOS</code>
                  </div>
                </div>
              </div>
            </CardContent>
          </Card>

          {/* Funcionalidades del Bot */}
          <Card>
            <CardHeader className="bg-gradient-to-r from-green-500 to-green-600 text-white rounded-t-lg">
              <CardTitle className="flex items-center gap-2">
                <Bot className="w-5 h-5" />
                Funcionalidades del Bot
              </CardTitle>
            </CardHeader>
            <CardContent className="p-6">
              <div className="space-y-4">
                <div className="grid md:grid-cols-2 gap-4">
                  <div className="p-4 bg-white rounded-lg border shadow-sm">
                    <div className="flex items-center gap-2 mb-2">
                      <Zap className="w-5 h-5 text-yellow-500" />
                      <h4 className="font-bold">Venta Automática</h4>
                    </div>
                    <ul className="text-sm text-gray-600 space-y-1 list-disc list-inside">
                      <li>Identifica tipo de vehículo</li>
                      <li>Ofrece coberturas con precios</li>
                      <li>Recopila datos del cliente</li>
                      <li>Crea cobertura en el sistema</li>
                      <li>Envía instrucciones de pago</li>
                    </ul>
                  </div>
                  <div className="p-4 bg-white rounded-lg border shadow-sm">
                    <div className="flex items-center gap-2 mb-2">
                      <Users className="w-5 h-5 text-blue-500" />
                      <h4 className="font-bold">Memoria de Clientes</h4>
                    </div>
                    <ul className="text-sm text-gray-600 space-y-1 list-disc list-inside">
                      <li>Recuerda nombre del cliente</li>
                      <li>Guarda DNI, email, vehículo</li>
                      <li>Personaliza conversaciones</li>
                      <li>No repite preguntas de datos</li>
                    </ul>
                  </div>
                  <div className="p-4 bg-white rounded-lg border shadow-sm">
                    <div className="flex items-center gap-2 mb-2">
                      <Clock className="w-5 h-5 text-orange-500" />
                      <h4 className="font-bold">Seguimiento Automático</h4>
                    </div>
                    <ul className="text-sm text-gray-600 space-y-1 list-disc list-inside">
                      <li>Si el cliente no responde en 10 min</li>
                      <li>Envía mensaje de despedida cordial</li>
                      <li>Invita a retomar la conversación</li>
                    </ul>
                  </div>
                  <div className="p-4 bg-white rounded-lg border shadow-sm">
                    <div className="flex items-center gap-2 mb-2">
                      <User className="w-5 h-5 text-purple-500" />
                      <h4 className="font-bold">Derivación a Humano</h4>
                    </div>
                    <ul className="text-sm text-gray-600 space-y-1 list-disc list-inside">
                      <li>Detecta cuando piden hablar con persona</li>
                      <li>Te notifica por WhatsApp</li>
                      <li>Podés pausar el bot para atender</li>
                    </ul>
                  </div>
                </div>
              </div>
            </CardContent>
          </Card>

          {/* Precios */}
          <Card>
            <CardHeader className="bg-gradient-to-r from-blue-500 to-blue-600 text-white rounded-t-lg">
              <CardTitle className="flex items-center gap-2">
                💰 Precios de Coberturas (30 días)
              </CardTitle>
            </CardHeader>
            <CardContent className="p-6">
              <div className="overflow-x-auto">
                <table className="w-full text-sm">
                  <thead>
                    <tr className="border-b">
                      <th className="text-left py-2 px-4">Vehículo</th>
                      <th className="text-center py-2 px-4">RC (Resp. Civil)</th>
                      <th className="text-center py-2 px-4">Completo</th>
                      <th className="text-center py-2 px-4">Estado</th>
                    </tr>
                  </thead>
                  <tbody>
                    {precios.length > 0 ? precios.map((p, idx) => (
                      <tr key={idx} className={`border-b ${!p.activo ? 'opacity-50' : ''}`}>
                        <td className="py-2 px-4 font-medium">{p.emoji} {p.tipo}</td>
                        <td className="text-center py-2 px-4">${p.rc?.toLocaleString('es-AR')}</td>
                        <td className="text-center py-2 px-4">${p.completo?.toLocaleString('es-AR')}</td>
                        <td className="text-center py-2 px-4">
                          <span className={`px-2 py-1 rounded text-xs ${p.activo ? 'bg-green-100 text-green-700' : 'bg-gray-100 text-gray-500'}`}>
                            {p.activo ? 'Activo' : 'Inactivo'}
                          </span>
                        </td>
                      </tr>
                    )) : (
                      <tr>
                        <td colSpan={4} className="text-center py-4 text-gray-500">
                          No hay precios configurados. Ve a la pestaña "Precios" para agregarlos.
                        </td>
                      </tr>
                    )}
                  </tbody>
                </table>
              </div>
              <p className="text-xs text-gray-500 mt-4">
                💡 Estos precios se cargan dinámicamente desde la configuración. Editálos en la pestaña "Precios".
              </p>
            </CardContent>
          </Card>

          {/* Técnicas de Venta */}
          <Card>
            <CardHeader className="bg-gradient-to-r from-amber-500 to-amber-600 text-white rounded-t-lg">
              <CardTitle className="flex items-center gap-2">
                <MessageSquare className="w-5 h-5" />
                Técnicas de Venta Implementadas
              </CardTitle>
            </CardHeader>
            <CardContent className="p-6">
              <div className="space-y-4">
                <div className="p-4 bg-amber-50 rounded-lg border border-amber-200">
                  <h4 className="font-bold text-amber-800 mb-2">Estilo de Comunicación</h4>
                  <ul className="text-sm text-amber-700 space-y-1 list-disc list-inside">
                    <li>Mensajes cortos y directos</li>
                    <li>Lenguaje simple, sin tecnicismos</li>
                    <li>No educar, no justificar, no debatir</li>
                    <li>Priorizar preguntas que avancen la venta</li>
                  </ul>
                </div>
                <div className="grid md:grid-cols-2 gap-4">
                  <div className="p-4 bg-white rounded-lg border shadow-sm">
                    <h4 className="font-bold text-gray-800 mb-2">✅ Confirmar Utilidad</h4>
                    <p className="text-sm text-gray-600 italic">"Sirve sin problema para eso 👍"</p>
                  </div>
                  <div className="p-4 bg-white rounded-lg border shadow-sm">
                    <h4 className="font-bold text-gray-800 mb-2">⏰ Urgencia Suave</h4>
                    <p className="text-sm text-gray-600 italic">"¿Lo necesitás para activarlo hoy?"</p>
                  </div>
                  <div className="p-4 bg-white rounded-lg border shadow-sm">
                    <h4 className="font-bold text-gray-800 mb-2">🎯 Reducción de Dudas</h4>
                    <p className="text-sm text-gray-600 italic">"La mayoría lo contrata para circular tranquilo."</p>
                  </div>
                  <div className="p-4 bg-white rounded-lg border shadow-sm">
                    <h4 className="font-bold text-gray-800 mb-2">📄 Frase de Refuerzo</h4>
                    <p className="text-sm text-gray-600 italic">"Te queda el certificado listo para circular."</p>
                  </div>
                </div>
                <div className="p-4 bg-red-50 rounded-lg border border-red-200">
                  <h4 className="font-bold text-red-800 mb-2">🚫 Palabras Prohibidas</h4>
                  <p className="text-sm text-red-700">
                    <span className="line-through">seguro, póliza, aseguradora, prima, indemnización</span>
                  </p>
                  <p className="text-sm text-green-700 mt-2">
                    ✓ Usar: cobertura, certificado, activación, circular
                  </p>
                </div>
              </div>
            </CardContent>
          </Card>

          {/* Flujo del Cliente */}
          <Card>
            <CardHeader className="bg-gradient-to-r from-indigo-500 to-indigo-600 text-white rounded-t-lg">
              <CardTitle className="flex items-center gap-2">
                📋 Flujo de Venta del Bot
              </CardTitle>
            </CardHeader>
            <CardContent className="p-6">
              <div className="space-y-3">
                <div className="flex items-start gap-3">
                  <div className="w-8 h-8 rounded-full bg-indigo-500 text-white flex items-center justify-center font-bold text-sm shrink-0">1</div>
                  <div>
                    <h4 className="font-bold">Cliente saluda</h4>
                    <p className="text-sm text-gray-600">Bot da bienvenida y pregunta tipo de vehículo</p>
                  </div>
                </div>
                <div className="flex items-start gap-3">
                  <div className="w-8 h-8 rounded-full bg-indigo-500 text-white flex items-center justify-center font-bold text-sm shrink-0">2</div>
                  <div>
                    <h4 className="font-bold">Ofrece opciones</h4>
                    <p className="text-sm text-gray-600">Muestra RC y Completo con precios</p>
                  </div>
                </div>
                <div className="flex items-start gap-3">
                  <div className="w-8 h-8 rounded-full bg-indigo-500 text-white flex items-center justify-center font-bold text-sm shrink-0">3</div>
                  <div>
                    <h4 className="font-bold">Recopila datos</h4>
                    <p className="text-sm text-gray-600">Pide TODOS los datos juntos: nombre, DNI, email, patente, marca/modelo, año</p>
                  </div>
                </div>
                <div className="flex items-start gap-3">
                  <div className="w-8 h-8 rounded-full bg-indigo-500 text-white flex items-center justify-center font-bold text-sm shrink-0">4</div>
                  <div>
                    <h4 className="font-bold">Confirma y crea</h4>
                    <p className="text-sm text-gray-600">Muestra resumen, cliente confirma, se crea la cobertura</p>
                  </div>
                </div>
                <div className="flex items-start gap-3">
                  <div className="w-8 h-8 rounded-full bg-indigo-500 text-white flex items-center justify-center font-bold text-sm shrink-0">5</div>
                  <div>
                    <h4 className="font-bold">Pago</h4>
                    <p className="text-sm text-gray-600">Envía datos bancarios, cliente paga y envía comprobante</p>
                  </div>
                </div>
                <div className="flex items-start gap-3">
                  <div className="w-8 h-8 rounded-full bg-green-500 text-white flex items-center justify-center font-bold text-sm shrink-0">✓</div>
                  <div>
                    <h4 className="font-bold">Admin confirma</h4>
                    <p className="text-sm text-gray-600">Admin escribe CONFIRMAR [RECIBO], cliente recibe comprobantes</p>
                  </div>
                </div>
              </div>
            </CardContent>
          </Card>

          {/* Consulta de Coberturas */}
          <Card>
            <CardHeader className="bg-gradient-to-r from-cyan-500 to-cyan-600 text-white rounded-t-lg">
              <CardTitle className="flex items-center gap-2">
                🔍 Consulta de Coberturas por DNI
              </CardTitle>
            </CardHeader>
            <CardContent className="p-6">
              <div className="grid md:grid-cols-2 gap-4">
                <div className="p-4 bg-cyan-50 rounded-lg border border-cyan-200">
                  <h4 className="font-bold text-cyan-800 mb-2">Vía WhatsApp Bot</h4>
                  <p className="text-sm text-cyan-700">El cliente puede escribir frases como:</p>
                  <ul className="text-sm text-cyan-600 mt-2 space-y-1 list-disc list-inside">
                    <li>"Consultar cobertura 12345678"</li>
                    <li>"Ver mi cobertura"</li>
                    <li>"Mis coberturas"</li>
                  </ul>
                </div>
                <div className="p-4 bg-cyan-50 rounded-lg border border-cyan-200">
                  <h4 className="font-bold text-cyan-800 mb-2">Vía Web</h4>
                  <p className="text-sm text-cyan-700">Portal público en:</p>
                  <code className="text-xs bg-cyan-100 px-2 py-1 rounded mt-2 block">/mis-coberturas</code>
                  <p className="text-sm text-cyan-600 mt-2">Ingresa DNI y ve todas sus coberturas</p>
                </div>
              </div>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  );
}

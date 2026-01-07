import { useState, useEffect, useRef } from 'react';
import { MessageCircle, QrCode, Settings, Send, Pause, Play, RefreshCw, Power, PowerOff, Bot, Save, Loader2, Phone, User, Check, CheckCheck } from 'lucide-react';
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
    } catch (error) {
      console.error('Error loading config:', error);
    }
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
        <TabsList className="grid w-full grid-cols-3 mb-6">
          <TabsTrigger value="conexion" className="flex items-center gap-2">
            <QrCode className="w-4 h-4" />
            Conexión
          </TabsTrigger>
          <TabsTrigger value="configuracion" className="flex items-center gap-2">
            <Settings className="w-4 h-4" />
            Configuración
          </TabsTrigger>
          <TabsTrigger value="conversaciones" className="flex items-center gap-2">
            <MessageCircle className="w-4 h-4" />
            Chats
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
      </Tabs>
    </div>
  );
}

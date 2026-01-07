import { useState, useEffect, useCallback } from 'react';
import { MessageCircle, QrCode, Settings, Users, Send, Pause, Play, RefreshCw, Power, PowerOff, Bot, Save, Loader2 } from 'lucide-react';
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
    bot_activo: true
  });
  const [configDirty, setConfigDirty] = useState(false);
  
  // Conversations state
  const [conversations, setConversations] = useState([]);
  const [pausedChats, setPausedChats] = useState([]);
  const [selectedChat, setSelectedChat] = useState(null);
  const [chatMessages, setChatMessages] = useState([]);
  const [newMessage, setNewMessage] = useState('');

  // Load initial data
  useEffect(() => {
    loadStatus();
    loadConfig();
    const interval = setInterval(loadStatus, 5000);
    return () => clearInterval(interval);
  }, []);

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
      
      if (data.status === 'connected') {
        loadConversations();
      }
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
    } catch (error) {
      toast.error('Error al guardar configuración');
    }
    setLoading(false);
  };

  const handlePauseChat = async (phoneNumber) => {
    try {
      await whatsappAPI.pauseChat(phoneNumber);
      toast.success(`Bot pausado para ${phoneNumber}`);
      loadStatus();
    } catch (error) {
      toast.error('Error al pausar chat');
    }
  };

  const handleResumeChat = async (phoneNumber) => {
    try {
      await whatsappAPI.resumeChat(phoneNumber);
      toast.success(`Bot reactivado para ${phoneNumber}`);
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
      toast.error('Error al cargar historial');
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
        <div className="flex items-center gap-2">
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
              ({connectedUser.name || connectedUser.id})
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
            Conversaciones
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
                    <p className="text-xs text-gray-400 mt-2">
                      WhatsApp → Menú → Dispositivos vinculados → Vincular dispositivo
                    </p>
                    <Button 
                      onClick={loadQR} 
                      variant="ghost" 
                      size="sm" 
                      className="mt-2"
                    >
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
                    <Button 
                      onClick={handleConnect} 
                      className="bg-[#25D366] hover:bg-[#128C7E]"
                      disabled={loading}
                    >
                      {loading ? (
                        <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                      ) : (
                        <Power className="w-4 h-4 mr-2" />
                      )}
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
                  <div className="w-6 h-6 bg-[#25D366] text-white rounded-full flex items-center justify-center text-sm font-bold">1</div>
                  <div>
                    <p className="font-medium">Abre WhatsApp en tu teléfono</p>
                    <p className="text-sm text-gray-500">La aplicación oficial de WhatsApp</p>
                  </div>
                </div>
                <div className="flex items-start gap-3">
                  <div className="w-6 h-6 bg-[#25D366] text-white rounded-full flex items-center justify-center text-sm font-bold">2</div>
                  <div>
                    <p className="font-medium">Ve a Configuración</p>
                    <p className="text-sm text-gray-500">Toca los tres puntos → Dispositivos vinculados</p>
                  </div>
                </div>
                <div className="flex items-start gap-3">
                  <div className="w-6 h-6 bg-[#25D366] text-white rounded-full flex items-center justify-center text-sm font-bold">3</div>
                  <div>
                    <p className="font-medium">Vincular un dispositivo</p>
                    <p className="text-sm text-gray-500">Toca "Vincular un dispositivo"</p>
                  </div>
                </div>
                <div className="flex items-start gap-3">
                  <div className="w-6 h-6 bg-[#25D366] text-white rounded-full flex items-center justify-center text-sm font-bold">4</div>
                  <div>
                    <p className="font-medium">Escanea el código QR</p>
                    <p className="text-sm text-gray-500">Apunta la cámara al código QR de arriba</p>
                  </div>
                </div>
                
                <div className="mt-6 p-4 bg-yellow-50 rounded-lg border border-yellow-200">
                  <p className="text-sm text-yellow-800">
                    <strong>⚠️ Importante:</strong> El teléfono debe permanecer conectado a internet para que el bot funcione.
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
                  <Button 
                    onClick={handleSaveConfig} 
                    disabled={!configDirty || loading}
                    className="bg-[#064E3B] hover:bg-[#064E3B]/90"
                  >
                    {loading ? (
                      <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                    ) : (
                      <Save className="w-4 h-4 mr-2" />
                    )}
                    Guardar Cambios
                  </Button>
                </div>
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-6">
              {/* Mensaje de Bienvenida */}
              <div>
                <Label className="text-base font-semibold">Mensaje de Bienvenida</Label>
                <p className="text-sm text-gray-500 mb-2">
                  Este mensaje se envía al inicio de una nueva conversación
                </p>
                <Textarea 
                  value={config.mensaje_bienvenida}
                  onChange={(e) => updateConfig('mensaje_bienvenida', e.target.value)}
                  rows={6}
                  placeholder="¡Hola! Soy el asistente virtual..."
                  className="font-mono text-sm"
                />
              </div>

              {/* Datos Bancarios */}
              <div>
                <Label className="text-base font-semibold">Datos Bancarios para Transferencias</Label>
                <p className="text-sm text-gray-500 mb-2">
                  El bot usará estos datos cuando un cliente pregunte cómo pagar
                </p>
                <Textarea 
                  value={config.datos_bancarios}
                  onChange={(e) => updateConfig('datos_bancarios', e.target.value)}
                  rows={4}
                  placeholder="CBU: 0000000000000000000000&#10;Alias: mi-alias&#10;Titular: Nombre Apellido&#10;CUIT/CUIL: 00-00000000-0"
                  className="font-mono text-sm"
                />
              </div>

              {/* Instrucciones del Bot */}
              <div>
                <Label className="text-base font-semibold">Instrucciones del Bot (Prompt de Sistema)</Label>
                <p className="text-sm text-gray-500 mb-2">
                  Instrucciones detalladas sobre cómo debe comportarse el bot. Usa {"{datos_bancarios}"} para insertar los datos bancarios.
                </p>
                <Textarea 
                  value={config.instrucciones_bot}
                  onChange={(e) => updateConfig('instrucciones_bot', e.target.value)}
                  rows={15}
                  placeholder="Eres el asistente virtual de Estonia Cobertura..."
                  className="font-mono text-sm"
                />
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        {/* Tab Conversaciones */}
        <TabsContent value="conversaciones" className="space-y-6">
          <div className="grid md:grid-cols-3 gap-6 h-[600px]">
            {/* Lista de Conversaciones */}
            <Card className="md:col-span-1 overflow-hidden flex flex-col">
              <CardHeader className="pb-2">
                <CardTitle className="flex items-center justify-between text-lg">
                  <span className="flex items-center gap-2">
                    <Users className="w-5 h-5" />
                    Chats
                  </span>
                  <Button variant="ghost" size="sm" onClick={loadConversations}>
                    <RefreshCw className="w-4 h-4" />
                  </Button>
                </CardTitle>
              </CardHeader>
              <CardContent className="flex-1 overflow-y-auto p-2">
                {conversations.length === 0 ? (
                  <div className="text-center text-gray-500 py-8">
                    <MessageCircle className="w-12 h-12 mx-auto mb-2 opacity-50" />
                    <p className="text-sm">No hay conversaciones</p>
                  </div>
                ) : (
                  <div className="space-y-2">
                    {conversations.map((conv) => (
                      <div 
                        key={conv.phone_number}
                        onClick={() => loadChatHistory(conv.phone_number)}
                        className={`p-3 rounded-lg cursor-pointer transition-colors ${
                          selectedChat === conv.phone_number 
                            ? 'bg-[#064E3B] text-white' 
                            : 'bg-gray-50 hover:bg-gray-100'
                        }`}
                      >
                        <div className="flex items-center justify-between">
                          <div className="flex-1 min-w-0">
                            <p className="font-medium truncate">
                              {conv.push_name || conv.phone_number}
                            </p>
                            <p className={`text-xs truncate ${
                              selectedChat === conv.phone_number ? 'text-white/70' : 'text-gray-500'
                            }`}>
                              +{conv.phone_number}
                            </p>
                          </div>
                          {conv.bot_paused || pausedChats.includes(conv.phone_number) ? (
                            <span className="text-xs bg-yellow-500 text-white px-2 py-0.5 rounded">
                              Pausado
                            </span>
                          ) : null}
                        </div>
                      </div>
                    ))}
                  </div>
                )}
              </CardContent>
            </Card>

            {/* Chat View */}
            <Card className="md:col-span-2 overflow-hidden flex flex-col">
              <CardHeader className="pb-2 border-b">
                {selectedChat ? (
                  <div className="flex items-center justify-between">
                    <CardTitle className="text-lg flex items-center gap-2">
                      <MessageCircle className="w-5 h-5 text-[#25D366]" />
                      +{selectedChat}
                    </CardTitle>
                    <div className="flex items-center gap-2">
                      {pausedChats.includes(selectedChat) ? (
                        <Button 
                          onClick={() => handleResumeChat(selectedChat)} 
                          size="sm"
                          className="bg-green-500 hover:bg-green-600"
                        >
                          <Play className="w-4 h-4 mr-1" />
                          Reactivar Bot
                        </Button>
                      ) : (
                        <Button 
                          onClick={() => handlePauseChat(selectedChat)} 
                          size="sm"
                          variant="outline"
                          className="text-yellow-600 border-yellow-600"
                        >
                          <Pause className="w-4 h-4 mr-1" />
                          Pausar Bot
                        </Button>
                      )}
                    </div>
                  </div>
                ) : (
                  <CardTitle className="text-lg text-gray-400">
                    Selecciona una conversación
                  </CardTitle>
                )}
              </CardHeader>
              
              <CardContent className="flex-1 overflow-y-auto p-4 bg-[#f0f2f5]">
                {selectedChat ? (
                  chatMessages.length === 0 ? (
                    <div className="text-center text-gray-500 py-8">
                      <p className="text-sm">No hay mensajes</p>
                    </div>
                  ) : (
                    <div className="space-y-3">
                      {chatMessages.map((msg, idx) => (
                        <div 
                          key={idx}
                          className={`flex ${msg.role === 'assistant' ? 'justify-end' : 'justify-start'}`}
                        >
                          <div className={`max-w-[80%] rounded-lg p-3 ${
                            msg.role === 'assistant' 
                              ? 'bg-[#dcf8c6] text-black' 
                              : 'bg-white text-black'
                          }`}>
                            <p className="text-sm whitespace-pre-wrap">{msg.message}</p>
                            <p className="text-xs text-gray-500 mt-1 text-right">
                              {new Date(msg.timestamp).toLocaleTimeString('es-AR', { hour: '2-digit', minute: '2-digit' })}
                            </p>
                          </div>
                        </div>
                      ))}
                    </div>
                  )
                ) : (
                  <div className="flex items-center justify-center h-full text-gray-400">
                    <div className="text-center">
                      <MessageCircle className="w-16 h-16 mx-auto mb-4 opacity-50" />
                      <p>Selecciona un chat para ver los mensajes</p>
                    </div>
                  </div>
                )}
              </CardContent>

              {/* Message Input */}
              {selectedChat && pausedChats.includes(selectedChat) && (
                <div className="border-t p-4 bg-white">
                  <div className="flex gap-2">
                    <Input 
                      value={newMessage}
                      onChange={(e) => setNewMessage(e.target.value)}
                      placeholder="Escribe un mensaje manual..."
                      onKeyDown={(e) => e.key === 'Enter' && !e.shiftKey && handleSendMessage()}
                      className="flex-1"
                    />
                    <Button 
                      onClick={handleSendMessage}
                      disabled={!newMessage.trim() || loading}
                      className="bg-[#25D366] hover:bg-[#128C7E]"
                    >
                      {loading ? (
                        <Loader2 className="w-4 h-4 animate-spin" />
                      ) : (
                        <Send className="w-4 h-4" />
                      )}
                    </Button>
                  </div>
                  <p className="text-xs text-yellow-600 mt-2">
                    ⚠️ Bot pausado - Puedes enviar mensajes manualmente
                  </p>
                </div>
              )}
              
              {selectedChat && !pausedChats.includes(selectedChat) && (
                <div className="border-t p-4 bg-gray-50 text-center">
                  <p className="text-sm text-gray-500">
                    🤖 El bot está respondiendo automáticamente
                  </p>
                  <p className="text-xs text-gray-400 mt-1">
                    Pausa el bot para enviar mensajes manualmente
                  </p>
                </div>
              )}
            </Card>
          </div>
        </TabsContent>
      </Tabs>
    </div>
  );
}

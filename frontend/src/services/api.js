import axios from 'axios';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

export const api = axios.create({
  baseURL: API,
  headers: {
    'Content-Type': 'application/json'
  }
});

export const segurosAPI = {
  cotizar: async (data) => {
    const response = await api.post('/seguros/cotizar', data);
    return response.data;
  },
  
  crear: async (data) => {
    const response = await api.post('/seguros/crear', data);
    return response.data;
  },
  
  uploadFoto: async (seguroId, foto, tipo) => {
    const formData = new FormData();
    formData.append('foto', foto);
    formData.append('tipo', tipo);
    
    const response = await api.post(`/seguros/${seguroId}/upload-foto`, formData, {
      headers: { 'Content-Type': 'multipart/form-data' }
    });
    return response.data;
  },
  
  obtenerPorDNI: async (dni) => {
    const response = await api.get(`/cliente/${dni}/seguros`);
    return response.data;
  },
  
  renovar: async (seguroId) => {
    const response = await api.post(`/seguros/${seguroId}/renovar`);
    return response.data;
  },
  
  descargarPDF: (seguroId) => {
    return `${API}/seguros/${seguroId}/comprobante/pdf`;
  },
  
  descargarImagen: (seguroId) => {
    return `${API}/seguros/${seguroId}/comprobante/imagen`;
  },
  
  verificar: async (numeroRecibo) => {
    const response = await api.get(`/verificar/${numeroRecibo}`);
    return response.data;
  }
};

export const pagosAPI = {
  crearPreferencia: async (seguroId) => {
    const response = await api.post('/pagos/crear-preferencia', { seguro_id: seguroId });
    return response.data;
  }
};

export const adminAPI = {
  login: async (username, password) => {
    const response = await api.post('/admin/login', { username, password });
    return response.data;
  },
  
  logout: async (token) => {
    const response = await api.post('/admin/logout', { token });
    return response.data;
  },
  
  verifyToken: async (token) => {
    const response = await api.get(`/admin/verify?token=${token}`);
    return response.data;
  },
  
  listarSeguros: async (skip = 0, limit = 50, token = null) => {
    const url = token 
      ? `/admin/seguros?skip=${skip}&limit=${limit}&token=${token}`
      : `/admin/seguros?skip=${skip}&limit=${limit}`;
    const response = await api.get(url);
    return response.data;
  },
  
  marcarProcesado: async (seguroId) => {
    const response = await api.post(`/admin/seguros/${seguroId}/marcar-procesado`);
    return response.data;
  },
  
  crearSeguroManual: async (data) => {
    const response = await api.post('/admin/seguros/crear-manual', data);
    return response.data;
  },
  
  actualizarSeguro: async (seguroId, data) => {
    const response = await api.put(`/admin/seguros/${seguroId}`, data);
    return response.data;
  },
  
  eliminarSeguro: async (seguroId) => {
    const response = await api.delete(`/admin/seguros/${seguroId}`);
    return response.data;
  },
  
  crearPromoCode: async (data) => {
    const response = await api.post('/admin/promo-codes', data);
    return response.data;
  },
  
  listarPromoCodes: async () => {
    const response = await api.get('/admin/promo-codes');
    return response.data;
  },
  
  eliminarPromoCode: async (codigo) => {
    const response = await api.delete(`/admin/promo-codes/${codigo}`);
    return response.data;
  },
  
  // Agentes
  crearAgente: async (data) => {
    const response = await api.post('/admin/agentes', data);
    return response.data;
  },
  
  listarAgentes: async () => {
    const response = await api.get('/admin/agentes');
    return response.data;
  },
  
  actualizarAgente: async (agenteId, data) => {
    const response = await api.put(`/admin/agentes/${agenteId}`, data);
    return response.data;
  },
  
  eliminarAgente: async (agenteId) => {
    const response = await api.delete(`/admin/agentes/${agenteId}`);
    return response.data;
  },
  
  asignarAgente: async (seguroId, agenteId) => {
    const response = await api.post(`/admin/seguros/${seguroId}/asignar-agente`, { agente_id: agenteId });
    return response.data;
  },
  
  agregarSaldoAgente: async (agenteId, monto, observacion) => {
    const response = await api.post(`/admin/agentes/${agenteId}/agregar-saldo`, { monto, observacion });
    return response.data;
  },
  
  obtenerMovimientosAgente: async (agenteId) => {
    const response = await api.get(`/admin/agentes/${agenteId}/movimientos`);
    return response.data;
  },
  
  registrarCobroAgente: async (agenteId, monto, observacion) => {
    const response = await api.post(`/admin/agentes/${agenteId}/registrar-cobro`, { monto, observacion });
    return response.data;
  },
  
  obtenerCobrosAgente: async (agenteId) => {
    const response = await api.get(`/admin/agentes/${agenteId}/cobros`);
    return response.data;
  },
  
  // Premios
  crearPremio: async (data) => {
    const response = await api.post('/admin/premios', data);
    return response.data;
  },
  
  listarPremios: async () => {
    const response = await api.get('/admin/premios');
    return response.data;
  },
  
  eliminarPremio: async (premioId) => {
    const response = await api.delete(`/admin/premios/${premioId}`);
    return response.data;
  },
  
  // Vencimientos
  obtenerVencimientos: async () => {
    const response = await api.get('/admin/vencimientos');
    return response.data;
  }
};

export const agenteAPI = {
  login: async (username, password) => {
    const response = await api.post('/agente/login', { username, password });
    return response.data;
  },
  
  logout: async (token) => {
    const response = await api.post('/agente/logout', { token });
    return response.data;
  },
  
  verifyToken: async (token) => {
    const response = await api.get(`/agente/verify?token=${token}`);
    return response.data;
  },
  
  misSeguros: async (token) => {
    const response = await api.get(`/agente/mis-seguros?token=${token}`);
    return response.data;
  },
  
  misVencimientos: async (token) => {
    const response = await api.get(`/agente/vencimientos?token=${token}`);
    return response.data;
  },
  
  crearSeguro: async (token, data) => {
    const response = await api.post('/agente/crear-seguro', { token, ...data });
    return response.data;
  }
};

export const whatsappAPI = {
  // Connection
  getStatus: async () => {
    const response = await api.get('/admin/whatsapp/status');
    return response.data;
  },
  
  getQR: async () => {
    const response = await api.get('/admin/whatsapp/qr');
    return response.data;
  },
  
  connect: async () => {
    const response = await api.post('/admin/whatsapp/connect');
    return response.data;
  },
  
  disconnect: async () => {
    const response = await api.post('/admin/whatsapp/disconnect');
    return response.data;
  },
  
  // Configuration
  getConfig: async () => {
    const response = await api.get('/admin/whatsapp/config');
    return response.data;
  },
  
  updateConfig: async (data) => {
    const response = await api.put('/admin/whatsapp/config', data);
    return response.data;
  },
  
  // Conversations
  getConversations: async () => {
    const response = await api.get('/admin/whatsapp/conversations');
    return response.data;
  },
  
  getChatHistory: async (phoneNumber, limit = 50) => {
    const response = await api.get(`/admin/whatsapp/chat/${phoneNumber}?limit=${limit}`);
    return response.data;
  },
  
  // Chat management
  pauseChat: async (phoneNumber) => {
    const response = await api.post('/admin/whatsapp/pause-chat', { phone_number: phoneNumber });
    return response.data;
  },
  
  resumeChat: async (phoneNumber) => {
    const response = await api.post('/admin/whatsapp/resume-chat', { phone_number: phoneNumber });
    return response.data;
  },
  
  sendMessage: async (phoneNumber, message) => {
    const response = await api.post('/admin/whatsapp/send', { phone_number: phoneNumber, message });
    return response.data;
  }
};

export default api;
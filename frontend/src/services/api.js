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
  }
};

export default api;
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
  listarSeguros: async (skip = 0, limit = 50) => {
    const response = await api.get(`/admin/seguros?skip=${skip}&limit=${limit}`);
    return response.data;
  },
  
  marcarProcesado: async (seguroId) => {
    const response = await api.post(`/admin/seguros/${seguroId}/marcar-procesado`);
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
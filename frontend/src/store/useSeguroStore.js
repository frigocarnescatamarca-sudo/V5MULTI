import { create } from 'zustand';

export const useSeguroStore = create((set) => ({
  seguroActual: null,
  cotizacion: null,
  loading: false,
  error: null,
  
  setSeguroActual: (seguro) => set({ seguroActual: seguro }),
  setCotizacion: (cotizacion) => set({ cotizacion }),
  setLoading: (loading) => set({ loading }),
  setError: (error) => set({ error }),
  reset: () => set({ seguroActual: null, cotizacion: null, loading: false, error: null })
}));
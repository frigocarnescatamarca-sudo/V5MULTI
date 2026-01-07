import '@/App.css';
import { BrowserRouter, Routes, Route } from 'react-router-dom';
import Home from '@/pages/Home';
import PagoExitoso from '@/pages/PagoExitoso';
import PagoFallido from '@/pages/PagoFallido';
import PortalCliente from '@/pages/PortalCliente';
import AdminPanel from '@/pages/AdminPanel';
import PanelAgente from '@/pages/PanelAgente';
import Verificar from '@/pages/Verificar';
import { Toaster } from '@/components/ui/sonner';

function App() {
  return (
    <div className="App">
      <BrowserRouter>
        <Routes>
          <Route path="/" element={<Home />} />
          <Route path="/pago-exitoso" element={<PagoExitoso />} />
          <Route path="/pago-fallido" element={<PagoFallido />} />
          <Route path="/cliente" element={<PortalCliente />} />
          <Route path="/admin" element={<AdminPanel />} />
          <Route path="/agente" element={<PanelAgente />} />
          <Route path="/verificar/:numero_recibo" element={<Verificar />} />
        </Routes>
      </BrowserRouter>
      <Toaster />
    </div>
  );
}

export default App;
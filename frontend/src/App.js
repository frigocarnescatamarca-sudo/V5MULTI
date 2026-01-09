import '@/App.css';
import { BrowserRouter, Routes, Route } from 'react-router-dom';
import Home from '@/pages/Home';
import PagoExitoso from '@/pages/PagoExitoso';
import PagoFallido from '@/pages/PagoFallido';
import PortalCliente from '@/pages/PortalCliente';
import AdminPanel from '@/pages/AdminPanel';
import AdminSelector from '@/pages/AdminSelector';
import AdminSandwich from '@/pages/AdminSandwich';
import PanelAgente from '@/pages/PanelAgente';
import Verificar from '@/pages/Verificar';
import MisCoberturas from '@/pages/MisCoberturas';
import Terminos from '@/pages/Terminos';
import Privacidad from '@/pages/Privacidad';
// GastroBot SaaS
import GastrobotLogin from '@/pages/GastrobotLogin';
import GastrobotSuperAdmin from '@/pages/GastrobotSuperAdmin';
import GastrobotClientPanel from '@/pages/GastrobotClientPanel';
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
          <Route path="/admin-selector" element={<AdminSelector />} />
          <Route path="/admin" element={<AdminPanel />} />
          <Route path="/admin-sandwich" element={<AdminSandwich />} />
          <Route path="/agente" element={<PanelAgente />} />
          <Route path="/verificar/:numero_recibo" element={<Verificar />} />
          <Route path="/mis-coberturas" element={<MisCoberturas />} />
          <Route path="/terminos" element={<Terminos />} />
          <Route path="/privacidad" element={<Privacidad />} />
          {/* GastroBot SaaS Routes */}
          <Route path="/gastrobot" element={<GastrobotLogin />} />
          <Route path="/gastrobot/super" element={<GastrobotSuperAdmin />} />
          <Route path="/gastrobot/panel" element={<GastrobotClientPanel />} />
        </Routes>
      </BrowserRouter>
      <Toaster />
    </div>
  );
}

export default App;
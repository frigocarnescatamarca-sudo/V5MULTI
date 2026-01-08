import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { toast } from 'sonner';
import api from '@/services/api';

export default function AdminSelector() {
  const navigate = useNavigate();
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    // Check if already authenticated
    const token = localStorage.getItem('admin_token');
    if (token) {
      setIsAuthenticated(true);
    }
  }, []);

  const handleLogin = async (e) => {
    e.preventDefault();
    setLoading(true);
    try {
      const response = await api.post('/admin/login', { username, password });
      if (response.data.success) {
        localStorage.setItem('admin_token', response.data.token);
        setIsAuthenticated(true);
        toast.success('Sesión iniciada correctamente');
      }
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Credenciales incorrectas');
    } finally {
      setLoading(false);
    }
  };

  const handleLogout = () => {
    localStorage.removeItem('admin_token');
    setIsAuthenticated(false);
    toast.info('Sesión cerrada');
  };

  const goToSystem = (system) => {
    if (system === 'cobertura') {
      navigate('/admin');
    } else if (system === 'sandwich') {
      navigate('/admin-sandwich');
    }
  };

  if (!isAuthenticated) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-slate-100 to-slate-200 flex items-center justify-center p-4">
        <Card className="w-full max-w-md shadow-lg">
          <CardHeader className="text-center">
            <div className="mx-auto w-16 h-16 bg-gradient-to-br from-emerald-500 to-emerald-600 rounded-xl flex items-center justify-center mb-4">
              <span className="text-3xl">🔐</span>
            </div>
            <CardTitle className="text-2xl">Panel Administrativo</CardTitle>
            <CardDescription>Ingresá tus credenciales para continuar</CardDescription>
          </CardHeader>
          <CardContent>
            <form onSubmit={handleLogin} className="space-y-4">
              <div>
                <Label htmlFor="username">Usuario</Label>
                <Input
                  id="username"
                  type="text"
                  placeholder="admin"
                  value={username}
                  onChange={(e) => setUsername(e.target.value)}
                  required
                />
              </div>
              <div>
                <Label htmlFor="password">Contraseña</Label>
                <Input
                  id="password"
                  type="password"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  required
                />
              </div>
              <Button type="submit" className="w-full bg-emerald-600 hover:bg-emerald-700" disabled={loading}>
                {loading ? 'Ingresando...' : 'Iniciar Sesión'}
              </Button>
            </form>
          </CardContent>
        </Card>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-100 to-slate-200 flex items-center justify-center p-4">
      <div className="w-full max-w-3xl">
        <div className="text-center mb-8">
          <h1 className="text-3xl font-bold text-gray-800">Panel de Administración</h1>
          <p className="text-gray-600 mt-2">Seleccioná qué sistema querés gestionar</p>
        </div>

        <div className="grid md:grid-cols-2 gap-6">
          {/* Estonia Cobertura */}
          <Card 
            className="cursor-pointer hover:shadow-xl transition-all duration-300 hover:scale-[1.02] border-2 border-transparent hover:border-emerald-500"
            onClick={() => goToSystem('cobertura')}
          >
            <CardHeader className="text-center">
              <div className="mx-auto w-20 h-20 bg-gradient-to-br from-emerald-500 to-emerald-600 rounded-2xl flex items-center justify-center mb-4">
                <span className="text-4xl">🚗</span>
              </div>
              <CardTitle className="text-xl">Estonia Cobertura</CardTitle>
              <CardDescription>Gestión de coberturas vehiculares, agentes y bot de WhatsApp</CardDescription>
            </CardHeader>
            <CardContent>
              <ul className="text-sm text-gray-600 space-y-2">
                <li>✅ Coberturas / Seguros</li>
                <li>✅ Agentes y comisiones</li>
                <li>✅ Bot WhatsApp de ventas</li>
                <li>✅ Códigos promocionales</li>
              </ul>
              <Button className="w-full mt-4 bg-emerald-600 hover:bg-emerald-700">
                Ingresar →
              </Button>
            </CardContent>
          </Card>

          {/* Sandwichería */}
          <Card 
            className="cursor-pointer hover:shadow-xl transition-all duration-300 hover:scale-[1.02] border-2 border-transparent hover:border-amber-500"
            onClick={() => goToSystem('sandwich')}
          >
            <CardHeader className="text-center">
              <div className="mx-auto w-20 h-20 bg-gradient-to-br from-amber-500 to-orange-500 rounded-2xl flex items-center justify-center mb-4">
                <span className="text-4xl">🥪</span>
              </div>
              <CardTitle className="text-xl">Sandwichería</CardTitle>
              <CardDescription>Gestión de pedidos, menú y bot de WhatsApp para delivery</CardDescription>
            </CardHeader>
            <CardContent>
              <ul className="text-sm text-gray-600 space-y-2">
                <li>✅ Pedidos y entregas</li>
                <li>✅ Menú y precios</li>
                <li>✅ Bot WhatsApp de pedidos</li>
                <li>✅ Estadísticas de ventas</li>
              </ul>
              <Button className="w-full mt-4 bg-amber-500 hover:bg-amber-600">
                Ingresar →
              </Button>
            </CardContent>
          </Card>
        </div>

        <div className="text-center mt-8">
          <Button variant="ghost" onClick={handleLogout} className="text-gray-500">
            Cerrar Sesión
          </Button>
        </div>
      </div>
    </div>
  );
}

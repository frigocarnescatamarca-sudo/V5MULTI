import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { toast } from 'sonner';
import api from '@/services/api';

export default function GastrobotLogin() {
  const navigate = useNavigate();
  const [loginType, setLoginType] = useState('tenant'); // 'tenant' or 'super'
  const [credentials, setCredentials] = useState({ username: '', password: '' });
  const [loading, setLoading] = useState(false);

  const handleLogin = async (e) => {
    e.preventDefault();
    
    if (!credentials.username || !credentials.password) {
      toast.error('Completá usuario y contraseña');
      return;
    }
    
    setLoading(true);
    
    try {
      if (loginType === 'super') {
        // Super admin login
        const response = await api.post('/gastrobot/super/login', credentials);
        
        if (response.data.success) {
          localStorage.setItem('gastrobot_super_token', response.data.token);
          toast.success('¡Bienvenido Super Admin!');
          navigate('/gastrobot/super');
        }
      } else {
        // Tenant login
        const response = await api.post('/gastrobot/tenant/login', credentials);
        
        if (response.data.success) {
          localStorage.setItem('gastrobot_tenant_token', response.data.token);
          localStorage.setItem('gastrobot_tenant_id', response.data.tenant.id);
          localStorage.setItem('gastrobot_tenant_name', response.data.tenant.nombre_negocio);
          toast.success(`¡Bienvenido a ${response.data.tenant.nombre_negocio}!`);
          navigate('/gastrobot/panel');
        }
      }
    } catch (error) {
      console.error('Login error:', error);
      toast.error(error.response?.data?.detail || 'Credenciales inválidas');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-900 via-slate-800 to-emerald-900 flex items-center justify-center p-4">
      <div className="w-full max-w-md">
        {/* Logo and branding */}
        <div className="text-center mb-8">
          <div className="text-6xl mb-4">🤖</div>
          <h1 className="text-4xl font-bold text-white mb-2">GastroBot</h1>
          <p className="text-emerald-300">Sistema de Pedidos por WhatsApp</p>
        </div>

        <Card className="bg-slate-800/80 backdrop-blur border-slate-700">
          <CardHeader>
            <Tabs value={loginType} onValueChange={setLoginType} className="w-full">
              <TabsList className="grid w-full grid-cols-2 bg-slate-700">
                <TabsTrigger value="tenant" className="data-[state=active]:bg-emerald-600">
                  🏪 Mi Negocio
                </TabsTrigger>
                <TabsTrigger value="super" className="data-[state=active]:bg-emerald-600">
                  👑 Super Admin
                </TabsTrigger>
              </TabsList>
            </Tabs>
          </CardHeader>
          <CardContent>
            <form onSubmit={handleLogin} className="space-y-4">
              <div>
                <Label className="text-slate-300">Usuario</Label>
                <Input
                  type="text"
                  value={credentials.username}
                  onChange={(e) => setCredentials({...credentials, username: e.target.value})}
                  placeholder={loginType === 'super' ? 'superadmin' : 'usuario_negocio'}
                  className="bg-slate-700 border-slate-600 text-white placeholder:text-slate-400"
                  autoFocus
                />
              </div>
              <div>
                <Label className="text-slate-300">Contraseña</Label>
                <Input
                  type="password"
                  value={credentials.password}
                  onChange={(e) => setCredentials({...credentials, password: e.target.value})}
                  placeholder="••••••••"
                  className="bg-slate-700 border-slate-600 text-white"
                />
              </div>
              <Button 
                type="submit" 
                className="w-full bg-emerald-600 hover:bg-emerald-700 text-white"
                disabled={loading}
              >
                {loading ? 'Ingresando...' : 'Ingresar'}
              </Button>
            </form>

            {loginType === 'tenant' && (
              <p className="text-center text-slate-400 text-sm mt-4">
                ¿No tenés cuenta? Contactá al administrador
              </p>
            )}
          </CardContent>
        </Card>

        {/* Features */}
        <div className="mt-8 grid grid-cols-3 gap-4 text-center">
          <div className="text-white/70">
            <div className="text-2xl mb-1">📱</div>
            <p className="text-xs">WhatsApp Bot</p>
          </div>
          <div className="text-white/70">
            <div className="text-2xl mb-1">📊</div>
            <p className="text-xs">Analytics</p>
          </div>
          <div className="text-white/70">
            <div className="text-2xl mb-1">🛵</div>
            <p className="text-xs">Delivery</p>
          </div>
        </div>

        <p className="text-center text-slate-500 text-sm mt-8">
          © 2025 GastroBot - Sistema SaaS de Pedidos
        </p>
      </div>
    </div>
  );
}

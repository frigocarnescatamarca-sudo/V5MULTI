import { AlertCircle, Home, RefreshCw } from 'lucide-react';
import { Button } from '@/components/ui/button';

export default function PagoFallido() {
  return (
    <div className="min-h-screen bg-gradient-to-br from-red-50 to-white flex items-center justify-center p-6">
      <div className="max-w-md w-full bg-white rounded-3xl shadow-2xl p-8 text-center" data-testid="pago-fallido-card">
        <div className="w-20 h-20 bg-red-500 rounded-full flex items-center justify-center mx-auto mb-6">
          <AlertCircle className="w-12 h-12 text-white" />
        </div>
        
        <h1 className="text-3xl font-bold text-[#064E3B] mb-4" style={{ fontFamily: 'Manrope, sans-serif' }}>
          Pago Rechazado
        </h1>
        
        <p className="text-[#64748B] mb-8">
          Hubo un problema al procesar tu pago. Por favor, intenta nuevamente con otro método de pago.
        </p>

        <div className="space-y-3">
          <Button
            onClick={() => window.location.href = '/'}
            className="w-full bg-[#064E3B] hover:bg-[#064E3B]/90"
          >
            <RefreshCw className="w-4 h-4 mr-2" />
            Intentar Nuevamente
          </Button>
          <Button
            onClick={() => window.location.href = '/'}
            variant="outline"
            className="w-full"
          >
            <Home className="w-4 h-4 mr-2" />
            Volver al Inicio
          </Button>
        </div>
      </div>
    </div>
  );
}
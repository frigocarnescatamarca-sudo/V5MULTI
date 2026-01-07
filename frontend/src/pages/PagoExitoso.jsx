import { useSearchParams } from 'react-router-dom';
import { CheckCircle, Home } from 'lucide-react';
import { Button } from '@/components/ui/button';

export default function PagoExitoso() {
  const [searchParams] = useSearchParams();
  const paymentId = searchParams.get('payment_id');
  const preferenceId = searchParams.get('preference_id');

  return (
    <div className="min-h-screen bg-gradient-to-br from-[#F0FDF4] to-white flex items-center justify-center p-6">
      <div className="max-w-md w-full bg-white rounded-3xl shadow-2xl p-8 text-center" data-testid="pago-exitoso-card">
        <div className="w-20 h-20 bg-[#10B981] rounded-full flex items-center justify-center mx-auto mb-6">
          <CheckCircle className="w-12 h-12 text-white" />
        </div>
        
        <h1 className="text-3xl font-bold text-[#064E3B] mb-4" style={{ fontFamily: 'Manrope, sans-serif' }}>
          ¡Pago Exitoso!
        </h1>
        
        <p className="text-[#64748B] mb-8">
          Tu seguro ha sido procesado correctamente. En breve recibirás el comprobante por email.
        </p>

        {paymentId && (
          <div className="bg-slate-50 rounded-xl p-4 mb-8">
            <p className="text-sm text-[#64748B] mb-1">ID de Pago</p>
            <p className="font-mono text-sm text-[#064E3B]">{paymentId}</p>
          </div>
        )}

        <div className="space-y-3">
          <Button
            onClick={() => window.location.href = '/cliente'}
            className="w-full bg-[#064E3B] hover:bg-[#064E3B]/90"
            data-testid="ir-portal-cliente-btn"
          >
            Ver Mis Seguros
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
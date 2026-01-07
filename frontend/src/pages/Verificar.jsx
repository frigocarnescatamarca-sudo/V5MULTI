import { useEffect, useState } from 'react';
import { useParams } from 'react-router-dom';
import { CheckCircle, XCircle, Shield, Loader2 } from 'lucide-react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { segurosAPI } from '@/services/api';

export default function Verificar() {
  const { numero_recibo } = useParams();
  const [resultado, setResultado] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (numero_recibo) {
      verificarSeguro();
    }
  }, [numero_recibo]);

  const verificarSeguro = async () => {
    setLoading(true);
    try {
      const data = await segurosAPI.verificar(numero_recibo);
      setResultado(data);
    } catch (error) {
      setResultado({
        valido: false,
        mensaje: 'Error al verificar el seguro'
      });
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-[#F8FAFC] to-white flex items-center justify-center">
        <div className="text-center">
          <Loader2 className="w-12 h-12 text-[#064E3B] animate-spin mx-auto mb-4" />
          <p className="text-[#64748B]">Verificando seguro...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-[#F8FAFC] to-white flex items-center justify-center p-6">
      <Card className={`max-w-2xl w-full ${
        resultado?.valido ? 'border-[#10B981] border-2' : 'border-red-500 border-2'
      }`} data-testid="verificacion-card">
        <CardHeader className="text-center">
          <div className={`w-24 h-24 rounded-full flex items-center justify-center mx-auto mb-6 ${
            resultado?.valido ? 'bg-[#10B981]' : 'bg-red-500'
          }`}>
            {resultado?.valido ? (
              <CheckCircle className="w-16 h-16 text-white" />
            ) : (
              <XCircle className="w-16 h-16 text-white" />
            )}
          </div>
          <CardTitle className={`text-4xl font-bold ${
            resultado?.valido ? 'text-[#10B981]' : 'text-red-500'
          }`} style={{ fontFamily: 'Manrope, sans-serif' }}>
            {resultado?.mensaje}
          </CardTitle>
        </CardHeader>
        
        {resultado?.datos && (
          <CardContent className="space-y-6">
            <div className="bg-slate-50 rounded-xl p-6 space-y-4">
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <p className="text-sm text-[#64748B]">Número de Recibo</p>
                  <p className="text-xl font-mono font-bold text-[#064E3B]">{resultado.datos.numero_recibo}</p>
                </div>
                <div>
                  <p className="text-sm text-[#64748B]">Patente</p>
                  <p className="text-xl font-bold text-[#064E3B]">{resultado.datos.patente}</p>
                </div>
                <div>
                  <p className="text-sm text-[#64748B]">Asegurado</p>
                  <p className="font-semibold text-[#064E3B]">{resultado.datos.nombre}</p>
                  <p className="text-xs text-[#64748B]">DNI: {resultado.datos.dni}</p>
                </div>
                <div>
                  <p className="text-sm text-[#64748B]">Vehículo</p>
                  <p className="font-semibold text-[#064E3B]">{resultado.datos.marca} {resultado.datos.modelo}</p>
                  <p className="text-xs text-[#64748B]">Año: {resultado.datos.ano}</p>
                </div>
                <div>
                  <p className="text-sm text-[#64748B]">Cobertura</p>
                  <p className="font-semibold text-[#064E3B]">{resultado.datos.cobertura}</p>
                </div>
                <div>
                  <p className="text-sm text-[#64748B]">Vigencia</p>
                  <p className="font-semibold text-[#064E3B]">
                    {resultado.datos.vigencia_desde} al {resultado.datos.vigencia_hasta}
                  </p>
                </div>
              </div>
            </div>

            {resultado.valido && (
              <div className="bg-[#F0FDF4] border-2 border-[#10B981] rounded-xl p-6 text-center">
                <Shield className="w-12 h-12 text-[#10B981] mx-auto mb-3" />
                <p className="text-xl font-bold text-[#064E3B]">Seguro Válido para Circular</p>
                <p className="text-sm text-[#64748B] mt-2">Estonia Seguros - 0800 555 3543</p>
              </div>
            )}
          </CardContent>
        )}

        {!resultado?.datos && (
          <CardContent className="text-center py-8">
            <p className="text-[#64748B]">{resultado?.mensaje}</p>
          </CardContent>
        )}
      </Card>
    </div>
  );
}
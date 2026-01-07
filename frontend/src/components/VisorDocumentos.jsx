import { useState } from 'react';
import { X, Image as ImageIcon, FileText, CheckCircle, XCircle } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Dialog, DialogContent, DialogHeader, DialogTitle } from '@/components/ui/dialog';

export default function VisorDocumentos({ seguro, onClose }) {
  const [imagenSeleccionada, setImagenSeleccionada] = useState(null);

  const tiposDocumentos = [
    { tipo: 'frente', label: 'Foto Frente' },
    { tipo: 'lado_izq', label: 'Foto Lado Izquierdo' },
    { tipo: 'lado_der', label: 'Foto Lado Derecho' },
    { tipo: 'trasera', label: 'Foto Trasera' },
    { tipo: 'cedula_vehiculo', label: 'Cédula del Vehículo' },
    { tipo: 'carnet_conductor', label: 'Carnet de Conductor' }
  ];

  const obtenerUrlFoto = (tipo) => {
    const foto = seguro.fotos?.find(f => f.tipo === tipo);
    if (foto) {
      // Construir URL de la foto
      return `${process.env.REACT_APP_BACKEND_URL}/uploads/${foto.filename}`;
    }
    return null;
  };

  return (
    <Dialog open={true} onOpenChange={onClose}>
      <DialogContent className="max-w-6xl max-h-[90vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle className="text-2xl font-bold text-[#064E3B]">
            Documentación del Seguro - {seguro.patente}
          </DialogTitle>
          <p className="text-[#64748B]">
            Cliente: {seguro.nombre} | DNI: {seguro.dni}
          </p>
        </DialogHeader>

        <div className="space-y-6">
          {/* Grid de documentos */}
          <div className="grid md:grid-cols-3 gap-4">
            {tiposDocumentos.map(({ tipo, label }) => {
              const url = obtenerUrlFoto(tipo);
              const existe = seguro.fotos?.some(f => f.tipo === tipo);

              return (
                <div
                  key={tipo}
                  className={`relative border-2 rounded-xl overflow-hidden cursor-pointer transition-all ${
                    existe ? 'border-[#10B981] hover:shadow-lg' : 'border-slate-300 bg-slate-50'
                  }`}
                  onClick={() => existe && setImagenSeleccionada({ url, label })}
                  data-testid={`doc-${tipo}`}
                >
                  {existe ? (
                    <>
                      <div className="aspect-video bg-slate-100 flex items-center justify-center">
                        <img
                          src={url}
                          alt={label}
                          className="w-full h-full object-cover"
                          onError={(e) => {
                            e.target.src = 'data:image/svg+xml,%3Csvg xmlns="http://www.w3.org/2000/svg" width="100" height="100"%3E%3Crect fill="%23ddd" width="100" height="100"/%3E%3Ctext x="50%25" y="50%25" text-anchor="middle" dy=".3em" fill="%23999"%3ENo disponible%3C/text%3E%3C/svg%3E';
                          }}
                        />
                      </div>
                      <div className="p-3 bg-white">
                        <div className="flex items-center justify-between">
                          <p className="text-sm font-semibold text-[#064E3B]">{label}</p>
                          <CheckCircle className="w-4 h-4 text-[#10B981]" />
                        </div>
                        <p className="text-xs text-[#64748B] mt-1">Click para ampliar</p>
                      </div>
                    </>
                  ) : (
                    <div className="aspect-video flex flex-col items-center justify-center p-4">
                      <ImageIcon className="w-12 h-12 text-slate-400 mb-2" />
                      <p className="text-sm font-semibold text-slate-500">{label}</p>
                      <p className="text-xs text-slate-400">No cargado</p>
                      <XCircle className="w-4 h-4 text-red-500 mt-2" />
                    </div>
                  )}
                </div>
              );
            })}
          </div>

          {/* Información del seguro */}
          <div className="bg-slate-50 rounded-xl p-4">
            <h4 className="font-bold text-[#064E3B] mb-3">Información del Vehículo</h4>
            <div className="grid md:grid-cols-3 gap-4 text-sm">
              <div>
                <p className="text-[#64748B]">Patente</p>
                <p className="font-semibold text-[#064E3B]">{seguro.patente}</p>
              </div>
              <div>
                <p className="text-[#64748B]">Marca/Modelo</p>
                <p className="font-semibold text-[#064E3B]">{seguro.marca} {seguro.modelo}</p>
              </div>
              <div>
                <p className="text-[#64748B]">Año</p>
                <p className="font-semibold text-[#064E3B]">{seguro.ano}</p>
              </div>
              <div>
                <p className="text-[#64748B]">Estado Documentación</p>
                <p className={`font-semibold ${
                  seguro.fotos?.length === 6 ? 'text-[#10B981]' : 'text-red-500'
                }`}>
                  {seguro.fotos?.length || 0}/6 documentos cargados
                </p>
              </div>
            </div>
          </div>
        </div>
      </DialogContent>

      {/* Modal para ampliar imagen */}
      {imagenSeleccionada && (
        <Dialog open={true} onOpenChange={() => setImagenSeleccionada(null)}>
          <DialogContent className="max-w-4xl">
            <DialogHeader>
              <DialogTitle>{imagenSeleccionada.label}</DialogTitle>
            </DialogHeader>
            <div className="relative">
              <img
                src={imagenSeleccionada.url}
                alt={imagenSeleccionada.label}
                className="w-full h-auto rounded-lg"
              />
            </div>
            <div className="flex justify-end gap-2">
              <Button
                onClick={() => window.open(imagenSeleccionada.url, '_blank')}
                variant="outline"
              >
                Abrir en Nueva Pestaña
              </Button>
              <Button onClick={() => setImagenSeleccionada(null)}>
                Cerrar
              </Button>
            </div>
          </DialogContent>
        </Dialog>
      )}
    </Dialog>
  );
}

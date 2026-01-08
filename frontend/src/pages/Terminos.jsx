import { Shield, ArrowLeft } from 'lucide-react';
import { Button } from '@/components/ui/button';

export default function Terminos() {
  return (
    <div className="min-h-screen bg-gradient-to-b from-[#F8FAFC] to-white">
      {/* Header */}
      <header className="bg-white/80 backdrop-blur-xl border-b border-white/20 shadow-sm sticky top-0 z-50">
        <div className="container mx-auto px-6 py-4 flex justify-between items-center">
          <a href="/" className="flex items-center gap-3">
            <div className="w-10 h-10 bg-[#064E3B] rounded-xl flex items-center justify-center">
              <Shield className="w-5 h-5 text-[#D9F99D]" />
            </div>
            <span className="text-xl font-bold text-[#064E3B]">Estonia Cobertura</span>
          </a>
          <Button variant="ghost" onClick={() => window.location.href = '/'}>
            <ArrowLeft className="w-4 h-4 mr-2" />
            Volver
          </Button>
        </div>
      </header>

      {/* Content */}
      <main className="container mx-auto px-6 py-12 max-w-4xl">
        <h1 className="text-3xl md:text-4xl font-bold text-[#064E3B] mb-8" style={{ fontFamily: 'Manrope, sans-serif' }}>
          Términos y Condiciones
        </h1>

        <div className="prose prose-slate max-w-none space-y-8 text-[#64748B]">
          
          <section>
            <h2 className="text-xl font-bold text-[#064E3B] mb-4">1. Naturaleza del Servicio</h2>
            <p>
              Estonia Cobertura Colaborativa <strong>NO es una compañía de seguros</strong> ni opera bajo la regulación de la Superintendencia de Seguros de la Nación. 
              No emitimos pólizas ni contratos de seguro en los términos de la Ley N° 17.418.
            </p>
            <p>
              Funcionamos bajo un <strong>sistema de economía colaborativa y solidaria</strong>, donde los aportes de los miembros conforman un fondo común 
              destinado a brindar asistencia económica ante siniestros viales.
            </p>
          </section>

          <section>
            <h2 className="text-xl font-bold text-[#064E3B] mb-4">2. Sistema de Fondo Solidario</h2>
            <p>
              Los aportes realizados por los usuarios se destinan a un fondo solidario común. Este fondo tiene por objeto brindar 
              asistencia económica a los miembros que sufran siniestros vehiculares durante el período de vigencia de su membresía.
            </p>
            <p>
              <strong>Las coberturas están sujetas a la disponibilidad del fondo.</strong> En ningún caso existe obligación de pago 
              garantizada ni derecho adquirido a indemnización automática.
            </p>
          </section>

          <section>
            <h2 className="text-xl font-bold text-[#064E3B] mb-4">3. Cobertura Solidaria para Pasajeros</h2>
            <p>
              La cobertura solidaria para pasajeros funciona mediante un sistema de <strong>reintegro de gastos</strong> contra 
              presentación de comprobantes válidos (facturas, recibos, etc.).
            </p>
            <p>
              Los montos máximos de reintegro son:
            </p>
            <ul className="list-disc list-inside space-y-2 ml-4">
              <li>Medicamentos y atención médica: hasta $80.000</li>
              <li>Lesiones mayores (fracturas, estudios, tratamientos): hasta $200.000</li>
            </ul>
            <p>
              Los reintegros <strong>no son automáticos</strong> y están sujetos a la evaluación del caso, presentación de documentación 
              válida y disponibilidad del fondo solidario.
            </p>
          </section>

          <section>
            <h2 className="text-xl font-bold text-[#064E3B] mb-4">4. Aceptación de Términos</h2>
            <p>
              Al contratar cualquier membresía o cobertura a través de Estonia Cobertura Colaborativa, el usuario declara:
            </p>
            <ul className="list-disc list-inside space-y-2 ml-4">
              <li>Haber leído y comprendido estos términos y condiciones</li>
              <li>Aceptar que el servicio NO constituye un seguro tradicional</li>
              <li>Entender que las asistencias están sujetas a disponibilidad del fondo</li>
              <li>Ser mayor de 18 años y tener capacidad legal para contratar</li>
              <li>Proporcionar información veraz y actualizada</li>
            </ul>
          </section>

          <section>
            <h2 className="text-xl font-bold text-[#064E3B] mb-4">5. Responsabilidad del Usuario</h2>
            <p>El usuario se compromete a:</p>
            <ul className="list-disc list-inside space-y-2 ml-4">
              <li>Proporcionar datos verídicos del vehículo y del titular</li>
              <li>Notificar cualquier siniestro dentro de las 72 horas de ocurrido</li>
              <li>Presentar documentación original y válida para cualquier reclamo</li>
              <li>No utilizar el servicio para actividades ilícitas</li>
              <li>Mantener el vehículo en condiciones aptas para circular</li>
            </ul>
          </section>

          <section>
            <h2 className="text-xl font-bold text-[#064E3B] mb-4">6. Exclusiones</h2>
            <p>No se brindará asistencia en los siguientes casos:</p>
            <ul className="list-disc list-inside space-y-2 ml-4">
              <li>Siniestros ocurridos bajo efectos de alcohol o sustancias prohibidas</li>
              <li>Vehículos sin habilitación para circular</li>
              <li>Conductor sin licencia de conducir vigente</li>
              <li>Daños intencionales o por negligencia grave</li>
              <li>Siniestros no reportados en tiempo y forma</li>
              <li>Información falsa o fraudulenta</li>
              <li>Casos de fuerza mayor que afecten la disponibilidad del fondo</li>
            </ul>
          </section>

          <section>
            <h2 className="text-xl font-bold text-[#064E3B] mb-4">7. Vigencia y Renovación</h2>
            <p>
              Las membresías tienen una vigencia de 30 días corridos desde la fecha de activación. 
              No existe renovación automática. El usuario deberá contratar una nueva membresía al vencimiento si desea continuar.
            </p>
          </section>

          <section>
            <h2 className="text-xl font-bold text-[#064E3B] mb-4">8. Modificaciones</h2>
            <p>
              Estonia Cobertura Colaborativa se reserva el derecho de modificar estos términos y condiciones en cualquier momento. 
              Las modificaciones serán comunicadas a través de nuestros canales oficiales y entrarán en vigencia para las nuevas 
              membresías contratadas a partir de su publicación.
            </p>
          </section>

          <section>
            <h2 className="text-xl font-bold text-[#064E3B] mb-4">9. Jurisdicción</h2>
            <p>
              Estos términos y condiciones se rigen por las leyes de la República Argentina. 
              Para cualquier controversia que pudiera surgir, las partes se someten a la jurisdicción de los 
              Tribunales Ordinarios de la Ciudad Autónoma de Buenos Aires, renunciando a cualquier otro fuero o jurisdicción que pudiera corresponderles.
            </p>
          </section>

          <section>
            <h2 className="text-xl font-bold text-[#064E3B] mb-4">10. Contacto</h2>
            <p>
              Para consultas sobre estos términos y condiciones, puede contactarnos a través de nuestro canal de WhatsApp 
              o mediante los medios de contacto disponibles en nuestra página web.
            </p>
          </section>

          <div className="mt-12 p-6 bg-[#F8FAFC] rounded-xl border border-slate-200">
            <p className="text-sm text-[#64748B]">
              <strong>Última actualización:</strong> Enero 2025
            </p>
            <p className="text-sm text-[#64748B] mt-2">
              Al utilizar nuestros servicios, usted acepta estos términos y condiciones en su totalidad.
            </p>
          </div>
        </div>
      </main>

      {/* Footer */}
      <footer className="bg-[#0F172A] text-white py-8 mt-12">
        <div className="container mx-auto px-6 text-center">
          <p className="text-white/50 text-sm">
            © 2025 Estonia Cobertura Colaborativa. Sistema de economía colaborativa. No constituye un seguro.
          </p>
        </div>
      </footer>
    </div>
  );
}

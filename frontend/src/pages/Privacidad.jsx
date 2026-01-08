import { Shield, ArrowLeft } from 'lucide-react';
import { Button } from '@/components/ui/button';

export default function Privacidad() {
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
          Política de Privacidad
        </h1>

        <div className="prose prose-slate max-w-none space-y-8 text-[#64748B]">
          
          <section>
            <h2 className="text-xl font-bold text-[#064E3B] mb-4">1. Introducción</h2>
            <p>
              Estonia Cobertura Colaborativa se compromete a proteger la privacidad de sus usuarios en cumplimiento 
              con la Ley N° 25.326 de Protección de los Datos Personales de la República Argentina y su Decreto Reglamentario 1558/2001.
            </p>
            <p>
              Esta política describe cómo recopilamos, usamos y protegemos su información personal.
            </p>
          </section>

          <section>
            <h2 className="text-xl font-bold text-[#064E3B] mb-4">2. Datos que Recopilamos</h2>
            <p>Para brindar nuestros servicios, recopilamos los siguientes datos personales:</p>
            
            <h3 className="text-lg font-semibold text-[#064E3B] mt-4 mb-2">Datos del Titular:</h3>
            <ul className="list-disc list-inside space-y-1 ml-4">
              <li>Nombre completo</li>
              <li>Documento Nacional de Identidad (DNI)</li>
              <li>Dirección de correo electrónico</li>
              <li>Número de teléfono / WhatsApp</li>
            </ul>

            <h3 className="text-lg font-semibold text-[#064E3B] mt-4 mb-2">Datos del Vehículo:</h3>
            <ul className="list-disc list-inside space-y-1 ml-4">
              <li>Patente/Dominio</li>
              <li>Marca y modelo</li>
              <li>Año de fabricación</li>
              <li>Tipo de vehículo</li>
            </ul>

            <h3 className="text-lg font-semibold text-[#064E3B] mt-4 mb-2">Datos de Uso:</h3>
            <ul className="list-disc list-inside space-y-1 ml-4">
              <li>Historial de conversaciones por WhatsApp</li>
              <li>Fecha y hora de contratación</li>
              <li>Información de pagos realizados</li>
            </ul>
          </section>

          <section>
            <h2 className="text-xl font-bold text-[#064E3B] mb-4">3. Finalidad del Uso de Datos</h2>
            <p>Los datos personales recopilados se utilizan exclusivamente para:</p>
            <ul className="list-disc list-inside space-y-2 ml-4">
              <li><strong>Prestación del servicio:</strong> Generar y gestionar las membresías de cobertura vehicular</li>
              <li><strong>Emisión de certificados:</strong> Crear los comprobantes de cobertura con los datos del titular y vehículo</li>
              <li><strong>Comunicación:</strong> Contactar al usuario por WhatsApp para gestiones relacionadas con el servicio</li>
              <li><strong>Verificación:</strong> Validar la identidad del titular en caso de siniestros o reclamos</li>
              <li><strong>Mejora del servicio:</strong> Análisis interno para mejorar la experiencia del usuario</li>
            </ul>
          </section>

          <section>
            <h2 className="text-xl font-bold text-[#064E3B] mb-4">4. Uso de WhatsApp</h2>
            <p>
              Utilizamos WhatsApp como canal principal de comunicación y contratación. Al interactuar con nuestro servicio por este medio:
            </p>
            <ul className="list-disc list-inside space-y-2 ml-4">
              <li>Sus mensajes pueden ser almacenados para brindar un mejor servicio</li>
              <li>Podemos enviar notificaciones relacionadas con su cobertura</li>
              <li>Las conversaciones son confidenciales y no se comparten con terceros</li>
              <li>Puede solicitar la eliminación de su historial de conversaciones en cualquier momento</li>
            </ul>
          </section>

          <section>
            <h2 className="text-xl font-bold text-[#064E3B] mb-4">5. No Cesión a Terceros</h2>
            <p>
              <strong>Sus datos personales NO serán vendidos, alquilados ni cedidos a terceros</strong> para fines comerciales o de marketing.
            </p>
            <p>
              Solo se compartirán datos con terceros en los siguientes casos excepcionales:
            </p>
            <ul className="list-disc list-inside space-y-2 ml-4">
              <li>Cuando exista una obligación legal o requerimiento judicial</li>
              <li>Para la gestión de pagos (procesadores de pago autorizados)</li>
              <li>Cuando sea necesario para la resolución de un siniestro con el consentimiento del titular</li>
            </ul>
          </section>

          <section>
            <h2 className="text-xl font-bold text-[#064E3B] mb-4">6. Seguridad de los Datos</h2>
            <p>
              Implementamos medidas de seguridad técnicas y organizativas para proteger sus datos personales contra:
            </p>
            <ul className="list-disc list-inside space-y-1 ml-4">
              <li>Acceso no autorizado</li>
              <li>Alteración o destrucción</li>
              <li>Pérdida accidental</li>
              <li>Divulgación no autorizada</li>
            </ul>
          </section>

          <section>
            <h2 className="text-xl font-bold text-[#064E3B] mb-4">7. Derechos del Usuario</h2>
            <p>
              De acuerdo con la Ley 25.326, usted tiene derecho a:
            </p>
            <ul className="list-disc list-inside space-y-2 ml-4">
              <li><strong>Acceso:</strong> Solicitar información sobre qué datos suyos tenemos almacenados</li>
              <li><strong>Rectificación:</strong> Corregir datos inexactos o incompletos</li>
              <li><strong>Actualización:</strong> Mantener sus datos actualizados</li>
              <li><strong>Supresión:</strong> Solicitar la eliminación de sus datos cuando ya no sean necesarios</li>
              <li><strong>Confidencialidad:</strong> Exigir que sus datos sean tratados de forma confidencial</li>
            </ul>
            <p className="mt-4">
              Para ejercer estos derechos, puede contactarnos a través de nuestro canal de WhatsApp o correo electrónico.
            </p>
          </section>

          <section>
            <h2 className="text-xl font-bold text-[#064E3B] mb-4">8. Conservación de Datos</h2>
            <p>
              Los datos personales se conservarán durante el tiempo necesario para cumplir con la finalidad 
              para la que fueron recopilados y para cumplir con obligaciones legales aplicables.
            </p>
            <p>
              Una vez finalizada la relación comercial, los datos podrán ser conservados por un período adicional 
              de hasta 10 años para cumplir con obligaciones legales, contables o fiscales.
            </p>
          </section>

          <section>
            <h2 className="text-xl font-bold text-[#064E3B] mb-4">9. Cambios en la Política</h2>
            <p>
              Nos reservamos el derecho de modificar esta Política de Privacidad en cualquier momento. 
              Los cambios serán publicados en esta página y, de ser significativos, serán comunicados a través de nuestros canales oficiales.
            </p>
          </section>

          <section>
            <h2 className="text-xl font-bold text-[#064E3B] mb-4">10. Autoridad de Control</h2>
            <p>
              La Agencia de Acceso a la Información Pública (AAIP) es el órgano de control de la Ley N° 25.326 
              en la República Argentina. Si considera que sus derechos no han sido respetados, puede presentar 
              una denuncia ante dicho organismo.
            </p>
            <p className="mt-2">
              <strong>Agencia de Acceso a la Información Pública</strong><br />
              Av. Pte. Julio A. Roca 710, Piso 2°<br />
              Ciudad Autónoma de Buenos Aires<br />
              www.argentina.gob.ar/aaip
            </p>
          </section>

          <section>
            <h2 className="text-xl font-bold text-[#064E3B] mb-4">11. Contacto</h2>
            <p>
              Para consultas sobre esta Política de Privacidad o para ejercer sus derechos, puede contactarnos 
              a través de nuestro canal de WhatsApp o los medios de contacto disponibles en nuestra página web.
            </p>
          </section>

          <div className="mt-12 p-6 bg-[#F8FAFC] rounded-xl border border-slate-200">
            <p className="text-sm text-[#64748B]">
              <strong>Última actualización:</strong> Enero 2025
            </p>
            <p className="text-sm text-[#64748B] mt-2">
              Al utilizar nuestros servicios, usted acepta esta política de privacidad en su totalidad.
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

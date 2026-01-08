import { useState, useEffect } from 'react';
import { Shield, Phone, CheckCircle, Clock, FileText, Car, Smartphone, MessageCircle, Users, Stethoscope, BadgeCheck, Zap, ArrowRight } from 'lucide-react';
import { Button } from '@/components/ui/button';

const API_URL = process.env.REACT_APP_BACKEND_URL;

export default function Home() {
  const [whatsappVentas, setWhatsappVentas] = useState('');

  // Fetch WhatsApp ventas number on mount
  useEffect(() => {
    const fetchWhatsappVentas = async () => {
      try {
        const response = await fetch(`${API_URL}/api/whatsapp/ventas`);
        if (response.ok) {
          const data = await response.json();
          setWhatsappVentas(data.whatsapp_ventas || '');
        }
      } catch (error) {
        console.error('Error fetching WhatsApp ventas:', error);
      }
    };
    fetchWhatsappVentas();
  }, []);

  const handleWhatsAppClick = () => {
    if (whatsappVentas) {
      const mensaje = encodeURIComponent('Hola, quiero contratar una cobertura vehicular.');
      window.open(`https://wa.me/${whatsappVentas}?text=${mensaje}`, '_blank');
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-b from-[#F8FAFC] to-white">
      {/* Header */}
      <header className="bg-white/80 backdrop-blur-xl border-b border-white/20 shadow-sm sticky top-0 z-50">
        <div className="container mx-auto px-6 py-4 flex justify-between items-center">
          <div className="flex items-center gap-3">
            <div className="w-12 h-12 bg-[#064E3B] rounded-xl flex items-center justify-center">
              <Shield className="w-6 h-6 text-[#D9F99D]" />
            </div>
            <div>
              <h1 className="text-xl md:text-2xl font-bold text-[#064E3B]" style={{ fontFamily: 'Manrope, sans-serif' }}>
                ESTONIA COBERTURA
              </h1>
            </div>
          </div>
          <div className="hidden md:flex gap-4 items-center">
            {whatsappVentas && (
              <Button 
                onClick={handleWhatsAppClick}
                className="bg-[#25D366] hover:bg-[#128C7E] text-white rounded-full"
              >
                <MessageCircle className="w-4 h-4 mr-2" />
                Contratar Ahora
              </Button>
            )}
            <Button 
              variant="ghost" 
              onClick={() => window.location.href = '/mis-coberturas'}
              className="text-[#064E3B]"
            >
              Consultar
            </Button>
          </div>
        </div>
      </header>

      {/* HERO PRINCIPAL - Visible sin scroll */}
      <section className="relative overflow-hidden bg-gradient-to-br from-[#064E3B] to-[#10B981] py-16 md:py-24">
        <div className="absolute inset-0 bg-[url('https://images.unsplash.com/photo-1449965408869-eaa3f722e40d?crop=entropy&cs=srgb&fm=jpg&q=85&w=1920')] bg-cover bg-center opacity-10"></div>
        <div className="container mx-auto px-6 relative z-10">
          <div className="max-w-4xl mx-auto text-center">
            
            <h1 className="text-4xl sm:text-5xl lg:text-6xl font-extrabold text-white leading-tight mb-6" style={{ fontFamily: 'Manrope, sans-serif' }}>
              Cobertura para circular hoy
            </h1>
            
            <p className="text-xl md:text-2xl text-[#D9F99D] mb-8" style={{ fontFamily: 'Inter, sans-serif' }}>
              Certificado inmediato para autos, Uber, taxis y motos
            </p>
            
            {/* CTA Principal */}
            <div className="flex flex-col sm:flex-row gap-4 justify-center mb-12">
              <Button
                onClick={handleWhatsAppClick}
                className="bg-[#25D366] hover:bg-[#128C7E] text-white rounded-full px-10 py-7 text-xl font-bold shadow-2xl hover:shadow-3xl transition-all transform hover:-translate-y-1"
                data-testid="generar-seguro-apps-btn"
              >
                <MessageCircle className="w-6 h-6 mr-3" />
                Activar por WhatsApp
              </Button>
            </div>

            {/* Beneficios rápidos */}
            <div className="grid md:grid-cols-3 gap-4 mt-8">
              <div className="bg-white/10 backdrop-blur-md rounded-xl p-4 border border-white/20">
                <Zap className="w-8 h-8 text-[#D9F99D] mb-2 mx-auto" />
                <p className="text-white font-semibold">Activación en el día</p>
              </div>
              <div className="bg-white/10 backdrop-blur-md rounded-xl p-4 border border-white/20">
                <BadgeCheck className="w-8 h-8 text-[#D9F99D] mb-2 mx-auto" />
                <p className="text-white font-semibold">Certificado con QR</p>
              </div>
              <div className="bg-white/10 backdrop-blur-md rounded-xl p-4 border border-white/20">
                <FileText className="w-8 h-8 text-[#D9F99D] mb-2 mx-auto" />
                <p className="text-white font-semibold">100% Digital</p>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* A QUIÉN APLICA */}
      <section className="py-16 bg-white">
        <div className="container mx-auto px-6">
          <h2 className="text-2xl md:text-3xl font-bold text-center text-[#064E3B] mb-4" style={{ fontFamily: 'Manrope, sans-serif' }}>
            ¿Para quién es?
          </h2>
          <p className="text-center text-[#64748B] mb-12">Cobertura vehicular de 30 días</p>
          
          <div className="grid grid-cols-2 md:grid-cols-4 gap-6 max-w-4xl mx-auto">
            <div className="text-center p-6 bg-[#F8FAFC] rounded-2xl hover:shadow-lg transition-all">
              <div className="w-16 h-16 bg-[#064E3B] rounded-full flex items-center justify-center mx-auto mb-4">
                <Car className="w-8 h-8 text-[#D9F99D]" />
              </div>
              <h3 className="font-bold text-[#064E3B]">Autos Particulares</h3>
            </div>
            <div className="text-center p-6 bg-[#F8FAFC] rounded-2xl hover:shadow-lg transition-all">
              <div className="w-16 h-16 bg-[#064E3B] rounded-full flex items-center justify-center mx-auto mb-4">
                <Smartphone className="w-8 h-8 text-[#D9F99D]" />
              </div>
              <h3 className="font-bold text-[#064E3B]">Uber / Apps</h3>
            </div>
            <div className="text-center p-6 bg-[#F8FAFC] rounded-2xl hover:shadow-lg transition-all">
              <div className="w-16 h-16 bg-[#064E3B] rounded-full flex items-center justify-center mx-auto mb-4">
                <Car className="w-8 h-8 text-[#D9F99D]" />
              </div>
              <h3 className="font-bold text-[#064E3B]">Taxis / Remises</h3>
            </div>
            <div className="text-center p-6 bg-[#F8FAFC] rounded-2xl hover:shadow-lg transition-all">
              <div className="w-16 h-16 bg-[#064E3B] rounded-full flex items-center justify-center mx-auto mb-4">
                <Car className="w-8 h-8 text-[#D9F99D]" />
              </div>
              <h3 className="font-bold text-[#064E3B]">Motos / Delivery</h3>
            </div>
          </div>
        </div>
      </section>

      {/* BENEFICIOS PRINCIPALES */}
      <section className="py-16 bg-gradient-to-br from-[#F8FAFC] to-white">
        <div className="container mx-auto px-6">
          <div className="grid md:grid-cols-3 gap-8 max-w-5xl mx-auto">
            <div className="bg-white rounded-2xl p-8 border border-slate-100 shadow-lg text-center">
              <div className="w-16 h-16 bg-[#D9F99D] rounded-full flex items-center justify-center mx-auto mb-6">
                <Clock className="w-8 h-8 text-[#064E3B]" />
              </div>
              <h3 className="text-xl font-bold text-[#064E3B] mb-3">Activación Inmediata</h3>
              <p className="text-[#64748B]">Empezá a circular hoy mismo. Sin esperas.</p>
            </div>
            
            <div className="bg-white rounded-2xl p-8 border border-slate-100 shadow-lg text-center">
              <div className="w-16 h-16 bg-[#D9F99D] rounded-full flex items-center justify-center mx-auto mb-6">
                <BadgeCheck className="w-8 h-8 text-[#064E3B]" />
              </div>
              <h3 className="text-xl font-bold text-[#064E3B] mb-3">Certificado Válido</h3>
              <p className="text-[#64748B]">Con QR verificable para controles viales.</p>
            </div>
            
            <div className="bg-white rounded-2xl p-8 border border-slate-100 shadow-lg text-center">
              <div className="w-16 h-16 bg-[#D9F99D] rounded-full flex items-center justify-center mx-auto mb-6">
                <MessageCircle className="w-8 h-8 text-[#064E3B]" />
              </div>
              <h3 className="text-xl font-bold text-[#064E3B] mb-3">100% por WhatsApp</h3>
              <p className="text-[#64748B]">Sin apps, sin trámites. Simple y rápido.</p>
            </div>
          </div>
        </div>
      </section>

      {/* CTA Intermedio */}
      <section className="py-12 bg-[#064E3B]">
        <div className="container mx-auto px-6 text-center">
          <p className="text-xl text-white mb-6">¿Necesitás circular hoy?</p>
          <Button
            onClick={handleWhatsAppClick}
            className="bg-[#25D366] hover:bg-[#128C7E] text-white rounded-full px-8 py-6 text-lg font-bold"
          >
            <MessageCircle className="w-5 h-5 mr-2" />
            Activar Cobertura Ahora
          </Button>
        </div>
      </section>

      {/* COBERTURA SOLIDARIA PARA PASAJEROS */}
      <section className="py-20 bg-gradient-to-br from-purple-50 to-white">
        <div className="container mx-auto px-6">
          <div className="max-w-5xl mx-auto">
            <div className="text-center mb-12">
              <div className="inline-flex items-center gap-2 px-4 py-2 bg-purple-100 rounded-full mb-4">
                <Stethoscope className="w-5 h-5 text-purple-600" />
                <span className="text-sm font-semibold text-purple-700">Para Taxi, Uber y Apps</span>
              </div>
              <h2 className="text-3xl md:text-4xl font-bold text-[#064E3B] mb-4" style={{ fontFamily: 'Manrope, sans-serif' }}>
                Cobertura Solidaria para Pasajeros
              </h2>
              <p className="text-lg text-[#64748B] max-w-2xl mx-auto">
                Asistencia económica ante accidentes durante el viaje. Sistema de reintegro respaldado por fondo solidario.
              </p>
            </div>

            <div className="grid md:grid-cols-2 gap-8 mb-12">
              {/* Qué cubre */}
              <div className="bg-white rounded-2xl p-8 shadow-lg border border-purple-100">
                <h3 className="text-xl font-bold text-[#064E3B] mb-6 flex items-center gap-2">
                  <Stethoscope className="w-6 h-6 text-purple-500" />
                  ¿Qué cubre?
                </h3>
                
                <div className="space-y-6">
                  <div className="p-4 bg-purple-50 rounded-xl">
                    <p className="text-sm text-purple-600 mb-1">Medicamentos y atención médica</p>
                    <p className="text-3xl font-bold text-purple-700">Hasta $80.000</p>
                    <p className="text-xs text-purple-500 mt-1">Reintegro contra comprobantes</p>
                  </div>
                  
                  <div className="p-4 bg-purple-50 rounded-xl">
                    <p className="text-sm text-purple-600 mb-1">Lesiones mayores (fracturas, estudios, tratamientos)</p>
                    <p className="text-3xl font-bold text-purple-700">Hasta $200.000</p>
                    <p className="text-xs text-purple-500 mt-1">Reintegro contra comprobantes</p>
                  </div>
                </div>
              </div>

              {/* Cómo funciona */}
              <div className="bg-white rounded-2xl p-8 shadow-lg border border-purple-100">
                <h3 className="text-xl font-bold text-[#064E3B] mb-6 flex items-center gap-2">
                  <CheckCircle className="w-6 h-6 text-purple-500" />
                  ¿Cómo funciona?
                </h3>
                
                <div className="space-y-4">
                  <div className="flex items-start gap-4">
                    <div className="w-8 h-8 bg-purple-100 rounded-full flex items-center justify-center shrink-0 text-purple-700 font-bold">1</div>
                    <p className="text-[#64748B]">Ocurre un accidente durante el viaje</p>
                  </div>
                  <div className="flex items-start gap-4">
                    <div className="w-8 h-8 bg-purple-100 rounded-full flex items-center justify-center shrink-0 text-purple-700 font-bold">2</div>
                    <p className="text-[#64748B]">El pasajero recibe atención médica</p>
                  </div>
                  <div className="flex items-start gap-4">
                    <div className="w-8 h-8 bg-purple-100 rounded-full flex items-center justify-center shrink-0 text-purple-700 font-bold">3</div>
                    <p className="text-[#64748B]">Se presentan las facturas o comprobantes</p>
                  </div>
                  <div className="flex items-start gap-4">
                    <div className="w-8 h-8 bg-purple-100 rounded-full flex items-center justify-center shrink-0 text-purple-700 font-bold">4</div>
                    <p className="text-[#64748B]">Se reintegra el gasto hasta el monto máximo</p>
                  </div>
                </div>
              </div>
            </div>

            {/* Precio y CTA */}
            <div className="bg-gradient-to-r from-purple-600 to-purple-700 rounded-2xl p-8 text-white text-center">
              <p className="text-purple-200 mb-2">Cobertura vehicular + Cobertura solidaria pasajeros</p>
              <p className="text-5xl font-bold mb-4">$11.000</p>
              <div className="flex flex-wrap justify-center gap-4 mb-6 text-sm">
                <span className="flex items-center gap-1"><FileText className="w-4 h-4" /> Certificado incluido</span>
                <span className="flex items-center gap-1"><Zap className="w-4 h-4" /> Activación en el día</span>
                <span className="flex items-center gap-1"><CheckCircle className="w-4 h-4" /> Proceso simple</span>
              </div>
              <Button
                onClick={handleWhatsAppClick}
                className="bg-white text-purple-700 hover:bg-purple-50 rounded-full px-8 py-6 text-lg font-bold"
              >
                <MessageCircle className="w-5 h-5 mr-2" />
                Contratar Cobertura Pasajeros
              </Button>
            </div>

            {/* Aclaración legal */}
            <p className="text-xs text-center text-[#94A3B8] mt-6 max-w-3xl mx-auto">
              La cobertura para pasajeros funciona bajo un sistema de economía colaborativa y solidaria. No constituye un seguro ni una póliza. Los reintegros están sujetos a las condiciones del sistema y a la disponibilidad del fondo común.
            </p>
          </div>
        </div>
      </section>

      {/* PLANES Y PRECIOS */}
      <section className="py-20 bg-white">
        <div className="container mx-auto px-6">
          <h2 className="text-3xl md:text-4xl font-bold text-center text-[#064E3B] mb-4" style={{ fontFamily: 'Manrope, sans-serif' }}>
            Planes y Precios
          </h2>
          <p className="text-center text-[#64748B] mb-12">Vigencia de 30 días • Activación inmediata</p>
          
          <div className="grid md:grid-cols-2 lg:grid-cols-4 gap-6 max-w-6xl mx-auto">
            <PlanCard 
              tipo="Autos" 
              icon={<Car className="w-8 h-8" />}
              planes={[
                { nombre: 'Responsabilidad Civil', precio: 6000 },
                { nombre: 'Terceros Completo', precio: 9000 }
              ]}
            />
            <PlanCard 
              tipo="Motos / Delivery" 
              icon={<Car className="w-8 h-8" />}
              planes={[
                { nombre: 'Responsabilidad Civil', precio: 3500 },
                { nombre: 'Terceros Completo', precio: 5500 }
              ]}
            />
            <PlanCard 
              tipo="Taxis / Remises" 
              icon={<Car className="w-8 h-8" />}
              planes={[
                { nombre: 'Responsabilidad Civil', precio: 10000 },
                { nombre: 'Terceros Completo', precio: 18000 },
                { nombre: 'RC + Pasajeros', precio: 11000, highlight: true }
              ]}
            />
            <PlanCard 
              tipo="Uber / Apps" 
              icon={<Smartphone className="w-8 h-8" />}
              highlight={true}
              planes={[
                { nombre: 'Responsabilidad Civil', precio: 6000 },
                { nombre: 'Terceros Completo', precio: 9000 },
                { nombre: 'RC + Pasajeros', precio: 11000, highlight: true }
              ]}
            />
          </div>
        </div>
      </section>

      {/* CTA FINAL */}
      <section className="py-20 bg-[#064E3B] text-white">
        <div className="container mx-auto px-6 text-center">
          <h2 className="text-3xl md:text-4xl font-bold mb-4" style={{ fontFamily: 'Manrope, sans-serif' }}>
            Activación hoy, entrega inmediata
          </h2>
          <p className="text-lg text-[#D9F99D] mb-8">Tu certificado listo para circular en minutos</p>
          
          <Button
            onClick={handleWhatsAppClick}
            className="bg-[#25D366] hover:bg-[#128C7E] text-white rounded-full px-10 py-7 text-xl font-bold shadow-lg"
            data-testid="cta-generar-seguro-btn"
          >
            <MessageCircle className="w-6 h-6 mr-3" />
            Contratar por WhatsApp
            <ArrowRight className="w-5 h-5 ml-2" />
          </Button>
          
          <p className="text-white/60 text-sm mt-6">Sin apps • Sin trámites • 100% digital</p>
        </div>
      </section>

      {/* Footer con enlaces legales */}
      <footer className="bg-[#0F172A] text-white py-12">
        <div className="container mx-auto px-6">
          <div className="grid md:grid-cols-4 gap-8">
            <div>
              <h3 className="text-xl font-bold mb-4">Estonia Cobertura</h3>
              <p className="text-white/70">Cobertura vehicular colaborativa para circular tranquilo.</p>
            </div>
            <div>
              <h4 className="font-bold mb-4">Contacto</h4>
              <p className="text-white/70 mb-2">WhatsApp disponible</p>
              <p className="text-white/70">Atención de Lunes a Viernes</p>
            </div>
            <div>
              <h4 className="font-bold mb-4">Enlaces</h4>
              <ul className="space-y-2 text-white/70">
                <li><a href="/mis-coberturas" className="hover:text-[#D9F99D]">Consultar Coberturas</a></li>
                <li><a href="/cliente" className="hover:text-[#D9F99D]">Portal Cliente</a></li>
              </ul>
            </div>
            <div>
              <h4 className="font-bold mb-4">Legal</h4>
              <ul className="space-y-2 text-white/70">
                <li><a href="/terminos" className="hover:text-[#D9F99D]">Términos y Condiciones</a></li>
                <li><a href="/privacidad" className="hover:text-[#D9F99D]">Política de Privacidad</a></li>
              </ul>
            </div>
          </div>
          <div className="border-t border-white/10 mt-8 pt-8 text-center text-white/50 text-sm">
            <p>© 2025 Estonia Cobertura Colaborativa. Sistema de economía colaborativa. No constituye un seguro.</p>
          </div>
        </div>
      </footer>

      {/* Floating WhatsApp Button */}
      {whatsappVentas && (
        <button
          onClick={handleWhatsAppClick}
          className="fixed bottom-6 right-6 z-50 w-16 h-16 bg-[#25D366] hover:bg-[#128C7E] text-white rounded-full shadow-2xl flex items-center justify-center transition-all hover:scale-110 animate-bounce"
          style={{ animationDuration: '2s' }}
          title="Contactar por WhatsApp"
        >
          <MessageCircle className="w-8 h-8" />
        </button>
      )}
    </div>
  );
}

function PlanCard({ tipo, icon, planes, highlight = false }) {
  return (
    <div className={`relative overflow-hidden bg-white rounded-3xl p-6 border-2 transition-all shadow-lg hover:shadow-xl ${
      highlight ? 'border-[#10B981] ring-2 ring-[#10B981]/20' : 'border-transparent hover:border-[#10B981]'
    }`}>
      {highlight && (
        <div className="absolute top-4 right-4 px-3 py-1 bg-[#10B981] text-white text-xs font-bold rounded-full">
          POPULAR
        </div>
      )}
      <div className="text-[#064E3B] mb-4">{icon}</div>
      <h3 className="text-lg font-bold text-[#064E3B] mb-4" style={{ fontFamily: 'Manrope, sans-serif' }}>
        {tipo}
      </h3>
      <div className="space-y-3">
        {planes.map((plan, idx) => (
          <div key={idx} className={`border-t border-slate-100 pt-3 ${plan.highlight ? 'bg-purple-50 -mx-2 px-2 rounded-lg' : ''}`}>
            <p className={`text-sm mb-1 ${plan.highlight ? 'text-purple-600 font-medium' : 'text-[#64748B]'}`}>{plan.nombre}</p>
            <p className={`text-xl font-bold ${plan.highlight ? 'text-purple-700' : 'text-[#064E3B]'}`} style={{ fontFamily: 'Space Grotesk, monospace' }}>
              ${plan.precio.toLocaleString('es-AR')}
            </p>
          </div>
        ))}
      </div>
    </div>
  );
}

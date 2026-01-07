import { useState } from 'react';
import { Shield, Phone, CheckCircle, Clock, FileText, Download } from 'lucide-react';
import FormularioSeguro from '@/components/FormularioSeguro';
import { Button } from '@/components/ui/button';

export default function Home() {
  const [mostrarFormulario, setMostrarFormulario] = useState(false);

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
              <h1 className="text-2xl font-bold text-[#064E3B]" style={{ fontFamily: 'Manrope, sans-serif' }}>
                ESTONIA SEGUROS
              </h1>
            </div>
          </div>
          <div className="hidden md:flex gap-6">
            <Button 
              variant="ghost" 
              onClick={() => window.location.href = '/cliente'}
              className="text-[#064E3B]"
            >
              Portal Cliente
            </Button>
            <Button 
              variant="ghost" 
              onClick={() => window.location.href = '/admin'}
              className="text-[#064E3B]"
            >
              Admin
            </Button>
          </div>
        </div>
      </header>

      {/* Hero Section */}
      <section className="relative overflow-hidden py-20 md:py-32">
        <div className="absolute inset-0 bg-gradient-to-r from-[#064E3B]/10 to-[#10B981]/10 opacity-50"></div>
        <div className="container mx-auto px-6 relative z-10">
          <div className="grid md:grid-cols-2 gap-12 items-center">
            <div className="space-y-8">
              <div className="inline-block px-4 py-2 bg-[#D9F99D] rounded-full">
                <span className="text-sm font-semibold text-[#064E3B]">Seguro Express - 30 días de cobertura</span>
              </div>
              
              <h1 className="text-4xl sm:text-5xl lg:text-6xl font-extrabold text-[#064E3B] leading-tight" style={{ fontFamily: 'Manrope, sans-serif' }}>
                Generá tu seguro rápidamente para circular
              </h1>
              
              <p className="text-lg text-[#64748B]" style={{ fontFamily: 'Inter, sans-serif' }}>
                Obtené tu comprobante de seguro al instante. Válido para controles viales. Sin trámites, 100% digital.
              </p>
              
              <div className="flex flex-col sm:flex-row gap-4">
                <Button
                  onClick={() => setMostrarFormulario(true)}
                  className="bg-[#064E3B] text-white hover:bg-[#064E3B]/90 rounded-full px-8 py-6 text-lg font-bold shadow-lg hover:shadow-xl transition-all transform hover:-translate-y-1"
                  data-testid="generar-seguro-btn"
                >
                  Generar Seguro Ahora
                </Button>
                <Button
                  variant="outline"
                  className="border-2 border-[#064E3B] text-[#064E3B] hover:bg-[#F0FDF4] rounded-full px-6 py-6 font-semibold"
                >
                  Ver Coberturas
                </Button>
              </div>
              
              <div className="flex gap-6 text-sm text-[#64748B]">
                <div className="flex items-center gap-2">
                  <Phone className="w-4 h-4 text-[#10B981]" />
                  <span>0800 555 3543</span>
                </div>
                <div className="flex items-center gap-2">
                  <Phone className="w-4 h-4 text-[#10B981]" />
                  <span>0810 362 0700</span>
                </div>
              </div>
            </div>
            
            <div className="relative hidden md:block">
              <div className="absolute inset-0 bg-gradient-to-br from-[#10B981]/20 to-[#064E3B]/20 rounded-3xl transform rotate-3"></div>
              <img 
                src="https://images.unsplash.com/photo-1765301657633-b00e77256475?crop=entropy&cs=srgb&fm=jpg&q=85&w=800" 
                alt="Car highway" 
                className="relative rounded-3xl shadow-2xl"
              />
            </div>
          </div>
        </div>
      </section>

      {/* Características */}
      <section className="py-20 bg-white">
        <div className="container mx-auto px-6">
          <h2 className="text-3xl md:text-4xl font-bold text-center text-[#064E3B] mb-16" style={{ fontFamily: 'Manrope, sans-serif' }}>
            ¿Por qué elegir Estonia Seguros?
          </h2>
          
          <div className="grid md:grid-cols-3 gap-8">
            <div className="bg-white rounded-2xl p-8 border border-slate-100 shadow-card hover:shadow-floating transition-all duration-300">
              <div className="w-14 h-14 bg-[#D9F99D] rounded-xl flex items-center justify-center mb-6">
                <Clock className="w-7 h-7 text-[#064E3B]" />
              </div>
              <h3 className="text-xl font-bold text-[#064E3B] mb-3">Inmediato</h3>
              <p className="text-[#64748B]">Generá y descargá tu comprobante en minutos. Sin esperas ni trámites complicados.</p>
            </div>
            
            <div className="bg-white rounded-2xl p-8 border border-slate-100 shadow-card hover:shadow-floating transition-all duration-300">
              <div className="w-14 h-14 bg-[#D9F99D] rounded-xl flex items-center justify-center mb-6">
                <CheckCircle className="w-7 h-7 text-[#064E3B]" />
              </div>
              <h3 className="text-xl font-bold text-[#064E3B] mb-3">Válido para Controles</h3>
              <p className="text-[#64748B]">Con QR verificable por autoridades. Presentalo digital o impreso.</p>
            </div>
            
            <div className="bg-white rounded-2xl p-8 border border-slate-100 shadow-card hover:shadow-floating transition-all duration-300">
              <div className="w-14 h-14 bg-[#D9F99D] rounded-xl flex items-center justify-center mb-6">
                <FileText className="w-7 h-7 text-[#064E3B]" />
              </div>
              <h3 className="text-xl font-bold text-[#064E3B] mb-3">100% Digital</h3>
              <p className="text-[#64748B]">Todo online. Descargá PDF e imagen desde tu celular o computadora.</p>
            </div>
          </div>
        </div>
      </section>

      {/* Coberturas y Precios */}
      <section className="py-20 bg-gradient-to-br from-[#F8FAFC] to-[#F0FDF4]">
        <div className="container mx-auto px-6">
          <h2 className="text-3xl md:text-4xl font-bold text-center text-[#064E3B] mb-4" style={{ fontFamily: 'Manrope, sans-serif' }}>
            Planes y Coberturas
          </h2>
          <p className="text-center text-[#64748B] mb-16">Vigencia de 30 días desde la emisión</p>
          
          <div className="grid md:grid-cols-2 lg:grid-cols-4 gap-6">
            <PlanCard 
              tipo="Autos" 
              icon="🚗"
              planes={[
                { nombre: 'Responsabilidad Civil', precio: 6000 },
                { nombre: 'Terceros Completo', precio: 9000 }
              ]}
            />
            <PlanCard 
              tipo="Motos" 
              icon="🏍️"
              planes={[
                { nombre: 'Responsabilidad Civil', precio: 5000 },
                { nombre: 'Terceros Completo', precio: 7500 }
              ]}
            />
            <PlanCard 
              tipo="Taxis/Remises" 
              icon="🚕"
              planes={[
                { nombre: 'Responsabilidad Civil', precio: 10000 },
                { nombre: 'Terceros Completo', precio: 18000 }
              ]}
            />
            <PlanCard 
              tipo="Apps (Uber/Didi)" 
              icon="📱"
              planes={[
                { nombre: 'Responsabilidad Civil', precio: 6000 },
                { nombre: 'Terceros Completo', precio: 9000 }
              ]}
            />
          </div>
        </div>
      </section>

      {/* CTA Section */}
      <section className="py-20 bg-[#064E3B] text-white">
        <div className="container mx-auto px-6 text-center">
          <h2 className="text-3xl md:text-4xl font-bold mb-6" style={{ fontFamily: 'Manrope, sans-serif' }}>
            Obtené tu seguro en 3 simples pasos
          </h2>
          <p className="text-lg text-[#D9F99D] mb-12">Rápido, seguro y sin complicaciones</p>
          
          <div className="grid md:grid-cols-3 gap-8 mb-12">
            <div>
              <div className="w-16 h-16 bg-[#D9F99D] rounded-full flex items-center justify-center mx-auto mb-4 text-[#064E3B] font-bold text-2xl">
                1
              </div>
              <h3 className="text-xl font-bold mb-2">Completá tus datos</h3>
              <p className="text-white/80">Información del vehículo y fotos</p>
            </div>
            <div>
              <div className="w-16 h-16 bg-[#D9F99D] rounded-full flex items-center justify-center mx-auto mb-4 text-[#064E3B] font-bold text-2xl">
                2
              </div>
              <h3 className="text-xl font-bold mb-2">Realizá el pago</h3>
              <p className="text-white/80">MercadoPago seguro y rápido</p>
            </div>
            <div>
              <div className="w-16 h-16 bg-[#D9F99D] rounded-full flex items-center justify-center mx-auto mb-4 text-[#064E3B] font-bold text-2xl">
                3
              </div>
              <h3 className="text-xl font-bold mb-2">Descargá tu comprobante</h3>
              <p className="text-white/80">PDF e imagen con QR verificable</p>
            </div>
          </div>
          
          <Button
            onClick={() => setMostrarFormulario(true)}
            className="bg-[#D9F99D] text-[#064E3B] hover:bg-[#BEF264] rounded-full px-8 py-6 text-lg font-bold shadow-lg"
            data-testid="cta-generar-seguro-btn"
          >
            Comenzar Ahora
          </Button>
        </div>
      </section>

      {/* Footer */}
      <footer className="bg-[#0F172A] text-white py-12">
        <div className="container mx-auto px-6">
          <div className="grid md:grid-cols-3 gap-8">
            <div>
              <h3 className="text-xl font-bold mb-4">Estonia Seguros</h3>
              <p className="text-white/70">Seguros express para circular sin preocupaciones</p>
            </div>
            <div>
              <h4 className="font-bold mb-4">Contacto</h4>
              <p className="text-white/70 mb-2">0800 555 3543</p>
              <p className="text-white/70">0810 362 0700</p>
            </div>
            <div>
              <h4 className="font-bold mb-4">Enlaces</h4>
              <ul className="space-y-2 text-white/70">
                <li><a href="/cliente" className="hover:text-[#D9F99D]">Portal Cliente</a></li>
                <li><a href="/admin" className="hover:text-[#D9F99D]">Panel Admin</a></li>
              </ul>
            </div>
          </div>
          <div className="border-t border-white/10 mt-8 pt-8 text-center text-white/50">
            <p>© 2025 Estonia Seguros. Todos los derechos reservados.</p>
          </div>
        </div>
      </footer>

      {/* Modal Formulario */}
      {mostrarFormulario && (
        <FormularioSeguro onClose={() => setMostrarFormulario(false)} />
      )}
    </div>
  );
}

function PlanCard({ tipo, icon, planes }) {
  return (
    <div className="relative overflow-hidden bg-white rounded-3xl p-8 border-2 border-transparent hover:border-[#10B981] transition-all shadow-card hover:shadow-floating">
      <div className="text-4xl mb-4">{icon}</div>
      <h3 className="text-xl font-bold text-[#064E3B] mb-6" style={{ fontFamily: 'Manrope, sans-serif' }}>
        {tipo}
      </h3>
      <div className="space-y-4">
        {planes.map((plan, idx) => (
          <div key={idx} className="border-t border-slate-100 pt-4">
            <p className="text-sm text-[#64748B] mb-1">{plan.nombre}</p>
            <p className="text-2xl font-bold text-[#064E3B]" style={{ fontFamily: 'Space Grotesk, monospace' }}>
              ${plan.precio.toLocaleString('es-AR')}
            </p>
          </div>
        ))}
      </div>
    </div>
  );
}
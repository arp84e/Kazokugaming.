'use client';

export default function NewsletterBlock() {
  return (
    <section className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-16">
      <div className="relative bg-[#171D2D] border border-[#20293D] rounded-2xl p-8 md:p-12 overflow-hidden shadow-2xl">
        {/* Efecto de fondo translúcido */}
        <div className="absolute top-0 right-0 -mt-12 -mr-12 w-72 h-72 bg-[#00A8FF]/10 rounded-full blur-3xl pointer-events-none" />
        
        <div className="max-w-2xl relative z-10 space-y-4">
          <h2 className="text-2xl sm:text-3xl font-extrabold tracking-tight text-white">
            Mantente a la vanguardia tecnológica
          </h2>
          <p className="text-gray-400 text-sm sm:text-base">
            Únete a más de 5,000 apasionados. Recibe semanalmente resúmenes de reviews de hardware, lanzamientos gaming clave e integraciones de Inteligencia Artificial directo en tu correo.
          </p>
          
          <form className="pt-4 flex flex-col sm:flex-row gap-3 max-w-md" onSubmit={(e) => e.preventDefault()}>
            <input 
              type="email" 
              placeholder="Tu correo electrónico" 
              className="w-full px-4 py-3 rounded-lg bg-[#0B0F19] border border-[#20293D] text-white placeholder-gray-500 focus:outline-none focus:border-[#66C0F4] text-sm transition-colors"
              required
            />
            <button className="w-full sm:w-auto px-6 py-3 bg-[#00A8FF] hover:bg-[#66C0F4] text-white font-semibold rounded-lg text-sm transition-all shadow-lg shadow-[#00A8FF]/20 flex-shrink-0">
              Suscribirse
            </button>
          </form>
        </div>
      </div>
    </section>
  );
}

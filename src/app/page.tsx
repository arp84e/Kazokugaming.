'use client';

import { motion } from 'framer-motion';

export default function HomePage() {
  return (
    <div className="relative min-h-screen flex items-center justify-center overflow-hidden px-4 sm:px-6 lg:px-8">
      {/* Fondo con sutil gradiente tecnológico */}
      <div className="absolute inset-0 bg-[radial-gradient(circle_at_top,_var(--tw-gradient-stops))] from-[#1B2838] via-[#0B0F19] to-[#0B0F19] -z-10" />

      <div className="max-w-4xl text-center space-y-8">
        {/* Badge superior animado */}
        <motion.div 
          initial={{ opacity: 0, y: -20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5 }}
          className="inline-flex items-center gap-2 px-3 py-1 rounded-full border border-[#66C0F4]/20 bg-[#171D2D] text-sm text-[#66C0F4]"
        >
          <span className="w-2 h-2 rounded-full bg-[#00A8FF] animate-pulse" />
          Plan Maestro 2026 • Próximamente
        </motion.div>

        {/* Título Principal */}
        <motion.h1 
          initial={{ opacity: 0, scale: 0.95 }}
          animate={{ opacity: 1, scale: 1 }}
          transition={{ duration: 0.6, delay: 0.1 }}
          className="text-5xl sm:text-7xl font-extrabold tracking-tight"
        >
          KAZOKU<span className="text-[#66C0F4]">GAMING</span>
        </motion.h1>

        {/* Subtítulo */}
        <motion.p 
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ duration: 0.6, delay: 0.3 }}
          className="text-lg sm:text-xl text-gray-400 max-w-2xl mx-auto"
        >
          El nexo definitivo donde convergen los **Videojuegos**, la **Tecnología** de vanguardia y la **Inteligencia Artificial**.
        </motion.p>

        {/* CTA (Botones de Acción) */}
        <motion.div 
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6, delay: 0.5 }}
          className="flex flex-col sm:flex-row gap-4 justify-center items-center"
        >
          <button className="w-full sm:w-auto px-8 py-4 bg-[#00A8FF] hover:bg-[#66C0F4] text-white font-semibold rounded-lg shadow-lg shadow-[#00A8FF]/20 transition-all duration-300 transform hover:-translate-y-0.5">
            Explorar Portal
          </button>
          <button className="w-full sm:w-auto px-8 py-4 bg-[#171D2D] hover:bg-[#20293D] border border-gray-700 hover:border-gray-500 text-white font-semibold rounded-lg transition-all duration-300">
            Unirse a la Comunidad
          </button>
        </motion.div>
      </div>
    </div>
  );
}

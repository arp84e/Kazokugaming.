'use client';

import { motion } from 'framer-motion';
import FeaturedNews from '@/components/home/FeaturedNews';
import TrendingGrid from '@/components/home/TrendingGrid';
import NewsletterBlock from '@/components/home/NewsletterBlock';

export default function HomePage() {
  return (
    <div className="bg-[#0B0F19] min-h-screen">
      {/* 1. SECCIÓN HERO */}
      <div className="relative h-[80vh] flex items-center justify-center overflow-hidden px-4">
        <div className="absolute inset-0 bg-[radial-gradient(circle_at_top,_var(--tw-gradient-stops))] from-[#1B2838] via-[#0B0F19] to-[#0B0F19] -z-10" />
        <div className="max-w-4xl text-center space-y-6">
          <motion.div 
            initial={{ opacity: 0, y: -20 }}
            animate={{ opacity: 1, y: 0 }}
            className="inline-flex items-center gap-2 px-3 py-1 rounded-full border border-[#66C0F4]/20 bg-[#171D2D] text-sm text-[#66C0F4]"
          >
            <span className="w-2 h-2 rounded-full bg-[#00A8FF] animate-pulse" />
            Plan Maestro 2026 • En Desarrollo
          </motion.div>
          <motion.h1 
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            className="text-5xl sm:text-7xl font-extrabold tracking-tight text-white"
          >
            KAZOKU<span className="text-[#66C0F4]">GAMING</span>
          </motion.h1>
          <motion.p className="text-lg text-gray-400 max-w-xl mx-auto">
            El nexo definitivo donde convergen los Videojuegos, la Tecnología y la Inteligencia Artificial.
          </motion.p>
        </div>
      </div>

      {/* 2. BLOQUES DINÁMICOS */}
      <div className="space-y-8 bg-[#0B0F19]">
        <FeaturedNews />
        <TrendingGrid />
        <NewsletterBlock />
      </div>
    </div>
  );
}

import Link from 'next/link';

const trendingMock = [
  { id: '1', title: 'Guía de Optimización: Windows 11 para Gaming en 2026', views: '12K', comments: 45, category: 'Guías' },
  { id: '2', title: 'Review: Steam Deck OLED 2 ¿Vale la pena el salto de hardware?', views: '9.5K', comments: 88, category: 'Reviews' },
  { id: '3', title: 'Cómo integrar la API de Gemini 1.5 en tus scripts de automatización', views: '8.2K', comments: 32, category: 'IA' },
  { id: '4', title: 'Los mejores teclados mecánicos custom por menos de 100€', views: '6.1K', comments: 19, category: 'Tecnología' },
];

export default function TrendingGrid() {
  return (
    <section className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
      <h2 className="text-2xl font-bold tracking-tight mb-8 flex items-center gap-3">
        <span className="w-1 h-6 bg-[#66C0F4] rounded-full" />
        Tendencias de la Semana
      </h2>

      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6">
        {trendingMock.map((item) => (
          <div 
            key={item.id} 
            className="bg-[#171D2D] border border-[#20293D] rounded-xl p-5 hover:border-[#66C0F4]/40 transition-all duration-300 flex flex-col justify-between group"
          >
            <div className="space-y-3">
              <span className="text-xs font-semibold text-[#66C0F4] tracking-wider uppercase">
                {item.category}
              </span>
              <h3 className="text-base font-bold text-white group-hover:text-[#66C0F4] transition-colors line-clamp-3">
                <Link href="#">{item.title}</Link>
              </h3>
            </div>

            {/* Métricas interactivas simuladas */}
            <div className="flex items-center justify-between text-xs text-gray-500 mt-6 pt-3 border-t border-[#20293D]">
              <span className="flex items-center gap-1">
                👁️ {item.views} lecturas
              </span>
              <span className="flex items-center gap-1">
                💬 {item.comments}
              </span>
            </div>
          </div>
        ))}
      </div>
    </section>
  );
}

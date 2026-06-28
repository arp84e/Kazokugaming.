import Link from 'next/link';

interface TrendingGridProps {
  articles: any[];
}

export default function TrendingGrid({ articles }: TrendingGridProps) {
  // Si la base de datos está vacía o cargando, evitamos errores devolviendo null
  if (!articles || articles.length === 0) return null;

  // Tomamos un máximo de 4 artículos para mantener la cuadrícula simétrica de la Home
  const trendingArticles = articles.slice(0, 4);

  return (
    <section className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
      <h2 className="text-2xl font-bold tracking-tight mb-8 flex items-center gap-3">
        <span className="w-1 h-6 bg-[#66C0F4] rounded-full" />
        Tendencias de la Semana
      </h2>

      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6">
        {trendingArticles.map((item) => (
          <div 
            key={item.id} 
            className="bg-[#171D2D] border border-[#20293D] rounded-xl p-5 hover:border-[#66C0F4]/40 transition-all duration-300 flex flex-col justify-between group"
          >
            <div className="space-y-3">
              {/* Categoría real extraída mediante la relación de Supabase */}
              <span className="text-xs font-semibold text-[#66C0F4] tracking-wider uppercase">
                {item.categories?.name || 'General'}
              </span>
              
              {/* Título enlazado dinámicamente mediante su slug único */}
              <h3 className="text-base font-bold text-white group-hover:text-[#66C0F4] transition-colors line-clamp-3">
                <Link href={`/articulos/${item.slug}`}>
                  {item.title}
                </Link>
              </h3>
            </div>

            {/* Métricas reales vinculadas a la base de datos */}
            <div className="flex items-center justify-between text-xs text-gray-500 mt-6 pt-3 border-t border-[#20293D]">
              <span className="flex items-center gap-1">
                👁️ {item.view_count ?? 0} lecturas
              </span>
              
              {/* Nota: Dejamos el contador de comentarios en 0 de momento, ya que los implementaremos en la FASE 3 */}
              <span className="flex items-center gap-1">
                💬 0
              </span>
            </div>
          </div>
        ))}
      </div>
    </section>
  );
}

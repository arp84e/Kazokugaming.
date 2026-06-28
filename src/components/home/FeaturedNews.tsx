import Link from 'next/link';

interface ArticleMock {
  id: string;
  title: string;
  category: 'Gaming' | 'Tecnología' | 'IA';
  image: string;
  date: string;
  slug: string;
}

const featuredMock: ArticleMock[] = [
  {
    id: '1',
    title: 'Análisis a fondo del nuevo motor gráfico con IA: ¿El fin de la optimización tradicional?',
    category: 'IA',
    image: 'https://images.unsplash.com/photo-1618005182384-a83a8bd57fbe?w=800&auto=format&fit=crop&q=60',
    date: 'Hace 2 horas',
    slug: 'analisis-motor-grafico-ia',
  },
  {
    id: '2',
    title: 'RTX 5090 vs RX 9900 XTX: La batalla por los 4K nativos en 2026',
    category: 'Tecnología',
    image: 'https://images.unsplash.com/photo-1591488320449-011701bb6704?w=500&auto=format&fit=crop&q=60',
    date: 'Hace 5 horas',
    slug: 'rtx-5090-vs-rx-9900-xtx',
  },
  {
    id: '3',
    title: 'GTA VI retrasa su parche de rendimiento para consolas de nueva generación',
    category: 'Gaming',
    image: 'https://images.unsplash.com/photo-1542751371-adc38448a05e?w=500&auto=format&fit=crop&q=60',
    date: 'Ayer',
    slug: 'gta-vi-retraso-parche',
  },
];

export default function FeaturedNews() {
  const [main, ...secondaries] = featuredMock;

  return (
    <section className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
      <h2 className="text-2xl font-bold tracking-tight mb-8 flex items-center gap-3">
        <span className="w-1 h-6 bg-[#00A8FF] rounded-full" />
        Destacados del Momento
      </h2>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Noticia Principal */}
        <Link 
          href={`/articulos/${main.slug}`}
          className="lg:col-span-2 group relative h-[450px] rounded-xl overflow-hidden bg-[#171D2D] border border-[#20293D] flex flex-col justify-end p-6 sm:p-8"
        >
          <div className="absolute inset-0 bg-cover bg-center transition-transform duration-500 group-hover:scale-105" style={{ backgroundImage: `url(${main.image})` }} />
          <div className="absolute inset-0 bg-gradient-to-t from-[#0B0F19] via-[#0B0F19]/60 to-transparent" />
          
          <div className="relative z-10 space-y-3">
            <span className="px-2.5 py-1 text-xs font-semibold rounded bg-[#00A8FF] text-white uppercase tracking-wider">
              {main.category}
            </span>
            <h3 className="text-2xl sm:text-3xl font-extrabold text-white group-hover:text-[#66C0F4] transition-colors line-clamp-2">
              {main.title}
            </h3>
            <p className="text-xs text-gray-400">{main.date}</p>
          </div>
        </Link>

        {/* Noticias Secundarias */}
        <div className="flex flex-col gap-6">
          {secondaries.map((article) => (
            <Link
              key={article.id}
              href={`/articulos/${article.slug}`}
              className="group relative h-[213px] rounded-xl overflow-hidden bg-[#171D2D] border border-[#20293D] flex flex-col justify-end p-5"
            >
              <div className="absolute inset-0 bg-cover bg-center transition-transform duration-500 group-hover:scale-105" style={{ backgroundImage: `url(${article.image})` }} />
              <div className="absolute inset-0 bg-gradient-to-t from-[#0B0F19] via-[#0B0F19]/70 to-transparent" />
              
              <div className="relative z-10 space-y-2">
                <span className="px-2 py-0.5 text-[10px] font-semibold rounded bg-[#1B2838] border border-[#66C0F4]/30 text-[#66C0F4] uppercase">
                  {article.category}
                </span>
                <h4 className="text-lg font-bold text-white group-hover:text-[#66C0F4] transition-colors line-clamp-2">
                  {article.title}
                </h4>
                <p className="text-xs text-gray-400">{article.date}</p>
              </div>
            </Link>
          ))}
        </div>
      </div>
    </section>
  );
}

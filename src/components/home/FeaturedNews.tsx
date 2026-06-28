import Link from 'next/link';

// Definimos la estructura extendida que devuelve el JOIN de Supabase para la categoría
interface ExtendedArticle {
  id: string;
  title: string;
  slug: string;
  image_url: string | null;
  published_at: string | null;
  categories: { name: string } | null;
}

export default function FeaturedNews({ articles }: { articles: any[] }) {
  if (!articles || articles.length === 0) return null;

  const [main, ...secondaries] = articles;

  return (
    <section className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
      <h2 className="text-2xl font-bold tracking-tight mb-8 flex items-center gap-3">
        <span className="w-1 h-6 bg-[#00A8FF] rounded-full" />
        Destacados desde la Base de Datos
      </h2>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Noticia Principal */}
        {main && (
          <Link 
            href={`/articulos/${main.slug}`}
            className="lg:col-span-2 group relative h-[450px] rounded-xl overflow-hidden bg-[#171D2D] border border-[#20293D] flex flex-col justify-end p-6 sm:p-8"
          >
            <div className="absolute inset-0 bg-cover bg-center transition-transform duration-500 group-hover:scale-105" style={{ backgroundImage: `url(${main.image_url})` }} />
            <div className="absolute inset-0 bg-gradient-to-t from-[#0B0F19] via-[#0B0F19]/60 to-transparent" />
            
            <div className="relative z-10 space-y-3">
              <span className="px-2.5 py-1 text-xs font-semibold rounded bg-[#00A8FF] text-white uppercase tracking-wider">
                {main.categories?.name || 'General'}
              </span>
              <h3 className="text-2xl sm:text-3xl font-extrabold text-white group-hover:text-[#66C0F4] transition-colors line-clamp-2">
                {main.title}
              </h3>
              <p className="text-xs text-gray-400">
                {main.published_at ? new Date(main.published_at).toLocaleDateString('es-ES') : 'Reciente'}
              </p>
            </div>
          </Link>
        )}

        {/* Noticias Secundarias */}
        <div className="flex flex-col gap-6">
          {secondaries.slice(0, 2).map((article) => (
            <Link
              key={article.id}
              href={`/articulos/${article.slug}`}
              className="group relative h-[213px] rounded-xl overflow-hidden bg-[#171D2D] border border-[#20293D] flex flex-col justify-end p-5"
            >
              <div className="absolute inset-0 bg-cover bg-center transition-transform duration-500 group-hover:scale-105" style={{ backgroundImage: `url(${article.image_url})` }} />
              <div className="absolute inset-0 bg-gradient-to-t from-[#0B0F19] via-[#0B0F19]/70 to-transparent" />
              
              <div className="relative z-10 space-y-2">
                <span className="px-2 py-0.5 text-[10px] font-semibold rounded bg-[#1B2838] border border-[#66C0F4]/30 text-[#66C0F4] uppercase">
                  {article.categories?.name || 'General'}
                </span>
                <h4 className="text-lg font-bold text-white group-hover:text-[#66C0F4] transition-colors line-clamp-2">
                  {article.title}
                </h4>
                <p className="text-xs text-gray-400">
                  {article.published_at ? new Date(article.published_at).toLocaleDateString('es-ES') : 'Reciente'}
                </p>
              </div>
            </Link>
          ))}
        </div>
      </div>
    </section>
  );
}

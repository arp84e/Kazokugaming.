import { createClient } from '@/utils/supabase/server';
import FeaturedNews from '@/components/home/FeaturedNews';
import TrendingGrid from '@/components/home/TrendingGrid';
import NewsletterBlock from '@/components/home/NewsletterBlock';
import { Article } from '@/types/database';

export const revalidate = 0;

export default async function HomePage() {
  const supabase = await createClient();

  const { data: articles } = await supabase
    .from('articles')
    .select('*, categories(name)')
    .eq('status', 'published')
    .order('published_at', { ascending: false });

  const safeArticles: Article[] = articles || [];

  return (
    <div className="bg-[#0B0F19] min-h-screen">
      {/* SECCIÓN HERO ESTÁTICA INTEGRADA */}
      <div className="relative h-[60vh] flex items-center justify-center overflow-hidden px-4">
        <div className="absolute inset-0 bg-[radial-gradient(circle_at_top,_var(--tw-gradient-stops))] from-[#1B2838] via-[#0B0F19] to-[#0B0F19] -z-10" />
        <div className="max-w-4xl text-center space-y-6">
          <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full border border-[#66C0F4]/20 bg-[#171D2D] text-sm text-[#66C0F4]">
            <span className="w-2 h-2 rounded-full bg-[#00A8FF] animate-pulse" />
            Conectado a Base de Datos Live
          </div>
          <h1 className="text-5xl sm:text-7xl font-extrabold tracking-tight text-white">
            KAZOKU<span className="text-[#66C0F4]">GAMING</span>
          </h1>
          <p className="text-lg text-gray-400 max-w-xl mx-auto">
            El nexo definitivo donde convergen los Videojuegos, la Tecnología y la Inteligencia Artificial.
          </p>
        </div>
      </div>

      {/* BLOQUES DINÁMICOS CON DATOS REALES */}
      <div className="space-y-8 bg-[#0B0F19] pb-12">
        <FeaturedNews articles={safeArticles} />
        <TrendingGrid articles={safeArticles} />
        <NewsletterBlock />
      </div>
    </div>
  );
}

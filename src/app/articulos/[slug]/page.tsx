import { createClient } from '@/utils/supabase/server';
import { notFound } from 'next/navigation';
import Link from 'next/link';

interface ArticlePageProps {
  params: Promise<{ slug: string }>;
}

export default async function ArticleDetailPage({ params }: ArticlePageProps) {
  // En Next.js 15, debemos "desenvolver" los params asíncronamente
  const { slug } = await params;
  
  const supabase = await createClient();

  // Buscamos el artículo por su slug e incluimos el nombre de la categoría
  const { data: article } = await supabase
    .from('articles')
    .select('*, categories(name)')
    .eq('slug', slug)
    .eq('status', 'published')
    .single(); // Esperamos un único resultado

  // Si el artículo no existe o no está publicado, disparamos un 404 nativo
  if (!article) {
    notFound();
  }

  // Verificar si el artículo tiene una puntuación de Review (Sección 13 del plan)
  const hasReview = article.review_scores !== null;

  return (
    <article className="min-h-screen bg-[#0B0F19] text-white py-12 px-4 sm:px-6 lg:px-8">
      <div className="max-w-4xl mx-auto space-y-8">
        
        {/* Migas de pan (Breadcrumbs) & Categoría */}
        <div className="flex items-center gap-2 text-xs text-gray-400 uppercase tracking-wider">
          <Link href="/" className="hover:text-[#66C0F4] transition-colors">Inicio</Link>
          <span>/</span>
          <span className="text-[#66C0F4] font-semibold">{article.categories?.name || 'General'}</span>
        </div>

        {/* Encabezado del Artículo */}
        <div className="space-y-4">
          <h1 className="text-3xl sm:text-5xl font-extrabold tracking-tight leading-tight">
            {article.title}
          </h1>
          <p className="text-lg sm:text-xl text-gray-400 font-medium italic">
            {article.excerpt}
          </p>

          {/* Meta Información */}
          <div className="flex flex-wrap items-center gap-4 text-xs text-gray-500 pt-2 border-b border-[#171D2D] pb-4">
            <span>⏱️ {article.read_time} min de lectura</span>
            <span>•</span>
            <span>📅 {new Date(article.published_at).toLocaleDateString('es-ES', { day: 'numeric', month: 'long', year: 'numeric' })}</span>
            <span>•</span>
            <span>👁️ {article.view_count} vistas</span>
          </div>
        </div>

        {/* Imagen Destacada */}
        {article.image_url && (
          <div className="relative h-[250px] sm:h-[450px] w-full rounded-2xl overflow-hidden border border-[#20293D]">
            {/* eslint-disable-next-line @next/next/no-img-element */}
            <img 
              src={article.image_url} 
              alt={article.title}
              className="w-full height-full object-cover"
            />
          </div>
        )}

        {/* Cuerpo del Artículo + Bloque de Review de Steam (Si aplica) */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8 items-start">
          
          {/* Contenido Principal */}
          <div className="lg:col-span-2 space-y-6 text-gray-300 leading-relaxed text-base sm:text-lg whitespace-pre-line">
            {article.content}
          </div>

          {/* Sidebar: Tarjeta de Puntuación de Review (Estilo Steam) */}
          {hasReview && (
            <div className="bg-[#171D2D] border border-[#66C0F4]/30 rounded-xl p-6 space-y-4 sticky top-24">
              <h3 className="text-sm font-bold text-[#66C0F4] uppercase tracking-widest text-center border-b border-[#20293D] pb-2">
                Análisis Kazoku
              </h3>
              
              {/* Nota Final */}
              <div className="text-center py-4 bg-[#1B2838] rounded-lg border border-[#20293D]">
                <span className="block text-4xl font-black text-white">{article.review_scores.final}</span>
                <span className="text-[10px] text-gray-400 uppercase tracking-wider">Puntuación Total</span>
              </div>

              {/* Desglose de Notas */}
              <div className="space-y-3 text-xs">
                <div className="flex justify-between">
                  <span className="text-gray-400">Gráficos / Rendimiento:</span>
                  <span className="font-bold text-white">{article.review_scores.graphics}/100</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-400">Rendimiento Técnico:</span>
                  <span className="font-bold text-white">{article.review_scores.performance}/100</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-400">Innovación:</span>
                  <span className="font-bold text-white">{article.review_scores.innovation}/100</span>
                </div>
              </div>
            </div>
          )}
        </div>

        {/* Etiquetas / Tags */}
        {article.tags && article.tags.length > 0 && (
          <div className="pt-6 border-t border-[#171D2D] flex flex-wrap gap-2">
            {article.tags.map((tag: string) => (
              <span key={tag} className="px-2.5 py-1 text-xs rounded bg-[#171D2D] border border-[#20293D] text-gray-400">
                #{tag}
              </span>
            ))}
          </div>
        )}

      </div>
    </article>
  );
}

import Link from 'next/link';

export default function Footer() {
  return (
    <footer className="bg-[#0B0F19] border-t border-[#171D2D] text-gray-400 text-sm mt-auto">
      <div className="max-w-7xl mx-auto px-4 py-12 sm:px-6 lg:px-8">
        <div className="grid grid-cols-2 md:grid-cols-4 gap-8">
          {/* Columna Branding */}
          <div className="col-span-2 md:col-span-1 space-y-4">
            <h3 className="text-white font-bold text-lg tracking-wider">
              KAZOKU<span className="text-[#66C0F4]">GAMING</span>
            </h3>
            <p className="text-xs text-gray-500">
              El nexo definitivo de videojuegos, hardware y soluciones impulsadas por Inteligencia Artificial.
            </p>
          </div>

          {/* Columna Contenido */}
          <div>
            <h4 className="text-white font-semibold mb-4 text-xs uppercase tracking-wider text-[#66C0F4]">Contenido</h4>
            <ul className="space-y-2 text-xs">
              <li><Link href="/gaming" className="hover:text-white transition-colors">Videojuegos</Link></li>
              <li><Link href="/tecnologia" className="hover:text-white transition-colors">Tecnología</Link></li>
              <li><Link href="/ia" className="hover:text-white transition-colors">Inteligencia Artificial</Link></li>
              <li><Link href="/reviews" className="hover:text-white transition-colors">Análisis y Reviews</Link></li>
            </ul>
          </div>

          {/* Columna Comunidad */}
          <div>
            <h4 className="text-white font-semibold mb-4 text-xs uppercase tracking-wider text-[#66C0F4]">Comunidad</h4>
            <ul className="space-y-2 text-xs">
              <li><Link href="/foro" className="hover:text-white transition-colors">Foro Oficial</Link></li>
              <li><Link href="/herramientas" className="hover:text-white transition-colors">Herramientas</Link></li>
              <li><a href="https://discord.gg" target="_blank" rel="noreferrer" className="hover:text-white transition-colors">Discord</a></li>
            </ul>
          </div>
        </div>

        {/* Barra Inferior de Copyright */}
        <div className="mt-12 pt-6 border-t border-[#171D2D] flex flex-col sm:flex-row items-center justify-between gap-4">
          <p className="text-xs text-gray-600">
            &copy; {new Date().getFullYear()} KazokuGaming. Todos los derechos reservados.
          </p>
          <div className="flex space-x-6 text-xs text-gray-600">
            <Link href="/privacy" className="hover:text-gray-400">Privacidad</Link>
            <Link href="/terms" className="hover:text-gray-400">Términos de Servicio</Link>
            <Link href="/legal" className="hover:text-gray-400">Aviso Legal</Link>
          </div>
        </div>
      </div>
    </footer>
  );
}

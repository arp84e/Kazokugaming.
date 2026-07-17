document.addEventListener("DOMContentLoaded", function() {
    const isRoot = window.location.pathname.endsWith('index.html') || window.location.pathname.split('/').pop() === '';
    const prefix = isRoot ? '' : '../';

    const headerHTML = `
    <header class="border-b border-violet-900/30 bg-[#03040b]/90 backdrop-blur-xl sticky top-0 z-50">
        <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-16 flex items-center justify-between">
            <a href="${prefix}index.html" class="text-2xl font-black tracking-tight bg-gradient-to-r from-cyan-400 via-violet-400 to-fuchsia-500 bg-clip-text text-transparent relative z-50">
                KAZOKU<span class="text-slate-100 font-normal">GAMING</span>
            </a>
            
            <nav class="hidden md:flex space-x-7 items-center">
                <a href="${prefix}noticias.html" class="text-sm font-semibold text-slate-300 hover:text-violet-400 transition">Noticias</a>
                <a href="${prefix}juegos.html" class="text-sm font-semibold text-slate-300 hover:text-violet-400 transition">Juegos</a>
                <a href="${prefix}tecnologia.html" class="text-sm font-bold text-amber-400 hover:text-amber-300 transition tracking-wide">Tecnología</a>
                <a href="${prefix}guias.html" class="text-sm font-semibold text-slate-300 hover:text-emerald-400 transition">Guías</a>
                <a href="${prefix}radar.html" class="text-sm font-semibold text-slate-300 hover:text-violet-400 transition">Radar</a>
            </nav>

            <div class="flex-1 max-w-xs ml-8 relative hidden lg:block">
                <input type="text" id="buscador-global-desktop" placeholder="Buscar..." class="w-full bg-slate-900/50 border border-slate-700 text-slate-200 text-sm rounded-full px-4 py-2 focus:outline-none focus:border-violet-500 transition shadow-inner">
            </div>
            
            <button id="mobile-menu-btn" class="md:hidden text-slate-300 p-2 relative z-50">☰</button>
        </div>
        
        <div id="mobile-menu" class="hidden md:hidden bg-[#050610] border-b border-violet-900/30 absolute w-full left-0 top-16 shadow-2xl">
            <nav class="flex flex-col px-6 pt-4 pb-8 space-y-4">
                <a href="${prefix}noticias.html" class="text-base text-slate-300">Noticias</a>
                <a href="${prefix}juegos.html" class="text-base text-slate-300">Juegos</a>
                <a href="${prefix}tecnologia.html" class="text-base font-bold text-amber-400">Tecnología</a>
                <a href="${prefix}guias.html" class="text-base text-slate-300">Guías</a>
                <a href="${prefix}radar.html" class="text-base text-slate-300">Radar</a>
            </nav>
        </div>
    </header>`;

    const container = document.getElementById('header-container');
    if (container) {
        container.innerHTML = headerHTML;
        document.getElementById('mobile-menu-btn')?.addEventListener('click', () => {
            document.getElementById('mobile-menu').classList.toggle('hidden');
        });
        
        // SEGURIDAD: Sanitización de la barra de búsqueda
        function procesarBusqueda(e) {
            if (e.key === 'Enter' && e.target.value.trim()) {
                let busquedaSegura = e.target.value.trim().replace(/[<>]/g, '');
                window.location.href = `${prefix}buscar.html?q=${encodeURIComponent(busquedaSegura)}`;
            }
        }
        document.getElementById('buscador-global-desktop')?.addEventListener('keypress', procesarBusqueda);
    }
});

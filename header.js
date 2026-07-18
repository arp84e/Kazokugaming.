document.addEventListener("DOMContentLoaded", function() {
    const isRoot = window.location.pathname.endsWith('index.html') || window.location.pathname.split('/').pop() === '';
    const prefix = isRoot ? '' : '../';

    const headerHTML = `
    <header class="border-b border-violet-900/30 bg-[#03040b]/90 backdrop-blur-xl sticky top-0 z-50 shadow-[0_4px_30px_rgba(0,0,0,0.5)]">
        <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-16 flex items-center justify-between">
            <a href="${prefix}index.html" class="text-2xl font-black tracking-tight bg-gradient-to-r from-cyan-400 via-violet-400 to-fuchsia-500 bg-clip-text text-transparent relative z-50">
                KAZOKU<span class="text-slate-100 font-normal">GAMING</span>
            </a>
            
            <nav class="hidden md:flex space-x-6 lg:space-x-8 items-center">
                <a href="${prefix}noticias.html" class="text-sm font-semibold text-slate-300 hover:text-white transition">Noticias</a>
                <a href="${prefix}juegos.html" class="text-sm font-semibold text-slate-300 hover:text-violet-400 transition">Juegos</a>
                <a href="${prefix}tecnologia.html" class="text-sm font-bold text-amber-400 hover:text-amber-300 transition tracking-wide">Tecnología</a>
                <a href="${prefix}guias.html" class="text-sm font-semibold text-slate-300 hover:text-emerald-400 transition">Guías</a>
                <a href="${prefix}proyectos.html" class="text-sm font-bold text-sky-400 hover:text-sky-300 transition tracking-wide">Proyectos</a>
                <a href="${prefix}radar.html" class="text-sm font-semibold text-slate-300 hover:text-cyan-400 transition">Radar</a>
            </nav>

            <div class="flex-1 max-w-xs ml-8 relative hidden lg:block">
                <div class="relative">
                    <span class="absolute inset-y-0 left-0 flex items-center pl-3 text-slate-500">🔍</span>
                    <input type="text" id="buscador-global-desktop" placeholder="Buscar expedientes..." class="w-full bg-slate-900/80 border border-slate-700/50 text-slate-200 text-sm rounded-full pl-10 pr-4 py-2 focus:outline-none focus:border-violet-500 transition shadow-inner placeholder-slate-500 focus:bg-slate-900">
                </div>
            </div>
            
            <button id="mobile-menu-btn" class="md:hidden text-slate-300 p-2 relative z-50 hover:text-white transition">
                <svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 6h16M4 12h16M4 18h16"></path></svg>
            </button>
        </div>
        
        <div id="mobile-menu" class="hidden md:hidden bg-[#050610] border-b border-violet-900/30 absolute w-full left-0 top-16 shadow-2xl backdrop-blur-xl">
            <nav class="flex flex-col px-6 pt-4 pb-8 space-y-4">
                <a href="${prefix}noticias.html" class="text-base text-slate-300">Noticias</a>
                <a href="${prefix}juegos.html" class="text-base text-slate-300">Juegos</a>
                <a href="${prefix}tecnologia.html" class="text-base font-bold text-amber-400">Tecnología</a>
                <a href="${prefix}guias.html" class="text-base text-slate-300">Guías</a>
                <a href="${prefix}proyectos.html" class="text-base font-bold text-sky-400">Proyectos DIY</a>
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

// header.js - Componente de Navegación Global
document.addEventListener("DOMContentLoaded", function() {
    const isRoot = window.location.pathname.endsWith('index.html') || window.location.pathname.split('/').pop() === '';
    const prefix = isRoot ? '' : '../';

    const headerHTML = `
    <header class="border-b border-slate-800/80 bg-slate-900/90 backdrop-blur-md sticky top-0 z-50">
        <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-16 flex items-center justify-between">
            
            <a href="${prefix}index.html" class="text-2xl font-black tracking-tight bg-gradient-to-r from-cyan-400 to-indigo-500 bg-clip-text text-transparent relative z-50">
                KAZOKU<span class="text-slate-100 font-normal">GAMING</span>
            </a>
            
            <nav class="hidden md:flex space-x-8 items-center">
                <a href="${prefix}index.html" class="text-sm font-semibold text-slate-300 hover:text-cyan-400 transition">Inicio</a>
                <a href="${prefix}noticias.html" class="text-sm font-semibold text-slate-300 hover:text-cyan-400 transition">Noticias</a>
                <a href="${prefix}telemetria.html" class="text-sm font-semibold text-slate-300 hover:text-cyan-400 transition">Telemetría</a>
                <a href="${prefix}guias.html" class="text-sm font-bold text-emerald-400 hover:text-emerald-300 transition tracking-wide">Guías</a>
                <a href="${prefix}radar.html" class="text-sm font-semibold text-slate-300 hover:text-cyan-400 transition">Radar</a>
                <a href="${prefix}index.html#terminal-acceso" class="text-sm font-semibold text-slate-300 hover:text-cyan-400 transition flex items-center gap-1 bg-slate-800/50 px-3 py-1 rounded-full border border-slate-700">
                    <span class="w-2 h-2 rounded-full bg-emerald-500"></span> Mi Cuenta
                </a>
            </nav>

            <div class="flex-1 max-w-xs ml-8 relative hidden lg:block">
                <input type="text" id="buscador-global-desktop" placeholder="Buscar juego, guía o noticia..." class="w-full bg-slate-950 border border-slate-800 text-slate-200 text-sm rounded-full pl-4 pr-4 py-2 focus:outline-none focus:border-cyan-500 transition">
            </div>

            <button id="mobile-menu-btn" class="md:hidden text-slate-300 hover:text-cyan-400 focus:outline-none p-2 relative z-50">
                <svg id="menu-icon" class="w-6 h-6 transition-transform duration-200" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 6h16M4 12h16M4 18h16"></path>
                </svg>
            </button>
        </div>

        <div id="mobile-menu" class="hidden md:hidden bg-slate-900 border-b border-slate-800/80 absolute w-full left-0 top-16 shadow-2xl">
            <nav class="flex flex-col px-6 pt-4 pb-8 space-y-5">
                <a href="${prefix}index.html" class="text-base font-semibold text-slate-300 hover:text-cyan-400 transition">Inicio</a>
                <a href="${prefix}noticias.html" class="text-base font-semibold text-slate-300 hover:text-cyan-400 transition">Noticias</a>
                <a href="${prefix}telemetria.html" class="text-base font-semibold text-slate-300 hover:text-cyan-400 transition">Telemetría</a>
                <a href="${prefix}guias.html" class="text-base font-bold text-emerald-400 hover:text-emerald-300 transition">Guías</a>
                <a href="${prefix}radar.html" class="text-base font-semibold text-slate-300 hover:text-cyan-400 transition">Radar</a>
                <a href="${prefix}index.html#terminal-acceso" class="text-base font-bold text-indigo-400 hover:text-indigo-300 transition">🔑 Mi Cuenta / Login</a>
                
                <div class="pt-5 mt-2 border-t border-slate-800">
                    <input type="text" id="buscador-global-mobile" placeholder="Buscar en KazokuGaming..." class="w-full bg-slate-950 border border-slate-800 text-slate-200 text-sm rounded-lg px-4 py-3 focus:outline-none focus:border-cyan-500 transition">
                </div>
            </nav>
        </div>
    </header>
    `;

    const container = document.getElementById('header-container');
    if (container) {
        container.innerHTML = headerHTML;

        document.getElementById('mobile-menu-btn')?.addEventListener('click', () => {
            const menu = document.getElementById('mobile-menu');
            const icon = document.getElementById('menu-icon');
            menu.classList.toggle('hidden');
            icon.innerHTML = menu.classList.contains('hidden') 
                ? '<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 6h16M4 12h16M4 18h16"></path>'
                : '<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"></path>';
        });

        function procesarBusqueda(e) {
            if (e.key === 'Enter' && e.target.value.trim()) {
                window.location.href = `${prefix}buscar.html?q=${encodeURIComponent(e.target.value.trim())}`;
            }
        }

        document.getElementById('buscador-global-desktop')?.addEventListener('keypress', procesarBusqueda);
        document.getElementById('buscador-global-mobile')?.addEventListener('keypress', procesarBusqueda);
    }
});

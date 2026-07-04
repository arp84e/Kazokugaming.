// header.js - Componente de Navegación Global
document.addEventListener("DOMContentLoaded", function() {
    // Detectamos si estamos en la raíz para que los enlaces no se rompan
    const isRoot = window.location.pathname.endsWith('index.html') || window.location.pathname.split('/').pop() === '';
    const prefix = isRoot ? '' : '../';

    const headerHTML = `
    <header class="border-b border-slate-800/80 bg-slate-900/80 backdrop-blur-md sticky top-0 z-50">
        <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-16 flex items-center justify-between">
            
            <a href="${prefix}index.html" class="text-2xl font-black tracking-tight bg-gradient-to-r from-cyan-400 to-indigo-500 bg-clip-text text-transparent">
                KAZOKU<span class="text-slate-100 font-normal">GAMING</span>
            </a>
            
            <nav class="hidden md:flex space-x-8 items-center">
                <a href="${prefix}index.html" class="text-sm font-semibold text-slate-300 hover:text-cyan-400 transition">Inicio</a>
                <a href="${prefix}telemetria.html" class="text-sm font-semibold text-slate-300 hover:text-cyan-400 transition">Telemetría</a>
                <a href="${prefix}radar.html" class="text-sm font-semibold text-slate-300 hover:text-cyan-400 transition">Radar</a>
                <a href="${prefix}foro.html" class="text-sm font-semibold text-slate-300 hover:text-cyan-400 transition flex items-center gap-2">
                    <span class="w-2 h-2 rounded-full bg-cyan-400 animate-pulse"></span>
                    Foro
                </a>
            </nav>

            <div class="flex-1 max-w-xs ml-8 relative hidden lg:block">
                <input type="text" id="buscador-global" placeholder="Buscar artículo o juego..." class="w-full bg-slate-950 border border-slate-800 text-slate-200 text-sm rounded-full pl-4 pr-4 py-2 focus:outline-none focus:border-cyan-500 transition">
            </div>
            
        </div>
    </header>
    `;

    // Inyectamos el menú en la página
    const container = document.getElementById('header-container');
    if(container) {
        container.innerHTML = headerHTML;
    }
});

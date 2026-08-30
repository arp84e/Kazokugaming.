document.addEventListener("DOMContentLoaded", function() {
    const isRoot = window.location.pathname.endsWith('index.html') || window.location.pathname.split('/').pop() === '';
    const prefix = isRoot ? '' : '../';

    const headerHTML = `
    <header class="border-b border-indigo-900/50 bg-[#0a0a0f]/95 backdrop-blur-xl sticky top-0 z-50 shadow-[0_4px_30px_rgba(79,70,229,0.15)]">
        <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-20 flex items-center justify-between">
            
            <!-- LOGO -->
            <a href="${prefix}index.html" class="flex items-center gap-2 text-2xl font-black tracking-tighter relative z-50">
                <div class="w-8 h-8 rounded-lg bg-gradient-to-br from-indigo-500 to-fuchsia-500 flex items-center justify-center text-white shadow-lg shadow-indigo-500/30">K</div>
                <span class="bg-gradient-to-r from-white via-slate-200 to-slate-400 bg-clip-text text-transparent">
                    KAZOKU<span class="text-indigo-400 font-bold">GAMING</span>
                </span>
            </a>
            
            <!-- NAVEGACIÓN DESKTOP -->
            <nav class="hidden md:flex space-x-8 items-center bg-slate-900/50 px-6 py-2 rounded-full border border-slate-800">
                <a href="${prefix}index.html" class="text-sm font-bold text-slate-300 hover:text-indigo-400 transition flex items-center gap-2">🎯 Partidas</a>
                <a href="${prefix}torneos.html" class="text-sm font-bold text-slate-300 hover:text-fuchsia-400 transition flex items-center gap-2">🏆 Torneos</a>
                <a href="${prefix}grupos.html" class="text-sm font-bold text-slate-300 hover:text-emerald-400 transition flex items-center gap-2">🛡️ Escuadrones</a>
            </nav>

            <!-- PERFIL / ACCESO -->
            <div class="hidden lg:flex items-center gap-4">
                <a href="${prefix}login.html" class="text-sm font-semibold text-slate-300 hover:text-white transition">Iniciar Sesión</a>
                <button id="btn-crear-evento" class="px-5 py-2.5 bg-gradient-to-r from-indigo-600 to-violet-600 hover:from-indigo-500 hover:to-violet-500 text-white text-sm font-bold rounded-xl transition-all shadow-lg shadow-indigo-500/25 hover:scale-105">
                    + Crear Partida
                </button>
            </div>
            
            <!-- MENÚ MÓVIL (BOTÓN) -->
            <button id="mobile-menu-btn" class="md:hidden text-slate-300 p-2 relative z-50 hover:text-white transition">
                <svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 6h16M4 12h16M4 18h16"></path></svg>
            </button>
        </div>
        
        <!-- MENÚ MÓVIL (DESPLEGABLE) -->
        <div id="mobile-menu" class="hidden md:hidden bg-[#0a0a0f] border-b border-indigo-900/50 absolute w-full left-0 top-20 shadow-2xl backdrop-blur-xl">
            <nav class="flex flex-col px-6 pt-4 pb-8 space-y-4">
                <a href="${prefix}index.html" class="text-base font-bold text-slate-300">🎯 Buscar Partidas</a>
                <a href="${prefix}torneos.html" class="text-base font-bold text-slate-300">🏆 Torneos Activos</a>
                <a href="${prefix}grupos.html" class="text-base font-bold text-slate-300">🛡️ Mis Escuadrones</a>
                <hr class="border-slate-800">
                <a href="${prefix}login.html" class="w-full py-3 bg-indigo-600 text-center block text-white font-bold rounded-xl mt-4">Iniciar Sesión</a>
            </nav>
        </div>
    </header>`;

    const container = document.getElementById('header-container');
    if (container) {
        container.innerHTML = headerHTML;
        document.getElementById('mobile-menu-btn')?.addEventListener('click', () => {
            document.getElementById('mobile-menu').classList.toggle('hidden');
        });
    }
});

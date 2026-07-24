// header.js
document.addEventListener("DOMContentLoaded", () => {
    const headerContainer = document.getElementById("header-container");

    if (headerContainer) {
        headerContainer.innerHTML = `
            <header class="fixed w-full top-0 z-50 glass-panel border-b border-slate-800/80">
                <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
                    <div class="flex items-center justify-between h-16">
                        <!-- Logo -->
                        <div class="flex-shrink-0">
                            <a href="index.html" class="flex items-center gap-2">
                                <span class="text-2xl font-black text-transparent bg-clip-text bg-gradient-to-r from-amber-400 to-amber-600 tracking-tighter">KAZOKU</span>
                                <span class="text-2xl font-black text-white tracking-tighter">GAMING</span>
                            </a>
                        </div>
                        
                        <!-- Navegación de Escritorio -->
                        <nav class="hidden md:block">
                            <ul class="flex space-x-8">
                                <li><a href="noticias.html" class="text-sm font-bold text-slate-300 hover:text-amber-400 transition-colors">Noticias</a></li>
                                <li><a href="juegos.html" class="text-sm font-bold text-slate-300 hover:text-amber-400 transition-colors">Juegos</a></li>
                                <li><a href="tecnologia.html" class="text-sm font-bold text-slate-300 hover:text-amber-400 transition-colors">Hardware</a></li>
                                <li><a href="guias.html" class="text-sm font-bold text-slate-300 hover:text-amber-400 transition-colors">Guías</a></li>
                                <li><a href="radar.html" class="text-sm font-bold text-amber-500 hover:text-amber-400 transition-colors flex items-center gap-1"><span class="w-1.5 h-1.5 rounded-full bg-amber-500 animate-pulse"></span> Radar de Ofertas</a></li>
                            </ul>
                        </nav>

                        <!-- Botón Menú Móvil -->
                        <div class="md:hidden flex items-center">
                            <button id="mobile-menu-btn" class="text-slate-300 hover:text-white focus:outline-none">
                                <svg class="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 6h16M4 12h16M4 18h16"/>
                                </svg>
                            </button>
                        </div>
                    </div>
                </div>

                <!-- Menú Móvil Desplegable -->
                <div id="mobile-menu" class="hidden md:hidden bg-[#03040b] border-b border-slate-800">
                    <ul class="px-2 pt-2 pb-3 space-y-1 sm:px-3">
                        <li><a href="noticias.html" class="block px-3 py-2 rounded-md text-base font-medium text-slate-300 hover:text-white hover:bg-slate-800">Noticias</a></li>
                        <li><a href="juegos.html" class="block px-3 py-2 rounded-md text-base font-medium text-slate-300 hover:text-white hover:bg-slate-800">Juegos</a></li>
                        <li><a href="tecnologia.html" class="block px-3 py-2 rounded-md text-base font-medium text-slate-300 hover:text-white hover:bg-slate-800">Hardware</a></li>
                        <li><a href="guias.html" class="block px-3 py-2 rounded-md text-base font-medium text-slate-300 hover:text-white hover:bg-slate-800">Guías</a></li>
                        <li><a href="radar.html" class="block px-3 py-2 rounded-md text-base font-medium text-amber-500 hover:text-amber-400 hover:bg-slate-800">Radar de Ofertas</a></li>
                    </ul>
                </div>
            </header>
        `;

        // Lógica para abrir/cerrar el menú en celulares
        const btn = document.getElementById("mobile-menu-btn");
        const menu = document.getElementById("mobile-menu");
        if(btn && menu) {
            btn.addEventListener("click", () => {
                menu.classList.toggle("hidden");
            });
        }
    }
});

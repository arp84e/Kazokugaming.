// header.js - Componente de Navegación Universal Responsivo
document.addEventListener("DOMContentLoaded", function() {
    // 1. Estructura HTML con Doble Menú (Escritorio + Móvil)
    const headerHTML = `
    <header class="border-b border-slate-800/80 bg-slate-900/50 backdrop-blur-md sticky top-0 z-50">
        <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-16 flex items-center justify-between">
            
            <a href="index.html" class="text-xl font-extrabold tracking-tight bg-gradient-to-r from-cyan-400 to-indigo-500 bg-clip-text text-transparent z-50">
                KAZOKU<span class="text-slate-100">GAMING</span>
            </a>
            
            <nav class="hidden md:flex space-x-6 text-sm font-medium" id="main-nav">
                <a href="index.html" class="nav-link text-slate-400 hover:text-cyan-400 transition" id="link-index">Noticias</a>
                <a href="telemetria.html" class="nav-link text-slate-400 hover:text-cyan-400 transition" id="link-telemetria">Telemetría</a>
                <a href="radar.html" class="nav-link text-slate-400 hover:text-cyan-400 transition" id="link-radar">Radar de Ofertas</a>
                <a href="hardware.html" class="nav-link text-slate-400 hover:text-cyan-400 transition" id="link-hardware">Hardware</a>
                <a href="foro.html" class="nav-link text-amber-400 hover:text-amber-300 transition font-bold" id="link-foro">Foro 💬</a>
            </nav>

            <div class="md:hidden flex items-center z-50">
                <button id="mobile-menu-btn" class="text-slate-400 hover:text-white focus:outline-none cursor-pointer p-2 transition">
                    <svg class="h-6 w-6" id="menu-icon" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 6h16M4 12h16M4 18h16" />
                    </svg>
                </button>
            </div>
        </div>

        <div id="mobile-menu" class="hidden md:hidden bg-slate-900 border-b border-slate-800 absolute w-full shadow-2xl transition-all duration-300 origin-top">
            <div class="px-4 pt-2 pb-6 space-y-2 flex flex-col">
                <a href="index.html" class="block px-4 py-3 rounded-lg text-base font-medium text-slate-400 hover:text-white hover:bg-slate-800 transition" id="mob-link-index">Noticias</a>
                <a href="telemetria.html" class="block px-4 py-3 rounded-lg text-base font-medium text-slate-400 hover:text-white hover:bg-slate-800 transition" id="mob-link-telemetria">Telemetría</a>
                <a href="radar.html" class="block px-4 py-3 rounded-lg text-base font-medium text-slate-400 hover:text-white hover:bg-slate-800 transition" id="mob-link-radar">Radar de Ofertas</a>
                <a href="hardware.html" class="block px-4 py-3 rounded-lg text-base font-medium text-slate-400 hover:text-white hover:bg-slate-800 transition" id="mob-link-hardware">Hardware</a>
                <a href="foro.html" class="block px-4 py-3 rounded-lg text-base font-bold text-amber-400 hover:text-amber-300 hover:bg-slate-800 transition" id="mob-link-foro">Foro 💬</a>
            </div>
        </div>
    </header>
    `;

    // 2. Insertamos el menú al principio del <body>
    document.body.insertAdjacentHTML('afterbegin', headerHTML);

    // 3. Lógica para iluminar la pestaña activa (En Escritorio y en Móvil)
    let currentPage = window.location.pathname.split("/").pop().split(".")[0];
    if (!currentPage || currentPage === "") currentPage = "index"; 
    if (currentPage === "juego") currentPage = "telemetria";
    if (currentPage === "articulo") currentPage = "index";

    // Resaltar en escritorio
    const activeLink = document.getElementById('link-' + currentPage);
    if (activeLink) {
        activeLink.className = "text-cyan-400 border-b-2 border-cyan-400 px-1 pb-1 font-bold";
    }

    // Resaltar en el menú móvil
    const activeMobLink = document.getElementById('mob-link-' + currentPage);
    if (activeMobLink) {
        activeMobLink.className = "block px-4 py-3 rounded-lg text-base font-bold text-cyan-400 bg-cyan-900/20 border border-cyan-500/30";
    }

    // 4. Lógica Interactiva del Menú Hamburguesa
    const btnMenu = document.getElementById('mobile-menu-btn');
    const mobileMenu = document.getElementById('mobile-menu');
    const menuIcon = document.getElementById('menu-icon');

    btnMenu.addEventListener('click', function() {
        // Intercambiar visibilidad
        mobileMenu.classList.toggle('hidden');
        
        // Cambiar el ícono (Hamburguesa a X)
        if (mobileMenu.classList.contains('hidden')) {
            // Icono Hamburguesa
            menuIcon.innerHTML = '<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 6h16M4 12h16M4 18h16" />';
        } else {
            // Icono "X" para cerrar
            menuIcon.innerHTML = '<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />';
        }
    });
});

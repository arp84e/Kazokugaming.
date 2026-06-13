// header.js
document.addEventListener("DOMContentLoaded", function() {
    // 1. Definimos el diseño de nuestro menú una sola vez
    const headerHTML = `
    <header class="border-b border-slate-800/80 bg-slate-900/50 backdrop-blur-md sticky top-0 z-50">
        <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-16 flex items-center justify-between">
            <a href="index.html" class="text-xl font-extrabold tracking-tight bg-gradient-to-r from-cyan-400 to-indigo-500 bg-clip-text text-transparent">
                KAZOKU<span class="text-slate-100">GAMING</span>
            </a>
            <!-- Menú unificado: Se oculta en móviles (hidden) y se muestra en tablets/PC (md:flex) -->
            <nav class="hidden md:flex space-x-6 text-sm font-medium" id="main-nav">
                <a href="index.html" class="nav-link text-slate-400 hover:text-cyan-400 transition" id="link-index">Noticias</a>
                <a href="telemetria.html" class="nav-link text-slate-400 hover:text-cyan-400 transition" id="link-telemetria">Telemetría</a>
                <a href="radar.html" class="nav-link text-slate-400 hover:text-cyan-400 transition" id="link-radar">Radar de Ofertas</a>
                <a href="hardware.html" class="nav-link text-slate-400 hover:text-cyan-400 transition" id="link-hardware">Hardware</a>
                
                <!-- Tu nueva sección para la comunidad -->
                <a href="foro.html" class="nav-link text-amber-400 hover:text-amber-300 transition font-bold" id="link-foro">Foro 💬</a>
            </nav>
        </div>
    </header>
    `;

    // 2. Insertamos el menú justo al inicio de la etiqueta <body>
    document.body.insertAdjacentHTML('afterbegin', headerHTML);

    // 3. Lógica inteligente para iluminar la pestaña activa
    // Averiguamos en qué página estamos (ej. "radar")
    let currentPage = window.location.pathname.split("/").pop().split(".")[0];
    if (!currentPage || currentPage === "") currentPage = "index"; 

    // Buscamos el enlace correspondiente y le ponemos los colores de pestaña activa
    const activeLink = document.getElementById('link-' + currentPage);
    if (activeLink) {
        activeLink.className = "text-cyan-400 border-b-2 border-cyan-400 px-1 pb-1";
    }
});

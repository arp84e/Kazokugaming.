document.addEventListener("DOMContentLoaded", function() {
    const isRoot = window.location.pathname.endsWith('index.html') || window.location.pathname.endsWith('telemetria.html') || window.location.pathname.endsWith('hardware.html') || window.location.pathname.endsWith('radar.html') || window.location.pathname.endsWith('foro.html') || window.location.pathname.split('/').pop() === '';
    const prefix = isRoot ? '' : '../';

    const headerHTML = `
    <header class="border-b border-slate-800/80 bg-slate-900/90 backdrop-blur-md sticky top-0 z-50">
        <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-16 flex items-center justify-between">
            <a href="${prefix}index.html" class="text-2xl font-extrabold tracking-tight bg-gradient-to-r from-cyan-400 to-indigo-500 bg-clip-text text-transparent transition-transform hover:scale-105">
                KAZOKU<span class="text-slate-100">GAMING</span>
            </a>
            
            <!-- PASO 2: BUSCADOR GLOBAL UNIFICADO -->
            <div class="flex-1 max-w-lg mx-8 relative hidden md:block group">
                <div class="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                    <svg class="h-4 w-4 text-slate-500 group-focus-within:text-cyan-400 transition" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"/></svg>
                </div>
                <input type="text" id="global-search" placeholder="Buscar noticias, hardware, telemetría..." class="w-full bg-slate-950/50 text-sm text-white rounded-xl pl-10 pr-4 py-2.5 border border-slate-700/50 focus:outline-none focus:border-cyan-500 focus:ring-1 focus:ring-cyan-500 transition shadow-inner">
                
                <div id="search-results" class="absolute top-14 left-0 w-full bg-slate-800 border border-slate-700 rounded-xl shadow-2xl overflow-hidden hidden z-50 max-h-96 overflow-y-auto"></div>
            </div>

            <nav class="hidden md:flex space-x-8 text-sm font-bold tracking-wide">
                <a href="${prefix}index.html" class="text-slate-400 hover:text-cyan-400 transition">Noticias</a>
                <a href="${prefix}telemetria.html" class="text-slate-400 hover:text-cyan-400 transition">Telemetría</a>
                <a href="${prefix}radar.html" class="text-slate-400 hover:text-cyan-400 transition">Radar</a>
                <a href="${prefix}hardware.html" class="text-slate-400 hover:text-cyan-400 transition">Hardware</a>
                <a href="${prefix}foro.html" class="text-slate-400 hover:text-cyan-400 transition">Foro</a>
            </nav>
        </div>
    </header>`;
    
    const headerContainer = document.getElementById('header-container');
    if(headerContainer) {
        headerContainer.innerHTML = headerHTML;
    } else {
        document.body.insertAdjacentHTML('afterbegin', headerHTML);
    }

    // LÓGICA DEL BUSCADOR GLOBAL
    const searchInput = document.getElementById('global-search');
    const searchResults = document.getElementById('search-results');
    
    if(searchInput) {
        let allData = [];
        // Se cargan los JSON de forma asíncrona para armar el índice de búsqueda
        Promise.all([
            fetch(`${prefix}articulos.json`).then(r => r.ok ? r.json() : []),
            fetch(`${prefix}telemetria.json`).then(r => r.ok ? r.json() : {juegos:[]})
        ]).then(([arts, tele]) => {
            const listaArts = Array.isArray(arts) ? arts : (arts.articulos || []);
            const listaTele = tele.juegos || [];
            
            allData = [
                ...listaArts.map(a => ({ title: a.titulo, type: 'Noticia', url: `${prefix}articulos/${a.id.replace('art-','')}.html`})),
                ...listaTele.map(j => ({ title: j.titulo, type: 'Telemetría', url: `${prefix}telemetria/${j.id}.html`}))
            ];
        });

        searchInput.addEventListener('input', (e) => {
            const query = e.target.value.toLowerCase().trim();
            if(!query) {
                searchResults.classList.add('hidden');
                return;
            }
            const matches = allData.filter(item => item.title.toLowerCase().includes(query)).slice(0, 6);
            if(matches.length > 0) {
                searchResults.innerHTML = matches.map(m => `
                    <a href="${m.url}" class="block px-4 py-3 hover:bg-slate-700/80 transition border-b border-slate-700/50 last:border-0">
                        <span class="text-[10px] font-black text-cyan-500 uppercase block mb-0.5 tracking-wider">${m.type}</span>
                        <span class="text-sm font-semibold text-slate-200">${m.title}</span>
                    </a>`).join('');
                searchResults.classList.remove('hidden');
            } else {
                searchResults.innerHTML = `<div class="px-4 py-4 text-sm text-slate-500 text-center font-medium">Ningún resultado coincide con "${query}"</div>`;
                searchResults.classList.remove('hidden');
            }
        });
        
        document.addEventListener('click', (e) => {
            if(!searchInput.contains(e.target) && !searchResults.contains(e.target)) {
                searchResults.classList.add('hidden');
            }
        });
    }
});

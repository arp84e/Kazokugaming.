// header.js - Componente de Navegación Universal con Buscador Global Integrado
document.addEventListener("DOMContentLoaded", function() {
    const isRoot = window.location.pathname.endsWith('index.html') || window.location.pathname.endsWith('telemetria.html') || window.location.pathname.endsWith('hardware.html') || window.location.pathname.endsWith('radar.html') || window.location.pathname.endsWith('foro.html') || window.location.pathname.split('/').pop() === '';
    const prefix = isRoot ? '' : '../';

    const headerHTML = `
    <header class="border-b border-slate-800/80 bg-slate-900/80 backdrop-blur-md sticky top-0 z-50">
        <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-16 flex items-center justify-between">
            <a href="${prefix}index.html" class="text-2xl font-black tracking-tight bg-gradient-to-r from-cyan-400 to-indigo-500 bg-clip-text text-transparent">
                KAZOKU<span class="text-slate-100 font-normal">GAMING</span>
            </a>
            
            <div class="flex-1 max-w-md mx-8 relative hidden md:block group">
                <div class="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                    <svg class="h-4 w-4 text-slate-500 group-focus-within:text-cyan-400 transition" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"/></svg>
                </div>
                <input type="text" id="global-search" placeholder="Buscar noticias, telemetría..." class="w-full bg-slate-950/40 text-sm text-white rounded-xl pl-10 pr-4 py-2 border border-slate-800 focus:outline-none focus:border-cyan-500 transition">
                
                <div id="search-results" class="absolute top-13 left-0 w-full bg-slate-900 border border-slate-800 rounded-xl shadow-2xl hidden z-50 max-h-80 overflow-y-auto"></div>
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
    
    const container = document.getElementById('header-container') || document.body;
    if (document.getElementById('header-container')) {
        document.getElementById('header-container').innerHTML = headerHTML;
    } else {
        document.body.insertAdjacentHTML('afterbegin', headerHTML);
    }

    // LÓGICA DE BÚSQUEDA DINÁMICA
    const sInput = document.getElementById('global-search');
    const sResults = document.getElementById('search-results');
    
    if(sInput) {
        let database = [];
        Promise.all([
            fetch(`${prefix}articulos.json`).then(r => r.ok ? r.json() : []),
            fetch(`${prefix}telemetria.json`).then(r => r.ok ? r.json() : {juegos:[]})
        ]).then(([arts, tele]) => {
            const listArts = Array.isArray(arts) ? arts : (arts.articulos || []);
            const listTele = tele.juegos || [];
            
            database = [
                ...listArts.map(a => ({ title: a.titulo, type: 'Noticia', url: `${prefix}articulos/${a.id.replace('art-','')}.html` })),
                ...listTele.map(j => ({ title: j.titulo, type: 'Telemetría', url: `${prefix}telemetria/${j.id}.html` }))
            ];
        });

        sInput.addEventListener('input', (e) => {
            const query = e.target.value.toLowerCase().trim();
            if(!query) { sResults.classList.add('hidden'); return; }
            
            const filtered = database.filter(i => i.title.toLowerCase().includes(query)).slice(0, 5);
            if(filtered.length > 0) {
                sResults.innerHTML = filtered.map(m => `
                    <a href="${m.url}" class="block px-4 py-3 hover:bg-slate-800 border-b border-slate-800/60 last:border-0 transition">
                        <span class="text-[9px] font-black text-cyan-400 uppercase tracking-widest block">${m.type}</span>
                        <span class="text-sm font-semibold text-slate-200">${m.title}</span>
                    </a>`).join('');
                sResults.classList.remove('hidden');
            } else {
                sResults.innerHTML = `<div class="px-4 py-3 text-xs text-slate-500 text-center">No hay coincidencias para "${query}"</div>`;
                sResults.classList.remove('hidden');
            }
        });
        
        document.addEventListener('click', (e) => {
            if(!sInput.contains(e.target) && !sResults.contains(e.target)) sResults.classList.add('hidden');
        });
    }
});

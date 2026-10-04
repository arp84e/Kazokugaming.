# KazokuGaming — Guía de despliegue (Firebase + GitHub Pages)

## 1. Bugs corregidos

- **`login.html`**: tenía `overflow: hidden` en `body` y `h-screen` fijo — en móvil, con el teclado abierto, el formulario podía cortarse. Ahora usa `min-h-screen` y permite scroll.
- **Botones decorativos**: "Solicitar Ingreso", "Fundar Escuadrón", "Inscribirse", "Avisarme" y los filtros de `grupos.html` no hacían nada. Todos están conectados ahora (ver sección 2).
- **Contador de inscritos falso**: en el diseño original, "12/16 inscritos" era texto fijo en el HTML. Ahora se calcula contando documentos reales en Firestore (`getCountFromServer`), así nadie puede inflarlo manualmente ni el cliente puede escribir ese número directamente.

## 2. Qué es funcional, página por página

| Página | Qué hace |
|---|---|
| `index.html` | Partidas rápidas en tiempo real (Firestore), noticias reales en español, chat por partida |
| `muro.html` | Muro de la comunidad: publicaciones en tiempo real con filtro de contenido, reacciones 🔥, reportes y filtro por juego |
| `grupos.html` | Crear/filtrar escuadrones reales, solicitudes de ingreso con aprobación del dueño, chat por escuadrón |
| `torneos.html` | Torneos reales, inscripción con cupo contado en vivo, recordatorios ("Avisarme") |
| `admin.html` | Publicar/eliminar torneos, moderar escuadrones y partidas, gestionar reportes — solo para los correos admin |
| `perfil.html` | Editar tu gamertag/bio, ver tus escuadrones y torneos |
| `usuario.html` | Perfil público (solo lectura) de cualquier otro jugador |
| `login.html` | Registro con verificación de correo automática |
| `404.html` | Página de error personalizada |

## 3. Pasos que tienes que hacer tú (obligatorios)

### a) Ponte como administrador (para poder crear torneos y gestionar reportes)
Edita **dos archivos** con tu correo real, para que coincidan exactamente:

1. `firestore.rules` → dentro de `function esAdmin()`, reemplaza `'tu-correo-admin@ejemplo.com'` por tu correo (el mismo con el que te registrarás en `login.html`). Puedes poner varios, separados por coma, dentro de la lista `[...]`.
2. `admin.html` → busca `const CORREOS_ADMIN = ['tu-correo-admin@ejemplo.com'];` y pon el mismo correo.

Si solo cambias uno de los dos archivos, el panel puede *mostrarse* pero Firestore rechazará la escritura (o al revés). Deben coincidir.

### b) Publicar las reglas de seguridad
El archivo `firestore.rules` no protege nada por sí solo hasta que lo publiques:

1. [Firebase Console](https://console.firebase.google.com/) → proyecto `kazokugaming-758d5` → **Firestore Database** → pestaña **Reglas**.
2. Pega el contenido completo de `firestore.rules` (con tu correo ya puesto) → **Publicar**.
3. (Recomendado) Instala el [Firebase CLI](https://firebase.google.com/docs/cli) y usa `firebase deploy --only firestore:rules` para versionarlo junto al código.

### c) Confirmar que Firestore y Auth están activos
- Firebase Console → **Firestore Database** → si no existe, créala (modo producción).
- Firebase Console → **Authentication** → **Sign-in method** → confirma que **Correo/Contraseña** está habilitado.

### d) Crear tu primer torneo
Regístrate en `login.html` con el correo que pusiste como admin, luego entra a `admin.html` y publica un torneo desde el formulario. Aparecerá al instante en `torneos.html`.

### e) Coloca `404.html` en la raíz del repositorio
Debe ir al mismo nivel que `index.html` — GitHub Pages la detecta automáticamente por su nombre de archivo, sin configuración adicional.

## 4. Seguridad extra

### a) Verificación de correo — YA IMPLEMENTADO
Cada nuevo registro recibe automáticamente un correo de verificación. Si el usuario no lo ha confirmado, verá un aviso amarillo debajo del header en cualquier página, con un botón para reenviarlo. No tienes que hacer nada en la consola de Firebase para esto.

*(Nota: esto es solo un aviso visual, no bloquea el uso del sitio. Si más adelante quieres exigir correo verificado para ciertas acciones, se puede añadir esa condición en `firestore.rules` usando `request.auth.token.email_verified`.)*

### b) App Check — código listo, falta tu clave
Ya dejé preparado el código de App Check en `firebase-init.js`, desactivado por defecto (`APP_CHECK_HABILITADO = false`). Para activarlo:
1. Firebase Console → **App Check** → registra tu app web → elige **reCAPTCHA v3** → copia el "Site key".
2. Pega ese valor en la constante `RECAPTCHA_SITE_KEY` dentro de `firebase-init.js` (reemplaza `'PON_AQUI_TU_SITE_KEY'`).
3. Cambia `APP_CHECK_HABILITADO` de `false` a `true`. No hace falta comentar ni descomentar nada más.
4. Sube el cambio y **pruébalo a fondo** antes de activar "Enforce" en la consola de App Check — si activas la aplicación forzada sin probar antes, puedes bloquearte a ti mismo fuera de tu propia app.

### c) Restringir la apiKey por dominio — solo consola, sin código
Google Cloud Console → **APIs y servicios** → **Credenciales** → tu API key de Firebase → **Restricciones de la aplicación** → **Referentes HTTP (sitios web)** → agrega tu dominio de GitHub Pages, por ejemplo `tuusuario.github.io/*`.

⚠️ **Gotcha común:** además de restringir por dominio, revisa la pestaña **"Restricciones de API"** de esa misma key. Si la limitas a un listado de APIs, asegúrate de incluir **Identity Toolkit API**, **Token Service API**, y **Cloud Firestore API** — si olvidas alguna, el login o Firestore dejarán de funcionar aunque el dominio esté bien configurado. Prueba login, crear un escuadrón y enviar un mensaje de chat justo después de guardar cualquier restricción.

## 5. Índices de Firestore que tendrás que crear (con un clic)

Estas consultas necesitan un índice compuesto que Firestore no crea solo. La primera vez que cada una se ejecute, la consola del navegador mostrará un error como `"The query requires an index..."` con un **enlace directo** que abre la consola de Firebase con el índice ya preconfigurado — solo hay que hacer clic en "Crear índice" y esperar uno o dos minutos. No es un bug, es el comportamiento normal de Firestore la primera vez que se usa este tipo de consulta.

- **"Mis Torneos"** en `perfil.html` y `usuario.html` (collection group query sobre `inscripciones`).
- **Bandeja de reportes** en `admin.html` (filtro `estado == 'pendiente'` combinado con orden por `creadoEn`).

## 6. "Últimas Novedades" — videojuegos y tecnología, con imagen real

La sección de noticias en `index.html` (`noticias.js`) carga titulares reales de dos categorías, priorizando siempre que haya una **imagen real** en cada tarjeta:

1. **Tecnología → Xataka** (feed oficial confirmado y verificado: `feeds.weblogssl.com/xataka2`, en español). Cada noticia de Xataka trae su imagen incrustada en el propio resumen del feed, así que esta categoría siempre tiene fotos reales.
2. **Videojuegos → IGN + Google Noticias en español**. IGN (`feeds.ign.com/ign/all`) es un feed oficial que sí incluye imagen, pero está en inglés. Google Noticias (`news.google.com/rss/search?q=videojuegos&hl=es-419`) complementa con titulares en español, aunque Google Noticias **no incluye imágenes** en su RSS por diseño propio de Google (no es una limitación de este sitio) — esas noticias usan la ilustración de categoría en vez de una foto real.

**Por qué Videojuegos mezcla español e inglés:** intenté confirmar un medio de videojuegos en español (Vandal, 3DJuegos, HobbyConsolas) que garantizara imagen real como Xataka, pero no pude verificar con certeza ninguna URL de RSS suya. Si en algún momento confirmas tú mismo la URL de RSS de alguno de esos medios (probándola en `https://api.rss2json.com/v1/api.json?rss_url=TU_URL_AQUI` y viendo si las noticias traen `<img>` en su descripción), avísame y lo agregamos en su lugar — así Videojuegos podría quedar igual de bien resuelto que Tecnología: 100% en español y con foto real.

**Cómo se busca la imagen (mejorado):** antes solo se usaba el campo "thumbnail" que rss2json detecta automáticamente. Ahora, si ese campo viene vacío, el código busca por su cuenta la primera etiqueta `<img>` dentro del resumen de la noticia — esto es lo que permite aprovechar las imágenes de Xataka aunque rss2json no las hubiera detectado solo.

**Por qué es seguro en cuanto a derechos de autor:** solo se muestra el titular, un resumen recortado a ~140 caracteres (el mismo que cada medio publica en su feed para compartir), la imagen que el propio medio incluye en su resumen, y un enlace al artículo completo en el sitio original. Nunca se copia el cuerpo del artículo — el mismo patrón que usan Google News, Feedly o Apple News.

**Mejoras incluidas:** deduplicación de la misma noticia cubierta por más de un medio, fecha relativa ("hace 2 horas"), timeout de 8s por fuente para que una lenta no bloquee a las demás, un botón "Actualizar" manual, y una ilustración por categoría (en vez de una imagen genérica) para las noticias que no traen foto.

**Cómo funciona técnicamente:** se usa **rss2json.com** (servicio gratuito de terceros) como puente para convertir RSS a JSON, ya que los navegadores no pueden leer XML de RSS directamente por CORS. Las noticias se cachean en `sessionStorage` por 20 minutos.

**Si quieres agregar más fuentes:** verifica primero que el feed funcione pegando su URL en `https://api.rss2json.com/v1/api.json?rss_url=TU_URL_AQUI` — si devuelve `"status": "ok"` con artículos, es válida.

## 7. Perfiles públicos y reportes de la comunidad (nuevo)

### a) Perfiles públicos (`usuario.html`)
Cualquier gamertag que aparezca en el sitio (dueño de un escuadrón, autor de una partida, mensajes de chat, solicitudes pendientes) es un enlace a `usuario.html?uid=SU_UID`, que muestra su gamertag, bio, sus escuadrones y sus torneos, en solo lectura. Tu propio perfil sigue siendo `perfil.html` (editable); el header ya enlaza ahí.

### b) Reportes de la comunidad
Hay un botón 🚩 en cada tarjeta de escuadrón, cada tarjeta de partida, y en cada perfil público. Los reportes:
- Los puede **crear** cualquier usuario registrado.
- Los puede **leer/gestionar** solo el admin (así nadie puede ver quién reportó a quién).
- Aparecen en la bandeja "🚩 Reportes de la comunidad" en `admin.html`, con botones para marcar como revisado o eliminar, y un enlace directo al contenido reportado.

## 8. La web ahora se puede "instalar" como app (PWA)

Convertí el sitio en una **Progressive Web App**: en Android/Chrome, al visitar el sitio aparecerá la opción "Instalar app" o "Añadir a pantalla de inicio"; en iOS/Safari, desde el botón compartir → "Añadir a pantalla de inicio". Una vez instalada, abre en pantalla completa (sin la barra de direcciones del navegador) y tiene su propio ícono, como una app nativa.

**Qué se agregó:**
- `manifest.json` — nombre, colores, íconos y accesos directos (Familias, Eventos, Mi Perfil) que aparecen al mantener presionado el ícono ya instalado.
- `icons/` — íconos generados con la identidad visual del sitio (degradado índigo→fucsia con la "K"), en los tamaños que exige cada plataforma, incluyendo un favicon para la pestaña del navegador (el sitio no tenía ninguno antes).
- `sw.js` (Service Worker) — cachea el "shell" estático de la app (HTML, JS propio, íconos) para que cargue más rápido y siga abriendo incluso con mala conexión. **Nunca** cachea datos de Firebase, Firestore, ni las noticias — esas siempre se piden en vivo, para que jamás veas información desactualizada.
- **Persistencia offline de Firestore** (`firebase-init.js`) — los escuadrones, torneos y chats que ya viste quedan guardados en el dispositivo, así que la app abre al instante y sigue mostrando algo útil aunque el celular pierda señal por un momento.

**Lo que tienes que hacer:** solo subir todos los archivos, incluyendo la carpeta `icons/` completa, `manifest.json` y `sw.js` — deben quedar en la raíz del repositorio (mismo nivel que `index.html`). No requiere ninguna configuración en Firebase ni en GitHub Pages.

**Cómo probarlo:** abre el sitio ya subido a GitHub Pages desde el celular (tiene que ser `https://`, no funciona en `http://` ni en `file://`). En Chrome/Android debería aparecer un banner o la opción en el menú de "Instalar app"; en Safari/iOS, usa el botón compartir → "Añadir a pantalla de inicio". Si acabas de subir los cambios, es posible que tengas que recargar la página dos veces la primera vez para que el Service Worker termine de instalarse.

## 9. Auditoría de seguridad (importante — lee esto)

Se hizo una revisión completa del código y se encontraron y corrigieron varias vulnerabilidades reales. Resumen:

### 🔴 Crítico — XSS almacenado, corregido
La función `sanitizarHTML()`, repetida en 7 archivos (todas las páginas + `header.js`), escapaba `&`, `<`, `>` pero **no comillas dobles**. En varios lugares (nombre de escuadrón, título de partida) ese resultado se insertaba dentro de atributos HTML (`data-nombre="..."`), donde una comilla permite inyectar código. Cualquier usuario podía nombrar su escuadrón con un payload que se ejecutaba en el navegador de quien viera esa tarjeta. **Corregido**: las 7 copias ahora escapan también comillas simples y dobles.

El modal de "Reportar" (`ui-utils.js`) tenía el mismo problema con el gamertag/nombre reportado. También corregido.

### 🟠 Reglas de Firestore — gaps de integridad, corregidos
- El dueño de un escuadrón o autor de una partida podía **cambiar quién es el dueño/autor** al editar. Ahora esos campos son inmutables tras crear el documento.
- Al crear un escuadrón o partida, no se validaba que el array de miembros/interesados solo pudiera contener al propio creador — alguien podía "agregar" falsamente a otras personas sin su consentimiento. Corregido.
- El array `interesados` de una partida se podía usar para **expulsar** a otros interesados (no solo para unirse uno mismo). Ahora solo permite sumar, nunca quitar, y de a un uid por escritura.
- Se agregaron límites de tamaño que faltaban en inscripciones a torneos y en reportes.
- El campo `email` del perfil ahora no se puede alterar desde el cliente.

### 🟡 Menor — normalización de URLs de noticias
La validación de URLs de imágenes de noticias usaba la cadena original del feed en vez de la normalizada; una URL con una comilla incrustada podía colarse en el HTML. Corregido para usar siempre la versión normalizada por el navegador.

**Qué tienes que hacer:** subir todos los archivos actualizados, y **volver a publicar `firestore.rules`** en la consola de Firebase — los cambios de reglas no toman efecto hasta que lo hagas (ver sección 3b).

**Recomendación a futuro:** esta auditoría cubrió el código que ya existía. Cada vez que agreguemos una función nueva que muestre texto libre de un usuario (nombre, bio, mensaje, etc.) dentro de un atributo HTML, hay que usar `sanitizarHTML()` — y cada vez que un campo determine quién es dueño/autor de algo, las reglas de Firestore deben impedir que se reasigne después de creado. Si en el futuro trabajas con otra IA o quieres revisarlo tú mismo, esos son los dos patrones de bug más importantes a buscar.


## 10. Nuevas mejoras: buscador, estadísticas, cuenta regresiva, insignias e iconos

- **Buscador global** (icono de lupa en el header): busca al mismo tiempo en escuadrones, torneos y jugadores. Carga los datos una sola vez por visita a la página y filtra en el navegador — sin nuevas colecciones ni servicios de búsqueda externos.
- **Estadísticas animadas** en `index.html`: número real de escuadrones, torneos y jugadores registrados, con una animación de conteo ascendente que se dispara al hacer scroll hasta esa sección.
- **Fecha real y cuenta regresiva en torneos**: `admin.html` ahora usa un selector de fecha/hora real (antes era texto libre). `torneos.html` muestra la fecha formateada y una cuenta regresiva en vivo ("Empieza en 2d 4h") que se actualiza cada 30 segundos. Los torneos creados *antes* de este cambio (con fecha en texto libre) siguen mostrándose bien, solo que sin cuenta regresiva.
- **Insignias de perfil**: Fundador, Sociable (3+ escuadrones), Competidor (inscrito a un torneo) y Veterano (cuenta con 30+ días), calculadas con datos que ya existían — no se agregó ninguna colección nueva. Visibles en `perfil.html` y en el perfil público (`usuario.html`) de cualquier jugador.
- **Iconos SVG consistentes** (`iconos.js`, nuevo archivo): reemplacé los emojis de navegación (🎯🛡️🏆👤🔔🔍) por iconos de línea propios en el header, la barra inferior móvil, encabezados de sección y la página 404. Se ven igual en cualquier sistema operativo, a diferencia de los emojis. Los emojis "de contenido" (💬 chat, 🚩 reportar, 📤 compartir, 👑 insignias, etc.) se dejaron tal cual, ya que ahí funcionan como ilustración y no como parte de la marca/navegación.

**Lo que tienes que hacer:** sube todos los archivos actualizados, incluyendo el nuevo `iconos.js`. No requiere ningún cambio en Firebase ni en `firestore.rules`.

## 11. Filtros/orden en Torneos y "Añadir al calendario"

**Filtros y orden** (`torneos.html`): como el campo "juego" de un torneo es texto libre que escribes en `admin.html`, los botones de filtro se generan solos a partir de los juegos que realmente existen (sin distinguir mayúsculas: "Valorant" y "valorant" cuentan como el mismo). Si solo hay torneos de un juego, la barra de filtros se oculta porque no aportaría nada. El selector de orden ofrece:
- **Más próximos primero** (por defecto): primero los que aún no empiezan (el más cercano arriba), luego los que no tienen fecha real, y al final los que ya empezaron.
- **Publicados recientemente**: el orden en que los creaste.

**Añadir al calendario**: cada torneo con fecha real muestra un botón 📅 junto a "Inscribirse". Ofrece dos opciones: un enlace directo a **Google Calendar** y la descarga de un archivo **.ics** (Apple Calendar, Outlook y la mayoría de apps de calendario en Android). Como los torneos no tienen un campo de duración, el evento se agenda con una duración estimada de **2 horas**. Los torneos antiguos con fecha en texto libre no muestran el botón, porque no hay una fecha real que agendar.

**Lo que tienes que hacer:** subir `torneos.html` y `ui-utils.js` actualizados. No requiere ningún cambio en Firebase ni en `firestore.rules`.

## 12. El Muro (`muro.html`) y su moderación

El muro es una página donde los miembros publican mensajes cortos (hasta 280 caracteres), con un juego opcional, y reaccionan con 🔥. Las publicaciones aparecen en tiempo real. Está en el menú de escritorio y como pestaña en la barra inferior del móvil.

### Cómo se modera: cuatro capas
Ningún filtro automático es perfecto, así que no depende de una sola barrera:

1. **Filtro en el navegador** (`moderacion.js`): avisa mientras la persona escribe y bloquea antes de publicar. Detecta insultos, groserías, contenido sexual, odio, amenazas y acoso, enlaces, teléfonos/correos, estafas y publicidad, gritos en mayúsculas y repeticiones. Entiende intentos de esquivarlo como `p.u.t.a`, `pvta`, `m13rd4`, `puuuuta`, `p*ta`, letras de otros alfabetos y texto con tipografías "raras". No bloquea por palabras sueltas dentro de otras (por ejemplo, `computadora`, `ridículo` o `Puerto Rico` pasan sin problema).
2. **Respaldo en `firestore.rules`**: protege **aunque alguien se salte la página** y escriba directo contra la base de datos. Verifica la estructura de la publicación, que el nombre mostrado sea el gamertag real (evita suplantar a otros), que la fecha la ponga el servidor, y bloquea los términos más graves, los enlaces y los correos.
3. **Botón 🚩 Reportar** en cada publicación, que llega a la bandeja de reportes.
4. **Panel de administración** (`admin.html`): la bandeja de reportes tiene un botón **"Eliminar publicación"** que borra la publicación reportada y marca el reporte como revisado de una vez. Además hay una lista con las 50 publicaciones más recientes del muro, para borrar cualquiera.

### Para publicar hay que tener el correo verificado
Es una decisión de seguridad deliberada: es la medida más eficaz contra cuentas falsas y bots, y el muro es lo más expuesto al abuso. Quien no verificó su correo puede leer y dar 🔥, pero para publicar ve un aviso con botones "Reenviar correo" y "Ya lo verifiqué". **Si prefieres no exigirlo**: borra la línea `request.auth.token.email_verified == true` de la regla del muro en `firestore.rules` y pon `REQUIERE_CORREO_VERIFICADO = false` en `muro.html`.

### Qué tienes que hacer
1. Sube todos los archivos nuevos y actualizados (los nuevos son `muro.html` y `moderacion.js`).
2. **Vuelve a publicar `firestore.rules`** en la consola de Firebase. Sin esto, el muro no puede guardar nada.
3. **Pruébalo con esta secuencia:** (a) publica un mensaje normal, debería aparecer al instante; (b) escribe algo que el filtro debería bloquear (por ejemplo, un enlace) y comprueba que te avisa antes de publicar; (c) da 🔥 y quítalo; (d) repórtalo desde otra cuenta y comprueba que llega al panel de administración.
4. Si al publicar sale un error de permisos: casi siempre es (a) correo sin verificar, (b) reglas sin republicar, o (c) el gamertag del perfil no coincide con el mostrado. Si ocurre con un mensaje normal y todo lo anterior está bien, avísame: las reglas del muro incluyen expresiones regulares que pude probar con la misma lógica, pero **no pude ejecutarlas en el emulador de Firebase**, así que conviene confirmarlas en tu proyecto real.

### Limitaciones que conviene conocer
- **Falsos negativos:** hay formas de esquivar el filtro que no cubre, por ejemplo partir una palabra en dos (`pu ta`), jerga muy local, o el sarcasmo y la ironía (el filtro no entiende el contexto). Para eso están los reportes y el panel.
- **Falsos positivos:** un filtro estricto a veces bloquea algo inocente. Se probó con decenas de frases normales de gamers, pero puede haber casos que no previmos.
- **Frecuencia de publicación:** la espera de 20 segundos entre publicaciones y el aviso de mensaje repetido funcionan solo en el navegador; alguien técnico puede saltárselos. La protección real contra el abuso masivo es **App Check** (ver sección 4b).
- **Las publicaciones no se editan** (solo se pueden eliminar), y el texto se guarda en un solo párrafo, sin saltos de línea.
- **Las reglas** solo cubren los términos más graves, porque no pueden normalizar acentos ni letras parecidas como lo hace el filtro del navegador.

### Cómo ajustar el filtro
- **Severidad:** en `moderacion.js`, `NIVEL_FILTRO` puede ser `'estricto'` (también bloquea groserías suaves como "mierda", "joder" o "carajo", y es el valor por defecto) o `'moderado'` (solo lo grave).
- **Palabras:** edita las listas al inicio de `moderacion.js` (en minúsculas y sin acentos; la ñ sí se conserva). Si agregas una palabra *grave*, considera añadirla también a la expresión de `firestore.rules` para que el respaldo la cubra.

### Un error que encontré de paso (y corregí)
Las páginas de escuadrones y partidas usaban un diccionario de colores indexado por el nombre del juego. Como las reglas no validaban ese campo, alguien podía crear un escuadrón con el juego `constructor` y **romper la página de escuadrones para todos**. Ahora el código consulta el diccionario de forma segura y las reglas validan el campo (`juego` hasta 30 caracteres, `descripcion` hasta 280).

### Siguiente paso recomendado
Este mismo filtro puede proteger también los otros textos libres del sitio (gamertag, bio, nombre y descripción de escuadrones, mensajes de chat y de partidas), que hoy no pasan por ninguna revisión. Es un cambio pequeño porque `revisarTexto()` ya existe.

## 13. Esquema de datos (Firestore)

```
usuarios/{uid}                        { gamertag, email, bio, creadoEn, ultimasLecturas: {...}, ultimasLecturasPartidas: {...} }
partidas/{id}                         { juego, nivel, mensaje, espacios, autorId, autorNombre, interesados: [uid,...], creadoEn }
partidas/{id}/mensajes/{id}           { texto, autorId, autorNombre, creadoEn }
escuadrones/{id}                      { nombre, juego, descripcion, capacidad, duenoId, duenoNombre, miembros: [uid,...], creadoEn }
escuadrones/{id}/solicitudes/{uid}    { solicitanteId, solicitanteNombre, creadoEn }
escuadrones/{id}/mensajes/{id}        { texto, autorId, autorNombre, creadoEn }
torneos/{id}                          { titulo, juego, formato, fecha: Timestamp|null, recompensa, cupoMax, creadoPor, creadoEn }
torneos/{id}/inscripciones/{uid}      { uid, nombre, creadoEn }
recordatorios/{uid}_{eventoId}        { uid, eventoId, creadoEn }
muro/{id}                             { texto, autorId, autorNombre, juego, likes: [uid,...], creadoEn }
reportes/{id}                         { tipo: 'escuadron'|'partida'|'usuario'|'post', objetivoId, objetivoNombre, motivo, reportadoPor, reportadoPorNombre, estado, creadoEn }
```

Todo lo anterior está protegido por `firestore.rules` — no hay ninguna colección abierta a escritura libre.

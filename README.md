# Mapa EDO Castilla y León — X Concurso de Datos Abiertos JCyL

## Objetivo
Participar en la **X edición del Concurso de Datos Abiertos de la Junta de Castilla y
León** (bases: https://datosabiertos.jcyl.es/web/es/concurso-datos-abiertos/concurso-datos-abiertos.html),
categoría **"Productos y Servicios"** (exige una URL pública accesible).
Plazo de presentación: **22 jul – 21 sep 2026**.

Proyecto: un mapa interactivo por provincia de **casos y tasas de incidencia de las
Enfermedades de Declaración Obligatoria (EDO)** en Castilla y León.

## Estado
Dashboard funcional publicado en **GitHub Pages** (URL pública del concurso):
**https://luciahica.github.io/edocyl/**
Repo: https://github.com/LuciaHiCa/edocyl (público — requisito de Pages en plan
gratuito; el contenido es CC BY 4.0 de la JCyL, nada sensible).

> El primer despliegue fue un Claude Artifact
> (`4f40942a-7f4d-4427-8acb-b0836cf166b5`), pero quedó ligado a la cuenta del
> ordenador original y no es accesible desde otras. Se migró a GitHub Pages para
> tener una URL pública, estable y sin login, que es lo que exige la categoría
> "Productos y Servicios". `edo-map.html` se sigue generando por si se quiere
> volver a publicar como Artifact.

Incluye: mapa coroplético de las 9 provincias, buscador de enfermedad (sin
preselección — el usuario busca/elige), selector de año 2008–2024 con
reproducción automática, toggle tasa/casos, ranking provincial, evolución
temporal por provincia (con "emphasis" al pasar el cursor o fijar una provincia),
y KPIs (casos totales, tasa media, provincia con mayor tasa/casos, variación
interanual).

## Archivos de este directorio
- `template.html` — **fuente editable**. HTML/CSS/JS con dos placeholders,
  `__EDO_DATA_JSON__` y `__GEO_JSON__`, donde se inyectan los datos al construir.
  Edita este archivo, nunca `index.html` ni `edo-map.html` directamente.
- `build.py` — genera las dos salidas a partir de `template.html`. Ejecuta
  `python3 build.py` tras cada cambio en la plantilla o en los datos.
- `index.html` — **lo que sirve GitHub Pages**. Página autónoma: el mismo
  contenido más `<!doctype>/<html>/<head>/<body>` y un reset CSS equivalente al
  que el runtime de Artifact inyectaba (`margin:0`, `color-scheme`, imágenes
  fluidas, `[hidden]`), más `<meta>` de descripción/Open Graph y favicon.
- `edo-map.html` — build alternativo para el tool Artifact: el mismo cuerpo pero
  sin `<!doctype>/<html>/<head>/<body>` (el tool los añade).
- `data/edo_raw.json` — export completo y sin procesar del dataset oficial
  (10.645 registros, API Opendatasoft).
- `data/edo_compact.json` — dataset compactado para el frontend:
  `{ provinces: [9 nombres], diseases: [78 nombres], years: [2008..2024],
  series: { "<diseaseIdx>": { "<year>": [ [casos,tasa] x9 provincias, en el
  mismo orden que `provinces` ] } } }`. Generado a partir de `edo_raw.json`
  normalizando una única variante ortográfica duplicada ("gripe aviar" con/sin
  tilde → una sola entrada). Verificado: **cero combinaciones
  enfermedad-año incompletas** (si hay datos, están las 9 provincias).
- `data/cyl_provincias.geojson` — límites de las 9 provincias de Castilla y León,
  simplificados con mapshaper (8%) a partir de una fuente pública de provincias
  de España (SRID 4326), **ya corregidos** para el sentido de rotación de
  anillos que necesita D3 (ver "Gotcha" abajo). Los nombres en la propiedad
  `Texto` coinciden exactamente con `data.provinces`.

## Cómo reconstruir y publicar
```bash
python3 build.py          # regenera index.html y edo-map.html
git add -A && git commit -m "..." && git push
```
GitHub Pages sirve `index.html` desde la raíz de la rama `main`; el push despliega
solo (tarda ~1 min). No hay build server: Pages publica el HTML tal cual, por eso
todo va en un único archivo autónomo.

Para publicar en su lugar como Claude Artifact, usar `edo-map.html` con el tool
Artifact (pasando el `url` existente para actualizar el mismo enlace, no crear
uno nuevo).

## Fuente de datos y licencia
- Dataset: [Enfermedades de Declaración Obligatoria. Casos y tasas por
  provincia](https://datosabiertos.jcyl.es/web/jcyl/set/es/salud/enfermedades-declaracion-obligatoria-casos/1284839794579)
  — Junta de Castilla y León, licencia **CC BY 4.0 ES**.
  Actualización anual. Campos: `ano`, `enfermedad`, `provincia`, `casos`, `tasa`.
  `tasa` = casos por 100.000 habitantes/año (confirmado por consistencia con la
  población real de Valladolid).
- API completa (Opendatasoft v2.1), export directo sin paginar:
  `https://analisis.datosabiertos.jcyl.es/api/explore/v2.1/catalog/datasets/enfermedades-de-declaracion-obligatoria-casos-y-tasas-por-provincia/exports/json`
- Geometría de provincias: gist público
  `josemamira/3af52a4698d42b3f676fbc23f807a605` (provincias de España, SRID 4326),
  filtrado a `CCAA == "Castilla y León"` y simplificado con `mapshaper`.

## Gotcha ya resuelto (para no repetirlo)
El GeoJSON de origen tiene los anillos de los polígonos en el sentido que
espera RFC 7946, pero **D3 v7 (`d3.geoPath`/`d3.geoMercator`) necesita el
sentido contrario** para polígonos pequeños alejados del antimeridiano: si no
se invierte, cada `<path>` se dibuja como un rectángulo gigante (el área de
recorte completa) con el polígono real como "agujero" minúsculo en el centro.
`mapshaper -clean rewind` **no lo soluciona** (ya considera el ring "correcto"
según su propia convención). El fix real: invertir manualmente el orden de
los puntos de cada ring (`coordinates = coordinates.reverse()` por anillo, en
Polygon y MultiPolygon) antes de pasarlo a D3. Ya aplicado en
`data/cyl_provincias.geojson` — verificado con captura de pantalla (Playwright
headless) en claro y oscuro.

## Decisiones de diseño (por si se retoma el estilo)
- Paleta y método siguiendo el skill `dataviz` del proyecto: azul secuencial
  (magnitud, mapa/barras) + naranja `#eb6834`/`#d95926` (acento de
  selección/énfasis, no de magnitud). Rampa secuencial de 13 pasos documentada
  en el propio `template.html`; en oscuro se usa la rampa invertida ("flips
  anchor in dark").
- Tipografía: "Source Serif 4" (títulos), "IBM Plex Sans" (cuerpo/UI),
  "IBM Plex Mono" (cifras/KPIs).
- Evolución temporal con 9 provincias usa patrón "emphasis": líneas grises por
  defecto, una se resalta en naranja al hacer hover/pin (no se usó color
  categórico para 9 series, iría contra el límite del método de 3 series en
  formas "all-pairs").
- Sin enfermedad preseleccionada a propósito (pedido del usuario): al cargar,
  mapa/ranking/evolución muestran estado vacío con mensaje invitando a buscar.

## Pendiente / posibles siguientes pasos
- Revisar las bases completas del concurso en la sede electrónica (no se pudo
  confirmar ahí el detalle exacto del formulario de inscripción ni si piden
  memoria explicativa adicional aparte de la URL).
- Si piden memoria/descripción del proyecto, redactarla (aún no se ha hecho).
- Resuelto: la URL pública ya no depende de una cuenta de Claude — GitHub Pages
  es público por defecto mientras el repositorio lo sea.
- Revisar visualmente en el propio navegador (la verificación previa fue solo con
  capturas de Playwright, y Playwright no está instalado en este ordenador).

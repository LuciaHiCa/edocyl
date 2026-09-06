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
- `scripts/fix_2018_rates.py` — parche de datos: recalcula la tasa de 2018 en
  `data/edo_compact.json` (ver "Análisis de los datos" abajo). Ya aplicado.
  Idempotente; solo hay que volver a pasarlo si se regenera el compact.
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
  Los pares de **2018 con casos > 0** llevan un tercer elemento `[casos,tasa,1]`:
  su tasa es estimada (`scripts/fix_2018_rates.py`, ver abajo).
- `data/cyl_provincias.geojson` — límites de las 9 provincias de Castilla y León,
  simplificados con mapshaper (8%) a partir de una fuente pública de provincias
  de España (SRID 4326), **ya corregidos** para el sentido de rotación de
  anillos que necesita D3 (ver "Gotcha" abajo). Los nombres en la propiedad
  `Texto` coinciden exactamente con `data.provinces`.

## Cómo reconstruir y publicar
```bash
# python3 scripts/fix_2018_rates.py   # solo si se ha regenerado edo_compact.json
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
  (magnitud, mapa/barras/small-multiples) + naranja `#e15c1e`/`#ec7a3e` (acento
  de selección/énfasis, no de magnitud). Rampa secuencial de 13 pasos documentada
  en el propio `template.html`; en oscuro se usa la rampa invertida ("flips
  anchor in dark"). Neutros fríos, no cálidos.
- Tipografía: "IBM Plex Sans" (títulos + cuerpo + UI), "IBM Plex Mono"
  (cifras/KPIs/ejes). Se retiró la serif "Source Serif 4" en el rediseño de
  sep-2026 (petición del usuario: aspecto más moderno).
- Evolución temporal: **cada provincia con su color fijo** (petición explícita
  del usuario). Son 9 series en un gráfico de comparación libre, por encima del
  límite categórico CVD-seguro del método `dataviz` (que para formas "all-pairs"
  recomienda 3 y agrupar el resto). El validador (`scripts/validate_palette.js`)
  no aprueba ningún juego de 9 colores en modo `--pairs all`; el peor par en
  visión normal, rojo↔naranja ΔE 7.1, viene ya de los 8 colores de referencia.
  Se asume la petición del usuario y se compensa con **codificación secundaria**:
  leyenda con color + nombre siempre visible, etiquetas directas al final de las
  líneas seleccionadas, y el resto de líneas atenuadas a gris al elegir una o
  varias. Colores = los 8 tonos validados de la referencia (versión clara/oscura)
  + un 9.º cian; asignados por índice de provincia (alfabético), nunca por
  ranking. Selección múltiple: `state.selected` (array); alterna al pulsar en
  leyenda, mapa o ranking.
- Ranking provincial: la barra de relleno necesita `display:block` (era un
  `<span>` en línea y el ancho no se aplicaba). Además, cuando `maxVal <= 0`
  (todas las provincias a 0) se muestra un aviso en vez de barras planas — ver
  "Rareza de los datos" abajo.
- Small multiples "El mapa, año a año": un mini-mapa por año, **misma escala de
  color** (máximo global de la enfermedad en todos los años) para que sean
  comparables; al pulsar un año se fija en el mapa grande y se resalta durante la
  reproducción automática.
- Control "Año" (rediseño sep-2026): barra con los 17 años como botones
  (`#yearBar`, años sin datos deshabilitados) + botón único de reproducción
  "Ver evolución temporal en mapa …" con barra de progreso. Se eliminó el
  `<input type=range>`.
- Sección de notas (`.notes-panel`, sin título): **acordeón** de 4 `<details>`
  (terminología e interpretación del mapa · brotes reseñables y cambios
  destacables · rupturas en la serie · límites de la fuente). El de brotes
  contiene a su vez 4 `<details>` anidados (parotiditis, varicela, tos ferina,
  otras). Todo cerrado por defecto; se abre al pulsar. Resumen del análisis de
  datos (ver más abajo).
- Sin enfermedad preseleccionada a propósito (pedido del usuario): al cargar,
  mapa/ranking/evolución muestran estado vacío con mensaje invitando a buscar.

## Análisis de los datos y rarezas detectadas
Resumen del análisis hecho sobre `edo_raw.json` (lo relevante está también en la
sección **"Cuestiones importantes"** de la propia página).

**Totales por año (solo provincias, = lo que muestra el frontend):**
2008 ≈ 56 000 · 2009 ≈ 64 900 · 2010 ≈ 20 400 · 2011–2019 ≈ 38 000–55 000 ·
**2020 ≈ 170 300** · **2021 ≈ 5 300** · 2022 ≈ 29 100 · 2023 ≈ 5 000 · 2024 ≈ 6 000.
Descontada la gripe, el total 2008–2019 es estable (~6 000–9 500/año): casi toda
la variación interanual del total es gripe.

- **Pico 2009 / valle 2010:** pandemia de gripe A (H1N1). Gripe 2009 ≈ 58 000,
  2010 ≈ 14 000. El resto de EDO apenas se movió.
- **2020:** COVID-19 = 136 211 casos (EDO solo ese año; desde 2021 se vigila
  aparte y no aparece). Sin COVID, 2020 ≈ 34 000, normal.
- **2021:** caída real por las medidas anti-COVID (gripe 2 174, varicela 255,
  parotiditis 170…), probablemente acentuada por la sobrecarga de la red.
- **Ruptura 2023:** "Gripe" y "Gripe Grave" **salen de la lista de EDO** (a
  vigilancia centinela / SiVIRA). Eran la enfermedad más notificada, por eso
  2023–2024 caen a ~5 000–6 000 y **no son comparables** con años previos.
- **"2018 solo Ávila":** NO es un hueco. En crudo, las 9 provincias tienen fila
  todos los años; en enfermedades raras solo una tuvo casos > 0 y las demás
  salen en gris (= 0 declarado). Ej.: fiebres hemorrágicas víricas 2018 → 1 caso
  en Ávila; sarampión 2018 → solo Valladolid.
- **La tasa de 2018 está rota en la fuente y se recalcula.** Los ~270 registros
  con `casos` > 0 y `tasa` == 0 están **todos en 2018**: ese año solo Ávila trae
  tasas reales; para las otras 8 provincias la fuente publica `0.0` aunque haya
  miles de casos (Gripe 2018: Valladolid 7 523 casos, tasa 0). Y varias tasas que
  sí trae Ávila en 2018 también son incoherentes (Yersiniosis, 2 casos → 51,7).
  `scripts/fix_2018_rates.py` sustituye **toda** la columna de tasa de 2018 por
  `casos ÷ población_2017 × 100 000` (población de 2017 recuperada del propio
  dataset como mediana de `casos/tasa` sobre las filas limpias de 2017,
  dispersión < 1 %). Validación: Gripe de Ávila 2018 estimada = 1 183,7 vs
  1 184,0 de la fuente (< 0,1 %). Las celdas recalculadas se marcan con un tercer
  elemento `1` en el par (`[casos, tasa, 1]`); el frontend muestra "≈" y el aviso
  "tasa estimada" en mapa, tooltip, ranking, small-multiples y evolución.
  Efecto anterior del bug: como el indicador por defecto es la tasa, en 2018
  solo se coloreaba Ávila en cualquier enfermedad.
- El resto de años: si en una enfermedad-año concreta las 9 tasas son 0 (enferm.
  muy rara), el ranking por "Tasa" lo detecta (`maxVal <= 0`) y muestra un aviso
  sugiriendo "Casos".
- **Enfermedades renombradas** (aparecen 2 veces en la lista de 78, cada una con
  media serie "vacía"): "Fiebre del Dengue" (2014–2022) → "Dengue" (2023–24);
  "Otras ETS" → "Otras ITS"; 3 etiquetas para *E. coli* Shiga-toxigénica;
  "SIDA" → "Nuevas infecciones por VIH/Sida"; "Herpes Zoster" (0 casos siempre).
- **Dato inverosímil:** "Infección humana por virus de la gripe aviar" 2018 = 78
  casos repartidos por CyL. España no ha tenido prácticamente casos humanos de
  gripe aviar; casi seguro error de clasificación en el origen. (Además la tasa
  de esos 78 es 0,0 salvo Ávila.)
- **Filas `provincia == "CyL"`:** 133 registros, todos de 2023–2024, son el total
  regional que la fuente añade esos dos años. El build los descarta (solo 9
  provincias con nombre) — no hay pérdida de datos, pero ojo si se re-explota el
  raw: sumar sin filtrar duplica 2023–2024.
- **La lista de EDO cambia:** 69 enfermedades (2008–2018), 70 (2019–2020),
  67–68 (2021–2024), por las actualizaciones de la normativa estatal.

## Pendiente / posibles siguientes pasos
- Revisar las bases completas del concurso en la sede electrónica (no se pudo
  confirmar ahí el detalle exacto del formulario de inscripción ni si piden
  memoria explicativa adicional aparte de la URL).
- Si piden memoria/descripción del proyecto, redactarla (aún no se ha hecho).
- Resuelto: la URL pública ya no depende de una cuenta de Claude — GitHub Pages
  es público por defecto mientras el repositorio lo sea.
- Revisar visualmente en el propio navegador (la verificación previa fue solo con
  capturas de Playwright, y Playwright no está instalado en este ordenador).

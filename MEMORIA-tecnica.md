# Descripción técnica de la herramienta

Texto de apoyo para la memoria justificativa del X Concurso de Datos Abiertos de
la Junta de Castilla y León (categoría «Productos y Servicios»). Todos los datos
están verificados contra el código del repositorio.

- **URL pública:** https://luciahica.github.io/edocyl/
- **Repositorio (abierto):** https://github.com/LuciaHiCa/edocyl

## Alojamiento y arquitectura

La aplicación está publicada en **GitHub Pages** como sitio estático, con URL
pública y estable. Se sirve íntegramente por HTTPS, sin servidor de aplicación ni
base de datos: no hay backend, ni cookies, ni analítica ni seguimiento de
usuarios. Cada actualización se despliega con un `git push` (≈ 1 minuto).

## Tecnología

Es una página web **HTML5 + CSS3 + JavaScript**, escrita a mano, **sin framework**
(no usa React, Vue, Angular ni similares) y **sin proceso de compilación** (no hay
npm, bundler ni transpilación). El resultado es un único archivo `index.html`
autocontenido. Todo el código, tanto de la interfaz como de la preparación de
datos, se ha desarrollado con asistencia de **Claude (Anthropic)**.

- Interfaz temática clara/oscura automática (`prefers-color-scheme`) mediante
  variables CSS.
- Accesibilidad: estructura semántica, secciones plegables nativas
  (`<details>/<summary>`), etiquetas ARIA, foco de teclado visible y navegación
  completa por teclado.

## Origen y tratamiento de los datos

- **Fuente:** dataset *«Enfermedades de Declaración Obligatoria. Casos y tasas por
  provincia»* del Portal de Datos Abiertos de la Junta de Castilla y León
  (licencia CC BY 4.0), obtenido mediante la **API de Opendatasoft v2.1**
  (exportación JSON completa, sin paginar): 10.645 registros con los campos año,
  enfermedad, provincia, casos y tasa.
- **Preparación previa** (fuera de línea, scripts de Python documentados en el
  repositorio): el volcado íntegro (`edo_raw.json`, ≈ 1,1 MB) se reestructura a un
  JSON compacto (`edo_compact.json`, ≈ 105 KB) pivotado por enfermedad → año → 9
  provincias (9 provincias, 78 enfermedades, 2008–2024). Se unifica una variante
  ortográfica duplicada y se recalculan las tasas de 2018, que en la fuente
  original figuran como cero en 8 de las 9 provincias pese a haber casos (se
  marcan como «tasa estimada» en la interfaz).
- **En el navegador no se descarga ni se procesa ningún CSV/Excel/JSON en tiempo
  de ejecución:** los datos ya viajan incrustados dentro de la propia página como
  objetos JavaScript, junto con la geometría de las provincias (GeoJSON). No hay
  peticiones AJAX/*fetch*. La única dependencia externa que se carga al abrir la
  página es la librería de gráficos (D3) desde un CDN y las tipografías de Google
  Fonts.

## Librerías de mapa y gráficos

- **D3.js v7.9.0** (única librería, cargada desde cdnjs), utilizada para:
  - **Mapa coroplético:** proyección `d3.geoMercator` + `d3.geoPath` para dibujar
    las 9 provincias a partir de un GeoJSON como `<path>` SVG; color por magnitud
    con una escala secuencial (`d3.scaleLinear`).
  - **«El mapa, año a año»:** 17 mini-mapas (uno por año) que reutilizan el mismo
    generador de rutas de D3, con escala de color común para poder compararlos.
  - **Gráfica de evolución temporal:** escalas `d3.scaleLinear` y `d3.line` con
    suavizado `curveMonotoneX`, en SVG; una línea por provincia, con selección
    múltiple para comparar.
- El **ranking provincial**, los **indicadores clave (KPIs)** y la **leyenda**
  están construidos directamente con HTML/CSS/SVG, sin librería adicional.
- La paleta sigue un método de visualización de datos: rampa azul secuencial para
  la magnitud, naranja como color de selección/énfasis y una paleta de 9 colores
  para las provincias comprobada para daltonismo.

## Funcionamiento en móvil

Sí, es **responsive**. Incluye `<meta viewport>`; la maquetación usa CSS Grid y
Flexbox, de modo que los bloques de dos columnas (mapa + ranking, KPIs, controles)
pasan a una sola columna en pantallas estrechas; la barra de años y los mini-mapas
se reorganizan automáticamente en varias filas; y todos los gráficos son SVG con
`viewBox`, por lo que se escalan sin pérdida a cualquier ancho. Funciona en
teléfonos y tabletas con cualquier navegador moderno.

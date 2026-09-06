#!/usr/bin/env python3
"""Construye las dos salidas del proyecto a partir de template.html.

  edo-map.html  fragmento para publicar con el tool Artifact (sin doctype/html/head/body)
  index.html    pagina autonoma para GitHub Pages

Uso:  python3 build.py
"""
from pathlib import Path

BASE = Path(__file__).parent

TITLE = "Enfermedades de Declaración Obligatoria (EDO) en Castilla y León"
DESCRIPTION = ("Mapa interactivo de casos y tasas de incidencia de las Enfermedades "
               "de Declaración Obligatoria en las nueve provincias de Castilla y León, "
               "2008–2024. Datos abiertos de la Junta de Castilla y León.")

# El runtime de Artifact inyecta su propio reset (margin 0, color-scheme, img
# fluidas, [hidden]). Fuera de el hay que replicarlo o la pagina se descuadra.
STANDALONE_HEAD = """<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<meta name="description" content="@@DESCRIPTION@@">
<meta name="author" content="X Concurso de Datos Abiertos de la Junta de Castilla y León">
<meta property="og:title" content="@@TITLE@@">
<meta property="og:description" content="@@DESCRIPTION@@">
<meta property="og:type" content="website">
<meta name="twitter:card" content="summary_large_image">
<link rel="icon" href="data:image/svg+xml,<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 100 100'><text y='.9em' font-size='90'>🗺️</text></svg>">
<style>
  /* Reset equivalente al que Artifact inyecta, para que la pagina autonoma
     se vea exactamente igual que el artifact. */
  html{ color-scheme: light dark; }
  body{ margin: 0; font: 14px "IBM Plex Sans", system-ui, -apple-system, "Segoe UI", sans-serif;
        background: #f4f5f7; }
  img{ max-width: 100%; }
  [hidden]{ display: none !important; }
  .viz-root{ min-height: 100vh; }
  @media (prefers-color-scheme: dark){
    body{ background: #0d0e10; }
  }
</style>"""


def build() -> None:
    tpl = (BASE / "template.html").read_text(encoding="utf-8")
    edo = (BASE / "data" / "edo_compact.json").read_text(encoding="utf-8")
    geo = (BASE / "data" / "cyl_provincias.geojson").read_text(encoding="utf-8")

    body = tpl.replace("__EDO_DATA_JSON__", edo).replace("__GEO_JSON__", geo)

    # 1) Fragmento para el tool Artifact: tal cual, sin envoltorio.
    (BASE / "edo-map.html").write_text(body, encoding="utf-8")

    # 2) Pagina autonoma para GitHub Pages.
    head = (STANDALONE_HEAD
            .replace("@@TITLE@@", TITLE)
            .replace("@@DESCRIPTION@@", DESCRIPTION))
    standalone = (
        "<!doctype html>\n"
        '<html lang="es">\n'
        "<head>\n" + head + "\n" + body.split("<style>", 1)[0].rstrip() + "\n"
        "<style>" + body.split("<style>", 1)[1].split("</style>", 1)[0] + "</style>\n"
        "</head>\n"
        "<body>\n"
        + body.split("</style>", 1)[1].strip() + "\n"
        "</body>\n"
        "</html>\n"
    )
    (BASE / "index.html").write_text(standalone, encoding="utf-8")

    print(f"edo-map.html  {len(body):>8,} chars")
    print(f"index.html    {len(standalone):>8,} chars")


if __name__ == "__main__":
    build()

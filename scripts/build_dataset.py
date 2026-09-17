#!/usr/bin/env python3
"""Genera data/edo_compact.json a partir de data/edo_raw.json.

NO modifica nunca el archivo de origen. Todo el proceso es reproducible:
borrar el compact y volver a ejecutar este script debe dar el mismo resultado.

Hace tres cosas, en este orden:

1. SELECCIÓN. De las denominaciones del dataset provincial solo se conservan las
   que pueden asignarse con seguridad a una de las 56 Enfermedades de Declaración
   Obligatoria seleccionadas para EDO CyL (ver `EDO_SELECCIONADAS`). El resto se
   excluye de forma explícita y documentada en `EXCLUIDAS`.

   Referencia: Orden SSI/445/2015, de 9 de marzo (BOE-A-2015-2837).
     - ANEXO I, «Lista de enfermedades de declaración obligatoria»: 60 entradas.
       Cada EDO lleva abajo su número de anexo como comentario (I-1 ... I-60).
     - ANEXO II, «Modalidades de la declaración»: no contiene lista de
       enfermedades, solo regula cómo se declara. No aporta ninguna EDO.
     - ANEXO III, «Enfermedades endémicas de ámbito regional»: una única
       entrada, Enfermedad de Lyme, que por tanto forma parte de la selección.

   De las 60 del Anexo I quedan fuera 5:
     - Encefalitis transmitida por garrapatas (I-9), Linfogranuloma venéreo
       (I-37), Toxoplasmosis congénita (I-54) y Viruela (I-59): no están
       representadas de forma equivalente en el dataset provincial.
     - Gripe / Gripe humana por un nuevo subtipo de virus (I-23): excluida
       deliberadamente del proyecto, junto con el resto de categorías de gripe
       de la fuente.
   60 - 5 = 55, más Lyme del Anexo III = 56.

2. NORMALIZACIÓN. La fuente usa a lo largo de los años denominaciones distintas
   para una misma EDO. `NOMBRE_OFICIAL` es el mapeo explícito
   denominación de origen -> nombre visible en EDO CyL.

   Solo se agregan series cuando se ha comprobado que NO coexisten: es decir,
   que no hay ningún año-provincia con casos > 0 en dos denominaciones del mismo
   grupo. El script vuelve a comprobarlo en cada ejecución (`comprobar_solapes`)
   y aborta si alguna vez dejara de cumplirse.

   Caso deliberadamente NO agregado: la fuente publica «Nuevas infecciones por
   VIH/Sida» (2008-2024) y «SIDA» (2008-2018). Coexisten en 13 celdas
   año-provincia con casos en ambas (p. ej. Ávila 2010: 8 y 2), con tasas
   calculadas sobre la misma población, luego son recuentos independientes de
   hechos distintos. Se muestra solo la primera y se excluye «SIDA». El nombre
   visible conserva la sigla del Anexo I y precisa entre paréntesis qué
   representa la serie. Nota: ni la Orden SSI/445/2015 ni los metadatos del
   dataset definen qué mide cada categoría; la lectura como nuevos diagnósticos
   de VIH es un criterio epidemiológico adoptado por el proyecto.

3. TASAS DE 2018. En 2018 la fuente publica tasa 0 en ocho provincias pese a
   haber casos declarados, y algunas de las que sí trae Ávila son incoherentes.
   Se recalcula toda la columna de tasa de 2018 como
   casos / poblacion_2017 * 100.000. La población de 2017 de cada provincia se
   deduce del propio dataset, como mediana de casos/tasa*100.000 sobre TODAS las
   filas válidas de 2017 (también las de enfermedades excluidas: la población es
   una propiedad de la provincia, no de la enfermedad). Las celdas recalculadas
   con casos > 0 se marcan con un tercer elemento `1` en el par.

No se crean registros artificiales: un año solo aparece en una EDO si la fuente
trae filas para ese año. Las EDO sin ningún caso en 2008-2024 se conservan: que
no haya casos declarados también es información.

Uso:  python3 scripts/build_dataset.py
"""
import json
import statistics
import sys
from collections import defaultdict
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent
RAW = BASE / "data" / "edo_raw.json"
COMPACT = BASE / "data" / "edo_compact.json"

PROVINCIAS = ["Ávila", "Burgos", "León", "Palencia", "Salamanca",
              "Segovia", "Soria", "Valladolid", "Zamora"]
PROV_IDX = {p: i for i, p in enumerate(PROVINCIAS)}

ANIO_TASA_ROTA = 2018
ANIO_POBLACION = 2017

VIH = "VIH/SIDA (nuevos diagnósticos de VIH)"
ECOLI = "Infección por cepas de Escherichia coli productoras de toxina Shiga o Vero"
POLIO = "Poliomielitis/parálisis flácida aguda en menores de 15 años"
TETANOS = "Tétanos/Tétanos neonatal"

# denominación en el dataset -> nombre visible en EDO CyL
NOMBRE_OFICIAL = {
    # -- se mantienen tal cual (37) --
    "Botulismo": "Botulismo",
    "Brucelosis": "Brucelosis",
    "Campilobacteriosis": "Campilobacteriosis",
    "Carbunco": "Carbunco",
    "Cólera": "Cólera",
    "Criptosporidiosis": "Criptosporidiosis",
    "Difteria": "Difteria",
    "Enfermedad meningocócica": "Enfermedad meningocócica",
    "Enfermedad por virus Chikungunya": "Enfermedad por virus Chikungunya",
    "Fiebre Q": "Fiebre Q",
    "Fiebre amarilla": "Fiebre amarilla",
    "Fiebre exantemática mediterránea": "Fiebre exantemática mediterránea",
    "Giardiasis": "Giardiasis",
    "Hepatitis A": "Hepatitis A",
    "Hepatitis B": "Hepatitis B",
    "Hepatitis C": "Hepatitis C",
    "Hidatidosis": "Hidatidosis",
    "Infección gonocócica": "Infección gonocócica",
    "Enfermedad de Lyme": "Enfermedad de Lyme",     # ANEXO III (única entrada)
    "Legionelosis": "Legionelosis",
    "Leishmaniasis": "Leishmaniasis",
    "Lepra": "Lepra",
    "Leptospirosis": "Leptospirosis",
    "Listeriosis": "Listeriosis",
    "Paludismo": "Paludismo",
    "Parotiditis": "Parotiditis",
    "Peste": "Peste",
    "Rabia": "Rabia",
    "Rubéola": "Rubéola",
    "Rubéola congénita": "Rubéola congénita",
    "Sarampión": "Sarampión",
    # I-49: el Anexo I escribe «Shigellosis» (doble L); en la interfaz se conserva
    # «Shigelosis», la grafía del Excel y la de uso habitual en castellano.
    "Shigelosis": "Shigelosis",
    "Sífilis": "Sífilis",
    "Sífilis congénita": "Sífilis congénita",
    "Triquinosis": "Triquinosis",
    "Tularemia": "Tularemia",
    "Varicela": "Varicela",
    "Yersiniosis": "Yersiniosis",

    # -- solo cambia la denominación (14) --
    "Encefalopatías espongiformes": "Encefalopatías espongiformes transmisibles humanas",
    "Enfermedad invasora Haemophilus influenzae": "Enfermedad invasora por Haemophilus influenzae",
    "Enfermedad invasora por S. pneumoniae": "Enfermedad neumocócica invasora",
    "Fiebre del Nilo Occidental": "Fiebre del Nilo occidental",
    "Fiebre recurrente por garrapatas": "Fiebre recurrente transmitida por garrapatas",
    "Fiebres hemorrágicas virales": "Fiebres hemorrágicas víricas",
    "Fiebres tifoidea y paratifoidea": "Fiebre tifoidea/Fiebre paratifoidea",
    "Herpes Zoster": "Herpes zóster",
    "Infecciones por Chlamydia": "Infección por Chlamydia trachomatis",
    "Nuevas infecciones por VIH/Sida": VIH,
    "Salmonelosis de transmisión alimentaria": "Salmonelosis",
    "Síndrome respiratorio agudo severo": "SARS (Síndrome Respiratorio Agudo Grave)",
    "Tos Ferina": "Tos ferina",
    "Tuberculosis (cualquier localización)": "Tuberculosis",

    # -- varias denominaciones sucesivas de una misma EDO (9 -> 4) --
    "Fiebre del Dengue": "Dengue",                       # 2008-2022
    "Dengue": "Dengue",                                  # 2023-2024
    "Infección por cepas de Escherichia coli productoras de toxina Shiga o Vero": ECOLI,  # 2008-2022
    "Infección por E. coli productora de toxina shiga o vero (STEC/VTEC)": ECOLI,         # 2023
    "Infección por E. coli enterohemorrágica": ECOLI,                                     # 2024
    "Poliomielitis": POLIO,                              # sin casos en toda la serie
    "Parálisis flácida aguda": POLIO,                    # casos 2009-2019
    "Tétanos": TETANOS,                                  # casos 2008-2014
    "Tétanos neonatal": TETANOS,                         # sin casos en toda la serie
}

# grupos cuyas denominaciones se suman: hay que comprobar que no coexisten
GRUPOS_AGREGADOS = {
    "Dengue": ["Fiebre del Dengue", "Dengue"],
    ECOLI: ["Infección por cepas de Escherichia coli productoras de toxina Shiga o Vero",
            "Infección por E. coli productora de toxina shiga o vero (STEC/VTEC)",
            "Infección por E. coli enterohemorrágica"],
    POLIO: ["Poliomielitis", "Parálisis flácida aguda"],
    TETANOS: ["Tétanos", "Tétanos neonatal"],
}

# denominación excluida -> motivo
EXCLUIDAS = {
    "Gripe": "gripe excluida deliberadamente del proyecto",
    "Gripe Grave": "gripe excluida deliberadamente del proyecto",
    # la fuente trae las dos grafías, con y sin tilde, como categorías distintas
    "Infección humana por virus de la gripe aviar": "gripe excluida deliberadamente del proyecto",
    "Infeccion humana por virus de la gripe aviar": "gripe excluida deliberadamente del proyecto",
    "Infección por nuevo virus de la gripe A(H1N1)": "gripe excluida deliberadamente del proyecto",
    "SIDA": "indicador distinto de «Nuevas infecciones por VIH/Sida»; coexisten y no son agregables",
    "COVID-2019": "no figura en el Anexo I de la Orden SSI/445/2015",
    "Infección Respiratoria Aguda Grave (IRAG)": "no figura en el Anexo I",
    "Enfermedad invasiva Estreptococo grupo A (SGAi)": "no figura en el Anexo I",
    "Enfermedad por virus Zika": "no figura en el Anexo I",
    "MPOX": "no figura en el Anexo I",
    "Tifus exantemático": "no figura en ninguno de los tres anexos",
    "Toxoplasmosis": "el Anexo I recoge «Toxoplasmosis congénita» (I-54); el Excel no precisa\n                      que se trate de la forma congénita y no se asume la equivalencia",
    "Meningitis víricas": "categoría agrupada, no asignable a una EDO concreta",
    "Otras Meningitis Bacterianas": "categoría agrupada, no asignable a una EDO concreta",
    "Otras hepatitis víricas": "categoría agrupada, no asignable a una EDO concreta",
    "Otras ETS": "categoría agrupada, no asignable a una EDO concreta",
    "Otras ITS": "categoría agrupada, no asignable a una EDO concreta",
}

EDO_SELECCIONADAS = sorted(set(NOMBRE_OFICIAL.values()))


def cargar_raw():
    return json.loads(RAW.read_text(encoding="utf-8"))


def comprobar_cobertura(raw):
    """Toda denominación del Excel cae en «utilizada» o «excluida», y en una sola.

    Imprime el resultado de la validación para poder auditarla.
    """
    del_excel = {r["enfermedad"].strip() for r in raw
                 if r["provincia"].strip() in PROV_IDX}
    usadas, excluidas = set(NOMBRE_OFICIAL), set(EXCLUIDAS)

    sin_clasificar = del_excel - usadas - excluidas
    solapadas = usadas & excluidas
    inventadas = (usadas | excluidas) - del_excel

    print("VALIDACIÓN DE LA CLASIFICACIÓN")
    print("  denominaciones distintas en el Excel : %d" % len(del_excel))
    print("  utilizadas                           : %d" % len(usadas))
    print("  excluidas                            : %d" % len(excluidas))
    print("  utilizadas + excluidas               : %d  %s"
          % (len(usadas) + len(excluidas),
             "= total" if len(usadas) + len(excluidas) == len(del_excel) else "!= TOTAL"))
    print("  sin clasificar                       : %s" % (sorted(sin_clasificar) or "ninguna"))
    print("  en ambas listas a la vez (solape)    : %s" % (sorted(solapadas) or "ninguna"))
    print("  reglas sin denominación real         : %s" % (sorted(inventadas) or "ninguna"))
    print("  EDO resultantes                      : %d" % len(EDO_SELECCIONADAS))

    if sin_clasificar:
        sys.exit("ABORTA: denominaciones sin clasificar")
    if solapadas:
        sys.exit("ABORTA: denominaciones a la vez utilizadas y excluidas")
    if inventadas:
        sys.exit("ABORTA: reglas que no corresponden a ninguna denominación real")
    if len(usadas) + len(excluidas) != len(del_excel):
        sys.exit("ABORTA: la suma de utilizadas y excluidas no cuadra con el Excel")
    if len(EDO_SELECCIONADAS) != 56:
        sys.exit("ABORTA: el mapeo produce %d EDO, se esperaban 56" % len(EDO_SELECCIONADAS))
    print()


def comprobar_solapes(raw):
    """Aborta si dos denominaciones de un mismo grupo tienen casos a la vez.

    Si coexistieran, no serían un cambio de nombre sino indicadores distintos y
    sumarlas falsearía el dato.
    """
    casos = defaultdict(int)  # (denominación, año, provincia) -> casos
    for r in raw:
        p = r["provincia"].strip()
        if p not in PROV_IDX:
            continue
        casos[(r["enfermedad"].strip(), int(r["ano"]), p)] += r["casos"] or 0
    for destino, origenes in GRUPOS_AGREGADOS.items():
        choques = []
        anios = {a for (e, a, _) in casos if e in origenes}
        for a in sorted(anios):
            for p in PROVINCIAS:
                activas = [e for e in origenes if casos.get((e, a, p), 0) > 0]
                if len(activas) > 1:
                    choques.append((a, p, activas))
        if choques:
            sys.exit("«%s»: denominaciones con casos simultáneos, no son agregables: %s"
                     % (destino, choques[:5]))


def poblacion_2017(raw):
    """Población implícita de cada provincia, despejada de casos/tasa en 2017."""
    pob = {}
    for p in PROVINCIAS:
        muestras = [(r["casos"] or 0) / (r["tasa"] or 1) * 1e5
                    for r in raw
                    if r["provincia"].strip() == p
                    and int(r["ano"]) == ANIO_POBLACION
                    and (r["casos"] or 0) > 0 and (r["tasa"] or 0) > 0]
        if not muestras:
            sys.exit("Sin muestras para deducir la población %d de %s" % (ANIO_POBLACION, p))
        pob[p] = statistics.median(muestras)
    return pob


def construir(raw):
    """denominación normalizada -> año -> [[casos, tasa] x 9 provincias]."""
    series = defaultdict(dict)
    for r in raw:
        p = r["provincia"].strip()
        if p not in PROV_IDX:
            continue  # descarta el total regional «CyL» de 2023-2024
        enf = r["enfermedad"].strip()
        if enf in EXCLUIDAS:
            continue
        nombre = NOMBRE_OFICIAL[enf]
        anio = int(r["ano"])
        fila = series[nombre].setdefault(anio, [[0, 0.0] for _ in PROVINCIAS])
        celda = fila[PROV_IDX[p]]
        celda[0] += r["casos"] or 0
        celda[1] += r["tasa"] or 0.0
    for porAnio in series.values():
        for fila in porAnio.values():
            for celda in fila:
                celda[1] = round(celda[1], 2)
    return series


def corregir_tasas_2018(series, pob):
    n = 0
    for porAnio in series.values():
        fila = porAnio.get(ANIO_TASA_ROTA)
        if not fila:
            continue
        nueva = []
        for i, (casos, _tasa) in enumerate(fila):
            if casos and casos > 0:
                tasa = round(casos / pob[PROVINCIAS[i]] * 1e5, 1)
                nueva.append([casos, tasa, 1])
                n += 1
            else:
                nueva.append([casos, 0.0])
        porAnio[ANIO_TASA_ROTA] = nueva
    return n


def main():
    raw = cargar_raw()
    comprobar_cobertura(raw)
    comprobar_solapes(raw)

    series = construir(raw)
    estimadas = corregir_tasas_2018(series, poblacion_2017(raw))

    diseases = sorted(series)
    anios = sorted({a for porAnio in series.values() for a in porAnio})
    compact = {
        "provinces": PROVINCIAS,
        "diseases": diseases,
        "years": anios,
        "series": {str(i): {str(a): series[n][a] for a in sorted(series[n])}
                   for i, n in enumerate(diseases)},
    }
    COMPACT.write_text(json.dumps(compact, ensure_ascii=False, separators=(",", ":")),
                       encoding="utf-8")

    filas = sum(len(f) for porAnio in series.values() for f in [porAnio])
    celdas = sum(len(fila) for porAnio in series.values() for fila in porAnio.values())
    casos = sum(c[0] for porAnio in series.values() for fila in porAnio.values() for c in fila)
    print("EDO en el selector:      %d" % len(diseases))
    print("años:                    %d-%d" % (anios[0], anios[-1]))
    print("celdas enfermedad-año-provincia: %s" % f"{celdas:,}")
    print("casos declarados:        %s" % f"{casos:,}")
    print("tasas estimadas de %d:  %d celdas" % (ANIO_TASA_ROTA, estimadas))
    print("denominaciones excluidas: %d" % len(EXCLUIDAS))

    print("\nEDO formadas por varias etiquetas del Excel:")
    agrupadas = defaultdict(list)
    for origen, destino in NOMBRE_OFICIAL.items():
        agrupadas[destino].append(origen)
    for destino in sorted(agrupadas):
        origenes = agrupadas[destino]
        if len(origenes) > 1:
            print("  %s" % destino)
            for o in sorted(origenes):
                anios = sorted({int(r["ano"]) for r in raw
                                if r["enfermedad"].strip() == o
                                and r["provincia"].strip() in PROV_IDX})
                print("      <- «%s»  (%d-%d)" % (o, anios[0], anios[-1]))


if __name__ == "__main__":
    main()

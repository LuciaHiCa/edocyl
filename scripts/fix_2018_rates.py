#!/usr/bin/env python3
"""Recalcula la columna de TASA de 2018 en data/edo_compact.json.

Por qué: en el dataset oficial de la Junta, el año 2018 tiene la tasa rota.
Solo Ávila trae tasas reales; para las otras 8 provincias la fuente publica
`tasa = 0.0` aunque haya miles de casos (p. ej. Gripe 2018: Valladolid 7.523
casos, tasa 0,0). Y varias de las tasas que sí trae Ávila en 2018 también son
incoherentes (Yersiniosis 2 casos -> tasa 51,7). Resultado en el mapa: como el
indicador por defecto es la tasa, en 2018 solo se coloreaba Ávila.

Qué hace este script: para 2018 sustituye la tasa de TODAS las provincias por
`casos / poblacion_2017 * 100.000`, redondeada a 1 decimal como la fuente. La
población de 2017 de cada provincia se recupera del propio dataset, como mediana
de `casos / tasa * 100.000` sobre las filas de 2017 con casos>0 y tasa>0 (miles
de filas, dispersión < 1 %). Validación: con esa población, la tasa recalculada
de Ávila 2018 reproduce la tasa real de la fuente con < 1 % de error en las
enfermedades con muchos casos (Gripe: 1.183,7 vs 1.184,0).

Las celdas recalculadas con casos>0 se marcan añadiendo un tercer elemento `1`
al par: `[casos, tasa]` -> `[casos, tasa, 1]`. El frontend lo usa para avisar de
que esa tasa es una estimación. Las celdas con 0 casos quedan como `[0, 0.0]`.

Idempotente: si 2018 ya está marcado, no vuelve a tocar nada.
Uso:  python3 scripts/fix_2018_rates.py
"""
import json
import statistics
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent
RAW = BASE / "data" / "edo_raw.json"
COMPACT = BASE / "data" / "edo_compact.json"
BAD_YEAR = "2018"
POP_YEAR = "2017"


def pop_by_province(raw, provinces):
    pop = {}
    for p in provinces:
        samples = [
            (r["casos"] or 0) / (r["tasa"] or 1) * 1e5
            for r in raw
            if r["provincia"].strip() == p
            and str(r["ano"]) == POP_YEAR
            and (r["casos"] or 0) > 0
            and (r["tasa"] or 0) > 0
        ]
        if not samples:
            raise SystemExit(f"Sin muestras de población {POP_YEAR} para {p}")
        pop[p] = statistics.median(samples)
    return pop


def main():
    raw = json.loads(RAW.read_text(encoding="utf-8"))
    comp = json.loads(COMPACT.read_text(encoding="utf-8"))
    provinces = comp["provinces"]

    if BAD_YEAR not in [str(y) for y in comp["years"]]:
        raise SystemExit(f"{BAD_YEAR} no está en years")

    pop = pop_by_province(raw, provinces)

    patched_cells = 0
    patched_combos = 0
    for di, per_year in comp["series"].items():
        row = per_year.get(BAD_YEAR)
        if not row:
            continue
        if any(len(pair) > 2 for pair in row):
            continue  # ya parcheado
        new_row = []
        touched = False
        for prov_idx, pair in enumerate(row):
            casos = pair[0]
            if casos and casos > 0:
                tasa = round(casos / pop[provinces[prov_idx]] * 1e5, 1)
                new_row.append([casos, tasa, 1])
                patched_cells += 1
                touched = True
            else:
                new_row.append([casos, 0.0])
        per_year[BAD_YEAR] = new_row
        if touched:
            patched_combos += 1

    COMPACT.write_text(
        json.dumps(comp, ensure_ascii=False, separators=(",", ":")),
        encoding="utf-8",
    )
    print(f"Poblaciones {POP_YEAR} usadas:")
    for p in provinces:
        print(f"  {p:12s} {pop[p]:>10,.0f}")
    print(f"Celdas {BAD_YEAR} recalculadas (casos>0): {patched_cells}")
    print(f"Enfermedades con al menos una celda {BAD_YEAR} recalculada: {patched_combos}")


if __name__ == "__main__":
    main()

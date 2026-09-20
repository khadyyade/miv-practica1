"""
Fase 2 -- Modelitzacio de dades
Reconstruccio del pressupost inicial aprovat de la Generalitat de Catalunya (2003-2024)

Aquest fitxer distingeix EN CODI (no nomes en comentaris) les dues fonts:

  (A) get_pressupost_api(): Crida REAL a l'API SODA del portal de
      transparencia. Requereix connexio a internet.

  (B) PRESSUPOST_IDESCAT_MANUAL Transcrit manualment llegint la taula
      HTML d'Idescat.
"""

import csv
import json
import urllib.parse
import urllib.request

OUT_PATH = "pressupost_generalitat_2003_2024.csv"

# =============================================================================
# (A) FONT PRIMARIA: GENCAT (2010-2023)
# =============================================================================
# Dataset: "Pressupostos aprovats de la Generalitat de Catalunya" (id yd9k-7jhw)
# Portal:  analisi.transparenciacatalunya.cat -- API Socrata/SODA

API_URL = "https://analisi.transparenciacatalunya.cat/resource/yd9k-7jhw.json"
SOQL_QUERY = {
    "$select": "exercici, sum(import_sense_consolidar) as total",
    "$where": "ingr_s_despesa='D' AND subsector='Generalitat'",
    "$group": "exercici",
    "$order": "exercici",
}


def get_pressupost_api(timeout=15):
    """
    Crida real a l'API oberta. Retorna {any: import_meur}. Tot surt de la
    resposta JSON de la crida HTTP. Si la crida falla, el programa s'atura.
    """
    url = f"{API_URL}?{urllib.parse.urlencode(SOQL_QUERY)}"
    req = urllib.request.Request(url, headers={"User-Agent": "practica-miv/1.0"})
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        rows = json.loads(resp.read().decode("utf-8"))
    dades = {int(r["exercici"]): float(r["total"]) / 1_000_000 for r in rows}
    print(f"[API] {len(dades)} anys descarregats en directe des de {API_URL}")
    return dades, "api"


# =============================================================================
# (B) FONT SECUNDARIA: IDESCAT (2003-2009)
# =============================================================================
# Idescat no ofereix aquesta serie via API ni com a descarrega oberta.
# Aquests valors es van copiar A MA llegint la taula a https://www.idescat.cat/indicadors/?id=aec&n=15638
PRESSUPOST_IDESCAT_MANUAL = {
    2003: 16081.39,
    2004: 18710.82,
    2005: 21516.87,
    2006: 23924.46,
    2007: 26684.64,
    2008: 28243.34,
    2009: 29730.76,
}

# Anys sense pressupost NOU aprovat pel Parlament (pressupost prorrogat),
# deduits de l'absencia d'aquell any al dataset oficial (A). 2024 hi entra
# arran d'aquesta revisio: el projecte de 43.673 M€ el va aprovar el Govern
# en gabinet, pero mai el Parlament (eleccions anticipades).
ANYS_SENSE_PRESSUPOST = {2013, 2016, 2018, 2019, 2021, 2024}

# IPC Espanya, variacio interanual (%) desembre/desembre (INE) tambe introduit a ma.
IPC_VARIACIO_MANUAL = {
    2003: 2.6, 2004: 3.2, 2005: 3.7, 2006: 2.7, 2007: 4.2,
    2008: 1.4, 2009: 0.8, 2010: 3.0, 2011: 2.4, 2012: 2.9,
    2013: 0.3, 2014: -1.0, 2015: 0.0, 2016: 1.6, 2017: 1.1,
    2018: 1.2, 2019: 0.8, 2020: -0.5, 2021: 6.5, 2022: 5.7,
    2023: 3.1, 2024: 2.8,
}


def build_series():
    anys = list(range(2003, 2025))

    pressupost_api, font_api_label = get_pressupost_api()

    font = {y: "idescat" for y in PRESSUPOST_IDESCAT_MANUAL}
    font.update({y: font_api_label for y in pressupost_api})

    pressupost_aprovat = {**PRESSUPOST_IDESCAT_MANUAL, **pressupost_api}

    nominal, font_any, darrer_aprovat, darrera_font = {}, {}, None, None
    for any_ in anys:
        if any_ in pressupost_aprovat:
            nominal[any_] = pressupost_aprovat[any_]
            font_any[any_] = font[any_]
            darrer_aprovat, darrera_font = nominal[any_], font[any_]
        else:
            nominal[any_] = darrer_aprovat      # prorrogat
            font_any[any_] = darrera_font + "_prorrogat"

    ipc_index = {2003: 100.0}
    for any_ in anys[1:]:
        ipc_index[any_] = ipc_index[any_ - 1] * (1 + IPC_VARIACIO_MANUAL[any_] / 100)

    real = {any_: nominal[any_] / ipc_index[any_] * 100 for any_ in anys}

    rows = []
    for any_ in anys:
        rows.append({
            "any": any_,
            "pressupost_nou_aprovat": "no" if any_ in ANYS_SENSE_PRESSUPOST else "si",
            "font": font_any[any_],
            "nominal_meur": round(nominal[any_], 2),
            "ipc_index_2003_100": round(ipc_index[any_], 2),
            "real_2003_meur": round(real[any_], 2),
        })
    return rows


def main():
    rows = build_series()
    with open(OUT_PATH, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)

    print(f"\nCSV generat a {OUT_PATH}\n")
    header = f"{'Any':<6}{'Nou aprovat':<13}{'Font':<30}{'Nominal (M€)':<15}{'IPC(2003=100)':<15}{'Real 2003 (M€)':<15}"
    print(header)
    for r in rows:
        print(f"{r['any']:<6}{r['pressupost_nou_aprovat']:<13}{r['font']:<30}{r['nominal_meur']:<15}{r['ipc_index_2003_100']:<15}{r['real_2003_meur']:<15}")

    r2003, r2024 = rows[0], rows[-1]
    print(f"\n[NOMÉS ORIENTATIU -- 2003 és font 'idescat_manual_no_verificat']")
    print(f"Increment nominal 2003->2024: x{r2024['nominal_meur']/r2003['nominal_meur']:.3f}")
    print(f"Increment real (euros constants 2003) 2003->2024: x{r2024['real_2003_meur']/r2003['real_2003_meur']:.3f}")

    print(f"\n[SÈRIE SÒLIDA -- només font 'api', 2012 vs 2023]")
    r2012 = next(r for r in rows if r["any"] == 2012)
    r2023 = next(r for r in rows if r["any"] == 2023)
    print(f"Increment nominal 2012->2023: x{r2023['nominal_meur']/r2012['nominal_meur']:.3f}")
    print(f"Increment real 2012->2023: x{r2023['real_2003_meur']/r2012['real_2003_meur']:.3f}")


if __name__ == "__main__":
    main()
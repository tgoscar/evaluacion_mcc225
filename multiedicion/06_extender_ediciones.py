# -*- coding: utf-8 -*-
"""
Extension del dataset a varias ediciones del IESF
==================================================
Replica la construccion de manifest_local2.csv sobre informes adicionales de la
SBS, para pasar de una sola edicion (n=40) a un diseno de replicas independientes.

Salidas:
  <outdir>/images/<edicion>_grafico_XXX_<chart_id>.png
  <outdir>/manifest_<edicion>.csv        un manifiesto por edicion
  <outdir>/manifest_multiedicion.csv     los tres unidos, con columna 'edicion'

Estructura de captions (identica a manifest_local2.csv):
  caption_1  "Grafico X.Y: Titulo"
  caption_2  solo el titulo
  caption_3  "El grafico muestra <tema>. Segun el reporte, <oracion que lo cita>"
  caption_4  version condensada de caption_3

Decision de diseno importante
-----------------------------
Cada edicion se evalua como un pool de recuperacion SEPARADO. No se mezclan las
tres en una sola matriz de similitud por dos razones:

  1. Comparabilidad. El R@1 depende del numero de distractores; un pool de 106
     no es comparable con el de 40 ya reportado.
  2. Ground truth ambiguo. Varias ediciones repiten titulos casi identicos
     ("Crecimiento economico global" aparece en 2021 y 2024). En un pool unico
     esos pares dejan de tener una respuesta correcta unica.

Asi, cada edicion es una replica independiente del mismo experimento, y el
vector de aciertos pareado acumula n = 40 + 40 + 26 para las pruebas McNemar.

Uso:
  python 06_extender_ediciones.py --pdf IESF20242A.pdf --edicion 2024-2
  python 06_extender_ediciones.py --pdf Informe_de_Estabilidad_Financiera_2021I.pdf --edicion 2021-1
  python 06_extender_ediciones.py --unir            # construye el manifiesto combinado
"""

import argparse
import re
import subprocess
import unicodedata
from pathlib import Path

import pandas as pd

try:
    import fitz  # PyMuPDF
except ImportError:
    fitz = None

DPI = 170              # misma resolucion que el dataset original
MARGEN = 30.0          # puntos alrededor de la region detectada
GROSOR_MINIMO = 3.0
AREA_MINIMA = 200.0
RE_CHART = r"[IVX]+(?:\.[A-Z])?\.[0-9]+"


# ---------------------------------------------------------------------------
def sin_tildes(s: str) -> str:
    """El manifiesto original normaliza sin acentos; se mantiene el criterio."""
    s = unicodedata.normalize("NFD", str(s))
    s = "".join(c for c in s if unicodedata.category(c) != "Mn")
    return re.sub(r"\s+", " ", s).strip()


def texto_pagina(pdf: str, p: int) -> str:
    return subprocess.run(
        ["pdftotext", "-f", str(p), "-l", str(p), "-layout", pdf, "-"],
        capture_output=True, text=True, errors="replace").stdout


def n_paginas(pdf: str) -> int:
    out = subprocess.run(["pdfinfo", pdf], capture_output=True, text=True).stdout
    return int(out.split("Pages:")[1].split()[0])


# ---------------------------------------------------------------------------
def localizar_graficos(pdf: str) -> dict:
    """Devuelve {chart_id: (titulo, pagina_pdf)} leyendo los titulos del cuerpo.

    Se prefiere el cuerpo sobre la 'Tabla de Graficos' porque el indice parte
    los titulos largos en dos lineas y omite entradas; el titulo impreso sobre
    el grafico es la fuente fiable, y ademas da la pagina directamente.
    """
    hallados = {}
    total = n_paginas(pdf)
    for p in range(1, total + 1):
        t = texto_pagina(pdf, p)
        # las paginas de indice concentran muchas lineas con puntos de relleno
        if t.count("....") > 5:
            continue
        for m in re.finditer(rf"(?m)^\s*Gr[aá]fico\s+({RE_CHART})\s+(.{{5,120}}?)\s*$", t):
            cid, tit = m.group(1), m.group(2).strip()
            if "..." in tit or tit.count(".") > 6:
                continue
            if re.match(r"^\d", tit):        # numero de pagina pegado al titulo
                continue
            hallados.setdefault(cid, (tit, p))
    return hallados


def es_prosa(frase: str) -> bool:
    """Distingue una oracion narrativa del titulo del grafico o de sus etiquetas
    de ejes. Las etiquetas son cadenas cortas cargadas de cifras y sin verbos ni
    conectores; la prosa del informe tiene palabras funcionales."""
    if len(frase) < 70 or len(frase) > 700:
        return False
    bajo = frase.lower()
    if bajo.startswith(("grafico", "gráfico", "cuadro", "fuente", "nota")):
        return False
    tokens = frase.split()
    if not tokens:
        return False
    # proporcion de tokens que son cifras: alta en ejes y leyendas
    cifras = sum(bool(re.fullmatch(r"[-+]?[\d.,%]+", t)) for t in tokens)
    if cifras / len(tokens) > 0.25:
        return False
    conectores = (" que ", " de la ", " del ", " en el ", " en la ", " se ",
                  " para ", " con ", " por ", " los ", " las ", " este ", " esta ")
    return sum(c in bajo for c in conectores) >= 2


def oracion_que_cita(pdf: str, cid: str, pagina: int, ventana: int = 1) -> str:
    """Oracion del informe que menciona el grafico. Es texto literal de la SBS.

    Se priorizan las referencias entre parentesis o precedidas de 'ver', que son
    las que aparecen dentro del cuerpo narrativo; la primera aparicion del
    identificador suele ser el titulo impreso sobre el grafico, no una oracion.
    """
    texto = " ".join(texto_pagina(pdf, p)
                     for p in range(max(1, pagina - ventana), pagina + ventana + 1))
    texto = re.sub(r"\s+", " ", texto)
    patron = rf"Gr[aá]fico\s+{re.escape(cid)}(?![.\d])"

    # Segmentacion de oraciones: un punto solo cierra oracion si viene despues de
    # letra, parentesis o simbolo de porcentaje y le sigue espacio y mayuscula.
    # Asi no se parte en cifras decimales como "3.8%" ni en "S/ 62 318".
    cortes = [0] + [m.end() for m in re.finditer(
        r"(?<=[a-zA-Zaeiouñ)\]%])\.\s+(?=[A-ZÁÉÍÓÚ¿¡])", texto)] + [len(texto)]

    def oracion_en(pos):
        for i in range(len(cortes) - 1):
            if cortes[i] <= pos < cortes[i + 1]:
                return texto[cortes[i]:cortes[i + 1]].strip()
        return ""

    candidatas = []
    for m in re.finditer(patron, texto):
        frase = oracion_en(m.start())
        if not es_prosa(frase):
            continue
        antes = texto[max(0, m.start() - 6): m.start()].lower()
        prioridad = 0 if ("(" in antes or "ver" in antes) else 1
        candidatas.append((prioridad, len(frase), frase))

    if candidatas:
        candidatas.sort(key=lambda x: (x[0], -x[1]))
        return candidatas[0][2], "cita_explicita"

    # Respaldo. Las ediciones anteriores a 2026 no citan el grafico en el cuerpo:
    # lo insertan despues del parrafo que lo comenta. Se toma entonces la ultima
    # oracion de prosa anterior al titulo impreso. Se marca la procedencia porque
    # la diferencia entre ediciones es sistematica y hay que poder controlarla.
    titulos = list(re.finditer(patron, texto))
    if titulos:
        corte = titulos[-1].start()
        for i in range(len(cortes) - 1, 0, -1):
            if cortes[i] <= corte:
                frase = texto[cortes[i - 1]:cortes[i]].strip()
                if es_prosa(frase):
                    return frase, "parrafo_previo"
    return "", "ninguna"


# ---------------------------------------------------------------------------
def region_grafico(page, cid=None, margen=MARGEN):
    """Region del grafico combinando trazos vectoriales e imagenes incrustadas.
    En los IESF conviven ambos formatos segun la edicion.

    Dos correcciones necesarias en estas ediciones:
      - el logo institucional del encabezado es una imagen incrustada; si entra
        en la union, el recorte se estira hasta el borde superior de la pagina.
        Se descartan los elementos de las bandas de encabezado y pie.
      - cuando la pagina tiene dos graficos, la union abarca ambos. Se ancla el
        recorte al titulo del grafico buscado y se conservan solo los elementos
        que caen por debajo de ese titulo.
    """
    alto = page.rect.height
    zona_util = (0.10 * alto, 0.94 * alto)      # descarta encabezado y pie

    # ancla: posicion del titulo "Grafico X.Y"
    y_titulo = None
    if cid:
        for txt in (f"Gráfico {cid}", f"Grafico {cid}"):
            hits = page.search_for(txt)
            if hits:
                y_titulo = min(h.y0 for h in hits)
                break

    def admisible(r):
        if r.is_empty or r.is_infinite:
            return False
        if r.y1 < zona_util[0] or r.y0 > zona_util[1]:
            return False
        if y_titulo is not None and r.y1 < y_titulo:
            return False                         # queda arriba del titulo
        return True

    rects = []
    for d in page.get_drawings():
        r = d["rect"]
        if not admisible(r):
            continue
        if r.width < GROSOR_MINIMO and r.height < GROSOR_MINIMO:
            continue
        if r.get_area() < AREA_MINIMA and min(r.width, r.height) < GROSOR_MINIMO:
            continue
        rects.append(r)
    for im in page.get_images(full=True):
        for r in page.get_image_rects(im[0]):
            if admisible(r) and r.get_area() >= AREA_MINIMA:
                rects.append(r)
    if not rects:
        return None

    u = rects[0]
    for r in rects[1:]:
        u |= r

    y0 = y_titulo - 8 if y_titulo is not None else u.y0 - margen * 1.8
    return fitz.Rect(
        max(page.rect.x0, u.x0 - margen),
        max(page.rect.y0, min(y0, u.y0 - 5)),
        min(page.rect.x1, u.x1 + margen),
        min(page.rect.y1, u.y1 + margen),
    )


# ---------------------------------------------------------------------------
def construir_captions(cid, titulo, oracion):
    t = sin_tildes(titulo)
    tema = t.rstrip(".").lower()
    c1 = sin_tildes(f"Grafico {cid}: {titulo}")
    c2 = t
    if oracion:
        o = sin_tildes(oracion)
        c3 = f"El grafico muestra {tema}. Segun el reporte, {o}"
        # caption_4: condensa quitando parentesis y notas al pie numeradas
        o4 = re.sub(r"\([^)]*\)", "", o)
        o4 = re.sub(r"\s+", " ", o4).strip()
        c4 = f"{t[:1].upper()}{t[1:].rstrip('.')}. {o4}"
    else:
        c3 = f"El grafico muestra {tema}."
        c4 = t
    return c1, c2, c3, c4


def procesar(pdf: str, edicion: str, outdir: Path, reporte: str):
    if fitz is None:
        raise SystemExit("Falta PyMuPDF: pip install pymupdf")
    (outdir / "images").mkdir(parents=True, exist_ok=True)
    doc = fitz.open(pdf)
    zoom = DPI / 72.0
    matriz = fitz.Matrix(zoom, zoom)

    graficos = localizar_graficos(pdf)
    print(f"{edicion}: {len(graficos)} graficos localizados")

    filas, sin_region, sin_oracion = [], [], []
    for i, cid in enumerate(sorted(graficos, key=lambda c: graficos[c][1])):
        titulo, pagina = graficos[cid]
        page = doc[pagina - 1]
        caja = region_grafico(page, cid)
        if caja is None:
            sin_region.append(cid)
            continue
        nombre = f"{edicion}_grafico_{i:03d}_{cid.replace('.', '_')}.png"
        page.get_pixmap(matrix=matriz, clip=caja).save(str(outdir / "images" / nombre))

        oracion, fuente = oracion_que_cita(pdf, cid, pagina)
        if not oracion:
            sin_oracion.append(cid)
        c1, c2, c3, c4 = construir_captions(cid, titulo, oracion)

        filas.append({
            "image_id": f"{edicion}_img_{i:03d}",
            "image_path": f"images/{nombre}",
            "caption_1": c1, "caption_2": c2, "caption_3": c3, "caption_4": c4,
            "chart_id": cid,
            "chart_uid": f"{edicion}|{cid}",     # unico entre ediciones
            "edicion": edicion,
            "source_page_pdf": pagina,
            "source_report": reporte,
            "tiene_oracion": bool(oracion),
            "fuente_oracion": fuente,
        })

    df = pd.DataFrame(filas)
    salida = outdir / f"manifest_{edicion}.csv"
    df.to_csv(salida, index=False, encoding="utf-8")
    print(f"  {len(df)} pares -> {salida}")
    if sin_region:
        print(f"  sin region detectada ({len(sin_region)}): {sin_region}")
    if sin_oracion:
        print(f"  sin oracion en el informe ({len(sin_oracion)}): {sin_oracion}")
        print("  (caption_3 y caption_4 quedan con solo el titulo: caso honesto a declarar)")
    return df


# ---------------------------------------------------------------------------
def unir(outdir: Path, original: str = "manifest_local2.csv"):
    """Une el manifiesto original (2026-1) con los nuevos, sin mezclar pools."""
    partes = []
    if Path(original).exists():
        d = pd.read_csv(original)
        d["edicion"] = "2026-1"
        d["chart_uid"] = "2026-1|" + d["chart_id"].astype(str)
        d["tiene_oracion"] = True
        partes.append(d)
    for f in sorted(outdir.glob("manifest_2*.csv")):
        partes.append(pd.read_csv(f))
    if not partes:
        raise SystemExit("no hay manifiestos que unir")
    todo = pd.concat(partes, ignore_index=True)

    # verificaciones de integridad entre ediciones
    dup_uid = todo["chart_uid"][todo["chart_uid"].duplicated()].tolist()
    dup_img = todo["image_id"][todo["image_id"].duplicated()].tolist()
    colisiones = (todo.groupby(todo["caption_2"].str.lower().str.strip())["edicion"]
                    .nunique().pipe(lambda s: s[s > 1]))

    salida = outdir / "manifest_multiedicion.csv"
    todo.to_csv(salida, index=False, encoding="utf-8")
    print(f"\nManifiesto combinado: {len(todo)} pares -> {salida}")
    print(todo.groupby("edicion").size().to_string())
    print(f"\nchart_uid duplicados: {dup_uid or 'ninguno'}")
    print(f"image_id duplicados : {dup_img or 'ninguno'}")
    print(f"titulos repetidos entre ediciones: {len(colisiones)}")
    for t in colisiones.index[:10]:
        eds = todo.loc[todo.caption_2.str.lower().str.strip() == t, ["edicion", "chart_id"]]
        print("   ", t[:55], "->", list(eds.itertuples(index=False, name=None)))
    if len(colisiones):
        print("\n  Por esto cada edicion se evalua como pool separado: en un pool")
        print("  unico estos pares no tendrian una respuesta correcta unica.")
    return todo


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--pdf")
    ap.add_argument("--edicion")
    ap.add_argument("--reporte", default=None)
    ap.add_argument("--outdir", default="multiedicion")
    ap.add_argument("--unir", action="store_true")
    args = ap.parse_args()

    out = Path(args.outdir)
    if args.unir:
        unir(out)
        return
    if not (args.pdf and args.edicion):
        raise SystemExit("indica --pdf y --edicion, o usa --unir")
    reporte = args.reporte or f"SBS - Informe de Estabilidad del Sistema Financiero, {args.edicion}"
    procesar(args.pdf, args.edicion, out, reporte)


if __name__ == "__main__":
    main()

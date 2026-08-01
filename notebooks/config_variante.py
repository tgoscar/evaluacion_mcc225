# -*- coding: utf-8 -*-
"""
Selector de variante de imágenes
=================================
Punto único donde se decide si los notebooks trabajan con las imágenes que
incluyen el título impreso o con las recortadas.

Por qué existe
--------------
El manifiesto es el mismo para las dos variantes: cambia solo el directorio de
las imágenes. Repetir esa decisión en cada notebook invita a que una corrida use
un conjunto y otra el contrario sin que se note, y a que los resultados se
sobrescriban entre sí. Aquí la variante se declara una vez, y el nombre del
directorio de salida la arrastra, de modo que dos corridas nunca se pisan y
siempre se puede saber de dónde salió cada CSV.

Uso en un notebook
------------------
    from config_variante import VARIANTE, carpeta_imagenes, ruta_imagen, dir_salida

    IMGS = carpeta_imagenes(MULTI)          # multiedicion/images/<variante>/
    OUT  = dir_salida(BASE, "resultados_multiedicion")
    rutas = [ruta_imagen(MULTI, p) for p in g["image_path"]]

Para cambiar de variante basta editar VARIANTE aquí, o exportar la variable de
entorno MCC225_VARIANTE antes de abrir Jupyter.
"""

import os
from pathlib import Path

# --------------------------------------------------------------------------
# Variante activa: "con_titulo" o "sin_titulo"
# --------------------------------------------------------------------------
VARIANTE = os.environ.get("MCC225_VARIANTE", "sin_titulo")

# Las dos variantes viven dentro de multiedicion/images/
SUBCARPETA = "images"
CARPETAS = {
    "con_titulo": "con_titulo",
    "sin_titulo": "sin_titulo",
}

# Si las imágenes están sueltas en images/ sin subcarpeta, el módulo falla en
# lugar de adivinar: una corrida etiquetada "con_titulo" ejecutada sobre imágenes
# recortadas no dejaría ninguna traza del error, que es justo lo que hay que
# impedir.


def _validar(v):
    if v not in CARPETAS:
        raise ValueError(
            f"VARIANTE debe ser una de {list(CARPETAS)}; se recibió {v!r}")


def carpeta_imagenes(multi_dir, variante=None):
    """Directorio de imágenes de la variante activa.

    Lanza FileNotFoundError si no existe, en lugar de fallar más adelante al
    abrir la primera imagen: el mensaje es mucho más claro aquí.
    """
    v = variante or VARIANTE
    _validar(v)
    multi_dir = Path(multi_dir)

    principal = multi_dir / SUBCARPETA / CARPETAS[v]
    if principal.is_dir():
        return principal

    base_img = multi_dir / SUBCARPETA
    if base_img.is_dir() and any(base_img.glob("*.png")):
        raise FileNotFoundError(
            f"No existe {principal}, pero {base_img} contiene imágenes sueltas.\n"
            f"Un directorio sin sufijo no indica qué variante contiene, así que "
            f"no se usa automáticamente. Separarlas en subcarpetas:\n"
            f"    {base_img/CARPETAS['con_titulo']}/  y  "
            f"{base_img/CARPETAS['sin_titulo']}/")

    presentes = (sorted(d.name for d in base_img.iterdir() if d.is_dir())
                 if base_img.is_dir() else "el directorio images/ no existe")
    raise FileNotFoundError(
        f"No se encuentra {principal} para la variante '{v}'. "
        f"Subcarpetas presentes en images/: {presentes}")


def ruta_imagen(multi_dir, image_path, variante=None):
    """Resuelve una ruta del manifiesto contra la variante activa.

    El manifiesto guarda rutas del tipo 'images/xxx.png'; solo se conserva el
    nombre del archivo y se antepone el directorio de la variante.
    """
    return str(carpeta_imagenes(multi_dir, variante) / Path(image_path).name)


def dir_salida(base_dir, nombre, variante=None, crear=True):
    """Directorio de resultados con la variante en el nombre.

    'resultados_multiedicion' -> 'resultados_multiedicion_sin_titulo'
    """
    v = variante or VARIANTE
    _validar(v)
    d = Path(base_dir) / f"{nombre}_{v}"
    if crear:
        d.mkdir(parents=True, exist_ok=True)
    return d


def resumen(multi_dir, variante=None):
    """Línea informativa para imprimir al inicio de cada notebook."""
    v = variante or VARIANTE
    carpeta = carpeta_imagenes(multi_dir, v)
    n = len(list(carpeta.glob("*.png")))
    return f"variante: {v} | carpeta: {carpeta.name} | {n} imágenes"


def comparar_variantes(base_dir, nombre, metrica="i2t_R@1", archivo=None):
    """Une los resultados de ambas variantes en una tabla comparativa.

    Solo funciona si las dos corridas ya existen; devuelve None si falta alguna.
    """
    import pandas as pd

    partes = []
    for v in CARPETAS:
        d = Path(base_dir) / f"{nombre}_{v}"
        f = d / (archivo or "resumen_multiedicion.csv")
        if not f.exists():
            print(f"falta {f}; ejecutar el notebook con VARIANTE='{v}'")
            return None
        df = pd.read_csv(f)
        df["variante"] = v
        partes.append(df)

    todo = pd.concat(partes, ignore_index=True)
    claves = [c for c in ("modelo", "caption") if c in todo.columns]
    tabla = todo.pivot_table(index=claves, columns="variante", values=metrica)
    if set(CARPETAS) <= set(tabla.columns):
        tabla["caida"] = (tabla["sin_titulo"] - tabla["con_titulo"]).round(4)
        tabla["caida_%"] = (100 * tabla["caida"] / tabla["con_titulo"]).round(1)
    return tabla.round(4)


if __name__ == "__main__":
    base = Path(__file__).parent
    print(resumen(base / "multiedicion"))
    print("salida de ejemplo:", dir_salida(base, "resultados_multiedicion",
                                           crear=False).name)

# Notebooks 

Ejecutar en orden. Los dos primeros no necesitan GPU ni descargar modelos.

| Notebook | Qué hace | Requiere |
|---|---|---|
| `01_dataset_y_validacion.ipynb` | Une las tres ediciones, revisa colisiones de títulos, declara el confound de citación y corre 9 pruebas de integridad | pandas, matplotlib, Pillow |
| `02_cierre_numeral8.ipynb` | Evidencia de la sección 8.2: MRR, tabla de efectos, IC bootstrap, McNemar, truncación, casos | pandas, numpy|
| `03_evaluacion_multiedicion.ipynb` | Los tres modelos sobre las tres ediciones, con pools separados | GPU ~8 GB |
| `04_evaluacion_composicional.ipynb` | Winoground adaptado: 12 pares a mano o 40 con vocabulario idéntico | GPU |
| `05_reranking_dos_etapas.ipynb` | Bi-encoder + cross-encoder sobre vector agrupado y sobre parches | GPU |
| `06_distractores_duros.ipynb` | Pool por sección frente a pool aleatorio del mismo tamaño | GPU |

## Elegir la variante de imágenes

El manifiesto es el mismo para las dos variantes; cambia solo la subcarpeta:

```
multiedicion/images/
├── con_titulo/     95 PNG con el título impreso
└── sin_titulo/     95 PNG con la franja del título recortada
```

La decisión se toma en **un solo lugar**, `config_variante.py`:

```python
VARIANTE = "sin_titulo"      # o "con_titulo"
```

También se puede fijar sin editar el archivo, antes de abrir Jupyter:

```bash
MCC225_VARIANTE=con_titulo jupyter lab
```

Los notebooks 01 y 03 a 06 la leen de ahí e imprimen al inicio qué variante
están usando, cuántas imágenes encontraron y en qué carpeta.

## Los resultados llevan la variante en el nombre

Cada notebook escribe en un directorio con sufijo:

```
resultados_multiedicion_con_titulo/     resultados_multiedicion_sin_titulo/
resultados_winoground_con_titulo/       resultados_winoground_sin_titulo/
resultados_reranking_con_titulo/        resultados_reranking_sin_titulo/
resultados_distractores_con_titulo/     resultados_distractores_sin_titulo/
```

Así dos corridas nunca se sobrescriben y siempre se puede saber de dónde salió
cada CSV. Es la razón de ser del módulo: en una versión anterior una corrida sin
título sobrescribió los resultados con título y hubo que reconstruirlos.

## El caso del notebook 02

Este notebook no lee imágenes, así que la variante no le aplica directamente.
Lo que sí cambia por completo el significado de sus tablas es de qué corrida
provienen los rangos, y eso se declara en la primera celda:

```python
FUENTE = "cuaderno14"      # o "multiedicion"
```

| Fuente | Datos | Destino |
|---|---|---|
| `multiedicion` *(por defecto)* | las tres ediciones, n=95, en la variante activa | `resultados_cierre_<variante>/` |
| `cuaderno14` | los 40 gráficos de 2026-1 con título, corrida original | `resultados_cierre_cuaderno14/` |

Con `multiedicion` hay que haber ejecutado antes el notebook 03 con esa misma
variante; si falta, el notebook lo dice y señala qué ejecutar.

**Todo se recalcula sobre los 95 gráficos**, incluida la auditoría de tokens: no
se lee de un CSV previo, porque la del Cuaderno14 solo cubría 40 y las tasas de
truncación saldrían sesgadas. La celda usa `CLIPTokenizerFast` si `transformers`
está instalado y avisa si cae a la aproximación por palabras.

La primera celda imprime siempre la fuente y el destino. Esto existe porque la
procedencia de estos CSV llegó a perderse: `mcnemar_estabilidad.csv` no declaraba
de qué corrida salía y hubo que reconstruirlo.

Ninguna de las dos fuentes escribe ya en `results/`: cada una tiene su propio
directorio, de modo que conviven sin pisarse. Para la entrega, copiar a
`results/` el conjunto que se declare como definitivo:

```bash
cp resultados_cierre_sin_titulo/*.csv resultados_cierre_sin_titulo/*.json results/
```

## Comparar las dos variantes

Una vez ejecutadas ambas:

```python
from config_variante import comparar_variantes
comparar_variantes(BASE, "resultados_multiedicion")
```

Devuelve una tabla con el R@1 de cada variante, la caída absoluta y la relativa.

## Por qué el módulo falla en vez de adivinar

Si las imágenes están sueltas en `images/` sin subcarpeta, `carpeta_imagenes()`
lanza un error con instrucciones en lugar de usarlas. Un directorio sin sufijo no
indica qué contiene, y una corrida etiquetada `con_titulo` ejecutada sobre
imágenes recortadas no dejaría ninguna traza del error.

## Ejecución

```bash
pip install -r ../requirements-minimo.txt    # notebooks 01 y 02, sin GPU
pip install -r ../requirements.txt           # todo
```

Desde Jupyter: **Run > Run All Cells**. Los notebooks detectan si se ejecutan
desde `notebooks/` o desde la raíz del proyecto.

Para una prueba rápida del notebook 03, en la celda 3.3 reducir:

```python
modelos = ["CLIP-L"]
captions = ["caption_2"]
```

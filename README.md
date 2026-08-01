# Capacidad y límites de modelos tipo CLIP para el análisis de información gráfica en documentos financieros

**Oscar Benito Toledo Guerrero** · MCC225 — IA Generativa y Aprendizaje Multimodal · Período 2026-1



---

## Pregunta experimental

LongCLIP amplía la ventana de contexto de CLIP de 77 a 248 tokens conservando el
mismo encoder visual. Si un caption largo describe mejor un gráfico, LongCLIP
debería superar a CLIP-L.

> **Al recuperar el caption correcto de un gráfico financiero, ¿la ventaja de
> LongCLIP proviene de su ventana de contexto o de su encoder visual?**

El diseño separa ambas variables usando CLIP-L como puente:

| Modelo | Encoder | Parches (224×224) | Tokens |
|---|---|---|---|
| CLIP-B | ViT-B/32 | 49 | 77 |
| CLIP-L | ViT-L/14 | 256 | 77 |
| LongCLIP | ViT-L/14 | 256 | 248 |

- **efecto de tamaño** = CLIP-L − CLIP-B (mismo límite de tokens)
- **efecto de contexto** = LongCLIP − CLIP-L (mismo encoder)

Comparar CLIP-B con LongCLIP no separaría nada: cambian las dos cosas a la vez.

## Qué evalúa y qué NO evalúa

Evalúa **retrieval imagen-texto**: si la imagen de un gráfico recupera su
descripción correcta entre las candidatas. **No evalúa** lectura de valores
numéricos ni razonamiento financiero. Un R@1 alto significa que el modelo
distingue ese gráfico de los demás, no que haya leído sus ejes.

Los controles de la sección siguiente cuantifican esa distinción en lugar de
solo declararla.

## Resultado principal

R@1 imagen→texto, promedio ponderado sobre las tres ediciones (n=95):

| Modelo | caption_2 | caption_3 | caption_4 |
|---|---|---|---|
| CLIP-B | 0.400 | 0.474 | 0.358 |
| CLIP-L | **0.684** | 0.632 | 0.484 |
| LongCLIP | 0.600 | 0.642 | 0.453 |

Prueba pareada de McNemar (valores *p*):

| Comparación | Originales | Sin título |
|---|---|---|
| Efecto de tamaño (B→L) | 5/32 · **p<0.0001** | 9/20 · p=0.061 |
| Efecto de contexto, caption corto | 17/9 · p=0.169 | 13/4 · **p=0.049** |
| Efecto de contexto, caption largo | 16/13 · p=0.711 | 9/7 · p=0.804 |

Discordancias como `solo_1 / solo_2`. En las cuatro comparaciones de contexto el
saldo favorece a **CLIP-L**, es decir en sentido contrario al que la hipótesis
inicial esperaba de LongCLIP.

**Conclusión.** El efecto de contexto no se sostiene: no es distinguible del
ruido con las imágenes originales, y sin el título impreso resulta significativo
pero *negativo*. La ganancia atribuible a los 248 tokens no existe.

## Los cuatro controles

Cada uno elimina un atajo distinto que el modelo podría usar en lugar de leer el
gráfico.

**1. Ablación del título impreso.** Los gráficos llevan su título dentro de la
imagen y los captions contienen ese mismo título. Al recortar la franja, CLIP-L
cae de 0.684 a 0.326: cerca de la mitad del desempeño era coincidencia léxica.
El efecto de tamaño pierde significancia en el proceso, lo que sugiere que parte
de la ventaja de ViT-L/14 era capacidad de leer texto pequeño.

**2. Prueba composicional (Winoground).** 40 pares con **vocabulario idéntico**
entre las dos opciones, donde la coincidencia léxica deja de discriminar. Group
score con las imágenes originales: 0.125 / 0.075 / 0.175; sin título: 0.000 /
0.025 / 0.075, frente a un azar de 0.25. Ningún modelo lo alcanza, y sin título
los tres quedan *significativamente por debajo* (p ≈ 1e-5 para CLIP-B). El sesgo
por imagen resulta trece veces mayor que la señal por caption, lo que anula el
image score por construcción.

**3. Distractores duros.** Pool restringido a gráficos de la misma sección,
comparado contra un pool aleatorio **del mismo tamaño**. La ventaja de
`caption_3` sobre `caption_2` en CLIP-L pasa de +0.074 a −0.012 con las imágenes
originales y de +0.150 a +0.024 sin título. Identifica el mecanismo: lo que
aportaba el caption largo era **vocabulario temático, no descripción del
gráfico**. Con las imágenes originales tres de seis comparaciones son
significativas (p=0.039, p=0.0005, p=0.001).

**4. Reranking en dos etapas.** Dos cabezas sobre rasgos congelados de CLIP-L
(vector agrupado y atención sobre parches), con negativos semi-duros y validación
dejando una edición fuera. Ambas empeoran el ranking: con las originales 0.213 y
0.117 frente a 0.638 del bi-encoder; sin título 0.149 y 0.160 frente a 0.330.
Quedan apenas por encima de reordenar al azar (~0.075). Con 69 imágenes por
pliegue no es viable aprender un cross-encoder: es un límite de datos, no una
propiedad de la arquitectura.

## Dataset

95 gráficos de tres ediciones del Informe de Estabilidad del Sistema Financiero
de la SBS (documentos públicos, uso académico):

| Edición | Informe | Gráficos |
|---|---|---|
| 2021-1 | IESF mayo 2021 | 26 |
| 2024-2 | IESF noviembre 2024 | 29 |
| 2026-1 | IESF mayo 2026 | 40 |

Recorte automático de la región del gráfico (PyMuPDF, 170 DPI). Cuatro captions
por imagen: `caption_2` es el título, `caption_3` añade la oración literal del
informe que lo comenta, `caption_4` es su versión condensada.

**Particiones.** Cada edición se evalúa como un **pool de recuperación
independiente**. No se mezclan las 95 imágenes en una sola matriz porque el R@1
depende del número de distractores, y porque tres títulos se repiten entre
ediciones y dejarían pares sin respuesta correcta única.

**Variantes de imagen.** `multiedicion/images/` (originales) y
`multiedicion/images_sin_titulo/` (sin la franja del título).


## Ejecución

```bash
# solo análisis, sin GPU, instala en ~1 minuto
pip install -r requirements-minimo.txt
python tests_dataset.py

# todo, incluida la evaluación de modelos
pip install -r requirements.txt
```

Ejecutar los notebooks en orden. Los notebooks 01 y 02 no requieren GPU y
regeneran todas las tablas del informe. Del 03 al 06 requieren GPU (~8 GB) y
descargan los checkpoints desde Hugging Face.

**Nota sobre LongCLIP.** Hay que ampliar `max_position_embeddings` a 248 *antes*
de cargar los pesos; sin ese paso el modelo se instancia con las 77 posiciones de
CLIP y la variable central del estudio no se activa. Los notebooks lo verifican
con un `assert`.

**Nota sobre torch.** Con torch anterior a 2.6, `transformers` bloquea la carga
por CVE-2025-32434. La solución es `use_safetensors=True`, que ya está en el
código; no hace falta actualizar torch.

## Configuración reproducible

Semilla 22514, decodificación determinista, rutas relativas al proyecto.
Checkpoints: `openai/clip-vit-base-patch32`, `openai/clip-vit-large-patch14`,
`zer0int/LongCLIP-GmP-ViT-L-14`. Registro completo en
`results/configuracion_experimental.json`.

## Limitaciones declaradas

- **Cambio de convención entre ediciones.** Desde 2026 la SBS cita los gráficos
  explícitamente en el texto; antes no. La columna `fuente_oracion` lo registra y
  se controla comparando modelos *dentro* de cada edición.
- **Poder estadístico.** IC95 de ±0.096 con n=95. La prueba composicional usa 12
  pares y es indicativa, no concluyente.
- **Alcance.** Evalúa retrieval y, como descubrimiento, OCR. Mide negativamente
  la lectura de tendencias. No evalúa VQA financiero, fuera del alcance de un
  dual encoder.

## Fuente

SBS Perú, Informe de Estabilidad del Sistema Financiero, ediciones mayo 2021,
noviembre 2024 y mayo 2026. Documentos públicos, uso académico.

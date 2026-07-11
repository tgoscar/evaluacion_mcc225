# Image-Text Retrieval con CLIP Models



## Descripción

Evaluación comparativa de modelos CLIP (CLIP-B, CLIP-L y LongCLIP) para recuperación de imágenes y texto en gráficos del SBS IESF. El experimento evalúa 40 gráficos extraídos con 3 variantes de descripciones (caption_2, caption_3, caption_4).

## Base de datos

Construida a partir de la información de los informes de Estabilidad Financiera - SBS

## Estrategia

Objetivo: Identificar el modelo que extrae la información visual más relevante de las imágenes.

Métrica principal: imagen→texto R@1. Esta mide directamente la capacidad de lectura visual: con qué frecuencia la imagen encuentra su descripción correcta en el primer intento. Es la prioridad absoluta, por encima de otras métricas como texto→imagen (mide comprensión de texto) o el score combinado (prioriza rendimiento general, no lectura visual).

Pasos de la estrategia:

Primero, comparar modelos usando el mismo caption para aislar el efecto del modelo. Con caption_2, LongCLIP obtiene 0.675, CLIP-L 0.650 y CLIP-B 0.450. LongCLIP es claramente superior.

Segundo, verificar que el rendimiento sea consistente en R@5 y R@10. LongCLIP con caption_2 mantiene 0.875 en R@5 y 0.950 en R@10, mostrando estabilidad.

Tercero, elegir el caption que mejor funciona con el modelo ganador. LongCLIP rinde igual o mejor con caption_2 (0.675) comparado con caption_4 (0.675) y solo ligeramente por debajo de caption_3 (0.725), pero caption_2 es más estable y consistente.



## Resultados Principales

**Mejor modelo para entender imágenes: LongCLIP + caption_2**
- R@1 (imagen→texto): **0.675** (mejor entre todos)
- R@5 (imagen→texto): 0.875
- R@10 (imagen→texto): 0.950

### Tabla Comparativa Completa

| Experimento | imagen→texto (R@1) | texto→imagen (R@1) | Score |
|-------------|-------------------|-------------------|--------|
| **LongCLIP + caption_2** | **0.675** | 0.875 | 0.296 |
| CLIP-B + caption_3 | 0.500 | 0.400 | **0.344** |
| CLIP-L + caption_2 | 0.650 | 0.750 | 0.313 |





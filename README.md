# Image-Text Retrieval con CLIP Models



## Descripción

Evaluación comparativa de modelos CLIP (CLIP-B, CLIP-L y LongCLIP) para recuperación de imágenes y texto en gráficos del SBS IESF. El experimento evalúa 40 gráficos extraídos con 3 variantes de descripciones (caption_2, caption_3, caption_4).

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





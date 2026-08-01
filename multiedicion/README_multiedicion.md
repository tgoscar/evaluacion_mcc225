# Extension multiedicion del dataset (Proyecto 2 MCC225)

Amplia el experimento de una sola edicion (n=40) a **tres ediciones del IESF de
la SBS**, convirtiendolo en un diseno de **replicas independientes**.

| Edicion | Informe | Graficos |
|---|---|---|
| 2021-1 | IESF Mayo 2021 | 26 |
| 2024-2 | IESF Noviembre 2024 | 29 |
| 2026-1 | IESF Mayo 2026 (original) | 40 |
| **Total** | | **95** |

## Que gana y que no gana el experimento con esto

**Gana precision y una prueba de generalizacion.** El IC95 pasa de +/-0.148 a
+/-0.096. Y por primera vez se puede responder si el ordenamiento de modelos se
sostiene en documentos distintos, separados por cinco anos de cambios de diseno.

**No rescata el efecto de contexto.** Escalando las discordancias observadas:

| Comparacion | n=40 | n=95 (proyectado) |
|---|---|---|
| Efecto tamano (B -> L) | p=0.057 | **p=0.001** |
| Efecto contexto (L -> Long, cap2) | p=1.000 | p=0.832 |
| Efecto contexto (L -> Long, cap3) | p=0.581 | p=0.281 |

Con 4 vs 5 discordancias el efecto de contexto es cercano a cero: mas muestra lo
estima con mas precision *como cero*, no lo vuelve significativo. El aporte real
de ampliar la muestra es poder afirmar "no es falta de datos" con respaldo.


## Archivos

```
manifest_2021-1.csv          26 pares
manifest_2024-2.csv          29 pares
manifest_multiedicion.csv    95 pares, con columnas 'edicion', 'chart_uid', 'fuente_oracion'
images/                      95 PNG a 170 DPI
tests_dataset.py             9 pruebas (duplicados evaluados por edicion)
```

`chart_uid` = "edicion|chart_id". Es necesario porque los identificadores se
repiten entre ediciones (I.A.1 existe en 2021 y en 2024).

## Reproduccion

```bash
pip install pymupdf pandas pillow
python 06_extender_ediciones.py --pdf IESF20242A.pdf --edicion 2024-2
python 06_extender_ediciones.py --pdf Informe_de_Estabilidad_Financiera_2021I.pdf --edicion 2021-1
python 06_extender_ediciones.py --unir
python tests_dataset.py
```

## Limitaciones de la extraccion

- Los recortes se detectan automaticamente (trazos vectoriales + imagenes
  incrustadas, anclados al titulo del grafico y excluyendo el logo del
  encabezado). Conviene revisar visualmente una muestra antes de la corrida final.
- En 2024-2 se localizaron 29 de los 40 graficos referenciados: los restantes
  aparecen en recuadros y anexos cuyo titulo no sigue el formato del cuerpo.
- El grafico I.B.9 de 2024-2 no tiene oracion asociada; sus caption_3 y caption_4
  quedan reducidos al titulo. Es un caso honesto, equivalente al I.A.8 del
  dataset original.

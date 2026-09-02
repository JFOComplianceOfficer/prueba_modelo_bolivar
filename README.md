# MIRA — Matriz Inteligente de Riesgos y Alertas

App web (Streamlit) que genera matrices de riesgo parametrizables — LA/FT/FP, C/ST, o riesgo
empresarial genérico — alineadas con la Circular Externa 100-000020 de 2026 (Supersociedades,
Capítulo IX), la normativa SARLAFT del sector transporte (Supertransporte), y estándares
internacionales (COSO ERM, ISO 31000, DAFP V6) para cualquier empresa sin obligación LA/FT.

**Proyecto de portafolio / demo técnica.**

## ¿Qué hace?

1. Caracteriza al cliente (ingresos, activos, sector) y determina automáticamente su régimen
   normativo aplicable según el alcance elegido — Capítulo IX, Transporte, o ninguno (genérico).
2. Sugiere un perfil de apetito de riesgo, editable por la junta directiva del cliente.
3. Genera la matriz de riesgos completa: inherente, controles, residual, alertas metodológicas.
4. Exporta el resultado a Excel con formato profesional.

## Catálogos incluidos

- **Riesgo Empresarial Genérico** (predeterminado) — 12 riesgos, 5 dimensiones de impacto base
  (Financiero, Operativo, Reputación, Legal y normativo, Seguridad y ambiente).
- **LA/FT/FP — Sector Transporte** — 15 riesgos, las 5 base + Contagio.
- **Sistema Unificado LA/FT/FP y C/ST — Capítulo IX** — 18 riesgos, las 5 base + Contagio.
- **SARLAFT — Superintendencia Financiera** — 16 riesgos, para entidades vigiladas por la SFC
  (bancos, aseguradoras, fiduciarias, comisionistas de bolsa). Usa las 4 dimensiones oficiales
  que define la propia norma — Reputacional, Legal, Operativo, Contagio — sin las genéricas.

Las dimensiones de impacto se detectan automáticamente de cualquier columna `imp_*` en el
catálogo — un cliente puede traer más, menos, o distintas dimensiones sin tocar código.

## Motor de cálculo

Validado con paridad perfecta (142/142, 100%) contra una matriz de riesgos real, y contrastado
contra el estándar internacional (Wolfsberg Group, ISO 31000, COSO ERM, DAFP V6, SARLAFT).

## Cómo correrla localmente

```bash
pip install -r requirements.txt
streamlit run app.py
```

## Estructura del proyecto

```
prueba_modelo_bolivar/
├── app.py                  # Interfaz web (Streamlit)
├── marca.py                 # Identidad visual (banner, secciones, pie de página)
├── motor/
│   ├── calculo.py            # Motor de cálculo
│   └── graficos.py           # Mapas de calor (Plotly)
├── assets/                  # Favicon
├── data/                    # Configuración y catálogos de riesgos (3 catálogos semilla)
├── .streamlit/config.toml    # Tema de color
└── requirements.txt
```

## Estado del proyecto

- ✅ Fase 1 — Motor de cálculo (cerrada, validada)
- ✅ Fase 2 — Parametrización (cerrada)
- ✅ Fase 3 — Interfaz web (cerrada)
- ✅ Fase 4 — Publicación en Streamlit Community Cloud (cerrada)
- 🔄 Beta pública — recogiendo feedback de la comunidad de creadores de contenido y colegas
  oficiales de cumplimiento; generador de documentación (políticas, manuales) pendiente de
  construir con base en ese feedback real.

"""
Identidad visual — Demo técnica MIRA (Matriz Inteligente de Riesgos y Alertas).

Centraliza el banner, las cabeceras de sección, la caja de introducción y el
pie de página para que toda la app comparta una sola fuente de verdad de
estilo.

Paleta:
  Azul Noche       #0D1B2A   (primario)
  Dorado Champagne #C8A96A   (acento — nunca fondo)
  Grafito          #1F1F1F   (texto secundario)
  Blanco           #F7F7F7
Tipografías: Playfair Display (títulos) · Montserrat (descriptor/UI)
"""

import streamlit as st

NAVY = "#0D1B2A"
GOLD = "#C8A96A"
GRAFITO = "#1F1F1F"
CREMA = "#F7F7F7"
GRIS = "#6B6B6B"

_FUENTES = (
    "@import url('https://fonts.googleapis.com/css2?"
    "family=Playfair+Display:wght@600;700&family=Montserrat:wght@400;600;700&display=swap');"
)


def inicio_marca():
    """Inyecta las fuentes UNA vez y dibuja el banner de encabezado con el
    nombre de la herramienta y la insignia BETA."""
    st.markdown(f"<style>{_FUENTES}</style>", unsafe_allow_html=True)
    st.markdown(
        f"""
        <div style="background:{NAVY}; padding:28px 36px; margin:-1rem -1rem 1.5rem -1rem;
                    border-bottom:3px solid {GOLD}; display:flex; justify-content:space-between;
                    align-items:center; flex-wrap:wrap; gap:12px;">
          <div>
            <span style="font-family:'Playfair Display', Georgia, serif; font-size:32px;
                        font-weight:700; color:{CREMA}; letter-spacing:1px;">
              MIRA
            </span>
            <div style="font-family:'Montserrat', sans-serif; font-size:11px; letter-spacing:3px;
                        color:{CREMA}; margin-top:2px;">DEMO TÉCNICA</div>
          </div>
          <div style="text-align:right;">
            <div style="display:flex; align-items:baseline; justify-content:flex-end; gap:10px;">
              <span style="background:{GOLD}; color:{NAVY}; font-size:10px; font-weight:700;
                          padding:2px 8px; border-radius:3px; letter-spacing:1px;">BETA</span>
            </div>
            <div style="font-family:'Montserrat', sans-serif; font-size:11px; letter-spacing:1.5px;
                        color:{GOLD}; margin-top:3px;">MATRIZ INTELIGENTE DE RIESGOS Y ALERTAS</div>
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def intro_box(html_texto):
    """Caja de introducción con acento dorado — reemplaza el st.info azul
    genérico por algo consistente con la marca."""
    st.markdown(
        f"""
        <div style="background:{CREMA}; border-left:3px solid {GOLD}; padding:16px 20px;
                    margin:0 0 20px 0; font-size:14.5px; color:{GRAFITO}; line-height:1.55;
                    border-radius:2px;">
          {html_texto}
        </div>
        """,
        unsafe_allow_html=True,
    )


def seccion(numero, titulo):
    """Cabecera de sección numerada (reemplazo de st.header) — círculo navy/
    dorado con el número, título en Montserrat, línea dorada divisoria."""
    st.markdown(
        f"""
        <div style="display:flex; align-items:center; gap:14px; margin:2.2rem 0 4px 0;">
          <div style="background:{NAVY}; color:{GOLD}; font-family:'Playfair Display', Georgia, serif;
                      font-weight:700; font-size:19px; width:36px; height:36px; border-radius:50%;
                      display:flex; align-items:center; justify-content:center; flex-shrink:0;">
            {numero}
          </div>
          <div style="font-family:'Montserrat', sans-serif; font-weight:700; font-size:19px;
                      color:{NAVY}; letter-spacing:0.2px;">{titulo}</div>
        </div>
        <hr style="border:none; border-top:1px solid {GOLD}; opacity:0.45; margin:8px 0 16px 0;">
        """,
        unsafe_allow_html=True,
    )


def footer_app():
    """Pie de página persistente — proyecto de demostración técnica."""
    st.markdown(
        f"""
        <div style="margin-top:3rem; padding:20px 4px 8px 4px; border-top:1px solid {GOLD};">
          <div style="display:flex; justify-content:space-between; align-items:center;
                      flex-wrap:wrap; gap:10px;">
            <div style="font-family:'Playfair Display', Georgia, serif; font-size:15px;
                        color:{NAVY}; font-weight:700;">
              MIRA
              <span style="font-family:'Montserrat', sans-serif; font-size:11px; color:{GRIS};
                          letter-spacing:1px; font-weight:400;"> — DEMO TÉCNICA</span>
            </div>
            <div style="font-family:'Montserrat', sans-serif; font-size:12px; color:{GRIS};">
              Proyecto de portafolio — Matriz Inteligente de Riesgos y Alertas
            </div>
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

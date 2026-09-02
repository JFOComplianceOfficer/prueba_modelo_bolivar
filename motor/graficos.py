"""
Visualizaciones — mapas de calor de riesgos (RD-008).
Separado de calculo.py a propósito: aquí vive presentación, no lógica de negocio.
Si esto se rompe, el motor de cálculo sigue intacto.
"""

import plotly.graph_objects as go

from .calculo import NIVEL_A_IMPACTO, NIVEL_A_PROBABILIDAD, PERFILES_APETITO

# Paleta semántica refinada (verde→rojo, como exige la convención de la industria
# y cualquier oficial de cumplimiento espera reconocer de un vistazo) pero con tonos
# más sobrios que el verde/amarillo/rojo saturado de Excel — más cerca de lo que se
# ve en un informe de junta directiva que en una hoja de cálculo.
COLOR_NIVEL = {
    "MUY BAJO": "#9CC7A1", "INSIGNIFICANTE": "#9CC7A1",
    "BAJO": "#C9D98A",
    "MODERADO": "#F0C25A", "MEDIO": "#F0C25A",
    "ALTO": "#E58F4F",
    "EXTREMO": "#C6524A", "SIGNIFICATIVO": "#C6524A",
}

# Mismos valores de paleta que marca.py (import directo crearía un ciclo
# motor→app, así que se repiten aquí; son solo 2 constantes de color).
NAVY = "#0D1B2A"
GOLD = "#C8A96A"
CREMA = "#F7F7F7"
FUENTE = "Montserrat, -apple-system, sans-serif"


def _dibujar_fondo(fig, apetito):
    """Dibuja las 25 celdas de la matriz de apetito, con su etiqueta de nivel. Reutilizado
    por las tres vistas para que las tres compartan exactamente los mismos colores y zonas."""
    for nivel_prob in range(1, 6):
        for nivel_imp in range(1, 6):
            etiqueta_nivel = apetito[nivel_prob][nivel_imp - 1]
            color = COLOR_NIVEL.get(etiqueta_nivel, "#DDDDDD")
            fig.add_shape(
                type="rect",
                x0=nivel_imp - 0.5, x1=nivel_imp + 0.5,
                y0=nivel_prob - 0.5, y1=nivel_prob + 0.5,
                fillcolor=color, opacity=0.65, line=dict(width=1.5, color=CREMA),
                layer="below",
            )
            fig.add_annotation(
                x=nivel_imp, y=nivel_prob, text=etiqueta_nivel,
                showarrow=False, font=dict(size=9, color="rgba(13,27,42,0.4)", family=FUENTE),
            )


def _ejes(fig, titulo):
    fig.update_xaxes(
        tickmode="array", tickvals=[1, 2, 3, 4, 5],
        ticktext=[NIVEL_A_IMPACTO[n] for n in range(1, 6)],
        title="Impacto", range=[0.4, 5.6], showgrid=False, zeroline=False,
    )
    fig.update_yaxes(
        tickmode="array", tickvals=[1, 2, 3, 4, 5],
        ticktext=[NIVEL_A_PROBABILIDAD[n] for n in range(1, 6)],
        title="Probabilidad", range=[0.4, 5.6], showgrid=False, zeroline=False,
    )
    fig.update_layout(
        title=dict(text=titulo, font=dict(family=FUENTE, size=17, color=NAVY)),
        height=520,
        plot_bgcolor=CREMA, paper_bgcolor="rgba(0,0,0,0)",
        font=dict(family=FUENTE, color="#1F1F1F"),
        margin=dict(t=60, b=40, l=40, r=20), showlegend=False,
    )


def _jitter(i):
    """Jitter determinístico (no aleatorio de verdad): riesgos en la misma celda no
    quedan exactamente apilados uno sobre otro, pero el resultado es siempre igual."""
    return ((i % 5) - 2) * 0.07, ((i // 5 % 5) - 2) * 0.07


def graficar_mapa_simple(matriz_df, tipo="inherente", apetito_nombre="moderado", titulo=None):
    """Un solo mapa de calor: solo el riesgo inherente, o solo el residual — no ambos.
    Los puntos NO llevan texto visible (se veían amontonados con muchos riesgos por
    celda); la identificación del riesgo viaja en 'customdata' (para el clic) y en el
    texto del hover (para pasar el mouse), sin ensuciar la imagen."""
    apetito = PERFILES_APETITO[apetito_nombre]
    columna_coord = "coord_inherente" if tipo == "inherente" else "coord_residual"
    columna_nivel = "nivel_inherente" if tipo == "inherente" else "nivel_residual"
    color_punto = CREMA if tipo == "inherente" else NAVY
    borde_punto = dict(width=2.5, color=NAVY) if tipo == "inherente" else dict(width=2, color=GOLD)

    fig = go.Figure()
    _dibujar_fondo(fig, apetito)

    for i, fila in matriz_df.reset_index(drop=True).iterrows():
        jitter_x, jitter_y = _jitter(i)
        y, x = fila[columna_coord][0] + jitter_y, fila[columna_coord][1] + jitter_x

        fig.add_trace(go.Scatter(
            x=[x], y=[y], mode="markers",
            marker=dict(size=15, color=color_punto, line=borde_punto),
            customdata=[[fila["id"]]],
            hovertext=(f"<b>{fila['id']}</b>: {fila[columna_nivel]}<br>"
                       f"{str(fila['descripcion'])[:70]}<br><i>Clic para ver el detalle completo</i>"),
            hoverinfo="text",
        ))

    if titulo is None:
        titulo = f"Mapa de calor — Riesgo {'Inherente' if tipo == 'inherente' else 'Residual'}"
    _ejes(fig, titulo)
    return fig


def graficar_mapa_desplazamiento(matriz_df, apetito_nombre="moderado", titulo="Desplazamiento inherente → residual"):
    """Vista avanzada: inherente y residual juntos, con flecha de desplazamiento entre
    ambos. El movimiento vertical evidencia controles preventivos/detectivos; el
    horizontal, correctivos (RD-002). Más informativa, también más cargada visualmente
    — mejor para explicar la metodología que para una lectura rápida."""
    apetito = PERFILES_APETITO[apetito_nombre]
    fig = go.Figure()
    _dibujar_fondo(fig, apetito)

    filas = matriz_df.reset_index(drop=True)
    for i, fila in filas.iterrows():
        jitter_x, jitter_y = _jitter(i)

        yi, xi = fila["coord_inherente"][0] + jitter_y, fila["coord_inherente"][1] + jitter_x
        yr, xr = fila["coord_residual"][0] + jitter_y, fila["coord_residual"][1] + jitter_x

        fig.add_annotation(
            x=xr, y=yr, ax=xi, ay=yi, xref="x", yref="y", axref="x", ayref="y",
            showarrow=True, arrowhead=2, arrowsize=1, arrowwidth=1.4,
            arrowcolor="rgba(200,169,106,0.85)",
        )

        descripcion_corta = str(fila["descripcion"])[:70]

        fig.add_trace(go.Scatter(
            x=[xi], y=[yi], mode="markers",
            marker=dict(size=11, color=CREMA, line=dict(width=2, color=NAVY)),
            name="Inherente", legendgroup="inherente", showlegend=(i == 0),
            hovertext=f"<b>{fila['id']}</b> (inherente): {fila['nivel_inherente']}<br>{descripcion_corta}",
            hoverinfo="text",
        ))
        fig.add_trace(go.Scatter(
            x=[xr], y=[yr], mode="markers",
            marker=dict(size=11, color=NAVY, line=dict(width=1.5, color=GOLD)),
            name="Residual", legendgroup="residual", showlegend=(i == 0),
            hovertext=f"<b>{fila['id']}</b> (residual): {fila['nivel_residual']}<br>{descripcion_corta}",
            hoverinfo="text",
        ))

    _ejes(fig, titulo)
    fig.update_layout(
        showlegend=True,
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1,
                    font=dict(family=FUENTE, size=12, color="#1F1F1F")),
    )
    return fig


# -*- coding: utf-8 -*-
"""
Encuesta de satisfacción — captura opiniones de cualquier visitante, no solo de
quien llega a generar una matriz completa. Se guarda en un Google Sheet (gratis,
persistente de verdad — a diferencia de un CSV local, que Streamlit Cloud borra
cada vez que la app duerme o se reinicia).

Requiere en .streamlit/secrets.toml (NUNCA subir este archivo a git — ya está en
.gitignore):

    [connections.gsheets]
    spreadsheet = "https://docs.google.com/spreadsheets/d/TU_ID_AQUI/edit"
    type = "service_account"
    project_id = "..."
    private_key_id = "..."
    private_key = "..."
    client_email = "..."
    client_id = "..."
    ... (el resto del JSON de la cuenta de servicio de Google Cloud)

Si esas credenciales todavía no están configuradas, la encuesta se sigue
mostrando pero avisa con un mensaje claro en vez de tronar la app — así no
bloquea a nadie mientras Juancho termina de configurar Google Cloud.
"""

from datetime import datetime

import pandas as pd
import streamlit as st

NOMBRE_HOJA = "Respuestas"
COLUMNAS = ["fecha", "nombre", "calificacion", "que_le_sirvio", "que_le_falto", "recomendaria"]


def _conexion_disponible():
    try:
        return "connections" in st.secrets and "gsheets" in st.secrets.get("connections", {})
    except Exception:
        # st.secrets lanza StreamlitSecretNotFoundError (no un dict vacío) cuando
        # todavía no existe NINGÚN archivo secrets.toml — exactamente el estado
        # normal antes de configurar Google Sheets. No debe tronar la app por eso.
        return False


def _guardar_respuesta(fila: dict):
    from streamlit_gsheets import GSheetsConnection

    conn = st.connection("gsheets", type=GSheetsConnection)
    try:
        existente = conn.read(worksheet=NOMBRE_HOJA, ttl=0)
        existente = existente.dropna(how="all")
    except Exception:
        existente = pd.DataFrame(columns=COLUMNAS)

    nueva = pd.concat([existente, pd.DataFrame([fila])], ignore_index=True)
    conn.update(worksheet=NOMBRE_HOJA, data=nueva)


def encuesta_satisfaccion():
    """Bloque de encuesta — se coloca donde tenga sentido en el flujo (hoy: al
    final de la página, visible para cualquiera, haya o no generado su matriz)."""
    with st.expander("💬 ¿Qué te pareció MIRA? — 1 minuto, nos ayuda muchísimo", expanded=False):
        if not _conexion_disponible():
            st.info(
                "La encuesta todavía se está configurando — vuelve pronto."
            )
            return

        with st.form("form_encuesta_satisfaccion", clear_on_submit=True):
            nombre = st.text_input("Tu nombre (opcional)")
            calificacion = st.slider("¿Qué tan útil te pareció MIRA?", 1, 5, 4,
                                      help="1 = nada útil, 5 = muy útil")
            que_le_sirvio = st.text_area("¿Qué fue lo que más te sirvió?", height=80)
            que_le_falto = st.text_area("¿Qué le faltó, o qué no se entendió?", height=80)
            recomendaria = st.radio("¿Se la recomendarías a un colega?",
                                     ["Sí", "Tal vez", "No"], horizontal=True)
            enviado = st.form_submit_button("Enviar")

        if enviado:
            fila = {
                "fecha": datetime.now().strftime("%Y-%m-%d %H:%M"),
                "nombre": nombre or "(anónimo)",
                "calificacion": calificacion,
                "que_le_sirvio": que_le_sirvio,
                "que_le_falto": que_le_falto,
                "recomendaria": recomendaria,
            }
            try:
                _guardar_respuesta(fila)
                st.success("¡Gracias! Tu respuesta quedó registrada. 🙌")
            except Exception as e:
                st.error(
                    "No se pudo guardar tu respuesta en este momento — inténtalo de nuevo "
                    "en unos minutos.\n\n"
                    f"Detalle técnico: {e}"
                )

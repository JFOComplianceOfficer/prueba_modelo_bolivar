"""
App de Matriz de Riesgos Parametrizable — Fase 3.
Nombre comercial de la app: MIRA (Matriz Inteligente de Riesgos y Alertas).
Ejecutar con: python -m streamlit run app.py
"""

import io
from pathlib import Path

import pandas as pd
import streamlit as st

from motor.calculo import (
    CATALOGOS_DISPONIBLES,
    CONFIG_DEFAULT,
    PERFILES_APETITO,
    alertas_del_riesgo,
    caracterizar_cliente,
    caracterizar_cliente_generico,
    caracterizar_cliente_sarlaft_sfc,
    caracterizar_cliente_transporte,
    cargar_catalogo,
    diagnosticar_calibracion,
    evaluar_riesgo,
    exportar_matriz,
)
from motor.graficos import COLOR_NIVEL, graficar_mapa_desplazamiento, graficar_mapa_simple
from encuesta import encuesta_satisfaccion
from marca import footer_app, inicio_marca, intro_box, seccion

_FAVICON = Path(__file__).resolve().parent / "assets" / "favicon.png"
st.set_page_config(
    page_title="MIRA — Demo",
    page_icon=str(_FAVICON) if _FAVICON.exists() else "🛡️",
    layout="wide",
)

# ------------------------------------------------------------------
# Estado de sesión
# ------------------------------------------------------------------
for clave, valor_inicial in [("caracterizacion", None), ("matriz", None), ("catalogo_activo", None)]:
    if clave not in st.session_state:
        st.session_state[clave] = valor_inicial

inicio_marca()

# ====================================================================
# INTRO — qué puede hacer la persona aquí, en una frase (feedback de comunidad)
# ====================================================================
intro_box(
    "<b>¿Qué puedes hacer aquí?</b> Descubre si tu empresa está vigilada en materia de "
    "lavado de activos, financiación del terrorismo y corrupción — por quién, qué "
    "régimen te aplica y desde cuándo — y genera tu matriz de riesgos completa en minutos. "
    "Empieza abajo con los datos básicos de tu empresa."
)

encuesta_satisfaccion()

# ====================================================================
# GUÍA + GLOSARIO — un solo punto de entrada, colapsado por defecto para
# no bloquear a quien ya conoce la app y solo quiere generar su matriz.
# Sigue siendo obviamente visible (primera línea bajo la intro), pero
# ya no es un ladrillo de texto obligatorio para el primer vistazo.
# ====================================================================
with st.expander("🧭 Guía y glosario — ábrelo si es tu primera vez aquí (2 min)", expanded=False):
    tab_guia, tab_glosario = st.tabs(["🚀 Cómo empezar", "📖 Glosario de términos"])

    with tab_guia:
        st.markdown("""
**¿Qué vas a hacer aquí, paso a paso?**
1. **Cuéntanos de tu empresa** (Paso 1 abajo): ingresos, activos, sector. La app calcula automáticamente si estás obligado, con qué régimen, y por qué — con la norma exacta que lo sustenta.
2. **Confirma el apetito de riesgo** (Paso 2): qué tan estricta quiere ser tu empresa al clasificar sus riesgos. Si no sabes cuál elegir, deja el que la app te sugiere — está pensado para tu régimen.
3. **Elige tu catálogo de riesgos** (Paso 3): el catálogo base de la app (riesgos típicos ya cargados) o el tuyo propio, con los riesgos reales de tu empresa.
4. **Genera tu matriz** (Paso 4): en segundos tendrás el mapa de calor interactivo, las alertas metodológicas y el Excel descargable.

**Sobre la escala de calificación — para que ningún número te tome por sorpresa:**  
Tanto la probabilidad como el impacto de cada riesgo se califican en una escala de **1 a 5** (1 = muy bajo o rara vez, 5 = muy alto o casi seguro). Es la escala estándar de la metodología de gestión de riesgos (ISO 31000, DAFP, SARLAFT) — no la inventamos nosotros, así trabaja toda la industria.

**¿Cómo pongo MIS riesgos reales, no los de ejemplo?**  
En el Paso 3, descarga el catálogo base con el botón "⬇️ Descargar este catálogo". Ábrelo en Excel: tiene dos hojas, *Riesgos* y *Controles*. Edita, borra o agrega filas con los riesgos y controles reales de tu empresa — conserva los nombres de las columnas y de las hojas. Luego vuelve al Paso 3, elige "Subir mi propio catálogo (Excel)" y sube tu archivo editado. La app recalcula todo con tus datos, no con los de ejemplo.

**¿Puedo usar menos (o más) dimensiones de impacto que las del catálogo base?**  
Sí. Las columnas de impacto en la hoja *Riesgos* siguen el patrón `imp_nombre` (ej. `imp_legal_normativo`, `imp_financiero`). Puedes dejar solo las que tu empresa realmente evalúa, o agregar dimensiones propias de tu industria. La app detecta automáticamente cuáles trajiste y calcula con esas, sin necesidad de tocar nada más.

**Dudas frecuentes:**
- *"No sé qué es un 'régimen' ni qué significan las siglas."* — Abre el glosario justo debajo de este texto (📖 ¿Qué significa cada opción?). Cada término está explicado sin tecnicismos.
- *"¿Qué pasa si no sé algún dato exacto (ingresos, activos)?"* — Usa tu mejor estimación para probar la app. Para un caso real, el régimen se puede corregir manualmente dejando el motivo por escrito — eso mismo exige la norma: trazabilidad de cada decisión.
- *"¿Esto reemplaza a mi oficial de cumplimiento o a mi asesor legal?"* — No. Es una herramienta de apoyo que acelera el cálculo técnico; la decisión final y la responsabilidad siguen siendo de tu junta directiva y tu oficial de cumplimiento.
- *"¿Por qué el mapa se ve distinto si cambio el perfil de apetito?"* — Porque el apetito de riesgo (conservador/moderado/agresivo) define qué tan exigente es la clasificación. Es una decisión de la junta directiva, no un error de la app.

**🔒 Sobre tus datos — para que pruebes sin miedo:**  
Esta app **no guarda ni almacena tu información en ningún servidor.** No hay base de datos detrás todavía. Todo lo que escribes, subes o generas vive únicamente en tu sesión del navegador — al cerrar o refrescar la página, desaparece. Nadie más que tú ve lo que ingresas aquí.

**🧪 Es una versión BETA.** Seguimos construyéndola activamente, y tu prueba de hoy nos ayuda a mejorarla. Si algo no se entiende, no funciona, o crees que le falta algo — escríbenos, todo el feedback es bienvenido.
""")

    with tab_glosario:
        st.markdown("""
**Regímenes — Sistema Unificado Capítulo IX (Supersociedades)**
| Régimen | Cuándo aplica |
|---|---|
| **General** | Ingresos o activos ≥ 4.929.017 UVB. El sistema completo, sin excepciones. |
| **RMM Ampliado** | Sectores específicos (farmacéutico, infraestructura, manufacturero, minero-energético) con ingresos ≥ 369.676 UVB o activos ≥ 616.127 UVB. Un régimen intermedio. |
| **Sistema Pleno** | Ciertos sectores (inmobiliario, activos virtuales, servicios jurídicos, etc.) obligados por su actividad, sin importar el tamaño. |
| **Por debajo del umbral** | No alcanza ninguno de los anteriores. Puede no estar obligado, o aplicar solo medidas básicas. |

**Regímenes — Sector Transporte (Supertransporte)**
| Régimen | Cuándo aplica |
|---|---|
| **SARLAFT Completo** | Ingresos totales ≥ 142.206,5 UVB. Sistema completo de administración de riesgos. |
| **RMS** (Régimen de Medidas Simplificadas) | Por debajo de ese umbral. Obligaciones más livianas, pensadas para transportadores pequeños. |

**SARLAFT — Superintendencia Financiera**  
Aplica a entidades vigiladas por la SFC (bancos, aseguradoras, fiduciarias, comisionistas de bolsa, etc.). A diferencia de Capítulo IX, aquí no hay un umbral de ingresos que calcular — el SARLAFT es obligatorio por el solo hecho de tener licencia de la Superintendencia Financiera.

**Modo de agregación de controles** — cuando un riesgo tiene varios controles, ¿cómo se combina su efecto?
- **Cascada** (default): cada control actúa sobre lo que dejó el anterior, en orden de mayor a menor eficacia. Es el método más común y el que exige el DAFP para entidades públicas. Tiende a reducir mucho el riesgo si hay varios controles.
- **Promedio**: se promedia la eficacia de todos los controles y se aplica una sola vez. Más conservador; no depende del orden.
- **Dominante**: solo cuenta el control más fuerte. Útil para diagnósticos rápidos.

**Modo de agregación de impacto** — cada riesgo se califica en varias dimensiones de impacto, y no todos los catálogos usan las mismas: el Genérico usa 5 dimensiones base (Financiero, Operativo, Reputación, Legal y normativo, Seguridad y ambiente — alineadas con COSO ERM y la guía DAFP V6); Capítulo IX y Transporte suman una sexta, Contagio, propia de la metodología Wolfsberg; y SARLAFT (Superfinanciera) usa las 4 dimensiones oficiales que define la propia norma — Reputacional, Legal, Operativo, Contagio — sin las genéricas. ¿Cómo se resumen en un solo número?
- **Máximo** (default): el impacto final es el de la dimensión más grave. Es el criterio conservador — si el riesgo tiene un impacto reputacional catastrófico, eso manda, aunque las demás dimensiones sean bajas.
- **Promedio**: se promedian todas las dimensiones. Menos conservador — un impacto muy alto se puede "diluir" entre dimensiones bajas.

**Perfiles de apetito de riesgo** — qué tan tolerante es la empresa a que un riesgo quede en cada nivel. Lo define la junta directiva, no el consultor.
- **Conservador**: sube rápido a niveles altos. Para empresas grandes, muy expuestas, o que prefieren pecar de cautelosas.
- **Moderado** (default): el punto medio, recomendado como punto de partida.
- **Agresivo**: tolera más antes de subir de nivel. Solo lo verdaderamente crítico se clasifica alto.
- **Metodología propia**: la escala original de 4 niveles del cliente, si ya tenía una matriz previa que se quiere preservar.
""")

# ====================================================================
# PASO 1 — Caracterización del cliente (RD-003)
# ====================================================================
seccion("1", "Caracterización del cliente")

SECTORES_CAPITULO_IX = [
    "farmaceutico", "infraestructura y construccion", "manufacturero", "minero-energetico",
    "inmobiliario", "metales y piedras preciosas", "servicios juridicos y contables",
    "construccion", "comercio de vehiculos", "activos virtuales", "camaras de comercio",
]
SECTORES_GENERALES = [
    "Transporte de carga y pasajeros", "Comercio al por menor", "Comercio al por mayor",
    "Servicios profesionales", "Tecnología y software", "Agroindustria", "Salud",
    "Educación", "Alimentos y bebidas", "Textil y confección", "Comunicaciones",
    "Energía", "Turismo y hotelería", "Otro / no listado",
]

col1, col2 = st.columns(2)
with col1:
    nombre_cliente = st.text_input("Nombre o razón social", placeholder="Ej. Transportadora XYZ S.A.S.")

    ingresos_cop = st.number_input(
        "Ingresos totales anuales (COP)", min_value=0, step=1_000_000, value=1_000_000_000, format="%d"
    )
    st.caption(f"= $ {ingresos_cop:,.0f}".replace(",", ".") + " COP")

    activos_cop = st.number_input(
        "Activos totales (COP)", min_value=0, step=1_000_000, value=800_000_000, format="%d",
        help="No aplica si el alcance elegido es 'Sector Transporte' — ese sistema mide solo por ingresos.",
    )
    st.caption(f"= $ {activos_cop:,.0f}".replace(",", ".") + " COP")

with col2:
    sector = st.selectbox(
        "Sector económico",
        options=["No aplica / genérico"] + SECTORES_GENERALES + SECTORES_CAPITULO_IX,
        help="Los sectores en minúscula son los que el Capítulo IX (CE 100-000020) trata de forma especial "
             "(Régimen de Medidas Mínimas ampliado o Sistema Pleno). Si tu sector no está en la lista, "
             "usa 'Otro / no listado'.",
    )
    alcance = st.selectbox(
        "Alcance de la matriz",
        options=list(CATALOGOS_DISPONIBLES.keys()),
        format_func=lambda k: CATALOGOS_DISPONIBLES[k]["nombre"],
    )
    st.caption("🔜 Próximamente: alcance C/ST puro (auditoría de corrupción/soborno como categoría independiente).")

if st.button("Caracterizar cliente", type="primary"):
    sector_valor = None if sector == "No aplica / genérico" else sector

    if alcance == "transporte_laft":
        resultado = caracterizar_cliente_transporte(ingresos_cop)
    elif alcance == "generico_empresarial":
        resultado = caracterizar_cliente_generico()
    elif alcance == "sarlaft_sfc":
        resultado = caracterizar_cliente_sarlaft_sfc()
    else:
        resultado = caracterizar_cliente(ingresos_cop, activos_cop, sector=sector_valor)

    st.session_state.caracterizacion = resultado
    st.session_state.alcance = alcance
    st.session_state.nombre_cliente = nombre_cliente or "Cliente sin nombre"
    st.session_state.matriz = None

if st.session_state.caracterizacion:
    r = st.session_state.caracterizacion
    if r["uvb_ingresos"] is not None:
        st.success(
            f"**Sistema aplicable:** {r['sistema']}  \n"
            f"**Régimen determinado:** {r['regimen_final']}  \n"
            f"**UVB ingresos:** {r['uvb_ingresos']:,.0f}"
            + (f"  ·  **UVB activos:** {r['uvb_activos']:,.0f}" if r['uvb_activos'] is not None else "")
            + f"  \n**Sustento:** {r['trazabilidad']}"
        )
    else:
        st.success(f"**Alcance:** {r['sistema']}  \n**Nota:** {r['trazabilidad']}")

    if st.session_state.alcance not in ("generico_empresarial", "sarlaft_sfc"):
        with st.expander("Ajustar régimen manualmente (exige comentario)"):
            opciones_regimen = (
                ["SARLAFT_Completo", "RMS"] if st.session_state.alcance == "transporte_laft"
                else ["General", "RMM_Ampliado", "Sistema_Pleno", "Por_Debajo_Umbral"]
            )
            override = st.selectbox("Corregir régimen a", options=[None] + opciones_regimen,
                                     format_func=lambda x: "— no corregir —" if x is None else x)
            comentario = st.text_area("Motivo del ajuste (obligatorio si corrige el régimen)")
            if st.button("Aplicar corrección de régimen"):
                if override and not comentario.strip():
                    st.error("Escribe el motivo del ajuste antes de aplicar la corrección — es obligatorio para dejar trazabilidad de la decisión.")
                elif override:
                    if st.session_state.alcance == "transporte_laft":
                        st.session_state.caracterizacion = caracterizar_cliente_transporte(
                            ingresos_cop, override_regimen=override, comentario_override=comentario
                        )
                    else:
                        sector_valor = None if sector == "No aplica / genérico" else sector
                        st.session_state.caracterizacion = caracterizar_cliente(
                            ingresos_cop, activos_cop, sector=sector_valor,
                            override_regimen=override, comentario_override=comentario,
                        )
                    st.rerun()

    # ================================================================
    # PASO 2 — Apetito de riesgo (RD-008)
    # ================================================================
    seccion("2", "Apetito de riesgo")
    apetito_elegido = st.selectbox(
        "Perfil de apetito de riesgo (definido por la junta directiva del cliente)",
        options=list(PERFILES_APETITO.keys()),
        index=list(PERFILES_APETITO.keys()).index(r["apetito_sugerido"]),
        help="Sugerido automáticamente según el régimen. Ver glosario arriba. La junta directiva puede elegir otro.",
    )

    with st.expander("Opciones metodológicas avanzadas"):
        modo_controles = st.selectbox(
            "Modo de agregación de controles", options=["cascada", "promedio", "dominante"],
            index=["cascada", "promedio", "dominante"].index(CONFIG_DEFAULT["modo_controles"]),
        )
        modo_impacto = st.selectbox(
            "Modo de agregación de impacto", options=["max", "promedio"],
            index=["max", "promedio"].index(CONFIG_DEFAULT["modo_impacto"]),
        )

    # ================================================================
    # PASO 3 — Catálogo de riesgos: el propio de la app, o uno propio
    # ================================================================
    seccion("3", "Catálogo de riesgos")

    # El catálogo SIEMPRE debe corresponder al alcance con el que se caracterizó
    # (st.session_state.alcance), no al valor actual del selector de arriba — si el
    # consultor cambia el alcance sin volver a pulsar "Caracterizar cliente", el
    # catálogo base y el régimen mostrado en pantalla quedarían de dos alcances
    # distintos sin que nadie lo note. Mismo principio que config_usada para el apetito.
    if alcance != st.session_state.alcance:
        st.warning(
            f"⚠️ Cambiaste el alcance de la matriz después de caracterizar (el régimen de arriba sigue "
            f"siendo el de **{CATALOGOS_DISPONIBLES[st.session_state.alcance]['nombre']}**). "
            "Vuelve a pulsar **Caracterizar cliente** para que el catálogo y el régimen mostrado correspondan al nuevo alcance."
        )

    modo_catalogo = st.radio(
        "¿Qué catálogo usar?",
        options=["Catálogo base de la app", "Subir mi propio catálogo (Excel)"],
        horizontal=True,
    )

    catalogo_fuente = None
    if modo_catalogo == "Catálogo base de la app":
        ruta_base = CATALOGOS_DISPONIBLES[st.session_state.alcance]["ruta"]
        catalogo_fuente = ruta_base
        with open(ruta_base, "rb") as f:
            st.download_button(
                "⬇️ Descargar este catálogo para revisarlo o editarlo",
                data=f.read(),
                file_name=ruta_base.name,
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            )
        st.caption("Edítalo en Excel (hojas 'Riesgos' y 'Controles') y súbelo de vuelta con la opción de arriba.")
    else:
        archivo_subido = st.file_uploader(
            "Sube un Excel con hojas 'Riesgos' y 'Controles' (misma estructura del catálogo base)",
            type=["xlsx"],
        )
        if archivo_subido is not None:
            catalogo_fuente = archivo_subido

    # ================================================================
    # PASO 4 — Generar la matriz
    # ================================================================
    seccion("4", "Generar la matriz")
    if st.button("Generar matriz de riesgos", type="primary", disabled=catalogo_fuente is None):
        config_cliente = {
            **CONFIG_DEFAULT, "apetito": apetito_elegido,
            "modo_controles": modo_controles, "modo_impacto": modo_impacto,
        }
        try:
            catalogo = cargar_catalogo(catalogo_fuente)
            if not catalogo:
                raise ValueError("El catálogo no tiene ninguna fila en la hoja 'Riesgos'.")
            matriz = pd.DataFrame([evaluar_riesgo(riesgo, config_cliente) for riesgo in catalogo])
        except Exception as e:
            st.error(
                "No se pudo generar la matriz con este catálogo. La causa más común es que falte una "
                "hoja ('Riesgos' o 'Controles'), una columna obligatoria (`id`, `familia`, `factor`, "
                "`descripcion`, `probabilidad_semilla`), o que quede alguna celda de impacto vacía o "
                "fuera del rango 1-5.\n\n"
                f"Detalle técnico: {e}"
            )
        else:
            st.session_state.matriz = matriz
            st.session_state.catalogo_raw = {r["id"]: r for r in catalogo}  # para el detalle al hacer clic
            # Se guarda la configuración CON la que se calculó esta matriz. Los mapas y
            # etiquetas deben dibujarse siempre con esta, no con lo que el selector muestre
            # después: si el consultor cambia el apetito sin regenerar, el fondo del mapa
            # cambiaría pero los niveles calculados no — una inconsistencia silenciosa.
            st.session_state.config_usada = {
                "apetito": apetito_elegido, "modo_controles": modo_controles, "modo_impacto": modo_impacto,
            }

if st.session_state.matriz is not None:
    matriz_completa = st.session_state.matriz
    catalogo_raw = st.session_state.get("catalogo_raw", {})
    config_usada = st.session_state.get("config_usada", dict(CONFIG_DEFAULT))
    apetito_matriz = config_usada["apetito"]  # el apetito con el que SE CALCULÓ la matriz
    st.subheader(f"Matriz de riesgos — {st.session_state.nombre_cliente}")

    # Si el consultor cambió apetito u opciones metodológicas DESPUÉS de generar,
    # lo que está en pantalla ya no corresponde a la selección actual — avisar.
    if st.session_state.caracterizacion and {
        "apetito": apetito_elegido, "modo_controles": modo_controles, "modo_impacto": modo_impacto,
    } != config_usada:
        st.warning(
            "⚠️ Cambiaste el apetito de riesgo o las opciones metodológicas después de generar "
            "esta matriz. Los resultados de abajo siguen calculados con la configuración anterior "
            f"(apetito **{apetito_matriz}**). Vuelve a pulsar **Generar matriz de riesgos** para aplicar el cambio."
        )

    # ----------------------------------------------------------------
    # Contador de riesgos por nivel — insignias con los colores del mapa
    # ----------------------------------------------------------------
    ESCALA_MODERNA = ["MUY BAJO", "BAJO", "MODERADO", "ALTO", "EXTREMO"]
    ESCALA_LEGADO = ["INSIGNIFICANTE", "MEDIO", "ALTO", "SIGNIFICATIVO"]

    def _fila_insignias(df, columna_nivel):
        """Fila compacta de insignias: un chip por nivel de la escala activa (incluyendo
        los que están en cero) + total, con exactamente los mismos colores del mapa."""
        escala = ESCALA_LEGADO if apetito_matriz == "metodologia_propia" else ESCALA_MODERNA
        conteos = df[columna_nivel].value_counts()
        chips = []
        for nivel in escala:
            n = int(conteos.get(nivel, 0))
            color = COLOR_NIVEL.get(nivel, "#DDDDDD")
            chips.append(
                f"<span style='background:{color}; padding:3px 10px; border-radius:12px; "
                f"margin-right:6px; font-size:0.85rem; color:#1a1a1a; white-space:nowrap;'>"
                f"<b>{nivel.title()}:</b> {n}</span>"
            )
        chips.append(
            f"<span style='padding:3px 10px; border-radius:12px; margin-left:4px; "
            f"font-size:0.85rem; border:1px solid #bbb; white-space:nowrap;'>"
            f"<b>Total:</b> {len(df)} riesgos</span>"
        )
        st.markdown("<div style='margin:2px 0 10px 0;'>" + "".join(chips) + "</div>", unsafe_allow_html=True)

    # ----------------------------------------------------------------
    # Segmentación básica — primer paso hacia la segmentación completa (v2, roadmap)
    # ----------------------------------------------------------------
    factores_disponibles = sorted(matriz_completa["factor"].dropna().unique().tolist())
    factores_elegidos = st.multiselect(
        "Filtrar por factor / proceso", options=factores_disponibles, default=factores_disponibles,
        help="Muestra solo los riesgos del factor o proceso que elijas. La segmentación estadística "
             "completa (por clúster) llegará en una versión futura del producto.",
    )
    matriz = matriz_completa[matriz_completa["factor"].isin(factores_elegidos)] if factores_elegidos else matriz_completa

    def _tarjeta_riesgo(fila, tipo_vista):
        """Una tarjeta con el detalle de UN riesgo — inherente o residual según la vista.
        Se reutiliza tanto para riesgos seleccionados como para el listado completo.
        Las alertas (piso RD-010, plan de tratamiento) solo aplican al ver el residual:
        el inherente es antes de cualquier control, no tiene sentido mostrarlas ahí."""
        riesgo_id = fila["id"]
        riesgo_original = catalogo_raw.get(riesgo_id, {})
        controles = riesgo_original.get("controles", [])
        nivel_actual = fila["nivel_inherente"] if tipo_vista == "inherente" else fila["nivel_residual"]
        color_nivel = COLOR_NIVEL.get(nivel_actual, "#DDDDDD")

        with st.container(border=True):
            st.markdown(
                f"""<div style="display:flex; align-items:center; gap:10px; margin-bottom:6px;">
                      <span style="font-family:'Montserrat', sans-serif; font-weight:700;
                                  font-size:17px; color:#0D1B2A;">{riesgo_id}</span>
                      <span style="background:{color_nivel}; color:#1a1a1a; font-size:11.5px;
                                  font-weight:600; padding:2px 11px; border-radius:10px;
                                  white-space:nowrap;">{nivel_actual.title()}</span>
                    </div>""",
                unsafe_allow_html=True,
            )
            st.markdown(fila["descripcion"])

            if tipo_vista == "inherente":
                c1, c2, c3 = st.columns(3)
                c1.metric("Probabilidad inherente", f"{fila['prob_inherente']:.0%}")
                c2.metric("Impacto inherente", f"{fila['imp_inherente']:.0%}")
                c3.metric("Nivel de riesgo inherente", fila["nivel_inherente"])

            else:  # residual
                for alerta in alertas_del_riesgo(dict(fila)):
                    if "plan de tratamiento" in alerta.lower():
                        st.error(f"📋 {alerta}")
                    elif "PISO DE MITIGACIÓN" in alerta:
                        st.info(f"⚖️ {alerta}")
                    else:
                        st.warning(alerta)

                c1, c2, c3 = st.columns(3)
                c1.metric("Probabilidad residual", f"{fila['prob_residual']:.0%}")
                c2.metric("Impacto residual", f"{fila['imp_residual']:.0%}")
                c3.metric("Nivel de riesgo residual", fila["nivel_residual"])

                st.markdown(f"**Controles que explican este resultado ({len(controles)}):**")
                if controles:
                    # Solo lo NUEVO: id_riesgo, probabilidad, impacto y nivel ya están
                    # arriba como métricas — repetirlos en la tabla sería redundante.
                    tabla_controles = pd.DataFrame([{
                        "id_control": c["id"], "descripcion_control": c["descripcion"],
                    } for c in controles])
                    st.dataframe(tabla_controles, width="stretch", hide_index=True)
                else:
                    st.warning("Este riesgo no tiene controles asociados — el residual es igual al inherente.")

    def _panel_detalle(evento, tipo_vista):
        """Si hay riesgos seleccionados (clic, o Shift+clic para varios), muestra SOLO
        esos. Si no hay ninguno seleccionado, lista TODOS los riesgos visibles (según
        el filtro de factor de arriba), uno debajo del otro."""
        puntos = evento.selection.points if (evento and evento.selection) else []
        ids_seleccionados = [p["customdata"][0] for p in puntos if p.get("customdata")]

        if ids_seleccionados:
            filas_a_mostrar = matriz[matriz["id"].isin(ids_seleccionados)]
            st.caption(f"Mostrando {len(filas_a_mostrar)} riesgo(s) seleccionado(s). "
                       "Mantén Shift y haz clic para seleccionar varios a la vez.")
        else:
            filas_a_mostrar = matriz
            st.caption(f"Ningún riesgo seleccionado — se listan los {len(filas_a_mostrar)} riesgos visibles. "
                       "Haz clic (o Shift+clic para varios) en el mapa para filtrar la lista.")

        for _, fila in filas_a_mostrar.iterrows():
            _tarjeta_riesgo(fila, tipo_vista)

    tab_inh, tab_res, tab_mov = st.tabs(["🟡 Riesgo Inherente", "🔵 Riesgo Residual", "➡️ Desplazamiento"])

    with tab_inh:
        _fila_insignias(matriz, "nivel_inherente")
        st.caption("Haz clic en un punto (o Shift+clic para varios) para filtrar la lista de abajo.")
        fig_inh = graficar_mapa_simple(matriz, tipo="inherente", apetito_nombre=apetito_matriz,
                                        titulo=f"Riesgo Inherente — {st.session_state.nombre_cliente}")
        evento_inh = st.plotly_chart(fig_inh, width="stretch", on_select="rerun",
                                      selection_mode="points", key="mapa_inherente")
        _panel_detalle(evento_inh, "inherente")

    with tab_res:
        _fila_insignias(matriz, "nivel_residual")
        st.caption("Haz clic en un punto (o Shift+clic para varios) para filtrar la lista de abajo.")
        fig_res = graficar_mapa_simple(matriz, tipo="residual", apetito_nombre=apetito_matriz,
                                        titulo=f"Riesgo Residual — {st.session_state.nombre_cliente}")
        evento_res = st.plotly_chart(fig_res, width="stretch", on_select="rerun",
                                      selection_mode="points", key="mapa_residual")
        _panel_detalle(evento_res, "residual")

    with tab_mov:
        st.caption(
            "Vista avanzada: inherente y residual juntos. Si la flecha se mueve en vertical, "
            "actuaron controles preventivos o detectivos; si se mueve en horizontal, actuaron "
            "correctivos. Con muchos riesgos, esta vista puede saturarse — para lectura rápida "
            "usa las dos pestañas anteriores."
        )
        fig_mov = graficar_mapa_desplazamiento(matriz, apetito_nombre=apetito_matriz,
                                                titulo=f"Desplazamiento — {st.session_state.nombre_cliente}")
        st.plotly_chart(fig_mov, width="stretch")

    # Alertas y exportación SIEMPRE sobre la matriz completa: el filtro por factor es
    # una ayuda visual para los mapas — el diagnóstico de calibración perdería sentido
    # sobre un subconjunto, y el Excel entregable jamás debe salir incompleto porque
    # el consultor tenía un filtro puesto al momento de descargar.
    n_requieren_tratamiento = int(matriz_completa["requiere_plan_tratamiento"].sum())
    alertas = diagnosticar_calibracion(matriz_completa)
    if n_requieren_tratamiento or alertas:
        st.subheader("⚠️ Alertas metodológicas")
        if n_requieren_tratamiento:
            st.error(f"📋 {n_requieren_tratamiento} riesgo(s) se encuentran fuera del apetito de riesgo "
                     "definido y requieren plan de tratamiento.")
        for a in alertas:
            st.warning(a)

    buffer = io.BytesIO()
    exportar_matriz(matriz_completa, catalogo_raw, buffer)
    buffer.seek(0)
    st.download_button(
        "⬇️ Descargar matriz en Excel",
        data=buffer,
        file_name=f"MIRA_{st.session_state.nombre_cliente.replace(' ', '_')}.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )

footer_app()

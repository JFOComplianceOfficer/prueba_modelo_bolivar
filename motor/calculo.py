"""
Motor de cálculo — MIRA (Matriz Inteligente de Riesgos y Alertas), App de Matriz de Riesgos Parametrizable
Extraído y consolidado del notebook motor_riesgos_v0.9.ipynb (Fase 1 y 2, verificado
con paridad 142/142 contra la matriz de origen).

Principios de diseño (sin cambios frente al notebook):
1. Configuración != lógica != datos. Este archivo es LÓGICA. Los valores viven en
   data/config_matriz_riesgos.xlsx y data/motor_settings.json.
2. Dato derivable no se almacena (eficacia de control, "qué reduce", etc. se calculan).
3. Cada criterio metodológico vive en una sola función, parametrizable por modo.
4. Rutas RELATIVAS al proyecto (Fase 3): funcionan igual en cualquier máquina o servidor.
"""

import json
import unicodedata
from pathlib import Path

import pandas as pd

# ============================================================
# Rutas portables — ancladas a la ubicación de ESTE archivo, no a una máquina.
# motor/calculo.py -> .parent = motor/ -> .parent = raíz del proyecto -> /data
# ============================================================
BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"

RUTA_CONFIG_EXCEL = DATA_DIR / "config_matriz_riesgos.xlsx"
RUTA_CONFIG_JSON = DATA_DIR / "motor_settings.json"
RUTA_CATALOGO_TRANSPORTE = DATA_DIR / "catalogo_riesgos_transporte_laft.xlsx"
RUTA_CATALOGO_SUPERSOCIEDADES = DATA_DIR / "catalogo_riesgos_supersociedades_capitulo_ix.xlsx"
RUTA_CATALOGO_GENERICO = DATA_DIR / "catalogo_riesgos_generico_empresarial.xlsx"
RUTA_CATALOGO_SARLAFT_SFC = DATA_DIR / "catalogo_riesgos_sarlaft_sfc.xlsx"

CATALOGOS_DISPONIBLES = {
    "generico_empresarial": {
        "nombre": "Riesgo Empresarial Genérico (5 dimensiones — sin atarse a LA/FT/FP)",
        "ruta": RUTA_CATALOGO_GENERICO,
    },
    "transporte_laft": {
        "nombre": "LA/FT/FP — Sector Transporte (Supertransporte)",
        "ruta": RUTA_CATALOGO_TRANSPORTE,
    },
    "capitulo_ix": {
        "nombre": "Sistema Unificado LA/FT/FP y C/ST — Capítulo IX (Supersociedades)",
        "ruta": RUTA_CATALOGO_SUPERSOCIEDADES,
    },
    "sarlaft_sfc": {
        "nombre": "SARLAFT — Superintendencia Financiera (bancos, aseguradoras, fiduciarias)",
        "ruta": RUTA_CATALOGO_SARLAFT_SFC,
    },
}

with open(RUTA_CONFIG_JSON, encoding="utf-8") as _f:
    _SETTINGS = json.load(_f)

PUNTAJE_MAXIMO = _SETTINGS["denominador_eficacia_control"]  # 15
_DECIMALES = _SETTINGS["redondeo_decimales"]  # 6


# ============================================================
# Utilidades internas
# ============================================================
def _norm(texto):
    """Normaliza texto para búsquedas en tablas: minúsculas, sin tildes, sin espacios extra."""
    if texto is None:
        return ""
    t = unicodedata.normalize("NFKD", str(texto).strip().lower())
    return "".join(ch for ch in t if not unicodedata.combining(ch))


def _buscar(tabla, clave, nombre_tabla):
    """Busca en una tabla de configuración con normalización y error explícito si no existe."""
    valor = tabla.get(_norm(clave))
    if valor is None:
        raise KeyError(f"'{clave}' no está en {nombre_tabla}. Opciones: {sorted(tabla)}")
    return valor


def _r(valor):
    """Redondeo estándar del motor: 6 decimales antes de cualquier comparación con umbrales."""
    return round(valor, _DECIMALES)


# ============================================================
# Configuración — cargada de config_matriz_riesgos.xlsx
# ============================================================
def cargar_ejes(ruta_excel=RUTA_CONFIG_EXCEL):
    """Lee la hoja 'Ejes' y arma las bandas de probabilidad e impacto (RD-008)."""
    df = pd.read_excel(ruta_excel, sheet_name="Ejes")
    bandas = {"Probabilidad": [], "Impacto": []}
    for _, fila in df.sort_values("Nivel").iterrows():
        bandas[fila["Tipo"]].append((float(fila["Limite_Superior"]), int(fila["Nivel"]), fila["Etiqueta"]))
    return bandas["Probabilidad"], bandas["Impacto"]


def cargar_rubrica(ruta_excel=RUTA_CONFIG_EXCEL):
    """Lee la hoja 'Rubrica_Controles' y arma los tres diccionarios de puntaje (RD-002)."""
    df = pd.read_excel(ruta_excel, sheet_name="Rubrica_Controles")

    def _sub(criterio):
        return {_norm(row["Opcion"]): row["Puntaje"] for _, row in df[df["Criterio"] == criterio].iterrows()}

    return _sub("Automatizacion"), _sub("Documentacion"), _sub("Periodicidad")


BANDAS_PROBABILIDAD, BANDAS_IMPACTO = cargar_ejes()
PUNTAJE_AUTOMATIZACION, PUNTAJE_DOCUMENTACION, PUNTAJE_PERIODICIDAD = cargar_rubrica()

NIVEL_A_PROBABILIDAD = {n: e for _, n, e in BANDAS_PROBABILIDAD}
NIVEL_A_IMPACTO = {n: e for _, n, e in BANDAS_IMPACTO}
VALOR_A_PORCENTAJE = {n: round(n / 5, _DECIMALES) for n in range(1, 6)}
TIPOS_QUE_REDUCEN_IMPACTO = {"correctivo"}

ESCALA_5_NIVELES = [(0.04, "MUY BAJO"), (0.16, "BAJO"), (0.40, "MODERADO"), (0.64, "ALTO"), (1.00, "EXTREMO")]
ESCALA_4_NIVELES = [(0.16, "INSIGNIFICANTE"), (0.24, "MEDIO"), (0.48, "ALTO"), (1.00, "SIGNIFICATIVO")]  # legacy

ORDEN_PROBABILIDAD_HOJA = ["Casi seguro", "Muy probable", "Probable", "Poco probable", "Rara vez"]


def cargar_apetito(nombre_hoja, ruta_excel=RUTA_CONFIG_EXCEL):
    """Lee una hoja de perfil de apetito (grid 5x5) y la convierte a {nivel_prob: [5 valores]}."""
    df = pd.read_excel(ruta_excel, sheet_name=nombre_hoja, index_col=0)
    grid = {}
    for i, etiqueta_prob in enumerate(ORDEN_PROBABILIDAD_HOJA):
        nivel_prob = 5 - i
        grid[nivel_prob] = df.loc[etiqueta_prob].tolist()
    return grid


APETITO_MODERADO = cargar_apetito("Apetito_Moderado")
APETITO_CONSERVADOR = cargar_apetito("Apetito_Conservador")
APETITO_AGRESIVO = cargar_apetito("Apetito_Agresivo")
APETITO_METODOLOGIA_PROPIA = cargar_apetito("Apetito_MetodologiaPropia")  # legacy, paridad

PERFILES_APETITO = {
    "moderado": APETITO_MODERADO,
    "conservador": APETITO_CONSERVADOR,
    "agresivo": APETITO_AGRESIVO,
    "metodologia_propia": APETITO_METODOLOGIA_PROPIA,
}

ORDEN_NIVELES_5 = {"MUY BAJO": 0, "BAJO": 1, "MODERADO": 2, "ALTO": 3, "EXTREMO": 4}
ORDEN_NIVELES_4 = {"INSIGNIFICANTE": 0, "MEDIO": 1, "ALTO": 2, "SIGNIFICATIVO": 3}  # legacy


def _valor_o_none(v):
    return None if pd.isna(v) or v == "" else v


def cargar_configuracion_cliente(ruta_excel=RUTA_CONFIG_EXCEL):
    """Lee 'Configuracion_Cliente': la configuración DEFAULT del producto.
    En la app, el formulario de caracterización sobrescribe 'apetito' con la elección
    del consultor; el resto queda en su valor de fábrica salvo que el cliente lo cambie."""
    df = pd.read_excel(ruta_excel, sheet_name="Configuracion_Cliente")
    valores = {row["Parametro"]: _valor_o_none(row["Valor"]) for _, row in df.iterrows()}

    tope = valores.get("tope_reduccion_agregada")
    descenso = valores.get("descenso_maximo_residual")

    return {
        "modo_impacto": valores["modo_impacto"],
        "modo_controles": valores["modo_controles"],
        "modo_clasificacion": valores["modo_clasificacion"],
        "apetito": valores["apetito"],
        "escala_multiplicacion": ESCALA_5_NIVELES,
        "tope_reduccion_agregada": float(tope) if tope is not None else None,
        "descenso_maximo_residual": int(descenso) if descenso is not None else None,
    }


CONFIG_DEFAULT = cargar_configuracion_cliente()


# ============================================================
# Caracterización del cliente (RD-003) — umbrales UVB, Capítulo IX
# ============================================================
def cargar_umbrales_uvb(ruta_excel=RUTA_CONFIG_EXCEL):
    """Lee la hoja 'Umbrales_UVB': valor de la UVB del año y los umbrales de régimen (Cap. IX)."""
    df = pd.read_excel(ruta_excel, sheet_name="Umbrales_UVB", header=None)

    valor_uvb = float(df[df[0] == "valor_uvb_cop"].iloc[0, 1])

    fila_header = df[df[0] == "Regimen"].index[0]
    tabla = df.iloc[fila_header + 1:].copy()
    tabla.columns = df.iloc[fila_header]
    tabla = tabla.dropna(subset=["Regimen"])

    umbrales = [(row["Regimen"], row["Tipo_Umbral"], float(row["Umbral_UVB"])) for _, row in tabla.iterrows()]
    return valor_uvb, umbrales


VALOR_UVB_COP, UMBRALES_REGIMEN = cargar_umbrales_uvb()

SECTORES_SISTEMA_PLENO = {
    "inmobiliario", "metales y piedras preciosas", "servicios juridicos y contables",
    "construccion", "comercio de vehiculos", "activos virtuales", "camaras de comercio",
}
SECTORES_RMM_AMPLIADO = {"farmaceutico", "infraestructura y construccion", "manufacturero", "minero-energetico"}

SUGERENCIA_APETITO_POR_REGIMEN = {
    "General": "conservador",
    "Sistema_Pleno": "conservador",
    "RMM_Ampliado": "moderado",
    "Por_Debajo_Umbral": "moderado",
}


def determinar_regimen(ingresos_cop, activos_cop, sector=None, valor_uvb=VALOR_UVB_COP, umbrales=UMBRALES_REGIMEN):
    """Determina el régimen aplicable por umbrales UVB (Capítulo IX), automático."""
    uvb_ingresos = round(ingresos_cop / valor_uvb, 2)
    uvb_activos = round(activos_cop / valor_uvb, 2)
    sector_norm = _norm(sector) if sector else None

    umbral_general = next(u for r, t, u in umbrales if r == "General")
    umbral_rmm_ing = next(u for r, t, u in umbrales if r == "RMM_Ampliado" and t == "ingresos")
    umbral_rmm_act = next(u for r, t, u in umbrales if r == "RMM_Ampliado" and t == "activos")

    if sector_norm in SECTORES_SISTEMA_PLENO:
        return ("Sistema_Pleno", uvb_ingresos, uvb_activos,
                f"Sector '{sector}' obligado por actividad (num. 9.5), independiente del tamaño.")

    if uvb_ingresos >= umbral_general or uvb_activos >= umbral_general:
        return ("General", uvb_ingresos, uvb_activos,
                f"Ingresos o activos ({max(uvb_ingresos, uvb_activos):,.0f} UVB) superan el umbral general "
                f"({umbral_general:,.0f} UVB).")

    if sector_norm in SECTORES_RMM_AMPLIADO and (uvb_ingresos >= umbral_rmm_ing or uvb_activos >= umbral_rmm_act):
        return ("RMM_Ampliado", uvb_ingresos, uvb_activos,
                f"Sector '{sector}' con ingresos/activos que superan el umbral de Medidas Mínimas ampliado.")

    return ("Por_Debajo_Umbral", uvb_ingresos, uvb_activos,
            "No alcanza los umbrales del Capítulo IX ni pertenece a un sector de sistema pleno.")


def caracterizar_cliente(ingresos_cop, activos_cop, sector=None, override_regimen=None, comentario_override=None):
    """Punto de entrada de RD-003: determina régimen (Capítulo IX, Supersociedades) y
    sugiere apetito de riesgo. Un override de régimen SIEMPRE exige comentario (traza de auditoría)."""
    regimen_calc, uvb_ing, uvb_act, sustento = determinar_regimen(ingresos_cop, activos_cop, sector)

    if override_regimen is not None:
        if not comentario_override:
            raise ValueError("RD-003: todo override de régimen exige un comentario obligatorio.")
        regimen_final = override_regimen
        trazabilidad = f"AUTOMÁTICO: {regimen_calc} ({sustento}) → CORREGIDO A: {regimen_final}. Motivo: {comentario_override}"
    else:
        regimen_final = regimen_calc
        trazabilidad = f"AUTOMÁTICO: {regimen_final}. {sustento}"

    return {
        "sistema": "Capítulo IX (Supersociedades)",
        "regimen_calculado": regimen_calc,
        "regimen_final": regimen_final,
        "uvb_ingresos": uvb_ing,
        "uvb_activos": uvb_act,
        "apetito_sugerido": SUGERENCIA_APETITO_POR_REGIMEN.get(regimen_final, "moderado"),
        "trazabilidad": trazabilidad,
    }


# ============================================================
# Caracterización — sector TRANSPORTE (Supertransporte, sistema propio y distinto)
# Circular Única de Infraestructura y Transporte, Cap. 6 Título V — Res. 2328/2025,
# modificada por 16615/2025 y 4607/2026. Umbral único sobre INGRESOS (no activos).
# ============================================================
UMBRAL_TRANSPORTE_UVB = 142_206.50  # Art. 2 de la Res. 4607/2026, modifica art. 5.6.4 de la 2328/2025

SUGERENCIA_APETITO_TRANSPORTE = {
    "SARLAFT_Completo": "conservador",
    "RMS": "moderado",
}


def determinar_regimen_transporte(ingresos_cop, valor_uvb=VALOR_UVB_COP, umbral=UMBRAL_TRANSPORTE_UVB):
    """Determina el régimen aplicable en el sector transporte: SARLAFT completo si los
    ingresos totales superan 142.206,5 UVB; si no, Régimen de Medidas Simplificadas (RMS)."""
    uvb_ingresos = round(ingresos_cop / valor_uvb, 2)
    if uvb_ingresos >= umbral:
        return ("SARLAFT_Completo", uvb_ingresos,
                f"Ingresos totales ({uvb_ingresos:,.0f} UVB) superan el umbral de {umbral:,.0f} UVB "
                "(art. 5.6.4, modificado por Res. 4607/2026): aplica SARLAFT completo.")
    return ("RMS", uvb_ingresos,
            f"Ingresos totales ({uvb_ingresos:,.0f} UVB) por debajo de {umbral:,.0f} UVB: "
            "aplica el Régimen de Medidas Simplificadas (RMS, arts. 5.6.15 y ss.).")


def caracterizar_cliente_transporte(ingresos_cop, override_regimen=None, comentario_override=None):
    """Caracterización para el sector transporte — sistema normativo propio (Supertransporte),
    distinto del Capítulo IX de Supersociedades. No usa umbrales de activos, solo ingresos."""
    regimen_calc, uvb_ing, sustento = determinar_regimen_transporte(ingresos_cop)

    if override_regimen is not None:
        if not comentario_override:
            raise ValueError("RD-003: todo override de régimen exige un comentario obligatorio.")
        regimen_final = override_regimen
        trazabilidad = f"AUTOMÁTICO: {regimen_calc} ({sustento}) → CORREGIDO A: {regimen_final}. Motivo: {comentario_override}"
    else:
        regimen_final = regimen_calc
        trazabilidad = f"AUTOMÁTICO: {regimen_final}. {sustento}"

    return {
        "sistema": "SARLAFT Transporte (Supertransporte)",
        "regimen_calculado": regimen_calc,
        "regimen_final": regimen_final,
        "uvb_ingresos": uvb_ing,
        "uvb_activos": None,
        "apetito_sugerido": SUGERENCIA_APETITO_TRANSPORTE.get(regimen_final, "moderado"),
        "trazabilidad": trazabilidad,
    }


# ============================================================
# Caracterización — alcance GENÉRICO EMPRESARIAL (sin régimen normativo propio)
# A diferencia de Capítulo IX o Transporte, este alcance no está atado a una
# obligación LA/FT/FP concreta — es una matriz de riesgo general (COSO ERM /
# DAFP), así que no hay régimen que determinar ni umbral que calcular.
# ============================================================
def caracterizar_cliente_generico():
    """Caracterización mínima para el alcance genérico: mantiene la misma forma de
    diccionario que caracterizar_cliente() y caracterizar_cliente_transporte() para
    que el resto de la app (Paso 2 en adelante) no necesite saber qué alcance es."""
    return {
        "sistema": "Riesgo Empresarial Genérico",
        "regimen_calculado": "No aplica",
        "regimen_final": "No aplica",
        "uvb_ingresos": None,
        "uvb_activos": None,
        "apetito_sugerido": "moderado",
        "trazabilidad": (
            "Este alcance no está atado a un régimen normativo LA/FT/FP específico — es una "
            "matriz de riesgo empresarial general (COSO ERM / DAFP). Si tu empresa sí es sujeto "
            "obligado, usa el alcance de Capítulo IX o de Transporte en su lugar."
        ),
    }


# ============================================================
# Caracterización — alcance SARLAFT SUPERINTENDENCIA FINANCIERA
# A diferencia de Capítulo IX (que obliga por umbral de ingresos/activos en
# UVB), las entidades vigiladas por la SFC están obligadas a tener SARLAFT
# por el solo hecho de tener licencia de la Superintendencia Financiera — no
# hay un umbral que calcular. Por eso esta caracterización es informativa,
# no un cálculo de régimen.
# ============================================================
def caracterizar_cliente_sarlaft_sfc():
    """Caracterización para el alcance SARLAFT (SFC): informa la obligación en
    vez de calcular un umbral, porque para entidades vigiladas por la Superfinanciera
    la obligación nace de la licencia, no de un monto de ingresos o activos."""
    return {
        "sistema": "SARLAFT — Superintendencia Financiera de Colombia",
        "regimen_calculado": "Obligatorio por vigilancia SFC",
        "regimen_final": "Obligatorio por vigilancia SFC",
        "uvb_ingresos": None,
        "uvb_activos": None,
        "apetito_sugerido": "conservador",
        "trazabilidad": (
            "Si tu empresa está vigilada por la Superintendencia Financiera (bancos, "
            "aseguradoras, fiduciarias, comisionistas de bolsa, etc.), el SARLAFT es obligatorio "
            "por el solo hecho de tener licencia — no depende de un umbral de ingresos o activos, "
            "a diferencia del Capítulo IX de Supersociedades."
        ),
    }


# ============================================================
# Motor de cálculo — impacto, controles, clasificación
# ============================================================
def calcular_impacto(impactos, modo="max"):
    """Agrega las dimensiones de impacto en un valor único 1-5.
    modo='max' (default conservador) | 'promedio'. Pendiente: promedio ponderado (RD-007)."""
    valores = list(impactos.values())
    if modo == "max":
        return max(valores)
    if modo == "promedio":
        return _r(sum(valores) / len(valores))
    raise ValueError(f"Modo de agregación de impacto desconocido: {modo}")


def calcular_eficacia_control(control):
    """Eficacia = (automatización + documentación + periodicidad) / 15 (RD-002)."""
    puntaje = (
        _buscar(PUNTAJE_AUTOMATIZACION, control["automatizacion"], "PUNTAJE_AUTOMATIZACION")
        + _buscar(PUNTAJE_DOCUMENTACION, control["documentacion"], "PUNTAJE_DOCUMENTACION")
        + _buscar(PUNTAJE_PERIODICIDAD, control["periodicidad"], "PUNTAJE_PERIODICIDAD")
    )
    return _r(puntaje / PUNTAJE_MAXIMO)


def que_reduce(control):
    """Correctivos reducen impacto (movimiento horizontal); preventivos/detectivos, probabilidad (vertical)."""
    return "impacto" if _norm(control["tipo"]) in TIPOS_QUE_REDUCEN_IMPACTO else "probabilidad"


def _eficacias_aplicables(controles, dimension):
    return [calcular_eficacia_control(c) for c in controles if que_reduce(c) == dimension]


def _cascada(valor, eficacias):
    """Modo 1 (DEFAULT) — Cascada secuencial, DAFP V5/V6. Orden descendente por RD-001."""
    for e in sorted(eficacias, reverse=True):
        valor = valor * (1 - e)
    return valor


def _promedio(valor, eficacias):
    """Modo 2 — Solidez del conjunto, DAFP V4. Independiente del orden."""
    return valor * (1 - sum(eficacias) / len(eficacias))


def _dominante(valor, eficacias):
    """Modo 3 — Control dominante: manda el más eficaz."""
    return valor * (1 - max(eficacias))


MODOS_CONTROLES = {"cascada": _cascada, "promedio": _promedio, "dominante": _dominante}


def aplicar_controles(valor_inherente, controles, dimension, modo="cascada", tope=None):
    """Valor residual de una dimensión según el modo de agregación (RD-001).
    tope: si se define (ej. 0.9), la reducción agregada nunca supera ese % (RD-009, opcional)."""
    eficacias = _eficacias_aplicables(controles, dimension)
    if not eficacias:
        return _r(valor_inherente)
    if modo not in MODOS_CONTROLES:
        raise ValueError(f"Modo de control desconocido: {modo}. Opciones: {sorted(MODOS_CONTROLES)}")

    residual = MODOS_CONTROLES[modo](valor_inherente, eficacias)

    if tope is not None:
        piso = valor_inherente * (1 - tope)
        residual = max(residual, piso)

    return _r(residual)


def ubicar_en_banda(valor, bandas):
    """(nivel, etiqueta) de la banda donde cae el valor. Rangos continuos, sin huecos (RD-005)."""
    for limite, nivel, etiqueta in bandas:
        if _r(valor) <= limite:
            return nivel, etiqueta
    return bandas[-1][1], bandas[-1][2]


def clasificar_por_multiplicacion(prob_valor, impacto_valor, escala=ESCALA_5_NIVELES):
    """Modo alternativo: clasifica el producto probabilidad x impacto contra bandas de %."""
    producto = _r(prob_valor * impacto_valor)
    for limite, etiqueta in escala:
        if producto <= limite:
            return etiqueta
    return escala[-1][1]


def clasificar_por_zona(prob_valor, impacto_valor, apetito=APETITO_MODERADO):
    """Modo DEFAULT (RD-008): clasifica por CUADRANTE en la matriz 5x5 de apetito de riesgo."""
    nivel_p, etiqueta_p = ubicar_en_banda(prob_valor, BANDAS_PROBABILIDAD)
    nivel_i, etiqueta_i = ubicar_en_banda(impacto_valor, BANDAS_IMPACTO)
    return apetito[nivel_p][nivel_i - 1], {
        "prob": nivel_p, "impacto": nivel_i, "etiqueta": f"{etiqueta_p} | {etiqueta_i}",
    }


def clasificar(prob_valor, impacto_valor, config):
    """Punto ÚNICO de clasificación. Devuelve (nivel, coordenadas)."""
    coords = clasificar_por_zona(prob_valor, impacto_valor)[1]
    if config["modo_clasificacion"] == "zona":
        apetito = PERFILES_APETITO[config["apetito"]]
        return apetito[coords["prob"]][coords["impacto"] - 1], coords
    if config["modo_clasificacion"] == "multiplicacion":
        nivel = clasificar_por_multiplicacion(prob_valor, impacto_valor, config["escala_multiplicacion"])
        return nivel, coords
    raise ValueError(f"Modo de clasificación desconocido: {config['modo_clasificacion']}")


def _orden_de_niveles(config):
    """Orden ordinal de severidad vigente según la configuración activa (RD-010)."""
    if config["modo_clasificacion"] == "multiplicacion":
        return {etiqueta: i for i, (_, etiqueta) in enumerate(config["escala_multiplicacion"])}
    if config.get("apetito") == "metodologia_propia":
        return ORDEN_NIVELES_4
    return ORDEN_NIVELES_5


def aplicar_piso_wolfsberg(nivel_inherente, nivel_residual, config):
    """RD-010 — Distancia máxima de mitigación (Wolfsberg Group).
    El residual no puede descender más de 'descenso_maximo_residual' niveles bajo el inherente."""
    descenso_maximo = config.get("descenso_maximo_residual")
    if descenso_maximo is None:
        return nivel_residual, False

    orden = _orden_de_niveles(config)
    if nivel_inherente not in orden or nivel_residual not in orden:
        return nivel_residual, False

    pos_inherente = orden[nivel_inherente]
    pos_residual = orden[nivel_residual]
    piso = max(0, pos_inherente - descenso_maximo)

    if pos_residual < piso:
        etiqueta_piso = next(et for et, pos in orden.items() if pos == piso)
        return etiqueta_piso, True

    return nivel_residual, False


def evaluar_riesgo(riesgo, config=None):
    """Evalúa un riesgo de principio a fin y devuelve su registro completo."""
    if config is None:
        config = CONFIG_DEFAULT

    impacto_nivel = calcular_impacto(riesgo["impactos"], config["modo_impacto"])

    prob_inh = VALOR_A_PORCENTAJE[riesgo["probabilidad"]]
    imp_inh = VALOR_A_PORCENTAJE[impacto_nivel] if isinstance(impacto_nivel, int) else _r(impacto_nivel / 5)

    nivel_inh, coord_inh = clasificar(prob_inh, imp_inh, config)

    prob_res = aplicar_controles(prob_inh, riesgo["controles"], "probabilidad",
                                  config["modo_controles"], config.get("tope_reduccion_agregada"))
    imp_res = aplicar_controles(imp_inh, riesgo["controles"], "impacto",
                                 config["modo_controles"], config.get("tope_reduccion_agregada"))

    nivel_res, coord_res = clasificar(prob_res, imp_res, config)
    nivel_res_final, piso_aplicado = aplicar_piso_wolfsberg(nivel_inh, nivel_res, config)

    return {
        "id": riesgo["id"],
        "descripcion": riesgo["descripcion"],
        "categoria": riesgo.get("categoria"),
        "factor": riesgo.get("factor"),
        "n_controles": len(riesgo["controles"]),
        "prob_inherente": prob_inh, "imp_inherente": imp_inh,
        "producto_inherente": _r(prob_inh * imp_inh),
        "nivel_inherente": nivel_inh, "coord_inherente": (coord_inh["prob"], coord_inh["impacto"]),
        "zona_inherente": coord_inh["etiqueta"],
        "prob_residual": prob_res, "imp_residual": imp_res,
        "producto_residual": _r(prob_res * imp_res),
        "nivel_residual": nivel_res_final,
        "nivel_residual_sin_piso": nivel_res,
        "piso_aplicado": piso_aplicado,
        "coord_residual": (coord_res["prob"], coord_res["impacto"]),
        "zona_residual": coord_res["etiqueta"],
        "mov_vertical": coord_inh["prob"] - coord_res["prob"],
        "mov_horizontal": coord_inh["impacto"] - coord_res["impacto"],
        "requiere_plan_tratamiento": requiere_plan_tratamiento(nivel_res_final, config),
    }


def requiere_plan_tratamiento(nivel_residual, config):
    """RD-011 — Umbral de plan de tratamiento. Si el riesgo residual es Moderado o
    superior (o su equivalente en la escala vigente), requiere plan de tratamiento,
    SIN IMPORTAR qué perfil de apetito de riesgo esté activo (moderado, conservador,
    agresivo). El apetito decide en qué NIVEL cae un riesgo; esta regla decide qué se
    hace una vez que cae ahí — son dos decisiones distintas y no deben mezclarse."""
    orden = _orden_de_niveles(config)

    if config["modo_clasificacion"] == "multiplicacion":
        es_escala_legado = config["escala_multiplicacion"] is ESCALA_4_NIVELES
    else:
        es_escala_legado = config.get("apetito") == "metodologia_propia"

    umbral = "MEDIO" if es_escala_legado else "MODERADO"  # "MEDIO" es el equivalente más cercano en la escala de 4 niveles

    if nivel_residual not in orden or umbral not in orden:
        return False
    return orden[nivel_residual] >= orden[umbral]


def alertas_del_riesgo(registro):
    """Alertas metodológicas por riesgo (RD-006)."""
    alertas = []
    if registro["mov_horizontal"] == 0 and registro["coord_residual"][1] >= 4:
        alertas.append(
            "MITIGACIÓN UNIDIMENSIONAL: el riesgo se mitigó solo en probabilidad. "
            f"La severidad permanece intacta en nivel {NIVEL_A_IMPACTO[registro['coord_residual'][1]]}. "
            "Considere controles correctivos o planes de continuidad."
        )
    if registro["n_controles"] == 0:
        alertas.append("SIN CONTROLES: el riesgo residual es igual al inherente.")
    if registro.get("piso_aplicado"):
        alertas.append(
            f"PISO DE MITIGACIÓN APLICADO: el nivel residual se ajustó de "
            f"'{registro['nivel_residual_sin_piso']}' a '{registro['nivel_residual']}' según la regla de "
            "distancia máxima frente al inherente (Wolfsberg Group)."
        )
    if registro.get("requiere_plan_tratamiento"):
        alertas.append(f"Este riesgo requiere plan de tratamiento por encontrarse en nivel {registro['nivel_residual']}.")
    return alertas


def diagnosticar_calibracion(matriz_df, umbral_nivel=0.50, umbral_banda=0.60):
    """Analiza la distribución de riesgos residuales y advierte concentración excesiva (RD-006)."""
    total = len(matriz_df)
    alertas = []

    conteo_nivel = matriz_df["nivel_residual"].value_counts(normalize=True)
    for nivel, proporcion in conteo_nivel.items():
        if proporcion > umbral_nivel:
            alertas.append(
                f"CONCENTRACIÓN EN NIVEL '{nivel}': {proporcion:.0%} de los riesgos residuales "
                f"({int(proporcion * total)} de {total}) caen en este único nivel. "
                "La matriz pierde poder para priorizar ante la junta directiva."
            )

    banda_prob = matriz_df["coord_residual"].apply(lambda c: c[0]).value_counts(normalize=True)
    for nivel, proporcion in banda_prob.items():
        if proporcion > umbral_banda:
            etiqueta = NIVEL_A_PROBABILIDAD[nivel]
            alertas.append(
                f"CONCENTRACIÓN EN PROBABILIDAD '{etiqueta}': {proporcion:.0%} de los riesgos residuales "
                "caen en esta banda. Revise el modo de agregación de controles o considere "
                "activar el tope de reducción agregada."
            )

    niveles_altos = {"ALTO", "EXTREMO", "SIGNIFICATIVO"}
    if not (set(conteo_nivel.index) & niveles_altos):
        alertas.append(
            "AUSENCIA DE RIESGOS RESIDUALES ALTOS: ningún riesgo alcanza los niveles superiores de la "
            "escala tras aplicar controles. Verifique que la eficacia declarada de los controles "
            "corresponda a evidencia real, no a una aspiración."
        )

    return alertas


# ============================================================
# Catálogos de riesgos — genérico, funciona con cualquier fuente compatible
# (ruta en disco O archivo subido desde el navegador vía st.file_uploader)
# ============================================================
def cargar_catalogo(fuente_excel):
    """Lee un catálogo de riesgos (hojas 'Riesgos' + 'Controles') y devuelve la lista de
    diccionarios que evaluar_riesgo() espera. 'fuente_excel' puede ser una ruta (str/Path)
    o un archivo subido por el usuario (UploadedFile de Streamlit) — pandas acepta ambos.

    Las dimensiones de impacto NO están fijas a las 7 de la metodología completa
    (normativo, legal, económico, liquidez, reputacional, operacional, contagio):
    se detectan dinámicamente a partir de cualquier columna 'imp_*' presente en la
    hoja 'Riesgos'. Un cliente puede traer 4 (ej. liquidez, legal, contagio,
    operacional), 7, o 10 dimensiones propias de su industria — calcular_impacto()
    en este mismo archivo ya agrega por máximo o promedio sobre el diccionario
    completo, sin depender de cuántas ni cuáles claves tenga."""
    riesgos_df = pd.read_excel(fuente_excel, sheet_name="Riesgos")
    controles_df = pd.read_excel(fuente_excel, sheet_name="Controles")

    columnas_impacto = [c for c in riesgos_df.columns if str(c).startswith("imp_")]
    if not columnas_impacto:
        raise ValueError(
            "El catálogo no tiene ninguna columna de impacto. Se esperan una o más columnas "
            "con el prefijo 'imp_' (ej. imp_legal, imp_liquidez) en la hoja 'Riesgos'."
        )

    catalogo = []
    for _, fila in riesgos_df.iterrows():
        controles_del_riesgo = controles_df[controles_df["riesgo_id"] == fila["id"]]
        controles = [
            {
                "id": c["control_id"], "descripcion": c["descripcion"], "tipo": c["tipo"],
                "automatizacion": c["automatizacion"], "documentacion": c["documentacion"],
                "periodicidad": c["periodicidad"],
            }
            for _, c in controles_del_riesgo.iterrows()
        ]
        catalogo.append({
            "id": fila["id"],
            "categoria": fila["familia"],
            "factor": fila["factor"],
            "descripcion": fila["descripcion"],
            "probabilidad": int(fila["probabilidad_semilla"]),
            "impactos": {
                col[len("imp_"):]: int(fila[col]) for col in columnas_impacto
            },
            "controles": controles,
        })
    return catalogo


def exportar_matriz(matriz_df, catalogo_raw, nombre_archivo="matriz_riesgos_evaluada.xlsx"):
    """Exporta la matriz evaluada a Excel en el formato acordado: una fila por control
    (o una fila con 'sin controles' si el riesgo no tiene ninguno — nunca se pierde un
    riesgo del reporte por no tener controles asociados).

    catalogo_raw: {id_riesgo: diccionario_del_riesgo_crudo}, para poder listar la
    descripción real de cada control aplicado (el DataFrame calculado no la conserva)."""
    columnas = ["id_riesgo", "descripcion_riesgo", "probabilidad_inherente", "impacto_inherente",
                "id_control", "descripcion_control", "probabilidad_residual", "impacto_residual", "nivel_residual"]

    filas_export = []
    for _, fila in matriz_df.iterrows():
        riesgo_id = fila["id"]
        controles = catalogo_raw.get(riesgo_id, {}).get("controles", [])
        base = {
            "id_riesgo": riesgo_id,
            "descripcion_riesgo": fila["descripcion"],
            "probabilidad_inherente": fila["prob_inherente"],
            "impacto_inherente": fila["imp_inherente"],
        }
        cola = {
            "probabilidad_residual": fila["prob_residual"],
            "impacto_residual": fila["imp_residual"],
            "nivel_residual": fila["nivel_residual"],
        }
        if controles:
            for c in controles:
                filas_export.append({**base, "id_control": c["id"], "descripcion_control": c["descripcion"], **cola})
        else:
            filas_export.append({**base, "id_control": "", "descripcion_control": "(sin controles asociados)", **cola})

    df = pd.DataFrame(filas_export, columns=columnas)

    with pd.ExcelWriter(nombre_archivo, engine="xlsxwriter") as writer:
        df.to_excel(writer, sheet_name="Matriz", index=False)
        libro = writer.book
        hoja = writer.sheets["Matriz"]

        formato_encabezado = libro.add_format({"bold": True, "bg_color": "#1F4E79", "font_color": "white", "border": 1})
        formato_decimal = libro.add_format({"num_format": "0.0000"})
        colores_nivel = {
            "MUY BAJO": "#C6EFCE", "INSIGNIFICANTE": "#C6EFCE",
            "BAJO": "#C6EFCE",
            "MODERADO": "#FFEB9C", "MEDIO": "#FFEB9C",
            "ALTO": "#FFC7CE", "EXTREMO": "#FF0000", "SIGNIFICATIVO": "#FF0000",
        }

        for col_num, nombre in enumerate(df.columns):
            hoja.write(0, col_num, nombre, formato_encabezado)

        anchos = {"id_riesgo": 10, "descripcion_riesgo": 48, "probabilidad_inherente": 16,
                  "impacto_inherente": 14, "id_control": 10, "descripcion_control": 45,
                  "probabilidad_residual": 16, "impacto_residual": 14, "nivel_residual": 14}
        for col_num, nombre in enumerate(df.columns):
            fmt = formato_decimal if ("probabilidad" in nombre or "impacto" in nombre) else None
            hoja.set_column(col_num, col_num, anchos.get(nombre, 15), fmt)

        col_nivel = df.columns.get_loc("nivel_residual")
        for nivel, color in colores_nivel.items():
            formato = libro.add_format({"bg_color": color})
            hoja.conditional_format(1, col_nivel, len(df), col_nivel,
                                     {"type": "text", "criteria": "containing", "value": nivel, "format": formato})

    return nombre_archivo

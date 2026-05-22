from __future__ import annotations

from io import BytesIO
import re
from datetime import date
from typing import Iterable

import pandas as pd
import streamlit as st


DEFAULT_EXCLUDED_PRODUCTS = "D600, D460"
DEFAULT_EXCLUDED_ASESOR_CODES = (
    "28005, 34400, 29403, 105-0000, 48400, 08417-001, "
    "11013, 436, 110-G010, Sin codigo, Sin codigo red"
)
DEFAULT_EXCLUDED_ASESOR_PREFIXES = "100-"

MONEY_COLUMNS = {
    "FACTURACION_BRUTA",
    "FACTURACION_ANULADA",
    "FACTURACION_NETA",
    "PRIMA_MEDIA",
}
PERCENT_COLUMNS = {"CHURN_POLIZAS", "CHURN_FACTURACION"}


# ============================================================
# Utilidades generales
# ============================================================


def normalize_column_key(value: object) -> str:
    text = str(value).strip().upper()
    replacements = {"Á": "A", "É": "E", "Í": "I", "Ó": "O", "Ú": "U", "Ü": "U"}
    for old, new in replacements.items():
        text = text.replace(old, new)
    text = re.sub(r"[^A-Z0-9]+", " ", text)
    return re.sub(r"\s+", " ", text).strip()


def find_column(df: pd.DataFrame, candidates: Iterable[str]) -> str | None:
    normalized = {normalize_column_key(col): col for col in df.columns}

    for candidate in candidates:
        key = normalize_column_key(candidate)
        if key in normalized:
            return normalized[key]

    return None


def require_column(df: pd.DataFrame, candidates: Iterable[str], label: str) -> str:
    col = find_column(df, candidates)
    if col is None:
        raise ValueError(
            f"No encuentro la columna {label}. Columnas leidas: {', '.join(map(str, df.columns))}"
        )
    return col


def parse_spanish_number(value: object) -> float:
    if pd.isna(value):
        return 0.0
    if isinstance(value, (int, float)):
        return float(value)

    text = str(value).replace("\xa0", " ").strip()
    text = re.sub(r"[^\d,.\-]", "", text)
    if not text or text in {"-", ",", "."}:
        return 0.0

    if "," in text and "." in text:
        if text.rfind(",") > text.rfind("."):
            text = text.replace(".", "").replace(",", ".")
        else:
            text = text.replace(",", "")
    elif "," in text:
        text = text.replace(".", "").replace(",", ".")

    try:
        return float(text)
    except ValueError:
        return 0.0


def normalize_text(value: object, default: str = "") -> str:
    if pd.isna(value) or str(value).strip() == "":
        return default
    text = str(value).strip()
    if re.fullmatch(r"\d+\.0", text):
        text = text[:-2]
    return text


def normalize_product(value: object) -> str:
    return normalize_text(value).upper()


def normalize_policy(value: object) -> str:
    return normalize_text(value)


def normalize_reason(value: object) -> str:
    text = normalize_text(value).upper()
    replacements = {"Á": "A", "É": "E", "Í": "I", "Ó": "O", "Ú": "U", "Ü": "U"}
    for old, new in replacements.items():
        text = text.replace(old, new)
    return text


def split_csv(text: str) -> list[str]:
    return [item.strip() for item in str(text).split(",") if item.strip()]


def format_euro(value: float) -> str:
    return f"{float(value):,.2f} €".replace(",", "X").replace(".", ",").replace("X", ".")


def format_percent(value: float) -> str:
    return f"{float(value):.2%}".replace(".", ",")


@st.cache_data(show_spinner=False)
def read_excel_uploaded(uploaded_file) -> pd.DataFrame:
    if uploaded_file is None:
        return pd.DataFrame()

    sheets = pd.read_excel(uploaded_file, sheet_name=None, dtype=str)
    frames = []
    for sheet_name, df in sheets.items():
        df = df.copy()
        df.columns = [str(c).strip() for c in df.columns]
        df["HOJA_ORIGEN"] = sheet_name
        frames.append(df)

    if not frames:
        return pd.DataFrame()

    return pd.concat(frames, ignore_index=True)


def available_date_columns(df: pd.DataFrame) -> list[str]:
    priority = [
        "FECHA GRABACION",
        "FECHA_GRABACION",
        "GRABACION",
        "GRABACION_INICIAL",
        "FECGRABA",
        "POLIALTA",
        "POLIEFECT",
        "POLIEFEC",
        "FECHA EFECTO",
        "FECHA ALTA",
    ]
    found = []
    for candidate in priority:
        col = find_column(df, (candidate,))
        if col and col not in found:
            found.append(col)

    for col in df.columns:
        key = normalize_column_key(col)
        if (
            "FECHA" in key
            or "FEC" in key
            or "GRABACION" in key
            or key in {"POLIALTA", "POLIEFECT", "POLIEFEC"}
        ) and col not in found:
            found.append(col)

    return found


def get_effect_column(df: pd.DataFrame) -> str:
    # Fecha efecto maxima: SIEMPRE se usa POLIEFECT/POLIEFEC.
    # POLIALTA puede elegirse como fecha de rango, pero no como tope de efecto.
    return require_column(
        df,
        ("POLIEFECT", "POLIEFEC", "FECHA EFECTO"),
        "POLIEFECT / POLIEFEC / FECHA EFECTO",
    )


# ============================================================
# Preparacion de datos
# ============================================================


def prepare_facturacion_mediador(df: pd.DataFrame, date_column: str) -> pd.DataFrame:
    producto_col = require_column(df, ("PRODUCTO",), "PRODUCTO")
    poliza_col = require_column(df, ("POLIZA",), "POLIZA")
    mediador_col = require_column(df, ("MEDIADOR", "CODIMEDI", "AGENTE"), "MEDIADOR / CODIMEDI")
    prima_col = require_column(df, ("PRIMA NETA", "PRIMA_NETA", "PRIMA NE"), "PRIMA NETA")
    effect_col = get_effect_column(df)

    work = df.copy()
    work["PRODUCTO_NORMALIZADO"] = work[producto_col].apply(normalize_product)
    work["POLIZA_NORMALIZADA"] = work[poliza_col].apply(normalize_policy)
    work["CODIGO"] = work[mediador_col].apply(lambda x: normalize_text(x, "Sin mediador"))
    work["NOMBRE"] = work["CODIGO"]

    # Fecha del rango: la selecciona el usuario.
    work["FECHA_RANKING"] = pd.to_datetime(work[date_column], dayfirst=True, errors="coerce")

    # Tope independiente de efecto: SIEMPRE POLIEFECT/POLIEFEC.
    work["FECHA_EFECTO"] = pd.to_datetime(work[effect_col], dayfirst=True, errors="coerce")

    work["PRIMA_NETA_VALOR"] = work[prima_col].apply(parse_spanish_number)
    return work


def prepare_facturacion_asesor(df: pd.DataFrame, date_column: str) -> pd.DataFrame:
    producto_col = require_column(df, ("PRODUCTO",), "PRODUCTO")
    poliza_col = require_column(df, ("POLIZA",), "POLIZA")
    codigo_col = require_column(
        df,
        ("CODIGO RED COMERCIAL", "CODIGO_RED_COMERCIAL", "CODIGO RED", "CODIGO R"),
        "CODIGO RED COMERCIAL",
    )
    comercial_col = require_column(df, ("COMERCIAL", "ASESOR"), "COMERCIAL")
    prima_col = require_column(df, ("PRIMA NETA", "PRIMA_NETA", "PRIMA NE"), "PRIMA NETA")
    effect_col = get_effect_column(df)

    work = df.copy()
    work["PRODUCTO_NORMALIZADO"] = work[producto_col].apply(normalize_product)
    work["POLIZA_NORMALIZADA"] = work[poliza_col].apply(normalize_policy)
    work["CODIGO"] = work[codigo_col].apply(lambda x: normalize_text(x, "Sin codigo red"))
    work["NOMBRE"] = work[comercial_col].apply(lambda x: normalize_text(x, "Sin asesor"))

    # Fecha del rango: la selecciona el usuario.
    work["FECHA_RANKING"] = pd.to_datetime(work[date_column], dayfirst=True, errors="coerce")

    # Tope independiente de efecto: SIEMPRE POLIEFECT/POLIEFEC.
    work["FECHA_EFECTO"] = pd.to_datetime(work[effect_col], dayfirst=True, errors="coerce")

    work["PRIMA_NETA_VALOR"] = work[prima_col].apply(parse_spanish_number)
    return work


def prepare_anulaciones(df: pd.DataFrame) -> pd.DataFrame:
    producto_col = require_column(df, ("PRODUCTO",), "PRODUCTO")
    poliza_col = require_column(df, ("POLIZA",), "POLIZA")
    prima_col = require_column(df, ("PRIMA NETA", "PRIMA_NETA", "PRIMA NE"), "PRIMA NETA")
    fecha_col = require_column(df, ("FECHA EMISION", "FECHA_EMISION", "FECHA BAJA", "FECHA ANULACION"), "FECHA EMISION")

    mediador_col = find_column(df, ("MEDIADOR", "CODIMEDI", "AGENTE"))
    causa_col = find_column(df, ("CAUSA",))
    motivo_col = find_column(df, ("MOTIVO",))

    work = df.copy()
    work["PRODUCTO_NORMALIZADO"] = work[producto_col].apply(normalize_product)
    work["POLIZA_NORMALIZADA"] = work[poliza_col].apply(normalize_policy)
    work["CODIGO"] = work[mediador_col].apply(lambda x: normalize_text(x, "Sin mediador")) if mediador_col else "Sin mediador"
    work["NOMBRE"] = work["CODIGO"]
    work["FECHA_RANKING"] = pd.to_datetime(work[fecha_col], dayfirst=True, errors="coerce")
    work["PRIMA_NETA_VALOR"] = work[prima_col].apply(parse_spanish_number)
    work["CAUSA_NORMALIZADA"] = work[causa_col].apply(normalize_reason) if causa_col else ""
    work["MOTIVO_NORMALIZADO"] = work[motivo_col].apply(normalize_reason) if motivo_col else ""
    return work


def filter_base(
    df: pd.DataFrame,
    fecha_desde: date,
    fecha_hasta: date,
    excluded_products: set[str],
    fecha_efecto_maxima: date | None,
) -> pd.DataFrame:
    mask = (
        df["FECHA_RANKING"].notna()
        & df["FECHA_RANKING"].dt.date.ge(fecha_desde)
        & df["FECHA_RANKING"].dt.date.le(fecha_hasta)
        & ~df["PRODUCTO_NORMALIZADO"].isin(excluded_products)
    )

    if fecha_efecto_maxima is not None:
        mask = (
            mask
            & df["FECHA_EFECTO"].notna()
            & df["FECHA_EFECTO"].dt.date.le(fecha_efecto_maxima)
        )

    return df[mask].copy()


def filter_anulaciones(
    df: pd.DataFrame,
    fecha_desde: date,
    fecha_hasta: date,
    excluded_products: set[str],
    excluir_defuncion_siniestro: bool,
) -> pd.DataFrame:
    mask = (
        df["FECHA_RANKING"].notna()
        & df["FECHA_RANKING"].dt.date.ge(fecha_desde)
        & df["FECHA_RANKING"].dt.date.le(fecha_hasta)
        & ~df["PRODUCTO_NORMALIZADO"].isin(excluded_products)
    )

    if excluir_defuncion_siniestro:
        causa = (
            df["CAUSA_NORMALIZADA"].astype(str)
            if "CAUSA_NORMALIZADA" in df.columns
            else pd.Series("", index=df.index)
        )
        motivo = (
            df["MOTIVO_NORMALIZADO"].astype(str)
            if "MOTIVO_NORMALIZADO" in df.columns
            else pd.Series("", index=df.index)
        )
        excluded_reason = (
            causa.str.startswith("DEFUNCION", na=False)
            | causa.str.startswith("INDIVIDUAL POR SINIESTRO", na=False)
            | motivo.str.startswith("DEFUNCION", na=False)
            | motivo.str.startswith("SINIESTRO TOTAL", na=False)
        )
        mask = mask & ~excluded_reason

    return df[mask].copy()


def exclude_asesor_codes(df: pd.DataFrame, exact_codes: list[str], prefixes: list[str]) -> pd.DataFrame:
    if df.empty:
        return df.copy()
    work = df.copy()
    codigo = work["CODIGO"].fillna("").astype(str).str.strip()
    nombre = work["NOMBRE"].fillna("").astype(str).str.strip().str.upper()
    exact = {str(c).strip() for c in exact_codes if str(c).strip()}

    mask = codigo.isin(exact) | nombre.eq("SIN ASESOR") | codigo.eq("")
    for prefix in prefixes:
        if prefix.strip():
            mask = mask | codigo.str.startswith(prefix.strip(), na=False)
    return work[~mask].copy()


def aggregate_detail(df: pd.DataFrame, amount_name: str, count_name: str) -> pd.DataFrame:
    if df.empty:
        return pd.DataFrame(columns=["CODIGO", "NOMBRE", amount_name, count_name])

    return (
        df.groupby(["CODIGO", "NOMBRE"], dropna=False)
        .agg(
            **{
                amount_name: ("PRIMA_NETA_VALOR", "sum"),
                count_name: ("POLIZA_NORMALIZADA", "nunique"),
            }
        )
        .reset_index()
    )


def build_ranking(
    facturacion_df: pd.DataFrame,
    anulaciones_df: pd.DataFrame,
    facturacion_asesor_df: pd.DataFrame | None,
    ranking_por: str,
    date_column: str,
    fecha_desde: date,
    fecha_hasta: date,
    excluded_products: list[str],
    fecha_efecto_maxima: date | None,
    metric: str,
    excluir_defuncion_siniestro: bool,
    solo_bajas_altas_mismo_anio: bool,
    excluded_asesor_codes: list[str],
    excluded_asesor_prefixes: list[str],
) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    excluded_products_set = {normalize_product(p) for p in excluded_products}

    if ranking_por == "Asesor / comercial":
        if facturacion_asesor_df is None or facturacion_asesor_df.empty:
            raise ValueError("Para ranking por asesor necesitas subir FACTURACION_DECESOS_ASESOR.")
        altas_prepared = prepare_facturacion_asesor(facturacion_asesor_df, date_column)
    else:
        altas_prepared = prepare_facturacion_mediador(facturacion_df, date_column)

    anulaciones_prepared = prepare_anulaciones(anulaciones_df)

    # ALTAS: se filtran por fecha del ranking seleccionada y opcionalmente por tope POLIEFECT.
    altas_detail = filter_base(
        altas_prepared,
        fecha_desde,
        fecha_hasta,
        excluded_products_set,
        fecha_efecto_maxima,
    )

    # ANULACIONES: se filtran por FECHA EMISION entre fecha_desde y fecha_hasta.
    anulaciones_detail_base = filter_anulaciones(
        anulaciones_prepared,
        fecha_desde,
        fecha_hasta,
        excluded_products_set,
        excluir_defuncion_siniestro,
    )

    if ranking_por == "Asesor / comercial":
        # Para imputar bajas a asesor cruzamos por POLIZA contra FACTURACION_DECESOS_ASESOR.
        lookup = altas_prepared[["POLIZA_NORMALIZADA", "CODIGO", "NOMBRE", "FECHA_EFECTO"]].copy()
        if solo_bajas_altas_mismo_anio:
            lookup = lookup[lookup["FECHA_EFECTO"].dt.year == fecha_hasta.year]
        lookup = lookup.drop_duplicates("POLIZA_NORMALIZADA")

        anulaciones_detail = pd.merge(
            anulaciones_detail_base.drop(columns=["CODIGO", "NOMBRE"], errors="ignore"),
            lookup[["POLIZA_NORMALIZADA", "CODIGO", "NOMBRE"]],
            on="POLIZA_NORMALIZADA",
            how="inner",
        )

        altas_detail = exclude_asesor_codes(altas_detail, excluded_asesor_codes, excluded_asesor_prefixes)
        anulaciones_detail = exclude_asesor_codes(anulaciones_detail, excluded_asesor_codes, excluded_asesor_prefixes)
    else:
        anulaciones_detail = anulaciones_detail_base

    altas = aggregate_detail(altas_detail, "FACTURACION_BRUTA", "POLIZAS_GRABADAS")
    anulaciones = aggregate_detail(anulaciones_detail, "FACTURACION_ANULADA", "POLIZAS_ANULADAS")

    ranking = pd.merge(altas, anulaciones, on=["CODIGO", "NOMBRE"], how="outer")

    if ranking.empty:
        return ranking, altas_detail, anulaciones_detail

    for col in ["FACTURACION_BRUTA", "POLIZAS_GRABADAS", "FACTURACION_ANULADA", "POLIZAS_ANULADAS"]:
        ranking[col] = pd.to_numeric(ranking[col], errors="coerce").fillna(0)

    ranking["FACTURACION_NETA"] = ranking["FACTURACION_BRUTA"] - ranking["FACTURACION_ANULADA"]
    ranking["POLIZAS_NETAS"] = ranking["POLIZAS_GRABADAS"] - ranking["POLIZAS_ANULADAS"]
    ranking["PRIMA_MEDIA"] = [
        fact / pol if pol else 0.0
        for fact, pol in zip(ranking["FACTURACION_NETA"], ranking["POLIZAS_NETAS"])
    ]
    ranking["CHURN_POLIZAS"] = [
        baja / alta if alta else 0.0
        for baja, alta in zip(ranking["POLIZAS_ANULADAS"], ranking["POLIZAS_GRABADAS"])
    ]
    ranking["CHURN_FACTURACION"] = [
        baja / alta if alta else 0.0
        for baja, alta in zip(ranking["FACTURACION_ANULADA"], ranking["FACTURACION_BRUTA"])
    ]

    ranking = ranking.sort_values(metric, ascending=False).reset_index(drop=True)
    ranking.insert(0, "POSICION", range(1, len(ranking) + 1))

    return ranking, altas_detail, anulaciones_detail


def format_for_display(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    for col in out.columns:
        if col in MONEY_COLUMNS:
            out[col] = out[col].apply(format_euro)
        elif col in PERCENT_COLUMNS:
            out[col] = out[col].apply(format_percent)
    return out


def to_excel_bytes(ranking: pd.DataFrame, altas: pd.DataFrame, anulaciones: pd.DataFrame, parametros: dict[str, object]) -> bytes:
    output = BytesIO()
    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        pd.DataFrame([parametros]).to_excel(writer, index=False, sheet_name="PARAMETROS")
        ranking.to_excel(writer, index=False, sheet_name="RANKING")
        altas.to_excel(writer, index=False, sheet_name="DETALLE_ALTAS")
        anulaciones.to_excel(writer, index=False, sheet_name="DETALLE_ANULACIONES")
    return output.getvalue()


# ============================================================
# UI Streamlit
# ============================================================


st.set_page_config(page_title="Ranking personalizado Decesos", layout="wide")
st.title("Ranking personalizado Decesos")
st.caption(
    "Constructor flexible para generar rankings por agente o asesor usando facturación y anulaciones de Decesos. "
    "El rango se calcula con la fecha que selecciones y el tope de efecto se calcula siempre con POLIEFECT/POLIEFEC."
)

with st.sidebar:
    st.header("1. Archivos")
    facturacion_file = st.file_uploader("FACTURACION_DECESOS", type=["xls", "xlsx", "xlsm"])
    anulaciones_file = st.file_uploader("FACTURACION_ANULACIONES_DECESOS", type=["xls", "xlsx", "xlsm"])
    facturacion_asesor_file = st.file_uploader(
        "FACTURACION_DECESOS_ASESOR (solo si ranking por asesor)",
        type=["xls", "xlsx", "xlsm"],
    )

    st.header("2. Ranking")
    ranking_por = st.radio("¿Qué ranking quieres?", ["Agente / mediador", "Asesor / comercial"], horizontal=False)

if facturacion_file is None or anulaciones_file is None:
    st.info("Sube al menos FACTURACION_DECESOS y FACTURACION_ANULACIONES_DECESOS para empezar.")
    st.stop()

try:
    facturacion_df = read_excel_uploaded(facturacion_file)
    anulaciones_df = read_excel_uploaded(anulaciones_file)
    facturacion_asesor_df = read_excel_uploaded(facturacion_asesor_file) if facturacion_asesor_file else pd.DataFrame()
except ImportError as error:
    st.error("Falta una librería para leer Excel antiguo .xls. Instala dependencias con: pip install xlrd openpyxl")
    st.exception(error)
    st.stop()
except Exception as error:
    st.error("No he podido leer alguno de los Excel.")
    st.exception(error)
    st.stop()

source_for_dates = facturacion_asesor_df if ranking_por == "Asesor / comercial" and not facturacion_asesor_df.empty else facturacion_df
date_cols = available_date_columns(source_for_dates)
if not date_cols:
    st.error("No encuentro columnas de fecha en el archivo de facturación.")
    st.stop()

# Seleccion por defecto: GRABACION si existe; si no, FECHA_GRABACION; si no, POLIALTA.
default_date_index = 0
for preferred in ["GRABACION", "FECHA GRABACION", "FECHA_GRABACION", "POLIALTA"]:
    found = find_column(source_for_dates, (preferred,))
    if found in date_cols:
        default_date_index = date_cols.index(found)
        break

with st.form("ranking_form"):
    st.subheader("Parámetros del ranking")

    c1, c2, c3 = st.columns(3)
    with c1:
        date_column = st.selectbox(
            "¿Qué fecha quieres usar para el rango del ranking?",
            date_cols,
            index=default_date_index,
            help="Puedes usar GRABACION para pólizas grabadas, POLIALTA para altas, etc.",
        )
        fecha_desde = st.date_input("Fecha desde", value=date(date.today().year, 1, 1), format="DD/MM/YYYY")
    with c2:
        fecha_hasta = st.date_input("Fecha hasta", value=date.today(), format="DD/MM/YYYY")
        usar_fecha_efecto_maxima = st.checkbox(
            "Fijar tope máximo de efecto",
            help="Este tope se aplica siempre sobre POLIEFECT/POLIEFEC, aunque el rango use GRABACION o POLIALTA.",
        )
    with c3:
        fecha_efecto_maxima_text = st.text_input(
            "Fecha efecto máxima (POLIEFECT)",
            value=f"31/12/{fecha_hasta.year}",
            disabled=not usar_fecha_efecto_maxima,
            help="Formato DD/MM/AAAA. Ejemplo: 01/07/2026",
        )

        excluded_products_text = st.text_input(
            "Productos excluidos",
            value=DEFAULT_EXCLUDED_PRODUCTS,
        )

    c4, c5, c6 = st.columns(3)
    with c4:
        metric_label = st.selectbox(
            "¿Qué parámetro quieres utilizar para ordenar el ranking?",
            [
                "Facturación neta",
                "Facturación bruta",
                "Pólizas grabadas",
                "Pólizas netas",
                "Facturación anulada",
                "Churn pólizas",
                "Churn facturación",
            ],
        )
    with c5:
        excluir_defuncion_siniestro = st.checkbox("Excluir bajas por defunción / siniestro", value=True)
        solo_bajas_altas_mismo_anio = st.checkbox(
            "En asesores: contar bajas solo si la póliza tuvo efecto ese mismo año",
            value=True,
        )
    with c6:
        asesor_codes_text = st.text_area(
            "Códigos excluidos en ranking asesor",
            value=DEFAULT_EXCLUDED_ASESOR_CODES,
            height=80,
        )
        asesor_prefixes_text = st.text_input(
            "Prefijos excluidos en ranking asesor",
            value=DEFAULT_EXCLUDED_ASESOR_PREFIXES,
        )

    submitted = st.form_submit_button("Crear ranking")

metric_map = {
    "Facturación neta": "FACTURACION_NETA",
    "Facturación bruta": "FACTURACION_BRUTA",
    "Pólizas grabadas": "POLIZAS_GRABADAS",
    "Pólizas netas": "POLIZAS_NETAS",
    "Facturación anulada": "FACTURACION_ANULADA",
    "Churn pólizas": "CHURN_POLIZAS",
    "Churn facturación": "CHURN_FACTURACION",
}

if submitted:
    try:
        if fecha_desde > fecha_hasta:
            raise ValueError("La fecha desde no puede ser posterior a la fecha hasta.")

        ranking, altas_detail, anulaciones_detail = build_ranking(
            facturacion_df=facturacion_df,
            anulaciones_df=anulaciones_df,
            facturacion_asesor_df=facturacion_asesor_df,
            ranking_por=ranking_por,
            date_column=date_column,
            fecha_desde=fecha_desde,
            fecha_hasta=fecha_hasta,
            excluded_products=split_csv(excluded_products_text),
            fecha_efecto_maxima=fecha_efecto_maxima if usar_fecha_efecto_maxima else None,
            metric=metric_map[metric_label],
            excluir_defuncion_siniestro=excluir_defuncion_siniestro,
            solo_bajas_altas_mismo_anio=solo_bajas_altas_mismo_anio,
            excluded_asesor_codes=split_csv(asesor_codes_text),
            excluded_asesor_prefixes=split_csv(asesor_prefixes_text),
        )

        st.success(f"Ranking creado: {len(ranking)} filas")

        total_grabadas = int(ranking["POLIZAS_GRABADAS"].sum()) if not ranking.empty else 0
        total_anuladas = int(ranking["POLIZAS_ANULADAS"].sum()) if not ranking.empty else 0
        total_neta = float(ranking["FACTURACION_NETA"].sum()) if not ranking.empty else 0.0
        churn_total = total_anuladas / total_grabadas if total_grabadas else 0.0

        k1, k2, k3, k4 = st.columns(4)
        k1.metric("Facturación neta", format_euro(total_neta))
        k2.metric("Pólizas grabadas", total_grabadas)
        k3.metric("Pólizas anuladas", total_anuladas)
        k4.metric("Churn pólizas", format_percent(churn_total))

        st.subheader("Ranking")
        st.dataframe(format_for_display(ranking), use_container_width=True, hide_index=True)

        with st.expander("Ver detalle usado en el cálculo"):
            st.write("Altas filtradas")
            st.dataframe(altas_detail, use_container_width=True)
            st.write("Anulaciones filtradas")
            st.dataframe(anulaciones_detail, use_container_width=True)

        parametros = {
            "ranking_por": ranking_por,
            "fecha_columna_rango": date_column,
            "fecha_desde": fecha_desde.strftime("%d/%m/%Y"),
            "fecha_hasta": fecha_hasta.strftime("%d/%m/%Y"),
            "fecha_efecto_maxima_POLIEFECT": fecha_efecto_maxima.strftime("%d/%m/%Y") if usar_fecha_efecto_maxima else "No aplicada",
            "productos_excluidos": excluded_products_text,
            "ordenado_por": metric_label,
            "excluir_defuncion_siniestro": excluir_defuncion_siniestro,
            "solo_bajas_altas_mismo_anio": solo_bajas_altas_mismo_anio,
        }
        excel_bytes = to_excel_bytes(ranking, altas_detail, anulaciones_detail, parametros)
        st.download_button(
            "Descargar ranking en Excel",
            data=excel_bytes,
            file_name="ranking_personalizado_decesos.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        )

    except Exception as error:
        st.error("No he podido crear el ranking con estos parámetros.")
        st.exception(error)

import warnings
from urllib3.exceptions import NotOpenSSLWarning
warnings.filterwarnings("ignore", category=NotOpenSSLWarning)

import streamlit as st
import pandas as pd
import requests
from io import BytesIO
from st_aggrid import AgGrid, GridOptionsBuilder, GridUpdateMode

# --- CONFIGURACIÓN DE GOOGLE DRIVE ---
FILE_ID = "1TVnBvEjwY0Alywyp75QTwWVw0yqdWJaV"
URL = f"https://drive.google.com/uc?export=download&id={FILE_ID}"

# --- FUNCIÓN PARA CARGAR DATOS ---
@st.cache_data(ttl=60)
def cargar_datos_drive():
    try:
        r = requests.get(URL)
        r.raise_for_status()
        xls = pd.ExcelFile(BytesIO(r.content))
        hojas = xls.sheet_names
        dataframes = []
        for hoja in hojas:
            df = pd.read_excel(xls, hoja, header=5)
            df["CAJA"] = hoja
            dataframes.append(df)
        if not dataframes:
            return pd.DataFrame()
        return pd.concat(dataframes, ignore_index=True)
    except Exception as e:
        st.error(f"No se pudo cargar el archivo desde Drive: {e}")
        return pd.DataFrame()

# --- CONFIGURACIÓN DE LA PÁGINA ---
st.set_page_config(page_title="Inventario de Anticuerpos", layout="wide")

# --- TÍTULO DE LA APP ---
st.markdown("<h1 style='color:#CD212A;'>Inventario de Anticuerpos CARDIO-INMUNO</h1>", unsafe_allow_html=True)

# --- CARGAR DATOS ---
df = cargar_datos_drive()
if df.empty:
    st.stop()

# --- INICIALIZAR session_state ---
if "fila_seleccionada_idx" not in st.session_state:
    st.session_state["fila_seleccionada_idx"] = None
if "actualizar_flag" not in st.session_state:
    st.session_state["actualizar_flag"] = False

# --- BÚSQUEDA ---
busqueda = st.text_input("🔎 Escribe el nombre del anticuerpo o Caja:", "").strip()
if busqueda:
    resultados = df[df.apply(lambda fila: fila.astype(str).str.contains(busqueda, case=False).any(), axis=1)].copy()
else:
    resultados = df.copy()

# --- COLUMNAS VISIBLES (B y C) ---
if len(df.columns) >= 3:
    columnas_visibles = df.columns[1:3]
else:
    columnas_visibles = df.columns

# --- RESULTADOS ---
st.write(
    f"Se encontraron **{len(resultados)}** resultados para: `{busqueda}`"
    if busqueda else
    "Mostrando todos los registros disponibles"
)

st.markdown("**Da click al anticuerpo para ver detalles**👇🏻")

# --- AÑADIR COLUMNA TEMPORAL CON ÍNDICE REAL ---
resultados["_fila_real"] = resultados.index

# --- CONFIGURAR TABLA INTERACTIVA ---
gb = GridOptionsBuilder.from_dataframe(resultados[list(columnas_visibles) + ["_fila_real"]])
gb.configure_columns(["_fila_real"], hide=True)
gb.configure_selection('single', use_checkbox=False)
gb.configure_grid_options(domLayout='autoHeight')
grid_options = gb.build()

grid_response = AgGrid(
    resultados[list(columnas_visibles) + ["_fila_real"]],
    gridOptions=grid_options,
    update_mode=GridUpdateMode.SELECTION_CHANGED,
    enable_enterprise_modules=False,
    fit_columns_on_grid_load=True,
    height=400,
    theme="streamlit"
)

# --- DETECCIÓN DE CLIC ---
selected = grid_response.get("selected_rows")
if selected and len(selected) > 0:
    fila_idx_real = selected[0].get("_fila_real")
    if fila_idx_real is not None:
        st.session_state["fila_seleccionada_idx"] = fila_idx_real

# --- MOSTRAR DETALLES EN EXPANDER ---
if st.session_state.get("fila_seleccionada_idx") is not None:
    fila_idx = st.session_state["fila_seleccionada_idx"]
    try:
        registro = df.loc[fila_idx]
        with st.expander(f"📋 **Detalles de {registro[columnas_visibles[0]]}**", expanded=True):
            for col, val in registro.items():
                if col == df.columns[0] and pd.api.types.is_numeric_dtype(val):
                    val = int(val)
                st.markdown(f"<span style='color:#C67FAE; font-weight:bold'>{col}:</span> {val}", unsafe_allow_html=True)
    except Exception as e:
        st.warning(f"No se pudo mostrar los detalles: {e}")

# --- BOTÓN DE ACTUALIZAR ---
if st.button("🔁 Actualizar después de modificar el Excel"):
    if hasattr(st, "cache_data"):
        st.cache_data.clear()
    st.session_state["actualizar_flag"] = True  # activar flag para rerun seguro

# --- EJECUTAR rerun de manera segura ---
if st.session_state.get("actualizar_flag"):
    st.session_state["actualizar_flag"] = False
    st.experimental_rerun()

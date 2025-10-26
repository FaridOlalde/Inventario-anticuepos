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
            df = pd.read_excel(xls, hoja, header=5)  # fila 6 = header=5
            df["Caja"] = hoja
            dataframes.append(df)
        if not dataframes:
            return pd.DataFrame()
        return pd.concat(dataframes, ignore_index=True)
    except Exception as e:
        st.error(f"No se pudo cargar el archivo desde Drive: {e}")
        return pd.DataFrame()

# --- CONFIGURACIÓN DE LA PÁGINA ---
st.set_page_config(page_title="Inventario de Anticuerpos", layout="wide")
st.title("🔬 Inventario de Anticuerpos")
st.caption("Busca los anticuerpos por nombre o caja. Haz clic en cualquier fila para ver los detalles.")

# --- CARGAR DATOS ---
df = cargar_datos_drive()
if df.empty:
    st.stop()

# --- BÚSQUEDA ---
busqueda = st.text_input("🔎 Escribe el nombre del anticuerpo o Caja:", "").strip()

if busqueda:
    resultados = df[df.apply(lambda fila: fila.astype(str).str.contains(busqueda, case=False).any(), axis=1)]
else:
    resultados = df.copy()

# --- COLUMNAS VISIBLES (B y C) ---
if len(df.columns) >= 3:
    columnas_visibles = df.columns[1:3]
else:
    columnas_visibles = df.columns

st.write(f"Se encontraron **{len(resultados)}** resultados para: `{busqueda}`" if busqueda else "Mostrando todos los registros disponibles")

# --- CONFIGURAR TABLA INTERACTIVA ---
gb = GridOptionsBuilder.from_dataframe(resultados[columnas_visibles])
gb.configure_selection('single', use_checkbox=False)
gb.configure_grid_options(domLayout='autoHeight')
grid_options = gb.build()

# --- MOSTRAR TABLA ---
grid_response = AgGrid(
    resultados[columnas_visibles],
    gridOptions=grid_options,
    update_mode=GridUpdateMode.SELECTION_CHANGED,
    enable_enterprise_modules=False,
    fit_columns_on_grid_load=True,
    height=400,
    theme="streamlit",  # opciones: "streamlit", "material", "balham", etc.
)

# --- DETECCIÓN DE CLIC Y MOSTRAR MODAL ---
selected = grid_response['selected_rows']

# --- DETECCIÓN DE CLIC Y MOSTRAR MODAL ---
selected = grid_response['selected_rows']

if selected is not None and len(selected) > 0:
    fila = selected[0]
    idx = resultados[resultados[columnas_visibles[0]] == fila[columnas_visibles[0]]].index[0]
    registro = resultados.iloc[idx]


    with st.modal(f"📋 Detalle de {registro[columnas_visibles[0]]}"):
        for col, val in registro.items():
            st.markdown(f"**{col}:** {val}")
        if st.button("Cerrar"):
            st.rerun()

# --- BOTÓN DE ACTUALIZAR ---
if st.button("🔁 Actualizar los datos"):
    st.cache_data.clear()
    st.rerun()

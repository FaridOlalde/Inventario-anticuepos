import warnings
from urllib3.exceptions import NotOpenSSLWarning
warnings.filterwarnings("ignore", category=NotOpenSSLWarning)

import streamlit as st
import pandas as pd
import requests
from io import BytesIO


FILE_ID = "1TVnBvEjwY0Alywyp75QTwWVw0yqdWJaV"
URL = f"https://drive.google.com/uc?export=download&id={FILE_ID}"


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
            df["Caja"] = hoja
            dataframes.append(df)
        if not dataframes:
            return pd.DataFrame()
        return pd.concat(dataframes, ignore_index=True)
    except Exception as e:
        st.error(f"No se pudo cargar el archivo desde Drive: {e}")
        return pd.DataFrame()


st.set_page_config(page_title="Inventario de Anticuerpos", layout="wide")
st.title("🔬 Inventario de Anticuerpos")
st.caption("Busca los anticuerpos por nombre o caja. Los datos se actualizan automáticamente desde Google Drive.")


df = cargar_datos_drive()
if df.empty:
    st.stop()


busqueda = st.text_input("🔎 Escribe el nombre del anticuerpo o Caja:", "").strip()

# --- FILTRO DE RESULTADOS ---
if busqueda:
    resultados = df[df.apply(lambda fila: fila.astype(str).str.contains(busqueda, case=False).any(), axis=1)]
else:
    resultados = df.copy()


if len(df.columns) >= 3:
    columnas_visibles = df.columns[1:3]
else:
    columnas_visibles = df.columns


st.write(f"Se encontraron **{len(resultados)}** resultados para: `{busqueda}`" if busqueda else "Mostrando todos los registros disponibles")


st.write("### Resultados")
st.dataframe(resultados[columnas_visibles].reset_index(drop=True), use_container_width=True)


columna_principal = columnas_visibles[0]
opciones = resultados[columna_principal].dropna().unique()

seleccion = st.selectbox("👆 Selecciona un anticuerpo para ver detalles:", opciones if len(opciones) > 0 else [])

if seleccion:
    fila_detalle = resultados[resultados[columna_principal] == seleccion].iloc[0]

    st.markdown("### 📋 Detalle completo")
    for col, val in fila_detalle.items():
        st.markdown(f"**{col}:** {val}")


if st.button("🔁 Actualizar los datos"):
    st.cache_data.clear()
    st.experimental_rerun()

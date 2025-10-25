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
st.caption("Busca anticuerpos por nombre o tipo celular (Caja). Los datos se actualizan automáticamente desde Google Drive.")

df = cargar_datos_drive()

if df.empty:
    st.stop()

busqueda = st.text_input("🔎 Escribe el nombre del anticuerpo o Caja:", "")

if busqueda:
    resultados = df[df.apply(lambda fila: fila.astype(str).str.contains(busqueda, case=False).any(), axis=1)]
else:
    resultados = df

st.write(f"Se encontraron **{len(resultados)}** resultados para: `{busqueda}`" if busqueda else "Mostrando todos los registros disponibles")
st.dataframe(resultados.reset_index(drop=True), use_container_width=True)

if "reload" not in st.session_state:
    st.session_state["reload"] = False

if st.button("🔁 Recargar datos desde Excel"):
    st.cache_data.clear()
    st.session_state["reload"] = not st.session_state["reload"]


df = cargar_datos_drive()



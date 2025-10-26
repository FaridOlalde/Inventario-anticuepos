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
st.caption("Busca los anticuerpos por nombre o caja. Haz clic en cualquier fila para ver todos los detalles.")

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

st.write(
    f"Se encontraron **{len(resultados)}** resultados para: `{busqueda}`"
    if busqueda else
    "Mostrando todos los registros disponibles"
)

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
    theme="streamlit",
)

# --- DETECCIÓN DE CLIC Y MOSTRAR MODAL FLOTANTE ---
selected = grid_response.get("selected_rows", [])

if selected and len(selected) > 0:
    row_index = int(selected[0]["_selectedRowNodeInfo"]["nodeId"])
    registro = resultados.iloc[row_index]

    # Modal flotante HTML + CSS + JS
    st.markdown(f"""
    <style>
    /* Fondo modal */
    .modal {{
      display: block;
      position: fixed;
      z-index: 9999;
      left: 0;
      top: 0;
      width: 100%;
      height: 100%;
      overflow: auto;
      background-color: rgba(0,0,0,0.4);
    }}
    /* Contenido del modal */
    .modal-content {{
      background-color: #f9f9f9;
      margin: 5% auto;
      padding: 20px;
      border: 1px solid #888;
      width: 60%;
      max-height: 70%;
      overflow-y: auto;
      border-radius: 10px;
      box-shadow: 0px 0px 15px rgba(0,0,0,0.3);
    }}
    .close-btn {{
      color: #aaa;
      float: right;
      font-size: 28px;
      font-weight: bold;
      cursor: pointer;
    }}
    .close-btn:hover {{
      color: black;
    }}
    </style>

    <div class="modal" id="myModal">
      <div class="modal-content">
        <span class="close-btn" onclick="document.getElementById('myModal').style.display='none'">&times;</span>
        <h3>Detalle de {registro[columnas_visibles[0]]}</h3>
        <hr>
        {"<br>".join([f"<b>{col}:</b> {val}" for col, val in registro.items()])}
      </div>
    </div>

    <script>
    // Cerrar modal con tecla ESC
    document.addEventListener('keydown', function(event) {{
        if(event.key === "Escape") {{
            document.getElementById('myModal').style.display='none';
        }}
    }});
    </script>
    """, unsafe_allow_html=True)

# --- BOTÓN DE ACTUALIZAR ---
if st.button("🔁 Actualizar los datos"):
    st.cache_data.clear()
    st.rerun()

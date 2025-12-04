import streamlit as st
import pandas as pd
from utils import read_sheet, append_row, ensure_headers

SHEET = "config"

EXPECTED_HEADERS = ["Tipo", "Valor"]

def show_config():
    ensure_headers(SHEET, EXPECTED_HEADERS)

    st.header("⚙ Configuración")

    tipo = st.text_input("Tipo de parámetro")
    valor = st.text_input("Valor")

    if st.button("Guardar Configuración"):
        append_row(SHEET, [tipo, valor])
        st.success("Guardado.")
        st.rerun()

    st.subheader("Datos actuales")
    df = pd.DataFrame(read_sheet(SHEET))
    if not df.empty:
        st.dataframe(df, width="stretch")

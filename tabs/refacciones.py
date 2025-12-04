import streamlit as st
from utils import read_sheet, append_row, ensure_headers
import pandas as pd

SHEET = "refacciones"

EXPECTED_HEADERS = ["Fecha", "Refaccion", "Cantidad", "Descripcion"]

def show_refacciones():

    ensure_headers(SHEET, EXPECTED_HEADERS)

    st.header("🔩 Refacciones")

    df = pd.DataFrame(read_sheet(SHEET))

    st.subheader("Agregar Refacción")

    nombre = st.text_input("Refacción")
    cantidad = st.number_input("Cantidad", min_value=1)
    desc = st.text_area("Descripción")

    if st.button("Guardar"):
        row = [
            datetime.now().strftime("%Y-%m-%d"),
            nombre,
            cantidad,
            desc
        ]
        append_row(SHEET, row)
        st.success("Guardada.")
        st.rerun()

    st.subheader("Inventario")
    df = pd.DataFrame(read_sheet(SHEET))
    if not df.empty:
        st.dataframe(df, width="stretch")

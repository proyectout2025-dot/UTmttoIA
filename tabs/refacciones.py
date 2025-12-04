import streamlit as st
import pandas as pd
from utils import read_sheet, append_row


def show_refacciones():
    st.header("🔩 Refacciones – Inventario")

    data = read_sheet("refacciones")
    if not data:
        st.info("No hay refacciones registradas.")
        return

    df = pd.DataFrame(data)
    st.dataframe(df, width="stretch")

    st.subheader("➕ Agregar refacción")

    col1, col2 = st.columns(2)

    with col1:
        nombre = st.text_input("Nombre")
        numero_parte = st.text_input("Número de parte")

    with col2:
        ubicacion = st.text_input("Ubicación")
        cantidad = st.number_input("Cantidad", min_value=0, step=1)

    if st.button("💾 Guardar refacción"):
        row = [nombre, numero_parte, ubicacion, cantidad]

        if append_row("refacciones", row):
            st.success("Refacción guardada.")
            st.rerun()

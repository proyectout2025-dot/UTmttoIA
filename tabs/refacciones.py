# ===========================================
# /tabs/refacciones.py — FINAL
# ===========================================

import streamlit as st
import pandas as pd
from utils import read_sheet, append_row

SHEET = "refacciones"

def load_df():
    data = read_sheet(SHEET)
    if not data:
        return pd.DataFrame()
    return pd.DataFrame(data)

def show_refacciones():
    st.header("🔩 Refacciones")

    df = load_df()

    st.subheader("📦 Registrar nueva refacción")
    col1, col2 = st.columns(2)

    with col1:
        num_parte = st.text_input("Número de parte")
        parte_cliente = st.text_input("Parte del cliente")
        locacion = st.text_input("Ubicación")
    with col2:
        existentes = st.number_input("Existencias", min_value=0, step=1)
        descripcion = st.text_area("Descripción")

    if st.button("💾 Guardar refacción"):
        row = [
            num_parte,
            parte_cliente,
            descripcion,
            locacion,
            existentes
        ]
        append_row(SHEET, row)
        st.success("Refacción registrada.")
        st.rerun()

    st.subheader("📋 Inventario actual")
    if df.empty:
        st.info("No hay refacciones registradas.")
    else:
        st.dataframe(df, width="stretch")

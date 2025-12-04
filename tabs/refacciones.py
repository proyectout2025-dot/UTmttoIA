import streamlit as st
import pandas as pd
from datetime import datetime
from utils import read_sheet, append_row

SHEET = "refacciones"

def show_refacciones():
    st.header("🔩 Refacciones — Inventario")

    data = read_sheet(SHEET)
    df = pd.DataFrame(data) if data else pd.DataFrame()

    st.subheader("📋 Inventario actual")
    if df.empty:
        st.info("No hay refacciones registradas.")
    else:
        st.dataframe(df, width="stretch")

    st.subheader("➕ Agregar refacción")

    with st.form("frm_ref", clear_on_submit=True):
        num_parte = st.text_input("Número de parte")
        parte_cliente = st.text_input("Parte del cliente")
        ubicacion = st.text_input("Ubicación")
        existencias = st.number_input("Existencias", min_value=0, step=1)
        guardar = st.form_submit_button("Guardar refacción")

    if guardar:
        row = [
            datetime.now().strftime("%Y-%m-%d"),
            num_parte,
            parte_cliente,
            "",
            ubicacion,
            existencias,
            ""
        ]
        if append_row(SHEET, row):
            st.success("Refacción guardada.")
            st.rerun()

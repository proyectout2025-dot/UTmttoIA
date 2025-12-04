# tabs/refacciones.py
import streamlit as st
import pandas as pd
from utils import read_sheet, append_row, get_gs_client, SHEET_URL

SHEET = "refacciones"

def show_refacciones():
    st.header("🔩 Refacciones — Inventario")

    data = read_sheet(SHEET) or []
    df = pd.DataFrame(data) if data else pd.DataFrame()

    st.subheader("📋 Inventario actual")
    if df.empty:
        st.info("No hay refacciones registradas.")
    else:
        st.dataframe(df, width="stretch")

    st.markdown("---")
    st.subheader("➕ Agregar refacción")

    with st.form("form_ref", clear_on_submit=True):
        num_parte = st.text_input("Número de parte", key="rf_num")
        parte_cliente = st.text_input("Parte del cliente", key="rf_cliente")
        ubicacion = st.text_input("Ubicación", key="rf_ubic")
        existentes = st.number_input("Existencias", min_value=0, step=1, key="rf_exist")
        guardar = st.form_submit_button("Guardar refacción", key="rf_save")

    if guardar:
        row = [
            datetime.now().strftime("%Y-%m-%d"),
            num_parte,
            parte_cliente,
            "",  # descripcion
            ubicacion,
            existentes,
            ""   # evidencia id
        ]
        ok = append_row(SHEET, row)
        if ok:
            st.success("Refacción guardada.")
            st.experimental_rerun()
        else:
            st.error("No se pudo guardar la refacción.")

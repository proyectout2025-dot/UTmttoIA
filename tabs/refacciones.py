# tabs/refacciones.py
import streamlit as st
import pandas as pd
from datetime import datetime
from utils import read_sheet, append_row, ensure_headers

SHEET = "refacciones"
ensure_headers(SHEET, ["Fecha","Refaccion","Cantidad","Descripcion","Comentarios","Evidencia_ID"])

def show_refacciones():
    st.header("🔩 Refacciones — Inventario")
    data = read_sheet(SHEET) or []
    df = pd.DataFrame(data) if data else pd.DataFrame()

    st.subheader("Agregar refacción")
    with st.form("form_ref", clear_on_submit=True):
        nombre = st.text_input("Refacción", key="r_name")
        cantidad = st.number_input("Cantidad", min_value=0, step=1, key="r_qty")
        descripcion = st.text_area("Descripción", key="r_desc")
        comentarios = st.text_area("Comentarios (opcional)", key="r_com")
        guardar = st.form_submit_button("Guardar refacción", key="r_save")
    if guardar:
        row = [
            datetime.now().strftime("%Y-%m-%d"),
            nombre,
            cantidad,
            descripcion,
            comentarios,
            ""  # Evidencia_ID (vacío por ahora)
        ]
        ok = append_row(SHEET, row)
        if ok:
            st.success("Refacción guardada.")
            st.rerun()
        else:
            st.error("No se pudo guardar la refacción.")

    st.divider()
    st.subheader("Inventario actual")
    if df.empty:
        st.info("No hay refacciones registradas.")
    else:
        st.dataframe(df, use_container_width=True)

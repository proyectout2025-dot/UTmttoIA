# tabs/config.py
import streamlit as st
import pandas as pd
from utils import read_sheet, append_row, get_gs_client, SHEET_URL

SHEET = "config"

def show_config():
    st.header("⚙️ Configuración")

    data = read_sheet(SHEET) or []
    if data:
        st.subheader("📋 Valores guardados")
        st.dataframe(pd.DataFrame(data), width="stretch")
    else:
        st.info("No hay parámetros en config.")

    st.markdown("---")
    st.subheader("➕ Agregar equipo / técnico")

    with st.form("form_cfg", clear_on_submit=True):
        equipo = st.text_input("Nuevo equipo", key="cfg_equipo")
        tecnico = st.text_input("Nuevo técnico", key="cfg_tecnico")
        guardar = st.form_submit_button("Guardar en config", key="cfg_save")

    if guardar:
        # Guardamos como fila simple [Parametro, Valor] para compatibilidad
        if equipo:
            append_row(SHEET, ["equipo", equipo])
        if tecnico:
            append_row(SHEET, ["tecnico", tecnico])
        st.success("Configuración actualizada.")
        st.experimental_rerun()

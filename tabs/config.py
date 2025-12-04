import streamlit as st
import pandas as pd
from utils import read_sheet, append_row


def show_config():
    st.header("⚙️ Configuración")

    config = read_sheet("config")
    df = pd.DataFrame(config)

    st.subheader("📦 Equipos y Técnicos Registrados")
    st.dataframe(df, width="stretch")

    st.divider()

    # ---------------------------
    st.subheader("➕ Agregar Equipo")
    new_equipo = st.text_input("Nuevo Equipo:")
    if st.button("Guardar Equipo"):
        append_row("config", [new_equipo, ""])
        st.success("Equipo agregado.")
        st.rerun()

    # ---------------------------
    st.subheader("➕ Agregar Técnico")
    new_tec = st.text_input("Nuevo Técnico:")
    if st.button("Guardar Técnico"):
        append_row("config", ["", new_tec])
        st.success("Técnico agregado.")
        st.rerun()

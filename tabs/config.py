import streamlit as st
from utils import read_sheet, append_row


def show_config():
    st.header("⚙️ Configuración del Sistema")

    # Mostrar datos actuales
    config_data = read_sheet("config")

    if config_data:
        st.subheader("📋 Datos actuales")
        st.dataframe(config_data, width="stretch")

    st.divider()
    st.subheader("➕ Agregar Equipo / Técnico")

    col1, col2 = st.columns(2)

    with col1:
        equipo = st.text_input("Nuevo equipo")

    with col2:
        tecnico = st.text_input("Nuevo técnico")

    if st.button("💾 Guardar en configuración"):
        append_row("config", [equipo, tecnico])
        st.success("Configuración actualizada.")
        st.rerun()

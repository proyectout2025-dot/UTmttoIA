import streamlit as st
from tabs.mantenimientos import show_mantenimientos
from tabs.refacciones import show_refacciones
from tabs.config import show_config

st.set_page_config(page_title="Sistema Integral", layout="wide")

st.title("Sistema Integral de Mantenimientos")

menu = st.sidebar.selectbox(
    "Selecciona una opción",
    ["Mantenimientos", "Refacciones", "Config"]
)

if menu == "Mantenimientos":
    show_mantenimientos()

elif menu == "Refacciones":
    show_refacciones()

elif menu == "Config":
    show_config()

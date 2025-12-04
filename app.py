# app.py
import streamlit as st
from tabs.mantenimientos import show_mantenimientos
from tabs.refacciones import show_refacciones
from tabs.config import show_config
import setup_sheets

st.set_page_config(page_title="Sistema de Mantenimiento UT", layout="wide")
st.title("🔧 Sistema de Mantenimiento UT — IA")

tabs = st.tabs(["🛠 Mantenimientos", "🔩 Refacciones", "⚙️ Configuración", "🧩 Setup Inicial"])

with tabs[0]:
    show_mantenimientos()

with tabs[1]:
    show_refacciones()

with tabs[2]:
    show_config()

with tabs[3]:
    setup_sheets.run_setup()

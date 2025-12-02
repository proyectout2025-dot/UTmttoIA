import streamlit as st
from tabs.mantenimientos import show_mantenimientos
from tabs.refacciones import show_refacciones
from tabs.config import show_config

st.set_page_config(page_title="Sistema de Mantenimiento", layout="wide")

st.title("📘 Sistema de Mantenimiento Industrial")

tabs = st.tabs(["🛠 Mantenimientos", "🔧 Refacciones", "⚙️ Config"])

with tabs[0]:
    show_mantenimientos()

with tabs[1]:
    show_refacciones()

with tabs[2]:
    show_config()

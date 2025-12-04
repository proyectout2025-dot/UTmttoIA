import streamlit as st
from tabs.mantenimientos import show_mantenimientos
from tabs.refacciones import show_refacciones
from tabs.config import show_config

st.set_page_config(page_title="Sistema de Mantenimientos", layout="wide")
st.title("🔧 Sistema de Mantenimiento UT — IA")

tabs = st.tabs([
    "🛠 Mantenimientos",
    "🔩 Refacciones",
    "⚙️ Configuración"
])

with tabs[0]:
    show_mantenimientos()

with tabs[1]:
    show_refacciones()

with tabs[2]:
    show_config()

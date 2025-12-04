import streamlit as st

from tabs.mantenimientos import show_mantenimientos
from tabs.refacciones import show_refacciones
from tabs.config import show_config

st.set_page_config(page_title="Sistema de Mantenimientos", layout="wide")
st.title("🔧 Sistema de Mantenimiento UT — IA")

tab1, tab2, tab3 = st.tabs([
    "🛠 Mantenimientos",
    "🔩 Refacciones",
    "⚙️ Configuración"
])

with tab1:
    show_mantenimientos()

with tab2:
    show_refacciones()

with tab3:
    show_config()

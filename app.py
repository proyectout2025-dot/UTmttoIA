# app.py
import streamlit as st

# Importar pestañas
from tabs.mantenimientos import show_mantenimientos
from tabs.refacciones import show_refacciones
from tabs.config import show_config

# Importar módulo temporal de setup
import setup_sheets


st.set_page_config(
    page_title="Sistema de Mantenimientos",
    layout="wide",
)

st.title("🔧 Sistema de Mantenimiento UT — IA")

# Crear pestañas
tabs = st.tabs([
    "🛠 Mantenimientos",
    "🔩 Refacciones",
    "⚙️ Configuración",
    "🧩 Setup Inicial"
])

# Pestaña: Mantenimientos
with tabs[0]:
    show_mantenimientos()

# Pestaña: Refacciones
with tabs[1]:
    show_refacciones()

# Pestaña: Configuración
with tabs[2]:
    show_config()

# Pestaña: Setup Inicial
with tabs[3]:
    setup_sheets.run_setup()

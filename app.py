# app.py
import streamlit as st

# Importar pestañas
from tabs.mantenimientos import show_mantenimientos
from tabs.refacciones import show_refacciones
from tabs.config import show_config

# Importar utilidades
from utils import ensure_headers

# ================================
# 🚀 CONFIGURACIÓN GENERAL
# ================================
st.set_page_config(
    page_title="Sistema de Mantenimiento UT — IA",
    layout="wide",
)

st.title("🔧 Sistema de Mantenimiento UT — IA")


# ================================
# 🛡 AUTO-FIX DE ENCABEZADOS (solo 1 vez)
# ================================
# Esto evita errores 429 y asegura que todas las hojas tengan encabezados correctos
ensure_headers("mantenimientos", [
    "Fecha", "Equipo", "Descripcion", "Realizado_por",
    "estatus", "tiempo_hrs", "hora_inicio", "hora_fin"
])

ensure_headers("checkin_activos", [
    "Equipo", "Realizado_por", "hora_inicio"
])

ensure_headers("refacciones", [
    "Fecha", "Refaccion", "Cantidad", "Descripcion"
])

ensure_headers("config", [
    "Tipo", "Valor"
])


# ================================
# 📌 CREACIÓN DE TABS
# ================================
tabs = st.tabs([
    "🛠 Mantenimientos",
    "🔩 Refacciones",
    "⚙️ Configuración",
])

# Pestaña: Mantenimientos
with tabs[0]:
    show_mantenimientos()

# Pestaña: Refacciones
with tabs[1]:
    show_refacciones()

# Pestaña: Config
with tabs[2]:
    show_config()

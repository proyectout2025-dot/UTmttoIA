# app.py
import streamlit as st

from tabs.mantenimientos import show_mantenimientos
from tabs.refacciones import show_refacciones
from utils import ensure_headers

# Asegurar encabezados UNA vez al inicio (escritura directa)
ensure_headers("mantenimientos", ["Fecha","Equipo","Descripcion","Realizado_por","estatus","tiempo_hrs","hora_inicio","hora_fin"])
ensure_headers("checkin_activos", ["Equipo","Realizado_por","hora_inicio","Tipo"])
ensure_headers("refacciones", ["Fecha","Refaccion","Cantidad","Descripcion","Comentarios","Evidencia_ID"])
ensure_headers("config", ["Tipo","Valor"])

st.set_page_config(page_title="Sistema de Mantenimiento UT", layout="wide")
st.title("🔧 Sistema de Mantenimiento UT — IA")

tabs = st.tabs(["🛠 Mantenimientos", "🔩 Refacciones", "⚙️ Configuración"])

with tabs[0]:
    show_mantenimientos()

with tabs[1]:
    show_refacciones()

with tabs[2]:
    st.info("Configuración mínima (usamos listas fijas en la versión estable).")

# app.py
import streamlit as st
from tabs.mantenimientos import show_mantenimientos

st.set_page_config(page_title="Sistema de Mantenimiento", layout="wide")
st.title("📘 Sistema de Mantenimiento")

tabs = st.tabs(["🛠 Mantenimientos", "🔧 Refacciones", "⚙️ Config"])

with tabs[0]:
    show_mantenimientos()

with tabs[1]:
    st.header("🔧 Refacciones")
    st.info("Pestaña Refacciones - por implementar (puedo generarla si la deseas).")

with tabs[2]:
    st.header("⚙️ Config")
    st.info("Pestaña Config - por implementar (subida de manuales, etc.).")

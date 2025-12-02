import streamlit as st
from utils import get_sheet, add_mantenimiento
from tabs.mantenimiento import mantenimiento_tab

st.set_page_config(page_title="UTM Mantenimiento IA", layout="wide")

# Cargar hojas
tabs = {
    "Mantenimientos": "mantenimientos",
    "Refacciones": "refacciones",
    "Configuración": "config"
}

sheet_dict = {}
for name, sheet_name in tabs.items():
    try:
        sheet_dict[name] = get_sheet(sheet_name)
    except Exception:
        sheet_dict[name] = None

# UI Tabs
menu = st.sidebar.radio("Menú", list(tabs.keys()))

if menu == "Mantenimientos":
    mantenimiento_tab(sheet_dict["Mantenimientos"])

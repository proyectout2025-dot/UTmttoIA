import streamlit as st
from tabs.mantenimientos import show_mantenimientos

st.set_page_config(page_title="Sistema de Mantenimiento", layout="wide")

tabs = st.tabs(["🛠 Mantenimientos"])

with tabs[0]:
    show_mantenimientos()

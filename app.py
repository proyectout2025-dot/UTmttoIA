import streamlit as st
from tabs.mantenimientos import show_mantenimientos

st.set_page_config(page_title="Mantenimientos UT", layout="wide")

show_mantenimientos()

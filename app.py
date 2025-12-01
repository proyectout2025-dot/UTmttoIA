import streamlit as st
from utils import read_sheet

st.set_page_config(page_title="Prueba Google Sheets", layout="wide")

st.title("🔧 Prueba de conexión con Google Sheets")

st.write("Intentando acceder a la hoja 'mantenimientos'...")

try:
    data = read_sheet("mantenimientos")
    st.success("✅ Google Sheets funciona correctamente")
    st.write("Datos recibidos:")
    st.write(data)

except Exception as e:
    st.error("❌ Error al acceder a Google Sheets")
    st.code(str(e))

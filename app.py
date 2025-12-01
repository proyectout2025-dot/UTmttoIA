import streamlit as st
from utils import read_sheet

st.title("🔍 Diagnóstico de Google Sheets")

st.write("Probando acceso a Google Sheets…")

try:
    # Intento de lectura simple
    data = read_sheet("config")
    st.success("✔ Conectado correctamente a Google Sheets.")
    st.write(data)

except Exception as e:
    st.error("❌ Error al acceder a Google Sheets")

    st.write("### 🔎 Error COMPLETO detectado:")
    st.code(repr(e))  # <-- imprime todo, siempre

    # Más diagnóstico
    import traceback
    full = traceback.format_exc()
    st.write("### 📄 Traceback completo:")
    st.code(full)

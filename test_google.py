import streamlit as st
from utils import read_sheet, append_sheet
import datetime

st.write("Probando lectura de sheet...")

try:
    df = read_sheet("mantenimientos")
    st.write(df)
    st.success("La lectura funcionó.")
except Exception as e:
    st.error(f"Error al leer: {e}")

st.write("Probando escritura...")

try:
    row = {
        "id": 999,
        "fecha": str(datetime.date.today()),
        "equipo": "PRUEBA",
        "descripcion": "Entrada de prueba",
        "realizado_por": "Sistema",
        "imagen_url": "",
        "estatus": "completado",
        "timestamp_registro": str(datetime.datetime.now())
    }
    append_sheet("mantenimientos", row)
    st.success("La escritura funcionó.")
except Exception as e:
    st.error(f"Error al escribir: {e}")


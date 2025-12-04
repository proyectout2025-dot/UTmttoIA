# tabs/refacciones.py
import streamlit as st
import pandas as pd
from utils import read_sheet, append_sheet, upload_file_to_drive

def show_refacciones():
    st.header("🔧 Refacciones")

    with st.form("form_refacciones", clear_on_submit=True):
        nombre = st.text_input("Nombre de la refacción")
        cantidad = st.number_input("Cantidad", min_value=1, value=1)
        ubicacion = st.text_input("Ubicación")
        responsable = st.text_input("Responsable")
        archivo = st.file_uploader("Adjuntar PDF (opcional)", type=["pdf"])

        guardar = st.form_submit_button("Guardar refacción")

    if guardar:
        file_id = ""
        if archivo:
            file_id = upload_file_to_drive(archivo, folder_name="Refacciones")
            if not file_id:
                st.error("No se pudo subir el archivo.")
                return

        row = {
            "Codigo": "",
            "Nombre": nombre,
            "Descripcion": "",
            "Ubicacion": ubicacion,
            "Stock": cantidad,
            "ArchivoID": file_id
        }
        ok = append_sheet("refacciones", row)
        if ok:
            st.success("Refacción guardada.")
        else:
            st.error("Error guardando refacción.")

    st.markdown("---")
    data = read_sheet("refacciones") or []
    if data:
        df = pd.DataFrame(data)
        st.dataframe(df, width="stretch")
    else:
        st.info("No hay refacciones registradas.")

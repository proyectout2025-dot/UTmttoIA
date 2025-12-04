# tabs/refacciones.py
import streamlit as st
import pandas as pd
from utils import read_sheet, append_sheet, upload_file_to_drive

SHEET = "refacciones"

def show_refacciones():
    st.header("🔩 Refacciones")

    with st.form("form_refacciones", clear_on_submit=True):
        num_parte = st.text_input("Número de parte", key="r_num")
        parte_cliente = st.text_input("Parte del cliente", key="r_cliente")
        ubicacion = st.text_input("Ubicación", key="r_ubic")
        existentes = st.number_input("Existencias", min_value=0, step=1, key="r_exist")
        archivo = st.file_uploader("Adjuntar PDF (opcional)", type=["pdf"], key="r_file")
        guardar = st.form_submit_button("Guardar refacción", key="r_guardar")

    if guardar:
        file_id = ""
        if archivo:
            file_id = upload_file_to_drive(archivo, folder_name="Refacciones")
            if not file_id:
                st.error("No se pudo subir el archivo.")
                return
        row = {
            "Numero_parte": num_parte,
            "Parte_cliente": parte_cliente,
            "Descripcion": "",
            "Ubicacion": ubicacion,
            "Existencias": existentes,
            "ArchivoID": file_id
        }
        ok = append_sheet(SHEET, row)
        if ok:
            st.success("Refacción guardada.")
        else:
            st.error("Error guardando refacción.")

    st.markdown("---")
    data = read_sheet(SHEET) or []
    if data:
        df = pd.DataFrame(data)
        st.dataframe(df, width="stretch")
    else:
        st.info("No hay refacciones registradas.")

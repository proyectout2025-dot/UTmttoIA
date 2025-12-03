# tabs/config.py
import streamlit as st
from utils import read_sheet, append_sheet, upload_file_to_drive

def show_config():
    st.header("⚙️ Archivos de Configuración")

    archivo = st.file_uploader("Subir archivo PDF de configuración", type=["pdf"], key="cfg_file")

    if st.button("Guardar archivo", key="cfg_save"):
        if archivo:
            pdf_id = upload_file_to_drive(archivo, folder_name="Config")
            if pdf_id:
                row = {
                    "Parametro": archivo.name,
                    "Valor": pdf_id
                }
                ok = append_sheet("config", row)
                if ok:
                    st.success("Archivo cargado ✔")
                else:
                    st.error("No se pudo guardar el registro en Sheets.")
            else:
                st.error("No se pudo subir el PDF a Drive.")
        else:
            st.error("Debes subir un PDF.")

    st.subheader("Archivos almacenados")
    data = read_sheet("config")
    if data:
        st.dataframe(data)
    else:
        st.info("No hay archivos guardados en configuración.")

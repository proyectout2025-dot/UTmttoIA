import streamlit as st
from utils import read_sheet, append_sheet, upload_file_to_drive

def show_config():
    st.header("⚙️ Archivos de Configuración")

    archivo = st.file_uploader("Subir archivo PDF de configuración", type=["pdf"])

    if st.button("Guardar archivo"):
        if archivo:
            pdf_url = upload_file_to_drive(archivo)
            append_sheet("config", [archivo.name, pdf_url])
            st.success("Archivo cargado ✔")
        else:
            st.error("Debes subir un PDF.")

    st.subheader("Archivos almacenados")
    data = read_sheet("config")
    st.dataframe(data)

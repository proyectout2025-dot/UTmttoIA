import streamlit as st
from utils import read_sheet, append_sheet, upload_file_to_drive

def show_mantenimientos():
    st.header("🛠 Registro de Mantenimientos")

    st.subheader("Agregar nuevo mantenimiento")

    equipo = st.text_input("Equipo")
    fecha = st.date_input("Fecha")
    descripcion = st.text_area("Descripción")
    archivo = st.file_uploader("Adjuntar PDF", type=["pdf"])

    if st.button("Guardar mantenimiento"):
        pdf_url = upload_file_to_drive(archivo) if archivo else ""
        append_sheet("mantenimientos", [str(equipo), str(fecha), descripcion, pdf_url])
        st.success("Registro guardado correctamente ✔")

    st.subheader("Histórico registrado")
    data = read_sheet("mantenimientos")
    st.dataframe(data)

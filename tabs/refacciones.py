import streamlit as st
from utils import read_sheet, append_sheet, upload_file_to_drive

def show_refacciones():
    st.header("🔧 Registro de Refacciones")

    st.subheader("Agregar nueva refacción")

    nombre = st.text_input("Nombre de la refacción")
    cantidad = st.number_input("Cantidad", min_value=1)
    proveedor = st.text_input("Proveedor")
    archivo = st.file_uploader("Adjuntar PDF", type=["pdf"])

    if st.button("Guardar refacción"):
        pdf_url = upload_file_to_drive(archivo) if archivo else ""
        append_sheet("refacciones", [nombre, cantidad, proveedor, pdf_url])
        st.success("Refacción guardada ✔")

    st.subheader("Inventario registrado")
    data = read_sheet("refacciones")
    st.dataframe(data)

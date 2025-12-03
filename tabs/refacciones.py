# tabs/refacciones.py
import streamlit as st
from utils import read_sheet, append_sheet, upload_file_to_drive

def show_refacciones():
    st.header("🔧 Registro de Refacciones")

    st.subheader("Agregar nueva refacción")

    nombre = st.text_input("Nombre de la refacción", key="ref_nombre")
    cantidad = st.number_input("Cantidad", min_value=1, key="ref_cantidad")
    proveedor = st.text_input("Proveedor", key="ref_proveedor")
    archivo = st.file_uploader("Adjuntar PDF (opcional)", type=["pdf"], key="ref_file")

    if st.button("Guardar refacción", key="ref_guardar"):
        pdf_id = ""
        if archivo:
            pdf_id = upload_file_to_drive(archivo, folder_name="Refacciones")
            if not pdf_id:
                st.error("No se pudo subir el PDF, la refacción no fue guardada.")
                return

        # Guardar (se usa append_sheet; internamente maneja dict->orden según headers)
        row = {
            "Fecha": "",  # opcional
            "Equipo": "",  # opcional
            "Refaccion": nombre,
            "Cantidad": cantidad,
            "Operacion": "",  # opcional
            "Responsable": proveedor,
            "ArchivoID": pdf_id
        }
        ok = append_sheet("refacciones", row)
        if ok:
            st.success("Refacción guardada ✔")
        else:
            st.error("Error guardando refacción en Google Sheets.")

    st.subheader("Inventario registrado")
    data = read_sheet("refacciones")
    if data:
        st.dataframe(data)
    else:
        st.info("No hay refacciones registradas.")

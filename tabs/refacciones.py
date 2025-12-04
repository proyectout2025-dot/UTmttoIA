import streamlit as st
from utils import append_row


def show_refacciones():
    st.header("🔩 Refacciones")

    nombre = st.text_input("Nombre de refacción")
    cantidad = st.number_input("Cantidad", min_value=0)
    descripcion = st.text_area("Descripción")

    if st.button("💾 Guardar refacción"):
        append_row("refacciones", [nombre, cantidad, descripcion])
        st.success("Refacción guardada.")
        st.rerun()

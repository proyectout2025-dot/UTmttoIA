import streamlit as st
from utils import add_mantenimiento

def mantenimiento_tab(df):
    st.title("Registro de Mantenimientos")

    with st.form("mtt_form"):
        equipo = st.text_input("Equipo")
        fecha = st.date_input("Fecha del mantenimiento")
        tecnico = st.text_input("Técnico responsable")
        descripcion = st.text_area("Descripción del trabajo realizado")

        submitted = st.form_submit_button("Guardar mantenimiento")

        if submitted:
            if not equipo or not tecnico or not descripcion:
                st.error("Todos los campos son obligatorios.")
            else:
                data = {
                    "equipo": equipo,
                    "fecha": str(fecha),
                    "tecnico": tecnico,
                    "descripcion": descripcion
                }
                add_mantenimiento(data)
                st.success("Mantenimiento guardado correctamente!")

    st.subheader("Historial")
    if df is not None and not df.empty:
        st.dataframe(df)
    else:
        st.info("Aún no hay registros de mantenimiento.")

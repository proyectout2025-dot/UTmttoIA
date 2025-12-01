import streamlit as st
from openai import OpenAI
from utils import read_sheet, append_sheet, upload_file_to_drive

st.set_page_config(page_title="Sistema Integral", layout="wide")

# -------------------------------------------------------
#  OPENAI CLIENT
# -------------------------------------------------------
client = OpenAI(api_key=st.secrets["openai"]["api_key"])

# -------------------------------------------------------
#  TABS
# -------------------------------------------------------
tab1, tab2, tab3, tab4 = st.tabs(["🤖 Chatbot", "📄 Manuales", "🛠 Mantenimientos", "🔧 Refacciones"])

# -------------------------------------------------------
# 1. CHATBOT
# -------------------------------------------------------
with tab1:
    st.header("Asistente basado en IA")

    st.write("Haz preguntas sobre el manual cargado. El sistema responderá basado en su contenido.")

    pregunta = st.text_area("Escribe tu pregunta")

    if st.button("Preguntar"):
        if pregunta.strip() == "":
            st.warning("Escribe una pregunta antes de continuar.")
        else:
            with st.spinner("Analizando..."):
                respuesta = client.chat.completions.create(
                    model="gpt-4o-mini",
                    messages=[
                        {"role": "system", "content": "Eres un asistente técnico experto en máquinas industriales. Responde con precisión basado en manuales del cliente."},
                        {"role": "user", "content": pregunta}
                    ],
                )
                st.success("Respuesta:")
                st.write(respuesta.choices[0].message.content)


# -------------------------------------------------------
# 2. MANUALES
# -------------------------------------------------------
with tab2:
    st.header("📄 Manuales Disponibles")
    st.write("Aquí puedes subir nuevos manuales en PDF o ver los existentes.")

    pdf = st.file_uploader("Cargar manual en PDF", type=["pdf"])

    if pdf:
        url = upload_file_to_drive(pdf)
        st.success("Manual cargado correctamente!")
        st.write("🔗 **Enlace al PDF:**")
        st.write(url)


# -------------------------------------------------------
# 3. MANTENIMIENTOS
# -------------------------------------------------------
with tab3:
    st.header("🛠 Registro de Mantenimientos")

    st.subheader("Agregar mantenimiento")

    col1, col2 = st.columns(2)

    with col1:
        fecha = st.date_input("Fecha del mantenimiento")
        descripcion = st.text_area("Descripción del trabajo realizado")

    with col2:
        tecnico = st.text_input("Técnico responsable")
        imagen = st.file_uploader("Foto (opcional)", type=["png", "jpg", "jpeg"])

    if st.button("Guardar mantenimiento"):
        if descripcion.strip() == "" or tecnico.strip() == "":
            st.warning("Los campos de descripción y técnico son obligatorios.")
        else:
            url_foto = upload_file_to_drive(imagen) if imagen else ""

            append_sheet(
                "mantenimientos",
                [
                    str(fecha),
                    descripcion,
                    tecnico,
                    url_foto
                ]
            )

            st.success("Mantenimiento registrado correctamente.")

    st.divider()
    st.subheader("Historial de mantenimientos")

    data = read_sheet("mantenimientos")
    st.dataframe(data, use_container_width=True)


# -------------------------------------------------------
# 4. REFACCIONES
# -------------------------------------------------------
with tab4:
    st.header("🔧 Inventario de Refacciones")

    data_refacciones = read_sheet("refacciones")
    st.dataframe(data_refacciones, use_container_width=True)

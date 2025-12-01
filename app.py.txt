import streamlit as st
from utils import read_sheet, append_sheet, upload_file_to_drive
from openai import OpenAI
import datetime
import io

st.set_page_config(page_title="Sistema Integral", layout="wide")
client = OpenAI()

# -----------------------------
# TABS
# -----------------------------
tab1, tab2, tab3, tab4 = st.tabs(["Chat del Manual", "Manuales", "Mantenimientos", "Refacciones"])


# -------------------------------------------------------
# TAB 1 - CHAT DEL MANUAL
# -------------------------------------------------------
with tab1:
    st.header("Chat del Manual")

    pregunta = st.text_area("Haz una pregunta sobre el manual:")

    if st.button("Preguntar"):
        respuesta = client.chat.completions.create(
            model="gpt-4.1-mini",
            messages=[
                {"role": "system", "content": "Eres un asistente experto en manuales técnicos."},
                {"role": "user", "content": pregunta}
            ]
        ).choices[0].message["content"]

        st.write("### Respuesta:")
        st.write(respuesta)


# -------------------------------------------------------
# TAB 2 - MANUALES
# -------------------------------------------------------
with tab2:
    st.header("Cargar Manual")

    pdf = st.file_uploader("Sube un manual en PDF", type="pdf")

    if pdf:
        file_bytes = pdf.read()
        uploaded = upload_file_to_drive(io.BytesIO(file_bytes), pdf.name)

        st.success("Manual subido correctamente.")
        st.json(uploaded)


# -------------------------------------------------------
# TAB 3 - MANTENIMIENTOS
# -------------------------------------------------------
with tab3:
    st.header("Registro de Mantenimientos")

    df = read_sheet("mantenimientos")
    st.dataframe(df)

    st.subheader("Agregar mantenimiento")

    equipo = st.text_input("Equipo")
    descripcion = st.text_area("Descripción")
    realizado = st.text_input("Realizado por")
    imagen = st.file_uploader("foto", type=["jpg", "png"])

    if st.button("Guardar"):
        row = {
            "id": len(df) + 1,
            "fecha": str(datetime.date.today()),
            "equipo": equipo,
            "descripcion": descripcion,
            "realizado_por": realizado,
            "imagen_url": "",
            "estatus": "completado",
            "timestamp_registro": str(datetime.datetime.now())
        }

        append_sheet("mantenimientos", row)
        st.success("Mantenimiento guardado.")


# -------------------------------------------------------
# TAB 4 - REFACCIONES
# -------------------------------------------------------
with tab4:
    st.header("Inventario de Refacciones")

    df2 = read_sheet("refacciones")
    st.dataframe(df2)

    st.subheader("Agregar refacción")

    num_parte = st.text_input("Número de parte")
    cliente = st.text_input("Parte del cliente")
    descripcion = st.text_input("Descripción")
    cantidad = st.number_input("Cantidad", 0)
    locacion = st.text_input("Locación")

    if st.button("Agregar refacción"):
        row2 = {
            "id": len(df2) + 1,
            "numero_parte": num_parte,
            "parte_cliente": cliente,
            "descripcion": descripcion,
            "cantidad_existente": cantidad,
            "locacion": locacion,
            "imagen_url": "",
            "timestamp_registro": str(datetime.datetime.now())
        }

        append_sheet("refacciones", row2)
        st.success("Refacción agregada.")

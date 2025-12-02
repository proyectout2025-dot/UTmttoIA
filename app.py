import streamlit as st
from openai import OpenAI
from utils import read_sheet, append_sheet

st.set_page_config(page_title="Chat – Mantenimiento", layout="wide")

# Inicializar cliente OpenAI
client = OpenAI(api_key=st.secrets["openai"]["api_key"])

# -----------------------------
# TAB 1: CHATBOT
# -----------------------------
st.title("🤖 Chatbot basado en tu manual")

manual_text = st.session_state.get("manual_text", None)

# Cargar el manual desde Google Sheet pestaña "config"
config = read_sheet("config")
if config is not None and len(config) > 0:
    manual_text = config.at[0, "manual"]
    st.session_state["manual_text"] = manual_text

if not manual_text:
    st.warning("⚠️ No hay manual cargado todavía. Ve a la pestaña CONFIG para subir uno.")
else:
    user_query = st.text_input("¿Qué deseas preguntar sobre el manual?")

    if user_query:
        with st.spinner("Consultando IA..."):
            response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {
                        "role": "system",
                        "content": f"Eres un asistente experto en mantenimiento. Responde únicamente con base en este manual:\n\n{manual_text}"
                    },
                    {"role": "user", "content": user_query}
                ]
            )
            answer = response.choices[0].message["content"]
            st.success(answer)

# -----------------------------
# TAB 2: MANUAL
# -----------------------------
st.header("📘 Manual cargado")

if manual_text:
    st.text_area("Contenido del manual:", manual_text, height=300)
else:
    st.info("No hay manual cargado aún.")

# -----------------------------
# TAB 3: MANTENIMIENTOS
# -----------------------------
st.header("🛠 Registrar mantenimiento")

with st.form("mnt_form"):
    fecha = st.date_input("Fecha")
    tarea = st.text_input("Descripción del mantenimiento")
    tecnico = st.text_input("Técnico responsable")

    enviar = st.form_submit_button("Guardar")

if enviar:
    append_sheet("mantenimientos", [str(fecha), tarea, tecnico])
    st.success("✔ Mantenimiento guardado")

# Mostrar historial
st.subheader("📄 Historial de mantenimientos")
mnt = read_sheet("mantenimientos")
if mnt is not None:
    st.dataframe(mnt)
else:
    st.info("No hay registros aún.")

# -----------------------------
# TAB 4: REFACCIONES
# -----------------------------
st.header("🔩 Refacciones")

ref = read_sheet("refacciones")
if ref is not None:
    st.dataframe(ref)
else:
    st.info("No hay refacciones registradas todavía.")

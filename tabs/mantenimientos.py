import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
from utils import read_sheet, append_sheet

SHEET = "base_datos_app"
WORKSHEET = "mantenimientos"


# -----------------------------
# Cargar datos desde Google Sheets
# -----------------------------
def _load_data():
    data = read_sheet(SHEET, WORKSHEET)
    if not data:
        return pd.DataFrame()
    return pd.DataFrame(data)


# -----------------------------
# Formulario para registrar mantenimiento
# -----------------------------
def _form_registro():
    st.subheader("📋 Registrar nuevo mantenimiento")

    with st.form("form_mantenimiento"):
        fecha = st.date_input("Fecha del mantenimiento")
        equipo = st.text_input("Equipo")
        descripcion = st.text_area("Descripción del trabajo realizado")

        realizado_por = st.text_input("Realizado por")
        estatus = st.selectbox("Estatus", ["Completado", "En proceso", "Pendiente"])
        tiempo_hrs = st.number_input("Tiempo invertido (Horas)", min_value=0.0, step=0.5)

        submit = st.form_submit_button("💾 Guardar registro")

    if submit:
        new_row = {
            "fecha": str(fecha),
            "equipo": equipo,
            "descripcion": descripcion,
            "realizado_por": realizado_por,
            "estatus": estatus,
            "tiempo_hrs": tiempo_hrs,
        }

        append_sheet(SHEET, WORKSHEET, new_row)
        st.success("✅ Mantenimiento guardado correctamente.")

        # Limpieza visual de campos
        st.rerun()


# -----------------------------
# Dashboard y reportes
# -----------------------------
def _dashboard(df: pd.DataFrame):
    st.subheader("📊 Dashboard de Mantenimientos")

    col1, col2, col3 = st.columns(3)
    col1.metric("Total de mantenimientos", len(df))
    col2.metric("Horas totales", df["tiempo_hrs"].astype(float).sum())
    col3.metric("Completados", len(df[df["estatus"] == "Completado"]))

    st.markdown("---")

    st.subheader("📈 Gráfica de horas por equipo")

    if "equipo" in df.columns and "tiempo_hrs" in df.columns:
        graf = df.groupby("equipo")["tiempo_hrs"].sum()

        fig, ax = plt.subplots()
        graf.plot(kind="bar", ax=ax)
        ax.set_ylabel("Horas")
        ax.set_title("Horas invertidas por equipo")
        st.pyplot(fig)
    else:
        st.warning("No hay datos suficientes para graficar.")


# -----------------------------
# Tabla de historial
# -----------------------------
def _historial(df: pd.DataFrame):
    st.subheader("📚 Historial de mantenimientos")
    st.dataframe(df, use_container_width=True)


# -----------------------------
# Vista principal de la pestaña
# -----------------------------
def show_mantenimientos():
    st.header("🛠 Mantenimientos — Registro y Reportes")

    df = _load_data()

    # Mostrar historial primero
    if df.empty:
        st.info("No hay datos registrados en *mantenimientos* todavía.")
    else:
        _historial(df)
        st.markdown("---")
        _dashboard(df)

    st.markdown("---")
    _form_registro()

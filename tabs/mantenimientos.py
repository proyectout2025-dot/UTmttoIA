import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
from datetime import datetime

from utils import (
    read_sheet,
    append_row,
    get_active_checkins,
    add_active_checkin,
    finalize_checkin
)

# ==========================
# LISTAS FIJAS (sin Sheets)
# ==========================
EQUIPOS = ["Equipo 1", "Equipo 2", "Equipo 3"]
TECNICOS = ["Técnico 1", "Técnico 2", "Técnico 3"]
TIPOS = ["Correctivo", "Preventivo", "Predictivo"]


# =====================================
# INTERFAZ PRINCIPAL
# =====================================
def show_mantenimientos():
    st.header("🛠 Sistema de Mantenimiento (Versión Estable)")

    # =====================================
    # CHECK-IN / CHECK-OUT (1 lectura fija)
    # =====================================
    st.subheader("⏱ Control de tiempos")

    equipo_sel = st.selectbox("Equipo", EQUIPOS, key="equipo_checkin")
    tecnico_sel = st.selectbox("Técnico", TECNICOS, key="tecnico_checkin")

    activos = get_active_checkins() or []
    activo = next((a for a in activos if a.get("Equipo") == equipo_sel), None)

    if activo:
        st.warning(f"🔴 Check-in activo desde: {activo.get('hora_inicio')}")

        if st.button("Finalizar Check-Out"):
            try:
                rownum = activos.index(activo) + 2
                if finalize_checkin(rownum):
                    st.success("Check-out registrado.")
                    st.rerun()
            except Exception as e:
                st.error(f"Error finalizando: {e}")

    else:
        if st.button("Iniciar Check-In"):
            add_active_checkin(equipo_sel, tecnico_sel)
            st.success("Check-in iniciado.")
            st.rerun()

    st.divider()

    # =====================================
    # REGISTRO MANUAL (sin lecturas)
    # =====================================
    st.subheader("📝 Registro Manual")

    fecha = st.date_input("Fecha", key="fecha_manual")
    equipo = st.selectbox("Equipo", EQUIPOS, key="equipo_manual")
    tipo = st.selectbox("Tipo de mantenimiento", TIPOS, key="tipo_manual")
    tecnico = st.selectbox("Técnico", TECNICOS, key="tecnico_manual")
    descripcion = st.text_area("Descripción", key="descripcion_manual")
    tiempo = st.number_input("Tiempo (hrs)", min_value=0.0, key="tiempo_manual")

    if st.button("Guardar", key="btn_manual"):
        row = [
            fecha.strftime("%Y-%m-%d"),
            equipo,
            tipo,
            tecnico,
            descripcion,
            tiempo,
            datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        ]
        append_row("mantenimientos", row)
        st.success("Guardado.")
        st.rerun()

    st.divider()

    # =====================================
    # HISTORIAL Y 1 SOLA GRAFICA
    # =====================================
    st.subheader("📊 Estadísticas")

    # Lectura única
    data = read_sheet("mantenimientos")

    if not data:
        st.info("No hay datos aún.")
        return

    df = pd.DataFrame(data)

    # Mostrar tabla
    st.dataframe(df, use_container_width=True)

    st.markdown("### Selecciona la gráfica a mostrar")

    grafica = st.selectbox(
        "Mostrar gráfica por:",
        ["Equipo", "Técnico", "Tipo de mantenimiento"],
        key="grafica_tipo"
    )

    fig, ax = plt.subplots()

    if grafica == "Equipo":
        df["Equipo"].value_counts().plot(kind="bar", ax=ax)
        ax.set_title("Mantenimientos por Equipo")

    elif grafica == "Técnico":
        df["Tecnico"].value_counts().plot(kind="bar", ax=ax)
        ax.set_title("Mantenimientos por Técnico")

    elif grafica == "Tipo de mantenimiento":
        df["Tipo"].value_counts().plot(kind="bar", ax=ax)
        ax.set_title("Mantenimientos por Tipo")

    st.pyplot(fig)

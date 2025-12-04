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


def show_mantenimientos():
    st.header("🛠 Mantenimientos")

    # =======================
    #   Configuración dinámica
    # =======================
    cfg = read_sheet("config")

    equipos = sorted({c["Equipo"] for c in cfg if c.get("Equipo")})
    tecnicos = sorted({c["Tecnico"] for c in cfg if c.get("Tecnico")})

    # ====================================
    #       CHECK-IN / CHECK-OUT
    # ====================================
    st.subheader("⏱ Control de tiempos")

    equipo_sel = st.selectbox("Equipo", equipos, key="equipo_checkin")
    tecnico_sel = st.selectbox("Técnico", tecnicos, key="tecnico_checkin")

    activos = get_active_checkins()
    activo = next((x for x in activos if x["Equipo"] == equipo_sel), None)

    if activo:
        st.warning(f"🔴 Check-in activo desde {activo['hora_inicio']}")

        if st.button("Finalizar Check-Out"):
            rownum = activos.index(activo) + 2
            if finalize_checkin(rownum):
                st.success("Check-out registrado.")
                st.rerun()
    else:
        if st.button("Iniciar Check-In"):
            add_active_checkin(equipo_sel, tecnico_sel)
            st.success("Check-in iniciado.")
            st.rerun()

    st.divider()

    # ====================================
    #      REGISTRO MANUAL
    # ====================================
    st.subheader("📝 Registro Manual")

    fecha = st.date_input("Fecha", key="fecha_manual")
    equipo = st.selectbox("Equipo (manual)", equipos, key="equipo_manual")
    tipo = st.selectbox("Tipo", ["Correctivo", "Preventivo", "Predictivo"], key="tipo_manual")
    tecnico = st.selectbox("Técnico", tecnicos, key="tecnico_manual")
    descripcion = st.text_area("Descripción", key="descripcion_manual")
    tiempo = st.number_input("Tiempo (hrs)", min_value=0.0, key="hrs_manual")

    if st.button("Guardar mantenimiento", key="guardar_manual"):
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
        st.success("Mantenimiento guardado.")
        st.rerun()

    st.divider()

    # ====================================
    #      HISTORIAL + GRÁFICAS
    # ====================================
    st.subheader("📚 Historial & Estadísticas")

    data = read_sheet("mantenimientos")
    if not data:
        st.info("No hay datos aún.")
        return

    df = pd.DataFrame(data)

    st.dataframe(df, use_container_width=True)

    # =======================
    #   GRAFICA 1
    # =======================
    st.subheader("📊 Mantenimientos por Tipo")

    if "Tipo" in df.columns:
        fig1, ax1 = plt.subplots()
        df["Tipo"].value_counts().plot(kind="bar", ax=ax1)
        ax1.set_title("Cantidad de mantenimientos por tipo")
        st.pyplot(fig1)

    # =======================
    #   GRAFICA 2
    # =======================
    st.subheader("📊 Horas trabajadas por Técnico")

    if "Tiempo" in df.columns and "Tecnico" in df.columns:
        horas_por_tecnico = df.groupby("Tecnico")["Tiempo"].sum()

        fig2, ax2 = plt.subplots()
        horas_por_tecnico.plot(kind="bar", ax=ax2)
        ax2.set_title("Horas trabajadas por técnico")
        st.pyplot(fig2)

    # =======================
    #   GRAFICA 3
    # =======================
    st.subheader("📊 Mantenimientos por Equipo")

    if "Equipo" in df.columns:
        fig3, ax3 = plt.subplots()
        df["Equipo"].value_counts().plot(kind="bar", ax=ax3)
        ax3.set_title("Mantenimientos por equipo")
        st.pyplot(fig3)

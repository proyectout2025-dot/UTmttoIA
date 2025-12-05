import streamlit as st
import pandas as pd
from datetime import datetime
from utils import (
    read_sheet,
    append_row,
    add_active_checkin,
    finalize_active_checkin,
    get_active_checkins
)

SHEET = "mantenimientos"

# Datos fijos para evitar lecturas
EQUIPOS = ["Equipo 1", "Equipo 2", "Equipo 3"]
TECNICOS = ["Técnico 1", "Técnico 2", "Técnico 3"]
TIPOS = ["Correctivo", "Preventivo", "Predictivo"]


def show_mantenimientos():
    st.header("🛠 Mantenimientos")

    st.subheader("⏱ Control de tiempo (Check-in / Check-out)")
    equipo_ci = st.selectbox("Equipo", EQUIPOS, key="ci_equipo")
    tecnico_ci = st.selectbox("Técnico", TECNICOS, key="ci_tecnico")
    tipo_ci = st.selectbox("Tipo de mantenimiento", TIPOS, key="ci_tipo")

    # -----------------------------
    # Obtener check-ins SOLO si el usuario lo pide
    # -----------------------------
    if st.button("🔄 Revisar estado del equipo", key="btn_refresh_estado"):
        st.session_state["checkin_cache"] = get_active_checkins()

    activos = st.session_state.get("checkin_cache", [])
    activo = next((a for a in activos if a.get("Equipo") == equipo_ci), None)

    # -----------------------------
    # Check-IN
    # -----------------------------
    if activo is None:
        if st.button("⏱ Iniciar Check-in", key="btn_start_ci"):
            add_active_checkin(equipo_ci, tecnico_ci, tipo_ci)
            st.success("Check-in iniciado.")
            st.stop()

    # -----------------------------
    # Check-OUT
    # -----------------------------
    else:
        st.warning(f"Equipo en mantenimiento desde {activo.get('hora_inicio')}")

        row_number = activos.index(activo) + 2  # +2 porque fila 1 = encabezados

        descripcion = st.text_area("Descripción (opcional)", key="desc_checkout")

        if st.button("✔ Finalizar Check-out", key="btn_end_ci"):
            ok = finalize_active_checkin(row_number, descripcion)
            if ok:
                st.success("Check-out finalizado.")
            st.stop()

    st.markdown("---")
    st.subheader("📝 Registro Manual de Mantenimiento")

    fecha = st.date_input("Fecha", key="m_fecha")
    equipo = st.selectbox("Equipo", EQUIPOS, key="m_equipo")
    tipo = st.selectbox("Tipo", TIPOS, key="m_tipo")
    tecnico = st.selectbox("Técnico", TECNICOS, key="m_tecnico")
    descripcion = st.text_area("Descripción", key="m_descripcion")
    tiempo = st.number_input("Tiempo (horas)", min_value=0.0, key="m_tiempo")

    if st.button("💾 Guardar mantenimiento manual", key="btn_save_manual"):
        row = [
            fecha.strftime("%Y-%m-%d"),
            equipo,
            descripcion,
            tecnico,
            "Manual",
            tiempo,
            "",
            ""
        ]
        append_row(SHEET, row)
        st.success("Guardado.")
        st.stop()

    st.markdown("---")

    # -----------------------------
    # Mostrar historial solo si el usuario lo pide
    # -----------------------------
    mostrar = st.checkbox("📄 Mostrar historial y estadísticas", value=False)
    if not mostrar:
        st.info("Activa esta casilla para ver historial (reduce lecturas y evita errores 429).")
        return

    data = read_sheet(SHEET)
    if not data:
        st.info("No hay datos registrados.")
        return

    df = pd.DataFrame(data)
    st.dataframe(df, width="stretch")

    # -----------------------------
    # Gráfica simple (solo una a la vez)
    # -----------------------------
    graf = st.selectbox("Ver gráfica por:", ["Equipo", "Técnico", "Tipo"], key="grafica_selector")

    if graf == "Equipo":
        chart = df.groupby("Equipo")["tiempo_hrs"].sum()
    elif graf == "Técnico":
        chart = df.groupby("Realizado_por")["tiempo_hrs"].sum()
    else:
        chart = df.groupby("estatus")["tiempo_hrs"].sum()

    st.bar_chart(chart)

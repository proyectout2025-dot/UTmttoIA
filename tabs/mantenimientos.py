import streamlit as st
import pandas as pd
from datetime import datetime
from utils import (
    read_sheet,
    append_row,
    add_active_checkin,
    finalize_active_checkin_by_rownum,
    get_active_checkins
)


SHEET = "mantenimientos"


# ==========================================================
#   LISTAS BASE
# ==========================================================
DEFAULT_EQUIPOS = ["Equipo 1", "Equipo 2", "Equipo 3"]
DEFAULT_TECNICOS = ["Wesley Cunningham", "Misael Lopez", "Eduardo Vazquez"]
TIPOS_MTTO = ["Correctivo", "Preventivo", "Predictivo"]


# ==========================================================
#   FUNCIÓN PRINCIPAL DE LA PESTAÑA
# ==========================================================
def show_mantenimientos():
    st.header("🛠 Mantenimientos – Registro, Tiempos e Historial")

    st.divider()
    st.subheader("⏱ Control de Tiempo (Check-In / Check-Out)")

    checkin_section()

    st.divider()
    st.subheader("📝 Registrar Mantenimiento Manual")

    registrar_mantenimiento_manual()

    st.divider()
    st.subheader("📊 Reporte y Gráficas")

    mostrar_reportes()


# ==========================================================
#   SECCIÓN CHECK-IN / CHECK-OUT
# ==========================================================
def checkin_section():
    activos = get_active_checkins()

    # --------------------------
    # Lista de equipos
    # --------------------------
    equipos_sheet = read_sheet("config")
    equipos = DEFAULT_EQUIPOS.copy()

    if equipos_sheet:
        for row in equipos_sheet:
            if row.get("equipo"):
                equipos.append(row["equipo"])

    equipos = list(sorted(set(equipos)))

    equipo_sel = st.selectbox("Seleccionar equipo", equipos, key="checkin_equipo")

    # --------------------------
    # Técnicos
    # --------------------------
    tecnicos = DEFAULT_TECNICOS.copy()
    if equipos_sheet:
        for row in equipos_sheet:
            if row.get("tecnico"):
                tecnicos.append(row["tecnico"])

    tecnicos = list(sorted(set(tecnicos)))

    tecnico_sel = st.selectbox("Realizado por", tecnicos, key="checkin_tecnico")

    # --------------------------
    # ACTIVIDAD
    # --------------------------
    activo = next(
        (a for a in activos if a.get("equipo") == equipo_sel),
        None
    )

    if activo:
        st.info(f"🔵 Check-IN activo desde: {activo.get('hora_inicio')}")

        if st.button("⏹ Finalizar Check-Out"):
            rownum = activos.index(activo) + 2

            ok = finalize_active_checkin_by_rownum(
                rownum,
                estatus="Completado",
                descripcion_override="Check-out automático"
            )

            if ok:
                st.success("Check-OUT completado.")
                st.rerun()

    else:
        if st.button("⏱ Iniciar Check-In"):
            add_active_checkin(equipo_sel, tecnico_sel)
            st.success("Check-IN iniciado.")
            st.rerun()


# ==========================================================
#   REGISTRO MANUAL DE MANTENIMIENTO
# ==========================================================
def registrar_mantenimiento_manual():
    col1, col2, col3 = st.columns(3)

    with col1:
        fecha = st.date_input("Fecha", datetime.now(), key="manual_fecha")

    # Equipos
    equipos_sheet = read_sheet("config")
    equipos = DEFAULT_EQUIPOS.copy()
    if equipos_sheet:
        for row in equipos_sheet:
            if row.get("equipo"):
                equipos.append(row["equipo"])

    equipos = list(sorted(set(equipos)))

    with col2:
        equipo = st.selectbox("Equipo", equipos, key="manual_equipo")

    with col3:
        tipo = st.selectbox("Tipo de mantenimiento", TIPOS_MTTO, key="manual_tipo")

    col4, col5 = st.columns(2)

    # Técnicos
    tecnicos = DEFAULT_TECNICOS.copy()
    if equipos_sheet:
        for row in equipos_sheet:
            if row.get("tecnico"):
                tecnicos.append(row["tecnico"])

    tecnicos = list(sorted(set(tecnicos)))

    with col4:
        tecnico = st.selectbox("Realizado por", tecnicos, key="manual_tecnico")

    with col5:
        horas = st.number_input("Duración (hrs)", min_value=0.0, max_value=48.0, step=0.1, key="manual_horas")

    descripcion = st.text_area("Descripción del mantenimiento", key="manual_desc")

    if st.button("💾 Guardar mantenimiento manual"):
        row = [
            fecha.strftime("%Y-%m-%d"),
            equipo,
            descripcion,
            tecnico,
            "Completado",
            horas,
            "",
            "",
            tipo
        ]

        if append_row(SHEET, row):
            st.success("Mantenimiento guardado correctamente.")
            st.rerun()


# ==========================================================
#   HISTORIAL Y GRÁFICAS
# ==========================================================
def mostrar_reportes():
    data = read_sheet(SHEET)

    if not data:
        st.info("No hay datos aún.")
        return

    df = pd.DataFrame(data)

    st.dataframe(df, width="stretch")

    # Gráfica de horas por equipo
    if "tiempo_hrs" in df.columns:
        horas = df.groupby("Equipo")["tiempo_hrs"].sum()

        st.subheader("⏱ Horas acumuladas por equipo")
        st.bar_chart(horas, width="stretch")

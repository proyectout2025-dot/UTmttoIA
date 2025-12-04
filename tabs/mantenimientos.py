import streamlit as st
import pandas as pd
from datetime import datetime
from utils import (
    read_sheet,
    append_row,
    get_active_checkins,
    add_active_checkin,
    finalize_active_checkin
)


# ============================================================
# CONFIGURACIÓN Y LISTAS BASE
# ============================================================

TIPOS_MTTO = ["Correctivo", "Preventivo", "Predictivo"]

TECNICOS_BASE = [
    "Wesley Cunningham",
    "Misael Lopez",
    "Eduardo Vazquez",
    "Agregar nuevo técnico..."
]

EQUIPOS_BASE = [
    "Equipo 1",
    "Equipo 2",
    "Equipo 3",
    "Agregar nuevo equipo..."
]


# ============================================================
# FUNCIÓN PRINCIPAL DE LA PESTAÑA
# ============================================================

def show_mantenimientos():
    st.title("🛠 Módulo de Mantenimientos")

    st.write("Registra mantenimientos y controla tiempos con Check-In / Check-Out.")

    # --------------------------------------------------------
    # Cargar datos
    # --------------------------------------------------------
    data = read_sheet("mantenimientos")
    df = pd.DataFrame(data) if data else pd.DataFrame()

    activos = get_active_checkins()

    # --------------------------------------------------------
    # SECCIÓN: CHECK-IN / CHECK-OUT
    # --------------------------------------------------------

    st.subheader("⏱ Control de Tiempos (Check-In / Check-Out)")

    # Selección de equipo
    equipo_sel = st.selectbox("Seleccione el equipo:", EQUIPOS_BASE)

    if equipo_sel == "Agregar nuevo equipo...":
        equipo_sel = st.text_input("Escriba el nuevo equipo")
    
    # Descripción (solo para Check-In)
    desc_sel = st.selectbox("Tipo de mantenimiento:", TIPOS_MTTO)

    # Técnico
    tecnico_sel = st.selectbox("Técnico:", TECNICOS_BASE)

    if tecnico_sel == "Agregar nuevo técnico...":
        tecnico_sel = st.text_input("Escriba el nombre del técnico")

    # Determinar si este equipo ya tiene Check-In activo
    activo_equipo = None
    for entry in activos:
        if entry.get("Equipo") == equipo_sel:
            activo_equipo = entry
            break

    # Mostrar estado
    if activo_equipo:
        st.warning(f"⚠ El equipo **{equipo_sel}** YA tiene Check-In activo desde: **{activo_equipo['hora_inicio']}**")

        # Botón Check-Out
        if st.button("✔ Finalizar (Check-Out)"):
            resultado = finalize_active_checkin(equipo_sel)
            if resultado:
                horas, descripcion, realizado_por, hora_inicio, hora_fin = resultado

                append_row("mantenimientos", [
                    hora_inicio.split(" ")[0],  # Fecha
                    equipo_sel,
                    descripcion,
                    realizado_por,
                    "Terminado",
                    horas,
                    hora_inicio,
                    hora_fin
                ])

                st.success(f"Check-Out completado. Tiempo total: **{horas} hrs**")

                st.rerun()

    else:
        if st.button("🔵 Iniciar (Check-In)"):
            add_active_checkin(equipo_sel, desc_sel, tecnico_sel)
            st.success("Check-In registrado correctamente.")
            st.rerun()

    st.write("---")

    # --------------------------------------------------------
    # SECCIÓN: REGISTRO MANUAL DE MANTENIMIENTOS
    # --------------------------------------------------------

    st.subheader("📝 Registro Manual")

    col1, col2 = st.columns(2)

    with col1:
        fecha = st.date_input("Fecha", datetime.now())
        equipo_manual = st.selectbox("Equipo", EQUIPOS_BASE)

        if equipo_manual == "Agregar nuevo equipo...":
            equipo_manual = st.text_input("Escriba el nuevo equipo")

    with col2:
        tipo_manual = st.selectbox("Tipo mantenimiento", TIPOS_MTTO)
        tecnico_manual = st.selectbox("Técnico", TECNICOS_BASE)

        if tecnico_manual == "Agregar nuevo técnico...":
            tecnico_manual = st.text_input("Nuevo técnico")

    if st.button("💾 Guardar mantenimiento manual"):
        append_row("mantenimientos", [
            fecha.strftime("%Y-%m-%d"),
            equipo_manual,
            tipo_manual,
            tecnico_manual,
            "Terminado",
            0,
            "",  # hora_inicio
            ""   # hora_fin
        ])

        st.success("Mantenimiento guardado correctamente.")
        st.rerun()

    st.write("---")

    # --------------------------------------------------------
    # SECCIÓN: HISTORIAL Y GRÁFICAS
    # --------------------------------------------------------

    st.subheader("📊 Historial de Mantenimientos")

    if df.empty:
        st.info("No hay registros todavía.")
        return

    # Filtros
    with st.expander("🔍 Filtros"):
        colf1, colf2, colf3 = st.columns(3)

        with colf1:
            equipos_filtro = st.multiselect("Equipo", df["Equipo"].unique())

        with colf2:
            tecnicos_filtro = st.multiselect("Técnico", df["Realizado_por"].unique())

        with colf3:
            tipo_filtro = st.multiselect("Tipo", df["Descripcion"].unique())

    filtrado = df.copy()

    if equipos_filtro:
        filtrado = filtrado[filtrado["Equipo"].isin(equipos_filtro)]
    if tecnicos_filtro:
        filtrado = filtrado[filtrado["Realizado_por"].isin(tecnicos_filtro)]
    if tipo_filtro:
        filtrado = filtrado[filtrado["Descripcion"].isin(tipo_filtro)]

    # Tabla
    st.dataframe(filtrado, width="stretch")

    # --------------------------------------------------------
    # GRÁFICAS
    # --------------------------------------------------------

    st.subheader("📈 Gráficas")

    if "tiempo_hrs" in filtrado.columns:
        horas_equipo = filtrado.groupby("Equipo")["tiempo_hrs"].sum()
        st.bar_chart(horas_equipo)

        horas_tecnico = filtrado.groupby("Realizado_por")["tiempo_hrs"].sum()
        st.bar_chart(horas_tecnico)

    # --------------------------------------------------------
    # EXPORTACIÓN
    # --------------------------------------------------------

    csv = filtrado.to_csv(index=False).encode("utf-8")

    st.download_button(
        "📥 Descargar historial (CSV)",
        csv,
        "historial_mantenimientos.csv",
        "text/csv"
    )

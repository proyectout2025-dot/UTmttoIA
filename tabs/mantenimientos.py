import streamlit as st
import pandas as pd
from utils import (
    read_sheet, append_row,
    get_active_checkins, start_checkin, finalize_checkin,
    ensure_headers
)

SHEET = "mantenimientos"

EXPECTED_HEADERS = [
    "Fecha", "Equipo", "Descripcion", "Realizado_por",
    "estatus", "tiempo_hrs", "hora_inicio", "hora_fin"
]

def show_mantenimientos():

    # ============================
    #  Asegurar encabezados
    # ============================
    ensure_headers(SHEET, EXPECTED_HEADERS)
    ensure_headers("checkin_activos", ["Equipo", "Realizado_por", "hora_inicio"])

    st.header("🛠 Mantenimientos")

    df = pd.DataFrame(read_sheet(SHEET))

    if df.empty:
        st.info("Aún no hay mantenimientos registrados.")

    # ========================================
    #         FORMULARIO MANUAL 
    # ========================================
    st.subheader("➕ Registrar Mantenimiento Manual")

    # Campos dinámicos
    equipos = sorted({x.get("Equipo","") for x in df.to_dict('records')})
    tecnicos = ["Wesley Cunningham", "Misael Lopez", "Eduardo Vazquez"]

    equipo_sel = st.selectbox("Equipo", equipos + ["Agregar nuevo"], key="equipo_manual")

    if equipo_sel == "Agregar nuevo":
        equipo_sel = st.text_input("Nuevo equipo")

    tipo_sel = st.selectbox("Tipo de Mantenimiento", ["Correctivo","Preventivo","Predictivo"], key="tipo_man")

    tecnico_sel = st.selectbox("Realizado por", tecnicos + ["Agregar nuevo"], key="tec_man")
    if tecnico_sel == "Agregar nuevo":
        tecnico_sel = st.text_input("Nuevo técnico")

    if st.button("Guardar Mantenimiento Manual"):
        row = [
            datetime.now().strftime("%Y-%m-%d"),
            equipo_sel,
            tipo_sel,
            tecnico_sel,
            "Completado",
            0,
            "",
            ""
        ]
        append_row(SHEET, row)
        st.success("Guardado correctamente.")
        st.rerun()

    # ========================================
    #         CHECK-IN ACTIVO
    # ========================================
    st.subheader("⏱ Check-in / Check-out")

    activos = get_active_checkins()
    equipos_activos = [a["Equipo"] for a in activos]

    equipo_ci = st.selectbox("Equipo", equipos + ["Agregar nuevo"], key="equipo_ci")

    if equipo_ci == "Agregar nuevo":
        equipo_ci = st.text_input("Nuevo equipo para Check-in")

    tecnico_ci = st.selectbox("Técnico", tecnicos + ["Agregar nuevo"], key="tecc_ci")
    if tecnico_ci == "Agregar nuevo":
        tecnico_ci = st.text_input("Nuevo técnico")

    # SI EL EQUIPO YA ESTÁ EN CHECK-IN
    if equipo_ci in equipos_activos:
        st.warning("Este equipo ya tiene un check-in activo.")

        row_number = equipos_activos.index(equipo_ci) + 2

        descripcion = st.selectbox("Tipo de Mantenimiento", ["Correctivo","Preventivo","Predictivo"], key="tipo_fin")
        estatus = st.selectbox("Estatus", ["Completado","Cancelado"], key="est_fin")

        if st.button("✔ Finalizar Check-out"):
            if finalize_checkin(row_number, descripcion, estatus):
                st.success("Check-out registrado.")
                st.rerun()

    else:
        if st.button("⏱ Iniciar Check-in"):
            start_checkin(equipo_ci, tecnico_ci)
            st.success("Check-in iniciado.")
            st.rerun()

    # ========================================
    #          HISTORIAL
    # ========================================
    st.subheader("📘 Historial de Mantenimientos")

    df = pd.DataFrame(read_sheet(SHEET))
    
    if not df.empty:
        st.dataframe(df, width="stretch")

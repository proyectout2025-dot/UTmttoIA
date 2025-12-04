import streamlit as st
import pandas as pd
from datetime import datetime
from utils import (
    read_sheet,
    append_row,
    get_active_checkins,
    add_active_checkin,
    finalize_checkin
)

SHEET = "mantenimientos"

# ============================================================
#      LISTAS PREDETERMINADAS (EDITABLES POR EL USUARIO)
# ============================================================
DEFAULT_EQUIPOS = ["Equipo 1", "Equipo 2", "Equipo 3"]
DEFAULT_TECNICOS = [
    "Wesley Cunningham",
    "Misael Lopez",
    "Eduardo Vazquez"
]
TIPOS_MANTENIMIENTO = ["Correctivo", "Preventivo", "Predictivo"]


# ============================================================
#                 CARGA BASE DE DATOS
# ============================================================
def load_mantenimientos():
    data = read_sheet(SHEET)
    df = pd.DataFrame(data) if data else pd.DataFrame()
    return df


# ============================================================
#                      CHECK-IN / CHECK-OUT
# ============================================================
def check_in_out_ui():
    st.subheader("⏱ Registro de Tiempo — Check-in / Check-out")
    activos = get_active_checkins()

    # ---- LISTA DE EQUIPOS ----
    equipos_data = read_sheet("config")
    equipos = DEFAULT_EQUIPOS.copy()
    if equipos_data:
        equipos += [x["Equipo"] for x in equipos_data if x["Equipo"] not in equipos]

    equipo_sel = st.selectbox("Equipo", equipos, key="check_equipo")

    # ---- LISTA DE TECNICOS ----
    tecnicos = DEFAULT_TECNICOS.copy()
    if equipos_data:
        tecnicos += [x["Tecnico"] for x in equipos_data if x["Tecnico"] not in tecnicos]

    realizado_por = st.selectbox("Técnico", tecnicos, key="check_tec")

    tipo = st.selectbox("Tipo de mantenimiento", TIPOS_MANTENIMIENTO, key="check_tipo")

    # CHECAR SI YA TIENE CHECK-IN ACTIVO
    activo = next((a for a in activos if a["Equipo"] == equipo_sel), None)

    if activo:
        st.warning(f"⏳ Este equipo YA tiene un check-in activo desde **{activo['hora_inicio']}**.")

        if st.button("✔ Finalizar Check-out", key="btn_finalizar"):
            ok = finalize_checkin(activo)
            if ok:
                st.success("Check-out completado")
                st.rerun()

    else:
        if st.button("⏱ Iniciar Check-in", key="btn_iniciar"):
            add_active_checkin(equipo_sel, realizado_por, tipo)
            st.success("Check-in iniciado")
            st.rerun()


# ============================================================
#                REGISTRO MANUAL DE MANTENIMIENTO
# ============================================================
def registro_manual_ui():
    st.subheader("✍ Registro Manual de Mantenimiento")

    equipos_data = read_sheet("config")
    equipos = DEFAULT_EQUIPOS.copy()
    if equipos_data:
        equipos += [x["Equipo"] for x in equipos_data]

    equipo = st.selectbox("Equipo", equipos, key="manual_equipo")

    descripcion = st.selectbox("Tipo de mantenimiento", TIPOS_MANTENIMIENTO, key="manual_desc")

    tecnicos = DEFAULT_TECNICOS.copy()
    if equipos_data:
        tecnicos += [x["Tecnico"] for x in equipos_data]

    realizado_por = st.selectbox("Realizado por", tecnicos, key="manual_tec")

    fecha = datetime.now().strftime("%Y-%m-%d")

    if st.button("💾 Guardar Mantenimiento", key="btn_guardar_mant"):
        row = [
            fecha,
            equipo,
            descripcion,
            realizado_por,
            "Completado",
            0,
            "",
            "",
            descripcion
        ]
        append_row(SHEET, row)
        st.success("Mantenimiento guardado")
        st.rerun()


# ============================================================
#                       GRÁFICAS
# ============================================================
def reportes_ui():
    st.subheader("📈 Reportes y Gráficas")

    df = load_mantenimientos()
    if df.empty:
        st.info("No hay datos aún.")
        return

    # Tiempo total por equipo
    if "tiempo_hrs" in df.columns and "Equipo" in df.columns:
        tiempo = df.groupby("Equipo")["tiempo_hrs"].sum()
        st.bar_chart(tiempo, width="stretch")


# ============================================================
#                       MAIN TAB
# ============================================================
def show_mantenimientos():
    st.header("🛠 Mantenimientos")

    check_in_out_ui()
    st.divider()

    registro_manual_ui()
    st.divider()

    reportes_ui()

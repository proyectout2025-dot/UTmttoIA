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

DEFAULT_EQUIPOS = ["Equipo 1", "Equipo 2", "Equipo 3"]
DEFAULT_TECNICOS = ["Wesley Cunningham", "Misael Lopez", "Eduardo Vazquez"]
TIPOS_MANTENIMIENTO = ["Correctivo", "Preventivo", "Predictivo"]


def load_mantenimientos():
    data = read_sheet(SHEET)
    return pd.DataFrame(data) if data else pd.DataFrame()


def check_in_out_ui():
    st.subheader("⏱ Registro de Tiempo — Check-in / Check-out")

    activos = get_active_checkins()
    config = read_sheet("config")

    equipos = DEFAULT_EQUIPOS.copy()
    if config:
        equipos += [x["Equipo"] for x in config if x.get("Equipo")]

    tecnicos = DEFAULT_TECNICOS.copy()
    if config:
        tecnicos += [x["Tecnico"] for x in config if x.get("Tecnico")]

    equipo_sel = st.selectbox("Equipo", equipos, key="chk_e1")
    tecnico_sel = st.selectbox("Técnico", tecnicos, key="chk_t1")
    tipo_sel = st.selectbox("Tipo de mantenimiento", TIPOS_MANTENIMIENTO, key="chk_tp")

    activo = next((a for a in activos if a["Equipo"] == equipo_sel), None)

    if activo:
        st.warning(f"⏳ Check-in activo desde **{activo['hora_inicio']}**")

        if st.button("✔ Finalizar Check-out", key="btn_ckout"):
            ok = finalize_checkin(activo)
            if ok:
                st.success("Check-out completado")
                st.rerun()

    else:
        if st.button("⏱ Iniciar Check-in", key="btn_ckin"):
            add_active_checkin(equipo_sel, tecnico_sel, tipo_sel)
            st.success("Check-in iniciado")
            st.rerun()


def registro_manual_ui():
    st.subheader("✍ Registro Manual de Mantenimiento")

    config = read_sheet("config")

    equipos = DEFAULT_EQUIPOS.copy()
    if config:
        equipos += [x["Equipo"] for x in config if x.get("Equipo")]

    tecnicos = DEFAULT_TECNICOS.copy()
    if config:
        tecnicos += [x["Tecnico"] for x in config if x.get("Tecnico")]

    equipo = st.selectbox("Equipo", equipos, key="man_e1")
    descripcion = st.selectbox("Tipo", TIPOS_MANTENIMIENTO, key="man_t1")
    realizado = st.selectbox("Realizado por", tecnicos, key="man_r1")

    fecha = datetime.now().strftime("%Y-%m-%d")

    if st.button("💾 Guardar Mantenimiento", key="btn_save_manual"):
        row = [fecha, equipo, descripcion, realizado, "Completado", 0, "", "", descripcion]
        append_row(SHEET, row)
        st.success("Guardado correctamente")
        st.rerun()


def reportes_ui():
    st.subheader("📈 Gráficas")

    df = load_mantenimientos()
    if df.empty:
        st.info("No hay datos aún.")
        return

    if "tiempo_hrs" in df and "Equipo" in df:
        st.bar_chart(df.groupby("Equipo")["tiempo_hrs"].sum(), width="stretch")


def show_mantenimientos():
    st.header("🛠 Mantenimientos")

    check_in_out_ui()
    st.divider()

    registro_manual_ui()
    st.divider()

    reportes_ui()

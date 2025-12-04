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


def show_mantenimientos():
    st.header("🛠 Mantenimientos")

    # =======================
    #   Datos dinámicos
    # =======================
    cfg = read_sheet("config")
    equipos = sorted({c["Equipo"] for c in cfg if c.get("Equipo")})
    tecnicos = sorted({c["Tecnico"] for c in cfg if c.get("Tecnico")})

    # ====================================
    #       CHECK-IN / CHECK-OUT
    # ====================================
    st.subheader("⏱ Control de tiempos")

    equipo_sel = st.selectbox("Equipo", equipos)
    tecnico_sel = st.selectbox("Técnico", tecnicos)

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

    fecha = st.date_input("Fecha")
    equipo = st.selectbox("Equipo (manual)", equipos)
    tipo = st.selectbox("Tipo", ["Correctivo", "Preventivo", "Predictivo"])
    tecnico = st.selectbox("Técnico", tecnicos)
    descripcion = st.text_area("Descripción")
    tiempo = st.number_input("Tiempo (hrs)", min_value=0.0)

    if st.button("Guardar mantenimiento"):
        row = [
            fecha.strftime("%Y-%m-%d"),
            equipo,
            tipo,
            tecnico,
            "Completado",
            tiempo,
            "",
            datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        ]
        append_row("mantenimientos", row)
        st.success("Mantenimiento guardado.")
        st.rerun()

    st.divider()

    # ====================================
    #     HISTORIAL
    # ====================================
    st.subheader("📚 Historial")

    data = read_sheet("mantenimientos")
    if not data:
        st.info("No hay datos.")
        return

    df = pd.DataFrame(data)
    st.dataframe(df, width="stretch")

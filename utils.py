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


# ====================================
# Helpers
# ====================================
def load_teams():
    cfg = read_sheet("config")
    return [c["Equipo"] for c in cfg] if cfg else []


def load_techs():
    cfg = read_sheet("config")
    return [c["Tecnico"] for c in cfg] if cfg else []


# ====================================
# UI PRINCIPAL
# ====================================
def show_mantenimientos():
    st.header("🛠 Mantenimientos")

    # ===================
    #    CHECK-IN ACTIVO
    # ===================
    with st.expander("⏱ Control de tiempos — Check-in / Check-out"):
        equipos = load_teams()
        tecnicos = load_techs()

        equipo_sel = st.selectbox("Equipo", equipos)
        tecnico_sel = st.selectbox("Técnico", tecnicos)

        activos = get_active_checkins()
        activo = next((a for a in activos if a["Equipo"] == equipo_sel), None)

        # -------- CHECK-OUT ---------
        if activo:
            st.warning(f"🔴 Check-in activo desde {activo['hora_inicio']}")

            if st.button("🔚 Finalizar Check-out"):
                row_number = activos.index(activo) + 2  # +2 por encabezado
                ok = finalize_checkin(row_number, descripcion="Trabajo completado")

                if ok:
                    st.success("Check-out registrado correctamente.")
                    st.rerun()

        # -------- CHECK-IN ---------
        else:
            if st.button("⏱ Iniciar Check-in"):
                add_active_checkin(equipo_sel, tecnico_sel)
                st.success("Check-in iniciado.")
                st.rerun()

    st.divider()

    # ===================
    #    REGISTRO MANUAL
    # ===================
    with st.expander("📝 Registro Manual de Mantenimientos"):
        equipos = load_teams()
        tecnicos = load_techs()

        fecha = st.date_input("Fecha")
        equipo = st.selectbox("Equipo", equipos)
        tipo = st.selectbox("Tipo", ["Correctivo", "Preventivo", "Predictivo"])
        realizado_por = st.selectbox("Técnico", tecnicos)
        descripcion = st.text_area("Descripción del trabajo realizado")
        tiempo = st.number_input("Tiempo (hrs)", min_value=0.0)

        if st.button("💾 Guardar mantenimiento"):
            row = [
                fecha.strftime("%Y-%m-%d"),
                equipo,
                tipo,
                realizado_por,
                "Completado",
                tiempo,
                "",
                datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            ]
            ok = append_row("mantenimientos", row)

            if ok:
                st.success("Guardado correctamente.")
                st.rerun()

    st.divider()

    # ===================
    #     HISTORIAL
    # ===================
    st.subheader("📚 Historial")

    data = read_sheet("mantenimientos")
    if not data:
        st.info("No hay mantenimientos registrados.")
        return

    df = pd.DataFrame(data)
    st.dataframe(df, width="stretch")

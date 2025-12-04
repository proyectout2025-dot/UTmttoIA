# ===========================================
# /tabs/mantenimientos.py — FINAL
# ===========================================

import streamlit as st
import pandas as pd
from datetime import datetime

from utils import (
    read_sheet,
    append_row,
    add_active_checkin,
    get_active_checkins,
    finalize_active_checkin
)

SHEET = "mantenimientos"


def load_df():
    data = read_sheet(SHEET)
    if not data:
        return pd.DataFrame()
    return pd.DataFrame(data)

# ========= FORMULARIO =========
def mantenimiento_form(df):
    st.subheader("📝 Registrar Mantenimiento")

    equipos = sorted(df["Equipo"].dropna().unique()) if "Equipo" in df else []
    equipos.append("➕ Agregar equipo")

    equipo_sel = st.selectbox("Equipo", equipos)
    equipo_final = equipo_sel

    if equipo_sel == "➕ Agregar equipo":
        equipo_final = st.text_input("Nuevo equipo")

    tecnicos = sorted(df["Realizado_por"].dropna().unique()) if "Realizado_por" in df else []
    tecnicos.append("➕ Agregar técnico")

    tecnico_sel = st.selectbox("Técnico", tecnicos)
    tecnico_final = tecnico_sel

    if tecnico_sel == "➕ Agregar técnico":
        tecnico_final = st.text_input("Nuevo técnico")

    tipo = st.selectbox("Tipo", ["Correctivo", "Preventivo", "Predictivo"])
    desc = st.text_area("Descripción")
    fecha = st.date_input("Fecha", datetime.now())

    if st.button("💾 Guardar"):
        row = [
            str(fecha),
            equipo_final,
            desc,
            tecnico_final,
            tipo,
            "",
            datetime.now().strftime("%H:%M:%S"),
            ""
        ]
        append_row(SHEET, row)
        st.success("Mantenimiento guardado.")
        st.rerun()

# ========= CHECK-IN =========
def check_in(df):
    st.subheader("⏱ Check-In / Check-Out")

    equipos = sorted(df["Equipo"].dropna().unique()) if "Equipo" in df else []
    equipos.append("➕ Agregar equipo")

    equipo_sel = st.selectbox("Equipo", equipos)
    equipo_final = equipo_sel

    if equipo_sel == "➕ Agregar equipo":
        equipo_final = st.text_input("Nuevo equipo")

    tecs = sorted(df["Realizado_por"].dropna().unique()) if "Realizado_por" in df else []
    tecs.append("➕ Agregar técnico")

    tecnico_sel = st.selectbox("Técnico", tecs)
    tecnico_final = tecnico_sel

    if tecnico_sel == "➕ Agregar técnico":
        tecnico_final = st.text_input("Nuevo técnico")

    activos = get_active_checkins()
    activo = next((a for a in activos if a["equipo"] == equipo_final), None)

    if activo:
        if st.button("✔ Finalizar Check-Out"):
            result = finalize_active_checkin(equipo_final)
            if result:
                horas, tecnico, ini, fin = result
                row = [
                    datetime.now().strftime("%Y-%m-%d"),
                    equipo_final,
                    "Trabajo",
                    tecnico,
                    "Completado",
                    horas,
                    ini,
                    fin
                ]
                append_row(SHEET, row)
                st.success("Check-out completado.")
                st.rerun()

    else:
        if st.button("⏱ Iniciar Check-in"):
            add_active_checkin(equipo_final, tecnico_final)
            st.success("Check-in iniciado.")
            st.rerun()

# ========= GRÁFICAS =========
def charts(df):
    st.subheader("📊 Reportes")

    if df.empty:
        st.info("No hay datos aún.")
        return

    col1, col2 = st.columns(2)

    with col1:
        try:
            st.bar_chart(df.groupby("Equipo")["tiempo_hrs"].sum())
        except:
            pass

    with col2:
        st.bar_chart(df.groupby("Realizado_por")["Descripcion"].count())

# ========= MAIN =========
def show_mantenimientos():
    df = load_df()

    mantenimiento_form(df)
    st.divider()

    check_in(df)
    st.divider()

    charts(df)

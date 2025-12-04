# ===========================================
# /tabs/mantenimientos.py — FINAL SIN ERRORES
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


# ---------------------------
# Cargar DataFrame
# ---------------------------
def load_df():
    data = read_sheet(SHEET)
    if not data:
        return pd.DataFrame()
    return pd.DataFrame(data)


# ---------------------------
# FORMULARIO DE MANTENIMIENTO
# ---------------------------
def mantenimiento_form(df):
    st.subheader("📝 Registrar Mantenimiento")

    # Equipos disponibles
    equipos = sorted(df["Equipo"].dropna().unique()) if "Equipo" in df else []
    equipos.append("➕ Agregar equipo")

    equipo_sel = st.selectbox("Equipo", equipos, key="form_equipo")
    equipo_final = equipo_sel

    if equipo_sel == "➕ Agregar equipo":
        equipo_final = st.text_input("Nuevo equipo", key="form_equipo_nuevo")

    # Técnicos
    tecnicos = sorted(df["Realizado_por"].dropna().unique()) if "Realizado_por" in df else []
    tecnicos.append("➕ Agregar técnico")

    tecnico_sel = st.selectbox("Técnico", tecnicos, key="form_tecnico")
    tecnico_final = tecnico_sel

    if tecnico_sel == "➕ Agregar técnico":
        tecnico_final = st.text_input("Nuevo técnico", key="form_tecnico_nuevo")

    tipo = st.selectbox(
        "Tipo de mantenimiento",
        ["Correctivo", "Preventivo", "Predictivo"],
        key="form_tipo"
    )

    desc = st.text_area("Descripción", key="form_descripcion")
    fecha = st.date_input("Fecha", datetime.now(), key="form_fecha")

    if st.button("💾 Guardar mantenimiento", key="btn_guardar_mto"):
        row = [
            str(fecha),
            equipo_final,
            desc,
            tecnico_final,
            tipo,
            "",
            "",
            ""
        ]

        append_row(SHEET, row)
        st.success("✔ Mantenimiento guardado correctamente")
        st.rerun()


# ---------------------------
# CHECK-IN / CHECK-OUT
# ---------------------------
def check_in(df):
    st.subheader("⏱ Check-In / Check-Out")

    # Equipos
    equipos = sorted(df["Equipo"].dropna().unique()) if "Equipo" in df else []
    equipos.append("➕ Agregar equipo")

    equipo_sel = st.selectbox("Equipo", equipos, key="ci_equipo")
    equipo_final = equipo_sel

    if equipo_sel == "➕ Agregar equipo":
        equipo_final = st.text_input("Nuevo equipo", key="ci_equipo_nuevo")

    # Técnicos
    tecnicos = sorted(df["Realizado_por"].dropna().unique()) if "Realizado_por" in df else []
    tecnicos.append("➕ Agregar técnico")

    tecnico_sel = st.selectbox("Técnico", tecnicos, key="ci_tecnico")
    tecnico_final = tecnico_sel

    if tecnico_sel == "➕ Agregar técnico":
        tecnico_final = st.text_input("Nuevo técnico", key="ci_tecnico_nuevo")

    activos = get_active_checkins()
    activo = next((a for a in activos if a["equipo"] == equipo_final), None)

    # Ya existe check-in → ofrecer check-out
    if activo:
        st.info(f"⏳ Check-in activo desde: {activo['hora_inicio']}")
        if st.button("✔ Finalizar Check-Out", key="btn_checkout"):
            result = finalize_active_checkin(equipo_final)
            if result:
                horas, tecnico, inicio, fin = result

                row = [
                    datetime.now().strftime("%Y-%m-%d"),
                    equipo_final,
                    "Trabajo",
                    tecnico,
                    "Completado",
                    horas,
                    inicio,
                    fin
                ]
                append_row(SHEET, row)
                st.success("✔ Check-out completado")
                st.rerun()

    # Aún no tiene check-in
    else:
        if st.button("⏱ Iniciar Check-In", key="btn_checkin"):
            add_active_checkin(equipo_final, tecnico_final)
            st.success("✔ Check-in iniciado")
            st.rerun()


# ---------------------------
# GRÁFICAS
# ---------------------------
def charts(df):
    st.subheader("📊 Reportes")

    if df.empty:
        st.info("No hay datos aún.")
        return

    col1, col2 = st.columns(2)

    with col1:
        try:
            st.bar_chart(df.groupby("Equipo")["tiempo_hrs"].sum(), use_container_width=True)
        except:
            st.info("No hay datos de 'tiempo_hrs' aún.")

    with col2:
        st.bar_chart(df.groupby("Realizado_por")["Descripcion"].count(), use_container_width=True)


# ---------------------------
# MAIN
# ---------------------------
def show_mantenimientos():
    df = load_df()

    mantenimiento_form(df)
    st.divider()

    check_in(df)
    st.divider()

    charts(df)

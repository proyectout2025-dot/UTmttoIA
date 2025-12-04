# ================================================
#  /tabs/mantenimientos.py — FINAL 100% FUNCIONAL
# ================================================

import streamlit as st
import pandas as pd
from datetime import datetime
from utils import (
    read_sheet,
    append_row,
    add_active_checkin,
    get_active_checkins,
    finalize_active_checkin,
)

# Nombre de la hoja principal
MAIN_SHEET = "mantenimientos"


# ==================================================
#   Cargar datos
# ==================================================
def load_df():
    data = read_sheet(MAIN_SHEET)
    if not data:
        return pd.DataFrame()
    return pd.DataFrame(data)


# ==================================================
#   Formulario principal para registrar mantenimiento
# ==================================================
def mantenimiento_form(df):
    st.subheader("📝 Registrar Mantenimiento")

    # Lista dinámica de equipos
    equipos_existentes = sorted(list(df["Equipo"].dropna().unique())) if "Equipo" in df else []
    equipos_existentes.append("➕ Agregar nuevo equipo")

    equipo_sel = st.selectbox("Equipo", equipos_existentes)

    nuevo_equipo = None
    if equipo_sel == "➕ Agregar nuevo equipo":
        nuevo_equipo = st.text_input("Escribe el nombre del nuevo equipo")
        if nuevo_equipo.strip() != "":
            equipo_final = nuevo_equipo.strip()
        else:
            equipo_final = None
    else:
        equipo_final = equipo_sel

    # Tipo de mantenimiento
    tipo_mant = st.selectbox(
        "Tipo de mantenimiento",
        ["Correctivo", "Preventivo", "Predictivo"]
    )

    # Lista dinámica de técnicos
    tecnicos = sorted(list(df["Realizado_por"].dropna().unique())) if "Realizado_por" in df else []
    tecnicos.append("➕ Agregar técnico")

    tecnico_sel = st.selectbox("Realizado por", tecnicos)

    if tecnico_sel == "➕ Agregar técnico":
        tecnico_nuevo = st.text_input("Nombre del nuevo técnico")
        if tecnico_nuevo.strip() != "":
            tecnico_final = tecnico_nuevo.strip()
        else:
            tecnico_final = None
    else:
        tecnico_final = tecnico_sel

    fecha = st.date_input("Fecha", datetime.now())
    descripcion = st.text_area("Descripción del mantenimiento")

    if st.button("💾 Guardar Mantenimiento"):
        if not equipo_final or not tecnico_final:
            st.error("Debes completar todos los campos.")
        else:
            hora_texto = datetime.now().strftime("%H:%M:%S")
            row = [
                str(fecha),
                equipo_final,
                descripcion,
                tecnico_final,
                tipo_mant,
                "",             # tiempo_hrs (vacío)
                hora_texto,      # hora_inicio
                "",              # hora_fin
            ]
            ok = append_row(MAIN_SHEET, row)
            if ok:
                st.success("Mantenimiento guardado correctamente.")
                st.rerun()


# ==================================================
#   Check-in / Check-out
# ==================================================
def checkin_section(df):
    st.subheader("⏱ Control de Tiempo — Check-in / Check-out")

    activos = get_active_checkins()

    equipos = sorted(list(df["Equipo"].dropna().unique())) if "Equipo" in df else []
    equipos.append("➕ Agregar nuevo equipo")

    equipo_sel = st.selectbox("Seleccionar equipo para Check-in", equipos)

    # nuevo equipo si aplica
    if equipo_sel == "➕ Agregar nuevo equipo":
        equipo_nuevo = st.text_input("Nombre nuevo del equipo")
        equipo_final = equipo_nuevo.strip() if equipo_nuevo.strip() != "" else None
    else:
        equipo_final = equipo_sel

    tecnicos = sorted(list(df["Realizado_por"].dropna().unique())) if "Realizado_por" in df else []
    tecnicos.append("➕ Agregar técnico")

    tecnico_sel = st.selectbox("Técnico", tecnicos)

    if tecnico_sel == "➕ Agregar técnico":
        tecnico_nuevo = st.text_input("Nuevo técnico")
        tecnico_final = tecnico_nuevo.strip() if tecnico_nuevo.strip() != "" else None
    else:
        tecnico_final = tecnico_sel

    # Si existe check-in activo en ese equipo, mostrar check-out
    equipo_activo = next((x for x in activos if x["equipo"] == equipo_final), None)

    if equipo_activo:
        st.warning(f"⏳ Este equipo ya tiene Check-IN activo desde {equipo_activo['hora_inicio']}")

        if st.button("✔ Finalizar Check-Out"):
            result = finalize_active_checkin(equipo_final)
            if result:
                horas, realizado_por, inicio, fin = result

                row = [
                    datetime.now().strftime("%Y-%m-%d"),
                    equipo_final,
                    "Trabajo (Check-in/out)",
                    realizado_por,
                    "Completado",
                    horas,
                    inicio,
                    fin,
                ]
                append_row(MAIN_SHEET, row)
                st.success(f"Check-out completado. Tiempo total: {horas} hrs")
                st.rerun()

    else:
        if st.button("⏱ Iniciar Check-in"):
            if equipo_final and tecnico_final:
                add_active_checkin(equipo_final, tecnico_final)
                st.success("Check-in iniciado.")
                st.rerun()
            else:
                st.error("Completa todos los campos para iniciar Check-in.")


# ==================================================
#   Gráficas
# ==================================================
def metrics_and_charts(df):
    st.subheader("📊 Reportes y Métricas")

    if df.empty:
        st.info("Aún no hay datos para graficar.")
        return

    col1, col2 = st.columns(2)

    # Horas por equipo
    with col1:
        st.write("Horas totales por equipo")
        if "tiempo_hrs" in df and df["tiempo_hrs"].dtype != object:
            horas_equipo = df.groupby("Equipo")["tiempo_hrs"].sum()
            st.bar_chart(horas_equipo)
        else:
            st.info("Aún no hay tiempos registrados.")

    # Mantenimientos por técnico
    with col2:
        st.write("Mantenimientos por técnico")
        conteo = df.groupby("Realizado_por")["Descripcion"].count()
        st.bar_chart(conteo)


# ==================================================
#   PANTALLA PRINCIPAL
# ==================================================
def show_mantenimientos():
    st.header("🛠 Mantenimientos")

    df = load_df()
    
    mantenimiento_form(df)
    st.divider()

    checkin_section(df)
    st.divider()

    metrics_and_charts(df)

import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
from datetime import datetime

from utils import (
    read_sheet,
    get_active_checkins,
    add_active_checkin,
    close_checkin
)

SPREADSHEET = "base_datos_app"
SHEET = "mantenimientos"


# -----------------------------
#  Cargar datos
# -----------------------------
def load_data():
    data = read_sheet(SPREADSHEET, SHEET)
    if not data:
        return pd.DataFrame()
    return pd.DataFrame(data)


# -----------------------------
#  INTERFAZ PRINCIPAL
# -----------------------------
def show_mantenimientos():
    st.header("🛠 Mantenimientos — Registro y Reportes")

    df = load_data()

    # -----------------------------
    #  1. REGISTROS ACTIVOS
    # -----------------------------
    st.subheader("⏳ Mantenimientos Activos (Check-in)")

    activos = get_active_checkins(SPREADSHEET)

    if activos:
        st.write(pd.DataFrame(activos.values()))
    else:
        st.info("No hay check-ins activos.")

    st.divider()

    # -----------------------------
    #  2. INICIAR CHECK-IN
    # -----------------------------
    st.subheader("✔ Iniciar mantenimiento (Check-in)")

    equipos_lista = ["Equipo 1", "Equipo 2", "Equipo 3", "Otro"]

    equipo = st.selectbox("Equipo", equipos_lista)
    realizado_por = st.text_input("Realizado por")

    if st.button("🚀 Iniciar Check-in"):
        if not realizado_por:
            st.warning("Ingresa el nombre del técnico.")
        else:
            add_active_checkin(SPREADSHEET, equipo, realizado_por)
            st.success("Check-in iniciado.")
            st.rerun()

    st.divider()

    # -----------------------------
    #  3. FINALIZAR CHECK-IN
    # -----------------------------
    st.subheader("📌 Finalizar mantenimiento (Check-out)")

    if activos:
        equipo_fin = st.selectbox("Equipo en trabajo", list(activos.keys()))
        descripcion = st.text_area("Descripción del trabajo realizado")
        estatus = st.selectbox("Estatus final", ["Completado", "Pendiente", "Cancelado"])

        if st.button("✔ Finalizar Check-out"):
            close_checkin(SPREADSHEET, equipo_fin, descripcion, estatus)
            st.success("Mantenimiento registrado correctamente.")
            st.rerun()
    else:
        st.info("No hay mantenimientos activos para finalizar.")

    st.divider()

    # -----------------------------
    #  4. HISTORIAL
    # -----------------------------
    st.subheader("📚 Historial de Mantenimientos")

    if df.empty:
        st.info("Aún no hay historial.")
    else:
        st.dataframe(df)

    st.divider()

    # -----------------------------
    #  5. REPORTES Y GRÁFICAS
    # -----------------------------
    st.subheader("📊 Reporte de tiempos (horas)")

    if not df.empty:
        horas = df.groupby("equipo")["tiempo_hrs"].sum()

        fig, ax = plt.subplots()
        horas.plot(kind="bar", ax=ax)
        ax.set_title("Horas totales por equipo")
        ax.set_ylabel("Horas")

        st.pyplot(fig)
    else:
        st.info("No hay datos suficientes para gráficas.")

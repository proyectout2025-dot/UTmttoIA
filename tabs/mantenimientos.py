import streamlit as st
import pandas as pd
from datetime import datetime
from utils import read_sheet, append_sheet

SHEET_NAME = "mantenimientos"

def show_mantenimientos():
    st.header("🔧 Registro de Mantenimientos")

    st.subheader("Historial de Mantenimientos")
    df = read_sheet(SHEET_NAME)

    if df is not None and not df.empty:
        st.dataframe(df)
    else:
        st.info("No hay registros todavía.")

    st.subheader("Registrar Nuevo Mantenimiento")

    # -----------------------------------------
    # VARIABLES CONTROLADAS
    # -----------------------------------------
    equipo = st.text_input("Equipo")
    descripcion = st.text_area("Descripción del mantenimiento")
    realizado_por = st.text_input("Realizado por")
    estatus = st.selectbox("Estatus", ["Completado", "En proceso", "Pendiente"])

    # Tiempo manual (se llenará automáticamente cuando haya Check-out)
    tiempo_hrs = st.number_input("Tiempo (Hrs)", min_value=0.0, format="%.2f")

    # -----------------------------------------
    # CHECK-IN / CHECK-OUT CONTROL
    # -----------------------------------------
    st.subheader("⏱ Control de Tiempos")

    if "check_in_time" not in st.session_state:
        st.session_state.check_in_time = None

    # Mostrar hora actual
    st.write("Hora actual:", datetime.now().strftime("%Y-%m-%d %H:%M:%S"))

    # Check-in
    if st.session_state.check_in_time is None:
        if st.button("Iniciar Check-in"):
            st.session_state.check_in_time = datetime.now()
            st.success(f"Check-in iniciado a las {st.session_state.check_in_time.strftime('%H:%M:%S')}")
    else:
        st.info(f"Check-in activo desde: {st.session_state.check_in_time.strftime('%Y-%m-%d %H:%M:%S')}")

        # Check-out
        if st.button("Finalizar Check-out"):
            check_out_time = datetime.now()
            diff = check_out_time - st.session_state.check_in_time
            horas = round(diff.total_seconds() / 3600, 2)
            tiempo_hrs = horas

            st.success(f"Check-out realizado. Tiempo total: {horas} horas")
            st.session_state.check_in_time = None  # reset

    # -----------------------------------------
    # GUARDAR REGISTRO
    # -----------------------------------------
    if st.button("Guardar Registro"):
        if not equipo or not descripcion or not realizado_por:
            st.error("Por favor completa todos los campos obligatorios.")
            return

        new_row = {
            "fecha": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "equipo": equipo,
            "descripcion": descripcion,
            "realizado_por": realizado_por,
            "estatus": estatus,
            "tiempo_hrs": tiempo_hrs
        }

        append_sheet(SHEET_NAME, new_row)

        st.success("Mantenimiento guardado correctamente.")

        # LIMPIAR CAMPOS
        st.experimental_rerun()

    # -----------------------------------------
    # GENERAR REPORTES Y GRAFICAS
    # -----------------------------------------
    st.subheader("📊 Reportes")

    if st.button("Generar Reportes"):
        if df is None or df.empty:
            st.warning("No hay datos para generar reportes.")
            return

        st.line_chart(df["tiempo_hrs"])
        st.bar_chart(df["estatus"].value_counts())

        st.success("Reportes generados.")

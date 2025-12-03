import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt

from utils import (
    read_sheet,
    append_sheet,
    add_active_checkin,
    get_active_checkins,
    finalize_active_checkin
)

def show_mantenimientos():

    st.title("🛠 Mantenimientos")

    # ================================
    # FORM MANUAL
    # ================================
    st.subheader("➕ Registrar mantenimiento manual")

    with st.form("manual"):
        fecha = st.date_input("Fecha")
        equipo = st.text_input("Equipo")
        descripcion = st.text_area("Descripción")
        realizado_por = st.text_input("Realizado por")
        estatus = st.selectbox("Estatus", ["Terminado", "Pendiente", "Cancelado"])
        tiempo = st.number_input("Tiempo (hrs)", min_value=0.0)
        h1 = st.time_input("Hora inicio")
        h2 = st.time_input("Hora fin")

        guardar = st.form_submit_button("Guardar")

        if guardar:
            row = {
                "Fecha": str(fecha),
                "Equipo": equipo,
                "Descripcion": descripcion,
                "Realizado_por": realizado_por,
                "estatus": estatus,
                "tiempo_hrs": tiempo,
                "hora_inicio": h1.strftime("%H:%M:%S"),
                "hora_fin": h2.strftime("%H:%M:%S"),
            }
            append_sheet("mantenimientos", row)
            st.success("Guardado correctamente.")
            st.rerun()


    st.divider()


    # ================================
    # CHECK-IN / CHECK-OUT
    # ================================

    st.header("⏱ Check-In / Check-Out")

    with st.expander("🔵 Iniciar Check-In"):
        with st.form("form_check_in"):
            eq = st.text_input("Equipo")
            desc = st.text_area("Descripción")
            rp = st.text_input("Realizado por")

            if st.form_submit_button("INICIAR"):
                add_active_checkin(eq, desc, rp)
                st.success("Check-in iniciado.")
                st.rerun()

    st.subheader("Check-ins activos")

    activos = get_active_checkins()

    if activos.empty:
        st.info("No hay check-ins activos.")
    else:
        st.dataframe(activos)

        indice = st.number_input(
            "Seleccionar fila", min_value=0, max_value=len(activos)-1, step=1
        )

        est_final = st.selectbox("Estatus final", ["Terminado", "Cancelado"])

        if st.button("FINALIZAR CHECK-OUT"):
            row = activos.iloc[indice].to_dict()
            finalize_active_checkin(row, est_final)
            st.success("Check-out completado.")
            st.rerun()

    st.divider()


    # ================================
    # DASHBOARD
    # ================================
    st.header("📊 Dashboard")

    df = read_sheet("mantenimientos")

    if df.empty:
        st.warning("No hay datos aún.")
        return

    st.subheader("Horas por equipo")

    horas = df.groupby("Equipo")["tiempo_hrs"].sum()

    fig, ax = plt.subplots()
    horas.plot(kind="bar", ax=ax)
    ax.set_ylabel("Horas")
    ax.set_title("Tiempo acumulado por equipo")

    st.pyplot(fig)

    st.dataframe(df)

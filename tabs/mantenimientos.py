import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt

from utils import (
    read_sheet,
    append_sheet,
    add_active_checkin,
    get_active_checkins,
    finalize_active_checkin,
)


def show_mantenimientos():

    st.title("🛠 Mantenimientos - Registro y Dashboard")

    st.subheader("➕ Registrar mantenimiento manual")

    with st.form("manual_form"):
        fecha = st.date_input("Fecha")
        equipo = st.text_input("Equipo")
        descripcion = st.text_area("Descripción")
        realizado_por = st.text_input("Realizado por")
        estatus = st.selectbox("Estatus", ["Terminado", "En proceso", "Pendiente"])
        tiempo_hrs = st.number_input("Tiempo (hrs)", min_value=0.0)
        hora_inicio = st.time_input("Hora inicio")
        hora_fin = st.time_input("Hora fin")

        enviar = st.form_submit_button("Guardar mantenimiento")

        if enviar:
            row = {
                "Fecha": str(fecha),
                "Equipo": equipo,
                "Descripcion": descripcion,
                "Realizado_por": realizado_por,
                "estatus": estatus,
                "tiempo_hrs": tiempo_hrs,
                "hora_inicio": hora_inicio.strftime("%H:%M:%S"),
                "hora_fin": hora_fin.strftime("%H:%M:%S"),
            }

            append_sheet("mantenimientos", row)
            st.success("Guardado correctamente.")
            st.rerun()

    st.divider()

    # ======================= CHECK-IN / OUT ==============================

    st.subheader("⏱ Registrar tiempo — CHECK-IN / CHECK-OUT")

    with st.expander("🔵 Check-In"):
        with st.form("checkin_form"):
            eq = st.text_input("Equipo")
            desc = st.text_area("Descripción")
            rp = st.text_input("Realizado por")

            if st.form_submit_button("Iniciar Check-In"):
                add_active_checkin(eq, desc, rp)
                st.success("Check-in iniciado.")
                st.rerun()

    st.subheader("🔴 Activos en Check-In:")
    activos = get_active_checkins()

    if not activos.empty:
        st.dataframe(activos)

        idx = st.number_input("ID del check-in a cerrar", min_value=0, max_value=len(activos)-1)
        est = st.selectbox("Estatus final", ["Terminado", "Cancelado"])

        if st.button("Finalizar Check-Out"):
            fila = activos.iloc[idx].to_dict()
            finalize_active_checkin(fila, est)
            st.success("Check-out finalizado.")
            st.rerun()
    else:
        st.info("No hay check-ins activos.")

    st.divider()

    # ======================= DASHBOARD ==============================

    st.header("📊 Dashboard")

    df = read_sheet("mantenimientos")

    if df.empty:
        st.warning("No hay registros aún.")
        return

    st.subheader("Horas por equipo")

    horas = df.groupby("Equipo")["tiempo_hrs"].sum()

    fig, ax = plt.subplots()
    horas.plot(kind="bar", ax=ax)
    ax.set_ylabel("Horas")
    ax.set_title("Tiempo acumulado por equipo")

    st.pyplot(fig)

    st.subheader("Tabla completa")
    st.dataframe(df)

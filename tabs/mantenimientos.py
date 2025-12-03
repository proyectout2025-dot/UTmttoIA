# tabs/mantenimientos.py
import streamlit as st
import pandas as pd
from datetime import datetime
from utils import (
    read_sheet,
    append_row,
    get_active_checkins,
    add_active_checkin,
    finalize_active_checkin_by_rownum,
)

def show_mantenimientos():
    st.header("🛠 Mantenimientos")

    # ==========================
    #   FORMULARIO DE REGISTRO
    # ==========================
    st.subheader("Registrar nuevo mantenimiento")

    fecha = st.date_input("Fecha")
    equipo = st.text_input("Equipo")
    descripcion = st.text_area("Descripción")
    realizado_por = st.text_input("Realizado por")
    estatus = st.selectbox("Estatus", ["Completado", "Pendiente"])

    # ------------------------------
    # CHECK-IN / CHECK-OUT
    # ------------------------------
    st.subheader("⏱ Control de Tiempos (Check-In / Check-Out)")

    activos = get_active_checkins()  # lista de dicts
    equipos_activos = [a["Equipo"] for a in activos] if activos else []

    equipo_sel = st.text_input("Equipo para control de tiempo")

    # Buscar check-in activo de este equipo
    activo = None
    if activos:
        for a in activos:
            if a["Equipo"] == equipo_sel:
                activo = a
                break

    # Estado actual
    if activo:
        st.warning(f"🔴 Check-IN ACTIVO desde: {activo['hora_inicio']}")
    else:
        st.info("🟢 No hay check-in activo para este equipo.")

    # ------------------ CHECK-IN ------------------
    if not activo:
        if st.button("Iniciar Check-In"):
            if equipo_sel.strip() == "":
                st.error("Debes escribir un equipo.")
            else:
                add_active_checkin(equipo_sel, descripcion, realizado_por)
                st.success("Check-In iniciado ✔")
                st.rerun()

    # ------------------ CHECK-OUT ------------------
    if activo:
        if st.button("Finalizar Check-Out"):
            # ubicar número de fila
            index = activos.index(activo)
            fila = index + 2  # porque fila 1 son encabezados

            ok = finalize_active_checkin_by_rownum(
                fila,
                estatus,
                descripcion,
            )
            if ok:
                st.success("✔ Check-Out completado y guardado.")
            else:
                st.error("No se pudo finalizar el check-out.")
            st.rerun()

    # ==========================
    #   REGISTRO MANUAL SIN CHECK-IN
    # ==========================
    st.subheader("Registro manual de mantenimiento (sin check-in)")
    if st.button("Guardar mantenimiento manual"):
        row = [
            str(fecha),
            equipo,
            descripcion,
            realizado_por,
            estatus,
            "",
            "",
            ""
        ]
        ok = append_row("mantenimientos", row)
        if ok:
            st.success("Mantenimiento guardado ✔")
        else:
            st.error("Error guardando mantenimiento.")

    # ==========================
    #   HISTORIAL
    # ==========================
    st.subheader("📘 Historial de Mantenimientos")

    data = read_sheet("mantenimientos")
    if data:
        df = pd.DataFrame(data)
        st.dataframe(df, use_container_width=True)

        # ======================
        #     GRAFICAS
        # ======================
        st.subheader("📊 Reporte de Horas por Equipo")
        if "tiempo_hrs" in df.columns:
            try:
                df["tiempo_hrs"] = pd.to_numeric(df["tiempo_hrs"], errors="coerce").fillna(0)
                horas = df.groupby("Equipo")["tiempo_hrs"].sum()

                st.bar_chart(horas)
            except Exception as e:
                st.error(f"Error generando gráfico: {e}")

    else:
        st.info("No hay mantenimientos registrados todavía.")

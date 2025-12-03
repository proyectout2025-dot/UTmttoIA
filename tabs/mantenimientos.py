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

    # ============================================
    #   FORMULARIO DE MANTENIMIENTO MANUAL
    # ============================================
    st.subheader("📄 Registro manual (sin check-in)")

    fecha_val = st.date_input("Fecha")
    equipo_val = st.text_input("Equipo")
    descripcion_val = st.text_area("Descripción")
    realizado_por_val = st.text_input("Realizado por")
    estatus_val = st.selectbox("Estatus", ["Completado", "Pendiente"])

    if st.button("Guardar mantenimiento manual"):
        row = [
            str(fecha_val),
            equipo_val,
            descripcion_val,
            realizado_por_val,
            estatus_val,
            "",     # tiempo_hrs
            "",     # hora_inicio
            ""      # hora_fin
        ]
        ok = append_row("mantenimientos", row)
        if ok:
            st.success("Mantenimiento guardado ✔")
        else:
            st.error("❌ No se pudo guardar el mantenimiento.")

    # ============================================
    #   CONTROL DE TIEMPOS (CHECK-IN / CHECK-OUT)
    # ============================================
    st.subheader("⏱ Control de Tiempos")

    activos = get_active_checkins()  # lista de dicts basada en encabezados reales
    equipos_activos = [a["Equipo"] for a in activos] if activos else []

    equipo_sel = st.text_input("Equipo para Check-In / Check-Out")

    # Identificar si este equipo tiene check-in activo
    activo = None
    if activos:
        for a in activos:
            if a["Equipo"] == equipo_sel:
                activo = a
                break

    # Mostrar estado
    if activo:
        st.warning(f"🔴 Check-IN ACTIVO desde: {activo['hora_inicio']}")
    else:
        st.info("🟢 No hay check-in activo para este equipo.")

    # ------------------ CHECK-IN ------------------
    descripcion_checkin = st.text_input("Descripción del mantenimiento (check-in)")
    realizado_por_checkin = st.text_input("Realizado por (check-in)")

    if not activo:
        if st.button("Iniciar Check-In"):
            if equipo_sel.strip() == "":
                st.error("Debes escribir un equipo.")
            else:
                add_active_checkin(
                    equipo_sel,
                    descripcion_checkin,
                    realizado_por_checkin
                )
                st.success("✔ Check-In iniciado")
                st.rerun()

    # ------------------ CHECK-OUT ------------------
    if activo:
        estatus_checkout = st.selectbox("Estatus", ["Completado", "Pendiente"], key="est_co")
        descripcion_checkout = st.text_area("Descripción final", key="des_co")

        if st.button("Finalizar Check-Out"):
            idx = activos.index(activo)
            fila = idx + 2  # fila 1 = encabezados, fila 2 = primer dato

            ok = finalize_active_checkin_by_rownum(
                fila,
                estatus_checkout,
                descripcion_checkout,
            )

            if ok:
                st.success("✔ Check-Out finalizado y registrado")
            else:
                st.error("❌ Error al finalizar Check-Out")

            st.rerun()

    # ============================================
    #   HISTORIAL DE MANTENIMIENTOS
    # ============================================
    st.subheader("📘 Historial de Mantenimientos")

    data = read_sheet("mantenimientos")
    if not data:
        st.info("No hay registros todavía.")
        return

    df = pd.DataFrame(data)

    st.dataframe(df, use_container_width=True)

    # ============================================
    #   GRAFICO DE HORAS POR EQUIPO
    # ============================================
    if "tiempo_hrs" in df.columns:
        try:
            df["tiempo_hrs"] = pd.to_numeric(df["tiempo_hrs"], errors="coerce").fillna(0)
            graf = df.groupby("Equipo")["tiempo_hrs"].sum()
            st.subheader("📊 Horas invertidas por equipo")
            st.bar_chart(graf)
        except Exception as e:
            st.error(f"Error generando gráfico: {e}")

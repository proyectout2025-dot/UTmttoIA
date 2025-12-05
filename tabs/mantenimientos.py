# tabs/mantenimientos.py
import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
from datetime import datetime

from utils import (
    read_sheet,
    append_row,
    get_active_checkins,
    start_checkin,
    finalize_checkin_by_equipo,
    ensure_headers
)

# FIJAMOS listas para mantener estabilidad y reducir lecturas
EQUIPOS = ["Equipo 1", "Equipo 2", "Equipo 3"]
TECNICOS = ["Técnico 1", "Técnico 2", "Técnico 3"]
TIPOS = ["Correctivo", "Preventivo", "Predictivo"]

MAINT_SHEET = "mantenimientos"
CHECKIN_SHEET = "checkin_activos"

# aseguramos encabezados (puedes quitar si ya los aseguraste en app.py)
ensure_headers(MAINT_SHEET, ["Fecha", "Equipo", "Descripcion", "Realizado_por", "estatus", "tiempo_hrs", "hora_inicio", "hora_fin"])
ensure_headers(CHECKIN_SHEET, ["Equipo", "Realizado_por", "hora_inicio", "Tipo"])

def show_mantenimientos():
    st.header("🛠 Mantenimientos (Versión Estable)")

    # ---- Check-in / Check-out ----
    st.subheader("⏱ Control de tiempos")
    equipo_ci = st.selectbox("Equipo (Check)", EQUIPOS, key="equipo_ci")
    tecnico_ci = st.selectbox("Técnico (Check)", TECNICOS, key="tecnico_ci")
    tipo_ci = st.selectbox("Tipo (Check)", TIPOS, key="tipo_ci")

    activos = get_active_checkins() or []
    activo = next((a for a in activos if a.get("Equipo") == equipo_ci), None)

    if activo:
        st.warning(f"🔴 Check-in activo desde: {activo.get('hora_inicio')}")
        if st.button("Finalizar Check-out", key="btn_finish"):
            ok = finalize_checkin_by_equipo(equipo_ci)
            if ok:
                st.success("Check-out finalizado y registrado.")
                st.rerun()
    else:
        if st.button("Iniciar Check-in", key="btn_start"):
            start_checkin(equipo_ci, tecnico_ci, tipo_ci)
            st.success("Check-in iniciado.")
            st.rerun()

    st.divider()

    # ---- Registro manual ----
    st.subheader("📝 Registro Manual de Mantenimiento")
    fecha = st.date_input("Fecha", value=datetime.now().date(), key="man_fecha")
    equipo_m = st.selectbox("Equipo", EQUIPOS, key="man_equipo")
    tipo_m = st.selectbox("Tipo de mantenimiento", TIPOS, key="man_tipo")
    tecnico_m = st.selectbox("Realizado por", TECNICOS, key="man_tecnico")
    descripcion = st.text_area("Descripción (breve)", key="man_desc")
    tiempo = st.number_input("Tiempo (hrs)", min_value=0.0, step=0.25, key="man_tiempo")

    if st.button("Guardar mantenimiento manual", key="btn_save_manual"):
        row = [
            fecha.strftime("%Y-%m-%d"),
            equipo_m,
            f"{descripcion} [Tipo:{tipo_m}]",
            tecnico_m,
            "Completado",
            tiempo,
            "",
            datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        ]
        append_row(MAINT_SHEET, row)
        st.success("Mantenimiento guardado.")
        st.rerun()

    st.divider()

    # ---- Historial y gráfica única ----
    st.subheader("📊 Historial y Estadística")

    data = read_sheet(MAINT_SHEET) or []
    if not data:
        st.info("No hay registros aún.")
        return

    df = pd.DataFrame(data)

    # Mostrar tabla (no recargar la hoja)
    st.dataframe(df, use_container_width=True)

    # Selector de tipo de gráfico (una sola a la vez)
    option = st.selectbox("Mostrar gráfico por", ["Equipo", "Realizado_por", "Tipo (extraído de Descripcion)"], key="graf_sel")

    fig, ax = plt.subplots(figsize=(6, 3))
    if option == "Equipo" and "Equipo" in df.columns:
        s = df["Equipo"].value_counts().sort_values(ascending=False)
        s.plot(kind="bar", ax=ax)
        ax.set_ylabel("Cantidad")
        ax.set_title("Mantenimientos por Equipo")
    elif option == "Realizado_por" and "Realizado_por" in df.columns:
        s = df["Realizado_por"].value_counts().sort_values(ascending=False)
        s.plot(kind="bar", ax=ax)
        ax.set_ylabel("Cantidad")
        ax.set_title("Mantenimientos por Técnico")
    else:
        # Extraer Tipo desde Descripcion: asumimos formato "... [Tipo:XXX]"
        def extract_tipo(desc):
            try:
                if not isinstance(desc, str):
                    return "Desconocido"
                if "[Tipo:" in desc:
                    part = desc.split("[Tipo:")[-1]
                    return part.split("]")[0].strip()
                return "Desconocido"
            except:
                return "Desconocido"
        df["_Tipo_ex"] = df.get("Descripcion", "").apply(extract_tipo) if "Descripcion" in df.columns else pd.Series(["Desconocido"] * len(df))
        s = df["_Tipo_ex"].value_counts().sort_values(ascending=False)
        s.plot(kind="bar", ax=ax)
        ax.set_ylabel("Cantidad")
        ax.set_title("Mantenimientos por Tipo")
    st.pyplot(fig)

# tabs/mantenimientos.py
import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
from io import BytesIO
from datetime import datetime

from utils import (
    read_sheet,
    append_row,
    append_sheet,
    get_active_checkins,
    add_active_checkin,
    finalize_active_checkin_by_rownum,
)

TIPOS_MTTO = ["Correctivo", "Preventivo", "Predictivo"]
MAIN_SHEET = "mantenimientos"

def _df_to_excel_bytes(df: pd.DataFrame) -> BytesIO:
    buf = BytesIO()
    with pd.ExcelWriter(buf, engine="openpyxl") as writer:
        df.to_excel(writer, index=False, sheet_name="mantenimientos")
    buf.seek(0)
    return buf

def _load_equipos():
    cfg = read_sheet("config") or []
    defaults = ["Equipo 1", "Equipo 2", "Equipo 3"]
    equipos = list(defaults)
    for r in cfg:
        if str(r.get("Parametro","")).strip().lower() == "equipo":
            v = str(r.get("Valor","")).strip()
            if v and v not in equipos:
                equipos.append(v)
    equipos.append("➕ Agregar nuevo equipo")
    return equipos

def _load_tecnicos():
    cfg = read_sheet("config") or []
    defaults = ["Wesley Cunningham", "Misael Lopez", "Eduardo Vazquez"]
    tecnicos = list(defaults)
    for r in cfg:
        if str(r.get("Parametro","")).strip().lower() == "tecnico":
            v = str(r.get("Valor","")).strip()
            if v and v not in tecnicos:
                tecnicos.append(v)
    tecnicos.append("➕ Agregar nuevo técnico")
    return tecnicos

def show_mantenimientos():
    st.header("🛠 Mantenimientos — Registro, Tiempos y Reportes")

    # Forms: manual
    equipos = _load_equipos()
    tecnicos = _load_tecnicos()

    with st.form("manual_form", clear_on_submit=True):
        col1, col2 = st.columns([2,1])
        with col1:
            fecha = st.date_input("Fecha", value=datetime.now().date(), key="manual_fecha")
            equipo = st.selectbox("Equipo", options=equipos, key="manual_equipo")
            if equipo == "➕ Agregar nuevo equipo":
                equipo_nuevo = st.text_input("Nombre del nuevo equipo", key="manual_equipo_nuevo")
            else:
                equipo_nuevo = None
            tipo = st.selectbox("Tipo de mantenimiento", TIPOS_MTTO, key="manual_tipo")
            descripcion = st.text_area("Descripción (breve)", max_chars=300, key="manual_descripcion")
        with col2:
            tecnico = st.selectbox("Realizado por", options=tecnicos, key="manual_tecnico")
            if tecnico == "➕ Agregar nuevo técnico":
                tecnico_nuevo = st.text_input("Nombre del nuevo técnico", key="manual_tecnico_nuevo")
            else:
                tecnico_nuevo = None
            estatus = st.selectbox("Estatus", ["Completado", "En proceso", "Pendiente"], key="manual_estatus")
            tiempo = st.number_input("Tiempo (hrs)", min_value=0.0, step=0.25, key="manual_tiempo")
        submitted = st.form_submit_button("Guardar mantenimiento", type="secondary", key="manual_submit")

    if submitted:
        final_equipo = equipo_nuevo.strip() if (equipo_nuevo and equipo_nuevo.strip()) else equipo
        final_tecnico = tecnico_nuevo.strip() if (tecnico_nuevo and tecnico_nuevo.strip()) else tecnico

        if equipo_nuevo:
            append_sheet("config", {"Parametro":"equipo","Valor":final_equipo})
        if tecnico_nuevo:
            append_sheet("config", {"Parametro":"tecnico","Valor":final_tecnico})

        row = {
            "Fecha": str(fecha),
            "Equipo": final_equipo,
            "Descripcion": descripcion,
            "Realizado_por": final_tecnico,
            "estatus": estatus,
            "tiempo_hrs": tiempo,
            "hora_inicio": "",
            "hora_fin": "",
            "Tipo": tipo
        }
        ok = append_sheet("mantenimientos", row)
        if ok:
            st.success("Mantenimiento guardado.")
            st.rerun()
        else:
            st.error("Error al guardar mantenimiento.")

    st.markdown("---")

    # Check-in form
    st.subheader("⏱ Check-In / Check-Out")
    activos = get_active_checkins() or []

    with st.expander("🔵 Ver check-ins activos", expanded=False):
        if activos:
            df_act = pd.DataFrame(activos)
            st.dataframe(df_act, width="stretch")
        else:
            st.info("No hay check-ins activos.")

    with st.form("checkin_form", clear_on_submit=True):
        ci_equipo = st.selectbox("Equipo (Check-In)", options=equipos, key="ci_equipo")
        if ci_equipo == "➕ Agregar nuevo equipo":
            ci_equipo_nuevo = st.text_input("Nombre nuevo equipo (CI)", key="ci_equipo_nuevo")
        else:
            ci_equipo_nuevo = None
        ci_desc = st.text_area("Descripción (CI)", max_chars=250, key="ci_descripcion")
        ci_tecnico = st.selectbox("Técnico (CI)", options=tecnicos, key="ci_tecnico")
        if ci_tecnico == "➕ Agregar nuevo técnico":
            ci_tecnico_nuevo = st.text_input("Nombre nuevo técnico (CI)", key="ci_tecnico_nuevo")
        else:
            ci_tecnico_nuevo = None

        iniciar = st.form_submit_button("Iniciar Check-In", type="primary", key="ci_submit")
    if iniciar:
        final_equipo_ci = ci_equipo_nuevo.strip() if (ci_equipo_nuevo and ci_equipo_nuevo.strip()) else ci_equipo
        final_tecnico_ci = ci_tecnico_nuevo.strip() if (ci_tecnico_nuevo and ci_tecnico_nuevo.strip()) else ci_tecnico

        exists = any((a.get("Equipo") == final_equipo_ci and a.get("Realizado_por") == final_tecnico_ci) for a in activos)
        if exists:
            st.warning("Ya existe un check-in activo para este equipo y técnico.")
        else:
            if ci_equipo_nuevo:
                append_sheet("config", {"Parametro":"equipo","Valor":final_equipo_ci})
            if ci_tecnico_nuevo:
                append_sheet("config", {"Parametro":"tecnico","Valor":final_tecnico_ci})
            add_active_checkin(final_equipo_ci, ci_desc, final_tecnico_ci)
            st.success("Check-In iniciado.")
            st.rerun()

    st.markdown("---")

    # Finalizar check-out selection
    st.subheader("Finalizar Check-Out")
    activos = get_active_checkins() or []
    if activos:
        choices = [f"{i+2} | {a.get('Equipo','')} | {a.get('Realizado_por','')} | {a.get('hora_inicio','')}" for i,a in enumerate(activos)]
        sel = st.selectbox("Selecciona Check-In a finalizar", options=["--"]+choices, key="sel_checkout")
        if sel and sel != "--":
            rownum = int(sel.split("|")[0].strip())
            estatus_checkout = st.selectbox("Estatus final", options=["Completado","Pendiente","Cancelado"], key="estatus_checkout")
            desc_final = st.text_area("Descripción final (opcional)", key="desc_final_checkout")
            if st.button("Finalizar Check-Out", key="btn_finalize_checkout"):
                ok = finalize_active_checkin_by_rownum(rownum, estatus_checkout, desc_final)
                if ok:
                    st.success("Check-Out finalizado y guardado en historial.")
                    st.rerun()
                else:
                    st.error("No se pudo finalizar el Check-Out.")
    else:
        st.info("No hay check-ins activos para finalizar.")

    st.markdown("---")

    # Historial y reportes
    st.subheader("Historial y Reportes")
    data = read_sheet("mantenimientos") or []
    if not data:
        st.info("No hay registros en el historial todavía.")
        return
    df = pd.DataFrame(data)
    if "Fecha" in df.columns:
        df["Fecha"] = pd.to_datetime(df["Fecha"], errors="coerce")

    # Sidebar filters
    st.sidebar.header("Filtros - Historial")
    min_date = df["Fecha"].min().date() if "Fecha" in df.columns and not df["Fecha"].isna().all() else None
    max_date = df["Fecha"].max().date() if "Fecha" in df.columns and not df["Fecha"].isna().all() else None
    date_range = st.sidebar.date_input("Rango de fechas", value=(min_date, max_date) if min_date else ())
    equipos_filter = st.sidebar.multiselect("Equipo", options=sorted(df["Equipo"].dropna().unique().tolist()) if "Equipo" in df.columns else [], key="f_equipos")
    tecnicos_filter = st.sidebar.multiselect("Técnico", options=sorted(df["Realizado_por"].dropna().unique().tolist()) if "Realizado_por" in df.columns else [], key="f_tecnicos")
    estatus_filter = st.sidebar.multiselect("Estatus", options=sorted(df["estatus"].dropna().unique().tolist()) if "estatus" in df.columns else [], key="f_estatus")
    tipo_filter = st.sidebar.multiselect("Tipo", options=sorted(df["Tipo"].dropna().unique().tolist()) if "Tipo" in df.columns else [], key="f_tipo")
    search_text = st.sidebar.text_input("Buscar (descripcion/equipo/tecnico)", key="f_search")

    df_filtered = df.copy()
    if isinstance(date_range, tuple) and len(date_range) == 2 and all(date_range):
        start, end = date_range
        df_filtered = df_filtered[(df_filtered["Fecha"].dt.date >= start) & (df_filtered["Fecha"].dt.date <= end)]
    if equipos_filter:
        df_filtered = df_filtered[df_filtered["Equipo"].isin(equipos_filter)]
    if tecnicos_filter:
        df_filtered = df_filtered[df_filtered["Realizado_por"].isin(tecnicos_filter)]
    if estatus_filter:
        df_filtered = df_filtered[df_filtered["estatus"].isin(estatus_filter)]
    if tipo_filter:
        df_filtered = df_filtered[df_filtered["Tipo"].isin(tipo_filter)]
    if search_text:
        mask = df_filtered.apply(lambda r: search_text.lower() in str(r.get("Descripcion","")).lower()
                                 or search_text.lower() in str(r.get("Equipo","")).lower()
                                 or search_text.lower() in str(r.get("Realizado_por","")).lower(), axis=1)
        df_filtered = df_filtered[mask]

    st.dataframe(df_filtered, width="stretch")

    # Export buttons
    csv_bytes = df_filtered.to_csv(index=False).encode("utf-8")
    st.download_button("📥 Descargar CSV", csv_bytes, file_name="mantenimientos_filtrados.csv", mime="text/csv")

    try:
        xlsx = _df_to_excel_bytes(df_filtered)
        st.download_button("📥 Descargar XLSX", xlsx, file_name="mantenimientos_filtrados.xlsx",
                           mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
    except Exception:
        pass

    st.markdown("---")
    st.subheader("📊 Gráficas")
    if "tiempo_hrs" in df_filtered.columns:
        try:
            df_filtered["tiempo_hrs"] = pd.to_numeric(df_filtered["tiempo_hrs"], errors="coerce").fillna(0)
            grp_e = df_filtered.groupby("Equipo")["tiempo_hrs"].sum().sort_values(ascending=False)
            if not grp_e.empty:
                fig_e, ax_e = plt.subplots()
                grp_e.plot(kind="bar", ax=ax_e)
                ax_e.set_ylabel("Horas")
                ax_e.set_title("Horas por equipo")
                st.pyplot(fig_e)

            grp_t = df_filtered.groupby("Realizado_por")["tiempo_hrs"].sum().sort_values(ascending=False)
            if not grp_t.empty:
                fig_t, ax_t = plt.subplots()
                grp_t.plot(kind="bar", ax=ax_t)
                ax_t.set_ylabel("Horas")
                ax_t.set_title("Horas por técnico")
                st.pyplot(fig_t)
        except Exception:
            st.warning("No se pudieron generar algunas gráficas.")

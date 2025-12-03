# tabs/mantenimientos.py
import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
from io import BytesIO

from utils import (
    read_sheet,
    append_sheet,
    add_active_checkin,
    get_active_checkins,
    finalize_active_checkin,
)

SPREADSHEET = "base_datos_app"
MANT_SHEET = "mantenimientos"
CHECKIN_SHEET = "checkin_activos"

st.set_option("deprecation.showPyplotGlobalUse", False)

def _df_to_excel_bytes(df: pd.DataFrame) -> BytesIO:
    buf = BytesIO()
    with pd.ExcelWriter(buf, engine="openpyxl") as writer:
        df.to_excel(writer, index=False, sheet_name="mantenimientos")
    buf.seek(0)
    return buf

def show_mantenimientos():
    st.header("🛠 Mantenimientos — Registro, Check-In/Out y Reportes")

    # --- Historial inicial (para mostrar en UI)
    df = read_sheet(SPREADSHEET, MANT_SHEET)
    if df is None or df.empty:
        df = pd.DataFrame(columns=["Fecha","Equipo","Descripcion","Realizado_por","estatus","tiempo_hrs","hora_inicio","hora_fin"])

    # Sidebar filtros
    st.sidebar.header("Filtros")
    min_date = pd.to_datetime(df["Fecha"], errors="coerce").min() if "Fecha" in df.columns else None
    max_date = pd.to_datetime(df["Fecha"], errors="coerce").max() if "Fecha" in df.columns else None
    date_range = st.sidebar.date_input("Rango fechas", value=(min_date.date() if min_date is not None else None, max_date.date() if max_date is not None else None))
    equipos = df["Equipo"].dropna().unique().tolist() if "Equipo" in df.columns else []
    tecnicos = df["Realizado_por"].dropna().unique().tolist() if "Realizado_por" in df.columns else []
    estatus_list = df["estatus"].dropna().unique().tolist() if "estatus" in df.columns else []

    sel_equipos = st.sidebar.multiselect("Equipo", options=equipos)
    sel_tecnicos = st.sidebar.multiselect("Técnico", options=tecnicos)
    sel_estatus = st.sidebar.multiselect("Estatus", options=estatus_list)

    # --- Check-ins activos
    st.subheader("🔵 Check-Ins activos")
    activos = get_active_checkins(SPREADSHEET)
    if activos:
        df_act = pd.DataFrame(activos)
        st.dataframe(df_act, use_container_width=True)
    else:
        st.info("No hay check-ins activos.")

    st.markdown("---")

    # --- Iniciar Check-In
    st.subheader("🔔 Iniciar Check-In")
    with st.form("form_checkin"):
        ci_equipo = st.text_input("Equipo", key="ci_equipo")
        ci_descripcion = st.text_area("Descripción", key="ci_descripcion")
        ci_tecnico = st.text_input("Realizado por", key="ci_tecnico")
        submitted_ci = st.form_submit_button("Iniciar Check-In")
    if submitted_ci:
        if not ci_equipo or not ci_tecnico:
            st.error("Equipo y Técnico son obligatorios.")
        else:
            ok = add_active_checkin(SPREADSHEET, ci_equipo, ci_descripcion, ci_tecnico)
            if ok:
                st.success("Check-In registrado.")
                st.rerun()
            else:
                st.error("No se pudo registrar Check-In.")

    st.markdown("---")

    # --- Finalizar Check-Out
    st.subheader("🔴 Finalizar Check-Out")
    activos = get_active_checkins(SPREADSHEET)
    if activos:
        # show select with human-friendly string
        choices = [f"{a['_row']} | {a.get('Equipo','')} | {a.get('Realizado_por','')} | {a.get('hora_inicio','')}" for a in activos]
        sel = st.selectbox("Seleccione check-in a finalizar", options=["--"] + choices, key="sel_checkout")
        if sel and sel != "--":
            row_num = int(sel.split("|")[0].strip())
            est_final = st.selectbox("Estatus final", ["Completado","Pendiente","Cancelado"], key="status_checkout")
            desc_override = st.text_area("Descripción final (opcional)", height=80)
            if st.button("Finalizar Check-Out", key="btn_finalize"):
                ok = finalize_active_checkin(SPREADSHEET, row_num, est_final, desc_override)
                if ok:
                    st.success("Check-Out finalizado y guardado en historial.")
                    st.rerun()
                else:
                    st.error("No se pudo finalizar el Check-Out.")
    else:
        st.info("No hay check-ins activos.")

    st.markdown("---")

    # --- Historial filtrado y gráficos
    st.subheader("📚 Historial (filtrado)")

    df = read_sheet(SPREADSHEET, MANT_SHEET)
    if df is None or df.empty:
        st.info("No hay registros en historial.")
        return

    # Apply filters
    df["Fecha"] = pd.to_datetime(df["Fecha"], errors="coerce")
    if isinstance(date_range, tuple) and len(date_range) == 2 and all(date_range):
        start, end = date_range
        df = df[(df["Fecha"].dt.date >= start) & (df["Fecha"].dt.date <= end)]
    if sel_equipos:
        df = df[df["Equipo"].isin(sel_equipos)]
    if sel_tecnicos:
        df = df[df["Realizado_por"].isin(sel_tecnicos)]
    if sel_estatus:
        df = df[df["estatus"].isin(sel_estatus)]

    st.dataframe(df, use_container_width=True)

    st.markdown("---")
    st.subheader("📊 Gráficas")

    # horas por equipo
    if "Equipo" in df.columns and "tiempo_hrs" in df.columns:
        grp = df.groupby("Equipo")["tiempo_hrs"].sum().sort_values(ascending=False)
        fig, ax = plt.subplots()
        grp.plot(kind="bar", ax=ax)
        ax.set_ylabel("Horas")
        ax.set_title("Horas por equipo")
        st.pyplot(fig)

    # horas por técnico
    if "Realizado_por" in df.columns and "tiempo_hrs" in df.columns:
        grp2 = df.groupby("Realizado_por")["tiempo_hrs"].sum().sort_values(ascending=False)
        fig2, ax2 = plt.subplots()
        grp2.plot(kind="bar", ax=ax2)
        ax2.set_ylabel("Horas")
        ax2.set_title("Horas por técnico")
        st.pyplot(fig2)

    # estatus counts
    if "estatus" in df.columns:
        est_counts = df["estatus"].value_counts()
        fig3, ax3 = plt.subplots()
        est_counts.plot(kind="bar", ax=ax3)
        ax3.set_ylabel("Cantidad")
        ax3.set_title("Mantenimientos por estatus")
        st.pyplot(fig3)

    # Export buttons
    csv_bytes = df.to_csv(index=False).encode("utf-8")
    st.download_button("📥 Descargar CSV (filtrado)", csv_bytes, "mantenimientos_filtrado.csv", "text/csv")

    try:
        xlsx = _df_to_excel_bytes(df)
        st.download_button("📥 Descargar XLSX (filtrado)", xlsx, "mantenimientos_filtrado.xlsx", "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
    except Exception as e:
        st.warning(f"No se pudo generar XLSX: {e}")

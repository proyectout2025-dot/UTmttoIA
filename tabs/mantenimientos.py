# tabs/mantenimientos.py
import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from io import BytesIO
from datetime import datetime, timezone
from utils import (
    read_sheet,
    append_sheet,
    add_active_checkin,
    get_active_checkins,
    finalize_active_checkin,
)

# CONSTANTES: nombre de spreadsheet y worksheet
SPREADSHEET = "base_datos_app"
WORKSHEET = "mantenimientos"
CHECKIN_SHEET = "checkin_activos"  # usado por utils internamente

# -------------------------
# Helpers
# -------------------------
def _load_data():
    df = read_sheet(SPREADSHEET, WORKSHEET)
    if df is None or len(df) == 0:
        return pd.DataFrame(columns=["Fecha", "Equipo", "Descripcion", "Realizado_por", "estatus", "tiempo_hrs", "hora_inicio", "hora_fin"])
    df = pd.DataFrame(df)
    # Normalizar nombres de columnas (asegurar que tengan exactamente los encabezados esperados)
    df.columns = [c.strip() for c in df.columns]
    # Convertir tipos
    if "Fecha" in df.columns:
        df["Fecha"] = pd.to_datetime(df["Fecha"], errors="coerce")
    if "hora_inicio" in df.columns:
        df["hora_inicio"] = pd.to_datetime(df["hora_inicio"], errors="coerce")
    if "hora_fin" in df.columns:
        df["hora_fin"] = pd.to_datetime(df["hora_fin"], errors="coerce")
    if "tiempo_hrs" in df.columns:
        df["tiempo_hrs"] = pd.to_numeric(df["tiempo_hrs"], errors="coerce").fillna(0.0)
    return df

def _seconds_to_hours_str(seconds):
    hrs = seconds / 3600.0
    return round(hrs, 2)

def _df_to_excel_bytes(df):
    output = BytesIO()
    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        df.to_excel(writer, index=False, sheet_name="mantenimientos")
        writer.save()
    output.seek(0)
    return output

# -------------------------
# UI principal
# -------------------------
def show_mantenimientos():
    st.header("🛠 Mantenimientos — Check-In / Check-Out, Dashboard y Reportes")

    # ---------- cargar datos ----------
    df = _load_data()

    # ---------- sidebar filtros ----------
    st.sidebar.header("Filtros")
    min_date = df["Fecha"].min().date() if ("Fecha" in df.columns and not df["Fecha"].isna().all()) else None
    max_date = df["Fecha"].max().date() if ("Fecha" in df.columns and not df["Fecha"].isna().all()) else None

    date_range = st.sidebar.date_input("Rango de fechas", value=(min_date, max_date) if min_date is not None else (), key="f_dates")
    equipos = df["Equipo"].dropna().unique().tolist() if "Equipo" in df.columns else []
    tecnicos = df["Realizado_por"].dropna().unique().tolist() if "Realizado_por" in df.columns else []
    estatus_list = df["estatus"].dropna().unique().tolist() if "estatus" in df.columns else []

    sel_equipos = st.sidebar.multiselect("Equipo", options=equipos, key="f_equipos")
    sel_tecnicos = st.sidebar.multiselect("Técnico", options=tecnicos, key="f_tecnicos")
    sel_estatus = st.sidebar.multiselect("Estatus", options=estatus_list, key="f_estatus")

    # Aplicar filtros
    df_filtered = df.copy()
    if date_range and len(date_range) == 2 and "Fecha" in df.columns:
        start, end = date_range
        df_filtered = df_filtered[(df_filtered["Fecha"].dt.date >= start) & (df_filtered["Fecha"].dt.date <= end)]
    if sel_equipos:
        df_filtered = df_filtered[df_filtered["Equipo"].isin(sel_equipos)]
    if sel_tecnicos:
        df_filtered = df_filtered[df_filtered["Realizado_por"].isin(sel_tecnicos)]
    if sel_estatus:
        df_filtered = df_filtered[df_filtered["estatus"].isin(sel_estatus)]

    # ---------- Check-Ins activos ----------
    st.subheader("🔵 Check-Ins activos")
    try:
        activos = get_active_checkins()  # lista de dicts
    except Exception as e:
        activos = []
        st.error(f"Error leyendo checkins activos: {e}")

    if activos:
        df_act = pd.DataFrame(activos)
        st.dataframe(df_act, use_container_width=True)
    else:
        st.info("No hay mantenimientos en curso.")

    st.markdown("---")

    # ---------- FORMULARIO: Iniciar Check-In ----------
    st.subheader("🔔 Iniciar mantenimiento (Check-In)")
    with st.form("form_checkin", clear_on_submit=False):
        ci_equipo = st.text_input("Equipo / Máquina", key="ci_equipo")
        ci_descripcion = st.text_area("Descripción breve", key="ci_descripcion")
        ci_tecnico = st.text_input("Realizado por", key="ci_tecnico")
        submitted_ci = st.form_submit_button("Iniciar Check-In")

    if submitted_ci:
        # Validación simple: no duplicados por mismo equipo+tecnico
        conflict = False
        for r in activos:
            if r.get("equipo") == ci_equipo and r.get("realizado_por") == ci_tecnico:
                conflict = True
                break
        if conflict:
            st.warning("Ya existe un Check-In activo para ese equipo / técnico.")
        else:
            record = {
                "id": str(pd.Timestamp.now().timestamp()).replace(".", ""),
                "equipo": ci_equipo,
                "descripcion": ci_descripcion,
                "realizado_por": ci_tecnico,
                "hora_inicio": datetime.now(timezone.utc).isoformat(),
                "estatus": "EN PROCESO",
            }
            try:
                add_active_checkin(record)
                st.success("Check-In registrado correctamente.")
                st.rerun()
            except Exception as e:
                st.error(f"Error al registrar Check-In: {e}")

    st.markdown("---")

    # ---------- Finalizar (Check-Out) ----------
    st.subheader("⏱ Finalizar mantenimiento (Check-Out)")
    activos = get_active_checkins() or []
    if activos:
        choices = [f"{r.get('id')} | {r.get('equipo')} | {r.get('realizado_por')} | {r.get('hora_inicio')}" for r in activos]
        sel = st.selectbox("Selecciona mantenimiento activo", options=["--"] + choices, key="select_checkout")
        if sel and sel != "--":
            chosen_id = sel.split("|")[0].strip()
            if st.button("Finalizar (Check-Out)", key="btn_checkout"):
                final_row, removed = finalize_active_checkin(chosen_id)
                if removed and final_row:
                    # Montar fila en orden de tu sheet: Fecha, Equipo, Descripcion, Realizado_por, estatus, tiempo_hrs, hora_inicio, hora_fin
                    row_list = [
                        final_row.get("fecha"),
                        final_row.get("equipo"),
                        final_row.get("descripcion"),
                        final_row.get("realizado_por"),
                        final_row.get("estatus"),
                        final_row.get("tiempo_hrs"),
                        final_row.get("hora_inicio"),
                        final_row.get("hora_fin"),
                    ]
                    try:
                        append_sheet(SPREADSHEET, WORKSHEET, {  # append_sheet espera row_dict en tu implementación final
                            "Fecha": row_list[0],
                            "Equipo": row_list[1],
                            "Descripcion": row_list[2],
                            "Realizado_por": row_list[3],
                            "estatus": row_list[4],
                            "tiempo_hrs": row_list[5],
                            "hora_inicio": row_list[6],
                            "hora_fin": row_list[7],
                        })
                        st.success("Check-Out finalizado y guardado en historial.")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Error guardando registro final: {e}")
                else:
                    st.error("No se pudo finalizar (registro no encontrado o ya eliminado).")
    else:
        st.info("No hay check-ins activos para finalizar.")

    st.markdown("---")

    # ---------- Historial filtrado y gráficos ----------
    st.subheader("📚 Historial (filtrado)")
    if df_filtered is None or df_filtered.empty:
        st.info("No hay registros que mostrar con los filtros actuales.")
    else:
        st.dataframe(df_filtered.reset_index(drop=True), use_container_width=True)

        st.markdown("---")
        st.subheader("📊 Gráficos")

        # Gráfico: estatus
        if "estatus" in df_filtered.columns:
            est_counts = df_filtered["estatus"].value_counts()
            fig, ax = plt.subplots()
            est_counts.plot(kind="bar", ax=ax)
            ax.set_title("Conteo por estatus")
            ax.set_ylabel("Cantidad")
            st.pyplot(fig)

        # Gráfico: horas por técnico
        if "Realizado_por" in df_filtered.columns and "tiempo_hrs" in df_filtered.columns:
            grp = df_filtered.groupby("Realizado_por")["tiempo_hrs"].sum().sort_values(ascending=False)
            fig2, ax2 = plt.subplots()
            grp.plot(kind="bar", ax=ax2)
            ax2.set_title("Horas por técnico")
            ax2.set_ylabel("Horas")
            st.pyplot(fig2)

        # Gráfico: horas por equipo
        if "Equipo" in df_filtered.columns and "tiempo_hrs" in df_filtered.columns:
            grp2 = df_filtered.groupby("Equipo")["tiempo_hrs"].sum().sort_values(ascending=False)
            fig3, ax3 = plt.subplots()
            grp2.plot(kind="bar", ax=ax3)
            ax3.set_title("Horas por equipo")
            ax3.set_ylabel("Horas")
            st.pyplot(fig3)

        # Gráfico: horas en el tiempo (semanal)
        date_col = "Fecha" if "Fecha" in df_filtered.columns else ("hora_inicio" if "hora_inicio" in df_filtered.columns else None)
        if date_col and "tiempo_hrs" in df_filtered.columns:
            ts = df_filtered.dropna(subset=[date_col]).set_index(pd.to_datetime(df_filtered[date_col]))
            weekly = ts["tiempo_hrs"].resample("W").sum()
            fig4, ax4 = plt.subplots()
            weekly.plot(ax=ax4)
            ax4.set_title("Horas por semana")
            ax4.set_ylabel("Horas")
            st.pyplot(fig4)

        # ---------- Export buttons ----------
        st.markdown("---")
        st.subheader("📥 Exportar datos")
        csv_bytes = df_filtered.to_csv(index=False).encode("utf-8")
        st.download_button("Descargar CSV", data=csv_bytes, file_name="mantenimientos_filtrados.csv", mime="text/csv", key="dl_csv")

        try:
            excel_io = _df_to_excel_bytes = _df_to_excel_bytes  # placeholder to call writer below
            # Use helper to produce excel
            excel_io = _df_to_excel_bytes(df_filtered)
            st.download_button("Descargar XLSX", data=excel_io, file_name="mantenimientos_filtrados.xlsx", mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", key="dl_xlsx")
        except Exception as e:
            st.warning(f"No se pudo generar XLSX: {e}")

    # Fin de la función

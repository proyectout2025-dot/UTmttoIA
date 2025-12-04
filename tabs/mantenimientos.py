# tabs/mantenimientos.py
import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
from io import BytesIO
from datetime import datetime

# Utils (asegúrate que utils.py expone estas funciones/nombres)
from utils import (
    read_sheet,
    append_row,
    append_sheet,
    get_active_checkins,
    add_active_checkin,
    finalize_active_checkin_by_rownum,
    get_gs_client,
    SHEET_URL
)


# ---------------------------
# Helpers
# ---------------------------
def _ensure_headers(sheet_name: str, required_headers: list):
    """
    Asegura que la hoja tiene al menos los encabezados requeridos.
    Si faltan, agrega las columnas faltantes al final de la fila de encabezados.
    """
    try:
        client = get_gs_client()
        sh = client.open_by_url(SHEET_URL)
        ws = sh.worksheet(sheet_name)
        existing = ws.row_values(1)
        if existing is None:
            existing = []
        # If any required header missing, append them
        missing = [h for h in required_headers if h not in existing]
        if missing:
            new_headers = existing + missing
            # replace header row (delete row 1 then insert new header)
            try:
                ws.delete_rows(1)
            except Exception:
                pass
            ws.insert_row(new_headers, index=1)
    except Exception as e:
        st.warning(f"No se pudo asegurar encabezados en '{sheet_name}': {e}")


def _df_to_excel_bytes(df: pd.DataFrame) -> BytesIO:
    buf = BytesIO()
    with pd.ExcelWriter(buf, engine="openpyxl") as writer:
        df.to_excel(writer, index=False, sheet_name="mantenimientos")
    buf.seek(0)
    return buf


# ---------------------------
# Config / List helpers
# ---------------------------
def _load_equipos():
    """
    Carga equipos desde la hoja config (Parametro='equipo') y añade defaults.
    """
    defaults = ["Equipo 1", "Equipo 2", "Equipo 3"]
    cfg = read_sheet("config") or []
    equipos = list(defaults)
    for r in cfg:
        p = str(r.get("Parametro", "")).strip()
        v = str(r.get("Valor", "")).strip()
        if p.lower() == "equipo" and v and v not in equipos:
            equipos.append(v)
    equipos.append("Agregar nuevo equipo")
    return equipos


def _load_tecnicos():
    """
    Carga técnicos desde hoja config (Parametro='tecnico') y añade defaults.
    """
    defaults = ["Wesley Cunningham", "Misael Lopez", "Eduardo Vazquez"]
    cfg = read_sheet("config") or []
    tecnicos = list(defaults)
    for r in cfg:
        p = str(r.get("Parametro", "")).strip()
        v = str(r.get("Valor", "")).strip()
        if p.lower() == "tecnico" and v and v not in tecnicos:
            tecnicos.append(v)
    tecnicos.append("Agregar nuevo técnico")
    return tecnicos


def _save_new_config_param(param_name: str, value: str):
    """
    Guarda un nuevo parámetro en config: fila {Parametro, Valor}
    Usa append_sheet (acepta dict y se alinea con encabezados).
    """
    if not value:
        return False
    row = {"Parametro": param_name, "Valor": value}
    return append_sheet("config", row)


# ---------------------------
# Main UI
# ---------------------------
def show_mantenimientos():
    st.header("🛠 Mantenimientos — Registro, Tiempos y Reportes")

    # Asegurar encabezados mínimos en hojas
    required_mant_headers = [
        "Fecha", "Equipo", "Descripcion", "Realizado_por",
        "estatus", "tiempo_hrs", "hora_inicio", "hora_fin", "Tipo"
    ]
    required_checkin_headers = ["Fecha", "Equipo", "Descripcion", "Realizado_por", "hora_inicio"]
    required_config_headers = ["Parametro", "Valor"]

    _ensure_headers("mantenimientos", required_mant_headers)
    _ensure_headers("checkin_activos", required_checkin_headers)
    _ensure_headers("config", required_config_headers)

    # -------------------------
    # Forms: manual + check-in
    # -------------------------
    st.subheader("📄 Registrar mantenimiento manual")

    # Prepare lists
    equipos = _load_equipos()
    tecnicos = _load_tecnicos()
    tipos = ["Correctivo", "Preventivo", "Predictivo"]

    # Formulario para registro manual (clear_on_submit hará limpieza automática)
    with st.form("form_manual", clear_on_submit=True):
        col1, col2 = st.columns([2, 1])
        with col1:
            fecha = st.date_input("Fecha", value=datetime.now().date(), key="m_fecha")
            equipo_sel = st.selectbox("Equipo", options=equipos, key="m_equipo")
            # If user chose add new equipment, show input
            if equipo_sel == "Agregar nuevo equipo":
                equipo_nuevo = st.text_input("Nombre del nuevo equipo", key="m_equipo_nuevo")
            else:
                equipo_nuevo = None

            tipo = st.selectbox("Tipo de mantenimiento", tipos, key="m_tipo")
            descripcion = st.text_area("Descripción (breve)", max_chars=300, key="m_descripcion")
        with col2:
            realizado_por = st.selectbox("Realizado por", options=tecnicos, key="m_tecnico")
            if realizado_por == "Agregar nuevo técnico":
                nuevo_tecnico = st.text_input("Nombre del nuevo técnico", key="m_tecnico_nuevo")
            else:
                nuevo_tecnico = None
            estatus = st.selectbox("Estatus", ["Completado", "En proceso", "Pendiente"], key="m_estatus")
            tiempo_hrs = st.number_input("Tiempo (hrs)", min_value=0.0, step=0.25, key="m_tiempo")

        guardar_manual = st.form_submit_button("💾 Guardar mantenimiento")

    if guardar_manual:
        # validate and persist any new equipo/tecnico
        final_equipo = equipo_nuevo.strip() if equipo_nuevo else equipo_sel
        final_tecnico = nuevo_tecnico.strip() if nuevo_tecnico else realizado_por

        if equipo_sel == "Agregar nuevo equipo" and (not final_equipo):
            st.error("Debes indicar el nombre del nuevo equipo.")
        elif realizado_por == "Agregar nuevo técnico" and (not final_tecnico):
            st.error("Debes indicar el nombre del nuevo técnico.")
        else:
            # persist new equipment/technician in config if added
            if equipo_nuevo:
                _save_new_config_param("equipo", final_equipo)
            if nuevo_tecnico:
                _save_new_config_param("tecnico", final_tecnico)

            # build dict and append using append_sheet so columns align with sheet headers
            row = {
                "Fecha": str(fecha),
                "Equipo": final_equipo,
                "Descripcion": descripcion,
                "Realizado_por": final_tecnico,
                "estatus": estatus,
                "tiempo_hrs": tiempo_hrs,
                "hora_inicio": "",  # manual entry
                "hora_fin": "",
                "Tipo": tipo
            }

            ok = append_sheet("mantenimientos", row)
            if ok:
                st.success("✅ Mantenimiento guardado.")
                # fields cleared by form (clear_on_submit) but also reset session keys if any
                # refresh UI lists (new config entries)
                st.experimental_rerun()
            else:
                st.error("❌ Error guardando el mantenimiento.")

    st.markdown("---")

    # -------------------------
    # Check-In / Check-Out
    # -------------------------
    st.subheader("⏱ Control de tiempos (Check-In / Check-Out)")

    activos = get_active_checkins() or []  # lista de dicts
    activos_df = pd.DataFrame(activos) if activos else pd.DataFrame(columns=required_checkin_headers)

    # Show active table
    with st.expander("🔵 Ver Check-Ins activos", expanded=False):
        if not activos_df.empty:
            st.dataframe(activos_df, use_container_width=True)
        else:
            st.info("No hay check-ins activos.")

    # Check-in form
    with st.form("form_checkin", clear_on_submit=True):
        ci_col1, ci_col2 = st.columns([2, 1])
        with ci_col1:
            equipo_ci = st.selectbox("Equipo (Check-In)", options=equipos, key="ci_equipo")
            if equipo_ci == "Agregar nuevo equipo":
                equipo_ci_nuevo = st.text_input("Nombre del nuevo equipo (Check-In)", key="ci_equipo_nuevo")
            else:
                equipo_ci_nuevo = None

            desc_ci = st.text_area("Descripción breve (Check-In)", max_chars=250, key="ci_descripcion")
        with ci_col2:
            tecnico_ci = st.selectbox("Técnico (Check-In)", options=tecnicos, key="ci_tecnico")
            if tecnico_ci == "Agregar nuevo técnico":
                tecnico_ci_nuevo = st.text_input("Nombre del nuevo técnico", key="ci_tecnico_nuevo")
            else:
                tecnico_ci_nuevo = None

        iniciar_checkin = st.form_submit_button("▶ Iniciar Check-In")

    if iniciar_checkin:
        final_equipo_ci = equipo_ci_nuevo.strip() if equipo_ci_nuevo else equipo_ci
        final_tecnico_ci = tecnico_ci_nuevo.strip() if tecnico_ci_nuevo else tecnico_ci

        if equipo_ci == "Agregar nuevo equipo" and not final_equipo_ci:
            st.error("Debes ingresar el nombre del nuevo equipo para Check-In.")
        elif tecnico_ci == "Agregar nuevo técnico" and not final_tecnico_ci:
            st.error("Debes ingresar el nombre del técnico.")
        else:
            # persist new values to config if needed
            if equipo_ci_nuevo:
                _save_new_config_param("equipo", final_equipo_ci)
            if tecnico_ci_nuevo:
                _save_new_config_param("tecnico", final_tecnico_ci)

            # check duplicate: avoid multiple active checkins for same equipo+tecnico
            found = False
            for e in activos:
                if e.get("Equipo") == final_equipo_ci and e.get("Realizado_por") == final_tecnico_ci:
                    found = True
                    break
            if found:
                st.warning("Ya existe un Check-In activo para este equipo y técnico.")
            else:
                add_active_checkin(final_equipo_ci, desc_ci, final_tecnico_ci)
                st.success("✔ Check-In iniciado.")
                st.experimental_rerun()

    st.markdown("—")

    # Finalizar check-out: seleccionar activo
    st.subheader("🔴 Finalizar Check-Out")
    if activos:
        choices = []
        for idx, a in enumerate(activos):
            # idx+2 = fila real en sheet (header row =1)
            display = f"{idx+2} | {a.get('Equipo','')} | {a.get('Realizado_por','')} | {a.get('hora_inicio','')}"
            choices.append(display)

        sel = st.selectbox("Selecciona Check-In a finalizar", options=["--"] + choices, key="sel_checkout")
        if sel and sel != "--":
            rownum = int(sel.split("|")[0].strip())
            estatus_checkout = st.selectbox("Estatus final", options=["Completado", "Pendiente", "Cancelado"], key="sel_estatus_checkout")
            desc_final = st.text_area("Descripción final (opcional)", key="desc_final_checkout")
            if st.button("Finalizar Check-Out", key="btn_finalize"):
                ok = finalize_active_checkin_by_rownum(rownum, estatus_checkout, desc_final)
                if ok:
                    st.success("✔ Check-Out finalizado y guardado en historial.")
                    st.experimental_rerun()
                else:
                    st.error("❌ No se pudo finalizar el Check-Out.")
    else:
        st.info("No hay check-ins activos para finalizar.")

    st.markdown("---")

    # -------------------------
    # Historial, filtros y graficas
    # -------------------------
    st.subheader("📚 Historial y Reportes")

    df = read_sheet("mantenimientos") or []
    if not df:
        st.info("No hay registros en el historial todavía.")
        return

    df = pd.DataFrame(df)
    # Normalize Fecha
    if "Fecha" in df.columns:
        df["Fecha"] = pd.to_datetime(df["Fecha"], errors="coerce")

    # Sidebar filters
    st.sidebar.header("Filtros - Historial")
    min_date = df["Fecha"].min().date() if not df["Fecha"].isna().all() else None
    max_date = df["Fecha"].max().date() if not df["Fecha"].isna().all() else None
    date_range = st.sidebar.date_input("Rango de fechas", value=(min_date, max_date) if min_date else ())
    equipos_filter = st.sidebar.multiselect("Equipo", options=sorted(df["Equipo"].dropna().unique().tolist()), key="f_equipos")
    tecnicos_filter = st.sidebar.multiselect("Técnico", options=sorted(df["Realizado_por"].dropna().unique().tolist()), key="f_tecnicos")
    estatus_filter = st.sidebar.multiselect("Estatus", options=sorted(df["estatus"].dropna().unique().tolist()), key="f_estatus")
    tipo_filter = st.sidebar.multiselect("Tipo", options=sorted(df["Tipo"].dropna().unique().tolist()) if "Tipo" in df.columns else [], key="f_tipo")
    search_text = st.sidebar.text_input("Buscar (descripcion/equipo/tecnico)", key="f_search")

    df_filtered = df.copy()
    # apply date filter
    if isinstance(date_range, tuple) and len(date_range) == 2 and all(date_range):
        start, end = date_range
        df_filtered = df_filtered[(df_filtered["Fecha"].dt.date >= start) & (df_filtered["Fecha"].dt.date <= end)]
    if equipos_filter:
        df_filtered = df_filtered[df_filtered["Equipo"].isin(equipos_filter)]
    if tecnicos_filter:
        df_filtered = df_filtered[df_filtered["Realizado_por"].isin(tecnicos_filter)]
    if estatus_filter:
        df_filtered = df_filtered[df_filtered["estatus"].isin(estatus_filter)]
    if tipo_filter and "Tipo" in df_filtered.columns:
        df_filtered = df_filtered[df_filtered["Tipo"].isin(tipo_filter)]
    if search_text:
        mask = df_filtered.apply(lambda r: search_text.lower() in str(r.get("Descripcion","")).lower()
                                 or search_text.lower() in str(r.get("Equipo","")).lower()
                                 or search_text.lower() in str(r.get("Realizado_por","")).lower(), axis=1)
        df_filtered = df_filtered[mask]

    st.markdown("### Resultados")
    st.dataframe(df_filtered.reset_index(drop=True), use_container_width=True)

    # Export buttons
    csv_bytes = df_filtered.to_csv(index=False).encode("utf-8")
    st.download_button("📥 Descargar CSV", csv_bytes, file_name="mantenimientos_filtrados.csv", mime="text/csv")

    try:
        xlsx = _df_to_excel_bytes(df_filtered)
        st.download_button("📥 Descargar XLSX", xlsx, file_name="mantenimientos_filtrados.xlsx",
                           mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
    except Exception as e:
        st.warning(f"No se pudo generar XLSX: {e}")

    st.markdown("---")
    st.subheader("📊 Gráficas")

    # Horas por equipo
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
        except Exception:
            st.warning("No se pudieron generar horas por equipo.")

    # Horas por técnico
    if "Realizado_por" in df_filtered.columns and "tiempo_hrs" in df_filtered.columns:
        try:
            grp_t = df_filtered.groupby("Realizado_por")["tiempo_hrs"].sum().sort_values(ascending=False)
            if not grp_t.empty:
                fig_t, ax_t = plt.subplots()
                grp_t.plot(kind="bar", ax=ax_t)
                ax_t.set_ylabel("Horas")
                ax_t.set_title("Horas por técnico")
                st.pyplot(fig_t)
        except Exception:
            st.warning("No se pudieron generar horas por técnico.")

    # Conteo por Tipo
    if "Tipo" in df_filtered.columns:
        try:
            ct = df_filtered["Tipo"].value_counts()
            if not ct.empty:
                fig_ct, ax_ct = plt.subplots()
                ct.plot(kind="bar", ax=ax_ct)
                ax_ct.set_title("Conteo por Tipo de mantenimiento")
                st.pyplot(fig_ct)
        except Exception:
            st.warning("No se pudo generar gráfico de tipos.")

    # Conteo por estatus
    if "estatus" in df_filtered.columns:
        try:
            ct2 = df_filtered["estatus"].value_counts()
            if not ct2.empty:
                fig_s, ax_s = plt.subplots()
                ct2.plot(kind="bar", ax=ax_s)
                ax_s.set_title("Mantenimientos por estatus")
                st.pyplot(fig_s)
        except Exception:
            st.warning("No se pudo generar gráfico de estatus.")

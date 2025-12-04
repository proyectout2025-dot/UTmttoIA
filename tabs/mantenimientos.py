# tabs/mantenimientos.py
import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
from io import BytesIO
from datetime import datetime

from utils import (
    read_sheet,
    append_row,
    add_active_checkin,
    get_active_checkins,
    finalize_active_checkin_by_rownum,
    get_gs_client,
    SHEET_URL
)

MAIN_SHEET = "mantenimientos"
CHECKIN_SHEET = "checkin_activos"
CONFIG_SHEET = "config"

DEFAULT_EQUIPOS = ["Equipo 1", "Equipo 2", "Equipo 3"]
DEFAULT_TECNICOS = ["Wesley Cunningham", "Misael Lopez", "Eduardo Vazquez"]
TIPOS_MTTO = ["Correctivo", "Preventivo", "Predictivo"]


def _df_to_excel_bytes(df: pd.DataFrame) -> BytesIO:
    buf = BytesIO()
    with pd.ExcelWriter(buf, engine="openpyxl") as writer:
        df.to_excel(writer, index=False, sheet_name=MAIN_SHEET)
    buf.seek(0)
    return buf


def _load_config_values():
    """Devuelve dict con listas: equipos, tecnicos."""
    cfg = read_sheet(CONFIG_SHEET) or []
    equipos = []
    tecnicos = []
    for r in cfg:
        # aceptamos distintas claves posibles para flexibilidad
        for k, v in r.items():
            if not v:
                continue
            key = str(k).strip().lower()
            val = str(v).strip()
            if key in ("equipo", "equipos", "parametro") and val:
                # si 'Parametro' fila con 'equipo' y 'Valor'
                # permitimos formato libre en config (simple)
                if val not in equipos:
                    equipos.append(val)
            if key in ("tecnico", "tecnicos"):
                if val not in tecnicos:
                    tecnicos.append(val)
    return {
        "equipos": sorted(set(equipos)),
        "tecnicos": sorted(set(tecnicos))
    }


def _get_equipo_list():
    cfg = _load_config_values()
    equipos = DEFAULT_EQUIPOS.copy()
    equipos.extend(cfg["equipos"])
    equipos = sorted(list(dict.fromkeys(equipos)))  # preserve unique
    equipos.append("➕ Agregar nuevo equipo")
    return equipos


def _get_tecnico_list():
    cfg = _load_config_values()
    tecnicos = DEFAULT_TECNICOS.copy()
    tecnicos.extend(cfg["tecnicos"])
    tecnicos = sorted(list(dict.fromkeys(tecnicos)))
    tecnicos.append("➕ Agregar nuevo técnico")
    return tecnicos


def show_mantenimientos():
    st.header("🛠 Mantenimientos — Registro, Tiempos y Reportes")

    # Load once
    mantenimientos = read_sheet(MAIN_SHEET) or []
    df_main = pd.DataFrame(mantenimientos) if mantenimientos else pd.DataFrame()

    # ---- Check-In / Check-Out ----
    st.subheader("⏱ Control de Tiempo (Check-In / Check-Out)")

    equipos = _get_equipo_list()
    tecnicos = _get_tecnico_list()

    ci_col1, ci_col2 = st.columns(2)
    with ci_col1:
        ci_equipo = st.selectbox("Equipo (Check-In)", options=equipos, key="ci_equipo")
        if ci_equipo == "➕ Agregar nuevo equipo":
            ci_equipo_nuevo = st.text_input("Nombre nuevo equipo (Check-In)", key="ci_equipo_nuevo")
        else:
            ci_equipo_nuevo = None
    with ci_col2:
        ci_tecnico = st.selectbox("Técnico (Check-In)", options=tecnicos, key="ci_tecnico")
        if ci_tecnico == "➕ Agregar nuevo técnico":
            ci_tecnico_nuevo = st.text_input("Nombre nuevo técnico (Check-In)", key="ci_tecnico_nuevo")
        else:
            ci_tecnico_nuevo = None

    activos = get_active_checkins() or []

    # check if this equipo already has active checkins (match using Equipo or equipo key variants)
    def _normalize_key(d, name):
        # try various casings
        return d.get(name) or d.get(name.capitalize()) or d.get(name.lower()) or d.get(name.upper())

    equipo_final = (ci_equipo_nuevo.strip() if ci_equipo_nuevo else ci_equipo)

    activo = None
    for a in activos:
        # check various possible header keys
        if _normalize_key(a, "Equipo") == equipo_final or _normalize_key(a, "equipo") == equipo_final:
            activo = a
            break

    if activo:
        st.warning(f"⚠ Check-IN activo desde: {_normalize_key(activo,'hora_inicio') or _normalize_key(activo,'Hora_inicio')}")
        if st.button("✔ Finalizar Check-Out", key="btn_finalize_checkout"):
            # build list index -> rownum in sheet (row 1 = headers, so offset +2)
            # find index in activos
            idx = next((i for i, v in enumerate(activos) if v is activo), None)
            if idx is None:
                st.error("No se pudo localizar el check-in para finalizar.")
            else:
                rownum = idx + 2
                ok = finalize_active_checkin_by_rownum(rownum, estatus="Completado", descripcion_override="Check-Out")
                if ok:
                    st.success("Check-Out finalizado y guardado.")
                    st.experimental_rerun()
                else:
                    st.error("No se pudo finalizar el Check-Out.")
    else:
        if st.button("🔵 Iniciar Check-In", key="btn_start_checkin"):
            final_equipo_ci = equipo_final
            final_tecnico_ci = (ci_tecnico_nuevo.strip() if ci_tecnico_nuevo else ci_tecnico)
            if not final_equipo_ci or not final_tecnico_ci:
                st.error("Debes indicar equipo y técnico.")
            else:
                # append a minimal checkin row: Equipo, Realizado_por, hora_inicio
                add_active_checkin(final_equipo_ci, final_tecnico_ci)
                st.success("Check-In registrado.")
                st.experimental_rerun()

    st.markdown("---")

    # ---- Registro manual de mantenimiento ----
    st.subheader("📝 Registro Manual de Mantenimiento")
    with st.form("manual_form", clear_on_submit=True):
        col1, col2 = st.columns(2)
        with col1:
            fecha = st.date_input("Fecha", value=datetime.now().date(), key="man_fecha")
            equipo_sel = st.selectbox("Equipo", options=equipos, key="man_equipo")
            if equipo_sel == "➕ Agregar nuevo equipo":
                equipo_nuevo = st.text_input("Nombre nuevo equipo", key="man_equipo_nuevo")
            else:
                equipo_nuevo = None

        with col2:
            tipo = st.selectbox("Tipo de mantenimiento", options=TIPOS_MTTO, key="man_tipo")
            tecnico_sel = st.selectbox("Realizado por", options=tecnicos, key="man_tecnico")
            if tecnico_sel == "➕ Agregar nuevo técnico":
                tecnico_nuevo = st.text_input("Nombre nuevo técnico", key="man_tecnico_nuevo")

        descripcion = st.text_area("Descripción (breve)", key="man_desc")
        tiempo_hrs = st.number_input("Tiempo (hrs)", min_value=0.0, step=0.25, key="man_horas")

        submit = st.form_submit_button("💾 Guardar mantenimiento", key="man_submit")

    if submit:
        final_equipo = equipo_nuevo.strip() if (locals().get("equipo_nuevo")) else (equipo_sel if 'equipo_sel' in locals() else equipo_final)
        final_tecnico = tecnico_nuevo.strip() if (locals().get("tecnico_nuevo")) else tecnico_sel
        row = [
            fecha.strftime("%Y-%m-%d"),
            final_equipo,
            descripcion,
            final_tecnico,
            "Completado",
            tiempo_hrs,
            "",
            "",
            tipo
        ]
        ok = append_row(MAIN_SHEET, row)
        if ok:
            st.success("Mantenimiento guardado.")
            st.experimental_rerun()
        else:
            st.error("No se pudo guardar el mantenimiento.")

    st.markdown("---")

    # ---- Historial y filtros ----
    st.subheader("📚 Historial y Reportes")
    hist = read_sheet(MAIN_SHEET) or []
    if not hist:
        st.info("No hay registros aún.")
        return
    df = pd.DataFrame(hist)
    # ensure Fecha as datetime if exists
    if "Fecha" in df.columns:
        df["Fecha"] = pd.to_datetime(df["Fecha"], errors="coerce")

    # Sidebar filters
    st.sidebar.header("Filtros")
    equipos_filter = st.sidebar.multiselect("Equipo", options=sorted(df["Equipo"].dropna().unique().tolist()) if "Equipo" in df.columns else [], key="f_equipos")
    tecnicos_filter = st.sidebar.multiselect("Técnico", options=sorted(df["Realizado_por"].dropna().unique().tolist()) if "Realizado_por" in df.columns else [], key="f_tecnicos")
    tipo_filter = st.sidebar.multiselect("Tipo", options=sorted(df["Tipo"].dropna().unique().tolist()) if "Tipo" in df.columns else [], key="f_tipo")
    search = st.sidebar.text_input("Buscar descripción/equipo/técnico", key="f_search")

    df_filtered = df.copy()
    if equipos_filter:
        df_filtered = df_filtered[df_filtered["Equipo"].isin(equipos_filter)]
    if tecnicos_filter:
        df_filtered = df_filtered[df_filtered["Realizado_por"].isin(tecnicos_filter)]
    if tipo_filter:
        df_filtered = df_filtered[df_filtered["Tipo"].isin(tipo_filter)]
    if search:
        mask = df_filtered.apply(lambda r: search.lower() in str(r.get("Descripcion","")).lower() or search.lower() in str(r.get("Equipo","")).lower() or search.lower() in str(r.get("Realizado_por","")).lower(), axis=1)
        df_filtered = df_filtered[mask]

    st.dataframe(df_filtered, width="stretch")

    # Exports
    csv_bytes = df_filtered.to_csv(index=False).encode("utf-8")
    st.download_button("📥 Descargar CSV", csv_bytes, file_name="mantenimientos_filtrados.csv", mime="text/csv")

    try:
        xlsx = _df_to_excel_bytes(df_filtered)
        st.download_button("📥 Descargar XLSX", xlsx, file_name="mantenimientos_filtrados.xlsx", mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
    except Exception:
        pass

    # Gráficas
    st.markdown("---")
    st.subheader("📈 Gráficas")
    try:
        if "tiempo_hrs" in df_filtered.columns:
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

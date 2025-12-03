# tabs/mantenimientos.py
import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages
from io import BytesIO
from datetime import datetime
from utils import read_sheet, append_sheet

st.set_option('deprecation.showPyplotGlobalUse', False)

SHEET = "mantenimientos"

def _load_data():
    data = read_sheet(SHEET)
    if data is None:
        return pd.DataFrame()
    df = pd.DataFrame(data)
    # Normalizar columnas (tolerante a ambos formatos: encabezados o ordenados)
    # Intentar convertir nombres a minúsculas sin espacios para buscar
    cols_map = {c: c for c in df.columns}
    # If columns are positional (no headers), handle when df has default columns 0..n-1 -> user must have headers
    return df

def _parse_dates(df):
    # Buscar columnas de fecha u hora si existen
    for c in df.columns:
        if "fecha" in c.lower() or "date" in c.lower():
            try:
                df[c] = pd.to_datetime(df[c], errors="coerce")
            except Exception:
                pass
    # Attempt parse hora_inicio/hora_fin
    if "hora_inicio" in df.columns:
        df["hora_inicio"] = pd.to_datetime(df["hora_inicio"], errors="coerce")
    if "hora_fin" in df.columns:
        df["hora_fin"] = pd.to_datetime(df["hora_fin"], errors="coerce")
    # Ensure tiempo_hrs numeric
    if "tiempo_hrs" in df.columns:
        df["tiempo_hrs"] = pd.to_numeric(df["tiempo_hrs"], errors="coerce").fillna(0.0)
    return df

def _compute_kpis(df):
    kpis = {}
    if df.empty:
        kpis["total_mantenimientos"] = 0
        kpis["horas_totales"] = 0.0
        kpis["promedio_horas"] = 0.0
        kpis["mttr"] = None
        kpis["mtbf_days"] = None
        return kpis

    kpis["total_mantenimientos"] = len(df)
    kpis["horas_totales"] = float(df["tiempo_hrs"].sum()) if "tiempo_hrs" in df.columns else 0.0
    kpis["promedio_horas"] = float(df["tiempo_hrs"].mean()) if "tiempo_hrs" in df.columns else 0.0

    # MTTR: mean time to repair = mean tiempo_hrs for completed
    if "estatus" in df.columns and "tiempo_hrs" in df.columns:
        completed = df[df["estatus"].str.lower() == "completado"]
        kpis["mttr"] = float(completed["tiempo_hrs"].mean()) if not completed.empty else None
    else:
        kpis["mttr"] = None

    # MTBF: mean time between failures per equipment (in days)
    if "equipo" in df.columns and ("fecha" in df.columns or "hora_inicio" in df.columns):
        # use fecha if present else hora_inicio
        date_col = "fecha" if "fecha" in df.columns else "hora_inicio"
        df_dates = df.dropna(subset=[date_col])
        if not df_dates.empty:
            diffs = []
            for eq, g in df_dates.groupby("equipo"):
                times = g[date_col].sort_values().values
                if len(times) > 1:
                    deltas = np.diff(times).astype('timedelta64[s]').astype(float) / (3600*24)
                    if len(deltas)>0:
                        diffs.extend(deltas.tolist())
            kpis["mtbf_days"] = float(np.mean(diffs)) if diffs else None
        else:
            kpis["mtbf_days"] = None
    else:
        kpis["mtbf_days"] = None

    return kpis

def _plot_time_by_equipo(df):
    if "equipo" not in df.columns or "tiempo_hrs" not in df.columns:
        st.info("No hay columnas 'equipo' o 'tiempo_hrs' para graficar tiempo por equipo.")
        return None
    grp = df.groupby("equipo")["tiempo_hrs"].sum().sort_values(ascending=False)
    fig, ax = plt.subplots(figsize=(8,4))
    grp.plot(kind="bar", ax=ax)
    ax.set_ylabel("Horas")
    ax.set_title("Tiempo total invertido por equipo")
    plt.tight_layout()
    return fig

def _plot_time_by_tecnico(df):
    if "realizado_por" not in df.columns or "tiempo_hrs" not in df.columns:
        st.info("No hay columnas 'realizado_por' o 'tiempo_hrs' para graficar.")
        return None
    grp = df.groupby("realizado_por")["tiempo_hrs"].sum().sort_values(ascending=False)
    fig, ax = plt.subplots(figsize=(8,4))
    grp.plot(kind="bar", ax=ax)
    ax.set_ylabel("Horas")
    ax.set_title("Tiempo total por técnico")
    plt.tight_layout()
    return fig

def _plot_status_pie(df):
    if "estatus" not in df.columns:
        st.info("No hay columna 'estatus' para graficar.")
        return None
    counts = df["estatus"].value_counts()
    fig, ax = plt.subplots(figsize=(4,4))
    counts.plot(kind="pie", autopct="%1.1f%%", ax=ax)
    ax.set_ylabel("")
    ax.set_title("Distribución por estatus")
    plt.tight_layout()
    return fig

def _plot_hours_over_time(df):
    # need fecha / hora_inicio column
    date_col = None
    if "fecha" in df.columns:
        date_col = "fecha"
    elif "hora_inicio" in df.columns:
        date_col = "hora_inicio"
    else:
        st.info("No hay columna de fecha/hora para gráfico temporal.")
        return None
    ts = df.dropna(subset=[date_col])
    ts = ts.set_index(pd.to_datetime(ts[date_col]))
    # resample weekly sum
    weekly = ts["tiempo_hrs"].resample('W').sum() if "tiempo_hrs" in ts.columns else None
    if weekly is None:
        st.info("No hay 'tiempo_hrs' para gráfico temporal.")
        return None
    fig, ax = plt.subplots(figsize=(8,3))
    weekly.plot(ax=ax)
    ax.set_title("Horas por semana")
    ax.set_ylabel("Horas")
    plt.tight_layout()
    return fig

def _export_excel(df):
    output = BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        df.to_excel(writer, sheet_name='mantenimientos', index=False)
        # optionally add summary sheet
        writer.save()
    output.seek(0)
    return output

def _export_csv(df):
    return df.to_csv(index=False).encode('utf-8')

def _export_pdf(df, figs):
    """
    figs: list of matplotlib figures to include
    Also include a table page with the df head.
    """
    buf = BytesIO()
    with PdfPages(buf) as pdf:
        # add figures
        for f in figs:
            if f is not None:
                pdf.savefig(f)
        # add a table page: render df.head() as a table figure
        try:
            fig, ax = plt.subplots(figsize=(11, 6))
            ax.axis('off')
            tbl = ax.table(cellText=df.head(30).values, colLabels=df.columns, loc='center')
            tbl.auto_set_font_size(False)
            tbl.set_fontsize(8)
            tbl.scale(1, 1.5)
            pdf.savefig(fig)
            plt.close(fig)
        except Exception:
            pass
    buf.seek(0)
    return buf

# -------------------------
# Main UI
# -------------------------
def show_mantenimientos():
    st.header("🛠 Mantenimientos — Dashboard y Reportes")

    df = _load_data()
    if df.empty:
        st.info("No hay datos en 'mantenimientos' todavía.")
        # Still allow user to register a new entry via previous form (if desired)
    else:
        df = _parse_dates(df)

    # --- Filters ---
    st.sidebar.header("Filtros")
    col_equipo = df["equipo"].unique().tolist() if "equipo" in df.columns else []
    col_tecnico = df["realizado_por"].unique().tolist() if "realizado_por" in df.columns else []
    col_estatus = df["estatus"].unique().tolist() if "estatus" in df.columns else []

    fecha_min = df["fecha"].min() if "fecha" in df.columns else None
    fecha_max = df["fecha"].max() if "fecha" in df.columns else None

    date_range = st.sidebar.date_input("Rango de fechas", value=(fecha_min.date() if fecha_min is not None else None,
                                                                fecha_max.date() if fecha_max is not None else None),
                                      key="filter_dates")
    sel_equipo = st.sidebar.multiselect("Equipo", options=col_equipo, key="filter_equipo")
    sel_tecnico = st.sidebar.multiselect("Técnico", options=col_tecnico, key="filter_tecnico")
    sel_estatus = st.sidebar.multiselect("Estatus", options=col_estatus, key="filter_estatus")

    # Apply filters
    df_filtered = df.copy()
    if date_range and len(date_range) == 2 and "fecha" in df.columns:
        start, end = date_range
        df_filtered = df_filtered[(df_filtered["fecha"].dt.date >= start) & (df_filtered["fecha"].dt.date <= end)]
    if sel_equipo:
        df_filtered = df_filtered[df_filtered["equipo"].isin(sel_equipo)]
    if sel_tecnico:
        df_filtered = df_filtered[df_filtered["realizado_por"].isin(sel_tecnico)]
    if sel_estatus:
        df_filtered = df_filtered[df_filtered["estatus"].isin(sel_estatus)]

    # --- KPIs ---
    st.subheader("KPIs")
    kpis = _compute_kpis(df_filtered)
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Total mantenimientos", kpis["total_mantenimientos"])
    c2.metric("Horas totales", f'{kpis["horas_totales"]:.2f}')
    c3.metric("Promedio horas", f'{kpis["promedio_horas"]:.2f}' if kpis["promedio_horas"] else "—")
    c4.metric("MTTR (hrs)", f'{kpis["mttr"]:.2f}' if kpis["mttr"] else "—")
    if kpis["mtbf_days"]:
        st.write(f"MTBF promedio: {kpis['mtbf_days']:.2f} días")
    else:
        st.write("MTBF: —")

    st.markdown("---")

    # --- Charts ---
    st.subheader("Gráficos")
    fig1 = _plot_time_by_equipo(df_filtered)
    if fig1:
        st.pyplot(fig1)
    fig2 = _plot_time_by_tecnico(df_filtered)
    if fig2:
        st.pyplot(fig2)
    fig3 = _plot_status_pie(df_filtered)
    if fig3:
        st.pyplot(fig3)
    fig4 = _plot_hours_over_time(df_filtered)
    if fig4:
        st.pyplot(fig4)

    st.markdown("---")

    # --- Table view ---
    st.subheader("Tabla (filtrada)")
    if not df_filtered.empty:
        st.dataframe(df_filtered.reset_index(drop=True), use_container_width=True)
    else:
        st.info("No hay filas que coincidan con los filtros seleccionados.")

    # --- Exports ---
    st.subheader("Exportar reportes")
    col1, col2, col3 = st.columns(3)

    if not df_filtered.empty:
        # CSV
        csv_bytes = _export_csv(df_filtered)
        col1.download_button("Descargar CSV", csv_bytes, "reporte_mantenimientos.csv", "text/csv", key="dl_csv")

        # Excel
        try:
            excel_io = _export_excel(df_filtered)
            col2.download_button("Descargar XLSX", excel_io, "reporte_mantenimientos.xlsx", "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", key="dl_xlsx")
        except Exception as e:
            col2.error(f"Error generando XLSX: {e}")

        # PDF from figures
        figs = [fig for fig in (fig1, fig2, fig3, fig4) if fig is not None]
        try:
            pdf_io = _export_pdf(df_filtered, figs)
            col3.download_button("Descargar PDF (figuras)", pdf_io, "reporte_mantenimientos.pdf", "application/pdf", key="dl_pdf")
        except Exception as e:
            col3.error(f"Error generando PDF: {e}")
    else:
        col1.info("No hay datos para exportar")
        col2.info("No hay datos para exportar")
        col3.info("No hay datos para exportar")

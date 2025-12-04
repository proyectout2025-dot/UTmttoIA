# tabs/config.py
import streamlit as st
import pandas as pd
from utils import read_sheet, append_sheet, get_gs_client, SHEET_URL

EXPECTED = {
    "mantenimientos": ["Fecha","Equipo","Descripcion","Realizado_por","estatus","tiempo_hrs","hora_inicio","hora_fin","Tipo"],
    "checkin_activos": ["Fecha","Equipo","Descripcion","Realizado_por","hora_inicio"],
    "refacciones": ["Codigo","Nombre","Descripcion","Ubicacion","Stock","ArchivoID"],
    "config": ["Parametro","Valor"]
}

def _ensure_headers(sheet_name, headers):
    try:
        client = get_gs_client()
        sh = client.open_by_url(SHEET_URL)
        try:
            ws = sh.worksheet(sheet_name)
            current = ws.row_values(1)
            current = [c.strip() for c in current]
            if current != headers:
                try:
                    ws.delete_rows(1)
                except Exception:
                    pass
                ws.insert_row(headers, index=1)
        except:
            # create sheet and insert headers
            sh.add_worksheet(title=sheet_name, rows=1000, cols=20)
            ws = sh.worksheet(sheet_name)
            ws.insert_row(headers, index=1)
    except Exception as e:
        st.error(f"Error asegurando encabezados: {e}")

def autofix_headers_ui():
    st.header("🔧 Auto-Fix de Encabezados")
    st.write("Asegura que las hojas tengan las columnas esperadas (solo modifica fila 1).")
    for k,v in EXPECTED.items():
        st.write(f"**{k}**: {', '.join(v)}")
    if st.button("Ejecutar Auto-Fix (todas las hojas)"):
        for k,v in EXPECTED.items():
            _ensure_headers(k, v)
        st.success("Auto-fix ejecutado.")

def show_config():
    st.header("⚙️ Configuración")
    st.write("Herramientas administrativas")
    autofix_headers_ui()

    st.markdown("---")
    st.subheader("Contenido de config")
    data = read_sheet("config") or []
    if data:
        df = pd.DataFrame(data)
        st.dataframe(df, width="stretch")
    else:
        st.info("No hay parámetros guardados en config.")

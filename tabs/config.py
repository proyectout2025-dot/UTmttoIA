# tabs/config.py
import streamlit as st
import pandas as pd
from utils import read_sheet, append_sheet, get_gs_client, SHEET_URL, EXPECTED_HEADERS as EXP

def _ensure_headers(sheet_name, headers):
    try:
        client = get_gs_client()
        sh = client.open_by_url(SHEET_URL)
        try:
            ws = sh.worksheet(sheet_name)
            cur = ws.row_values(1)
            cur = [c.strip() for c in cur]
            if cur != headers:
                try:
                    ws.delete_rows(1)
                except Exception:
                    pass
                ws.insert_row(headers, index=1)
        except:
            sh.add_worksheet(title=sheet_name, rows=1000, cols=20)
            ws = sh.worksheet(sheet_name)
            ws.insert_row(headers, index=1)
    except Exception as e:
        st.error(f"Error asegurando encabezados: {e}")

def show_config():
    st.header("⚙️ Configuración y Auto-Fix")

    st.write("Encabezados esperados:")
    for k, v in EXP.items():
        st.write(f"- **{k}**: {', '.join(v)}")

    if st.button("Ejecutar Auto-Fix (asegurar hojas)"):
        for k, v in EXP.items():
            _ensure_headers(k, v)
        st.success("Auto-Fix ejecutado en todas las hojas.")

    st.markdown("---")
    st.subheader("Parámetros guardados en config")
    data = read_sheet("config") or []
    if data:
        df = pd.DataFrame(data)
        st.dataframe(df, width="stretch")
    else:
        st.info("No hay parámetros guardados.")

# setup_sheets.py
import streamlit as st
from utils import get_gs_client, SHEET_URL, EXPECTED_HEADERS

def run_setup():
    st.header("🧩 Setup inicial - crear/asegurar hojas y encabezados")
    if st.button("Crear/Arreglar hojas y encabezados"):
        client = get_gs_client()
        if not client:
            st.error("No se pudo autenticar con Google.")
            return
        sh = client.open_by_url(SHEET_URL)
        for sheet, headers in EXPECTED_HEADERS.items():
            try:
                try:
                    ws = sh.worksheet(sheet)
                    st.info(f"Hoja '{sheet}' encontrada.")
                except:
                    sh.add_worksheet(title=sheet, rows=1000, cols=20)
                    st.success(f"Hoja '{sheet}' creada.")
                ws = sh.worksheet(sheet)
                cur = ws.row_values(1)
                cur = [c.strip() for c in cur]
                if cur != headers:
                    try:
                        ws.delete_rows(1)
                    except Exception:
                        pass
                    ws.insert_row(headers, index=1)
                    st.success(f"Encabezados en '{sheet}' asegurados.")
            except Exception as e:
                st.error(f"Error con hoja {sheet}: {e}")
        st.success("Setup completado.")

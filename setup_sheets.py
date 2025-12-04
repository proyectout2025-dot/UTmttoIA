# setup_sheets.py
import streamlit as st
from utils import get_gs_client, SHEET_URL

EXPECTED = {
    "mantenimientos": ["Fecha","Equipo","Descripcion","Realizado_por","estatus","tiempo_hrs","hora_inicio","hora_fin","Tipo"],
    "checkin_activos": ["Equipo","Realizado_por","hora_inicio"],
    "refacciones": ["Fecha","Numero_parte","Parte_cliente","Descripcion","Ubicacion","Existencias","ArchivoID"],
    "config": ["Parametro","Valor"]
}

def run_setup():
    st.header("🧩 Setup inicial - crear/asegurar hojas y encabezados")
    if st.button("Crear/Arreglar hojas y encabezados"):
        client = get_gs_client()
        if not client:
            st.error("No se pudo autenticar con Google.")
            return
        sh = client.open_by_url(SHEET_URL)
        for sheet, headers in EXPECTED.items():
            try:
                try:
                    ws = sh.worksheet(sheet)
                    st.info(f"Hoja '{sheet}' encontrada.")
                except:
                    sh.add_worksheet(title=sheet, rows=1000, cols=20)
                    st.success(f"Hoja '{sheet}' creada.")
                    ws = sh.worksheet(sheet)
                cur = ws.row_values(1)
                cur = [c.strip() for c in cur] if cur else []
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

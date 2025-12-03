# setup_sheets.py
import streamlit as st
import gspread
from google.oauth2.service_account import Credentials

SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive",
]

SHEET_NAME = "base_datos_app"

HEADERS = {
    "mantenimientos": [
        "Fecha", "Equipo", "Descripcion", "Realizado_por",
        "estatus", "tiempo_hrs", "hora_inicio", "hora_fin"
    ],
    "checkin_activos": [
        "Fecha", "Equipo", "Descripcion", "Realizado_por", "hora_inicio"
    ],
    "refacciones": [
        "Fecha", "Equipo", "Refaccion", "Cantidad", "Operacion", "Responsable"
    ],
    "config": [
        "Parametro", "Valor"
    ]
}

def get_client():
    creds_info = st.secrets["gcp_service_account"]
    creds = Credentials.from_service_account_info(creds_info, scopes=SCOPES)
    return gspread.authorize(creds)

def ensure_sheet_and_headers(client, sheet_name, headers):
    try:
        sh = client.open(SHEET_NAME)
        try:
            ws = sh.worksheet(sheet_name)
            st.success(f"✔ Hoja '{sheet_name}' encontrada.")
        except:
            st.warning(f"⚠ Hoja '{sheet_name}' no existe. Creando...")
            ws = sh.add_worksheet(title=sheet_name, rows=1000, cols=20)
            st.success(f"✔ Hoja '{sheet_name}' creada correctamente.")

        existing = ws.row_values(1)

        if existing != headers:
            st.warning(f"Encabezados incorrectos en '{sheet_name}'. Corrigiendo...")
            ws.delete_rows(1)
            ws.insert_row(headers, index=1)
            st.success(f"✔ Encabezados actualizados en '{sheet_name}'.")
        else:
            st.info(f"Encabezados correctos en '{sheet_name}'.")
    except Exception as e:
        st.error(f"❌ Error configurando '{sheet_name}': {e}")

def run_setup():
    st.header("🔧 Configuración automática de Google Sheets")

    if st.button("🔄 Ejecutar configuración automática"):
        try:
            client = get_client()
            st.info("Conectando con Google Sheets...")

            for sheet, headers in HEADERS.items():
                ensure_sheet_and_headers(client, sheet, headers)

            st.success("🎉 Configuración completa. Todo está listo.")
        except Exception as e:
            st.error(f"❌ Error general: {e}")


if __name__ == "__main__":
    run_setup()

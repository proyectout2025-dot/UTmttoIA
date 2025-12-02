import streamlit as st
import gspread
from google.oauth2.service_account import Credentials

# ==========================
# 1. CONFIGURACIÓN INICIAL
# ==========================

st.set_page_config(page_title="App Mantenimiento", layout="wide")

st.title("📋 Sistema de Mantenimiento – Panel Principal")

# Conexión con Google Sheets
def get_connection():
    try:
        creds = Credentials.from_service_account_info(
            st.secrets["gcp_service_account"],
            scopes=["https://www.googleapis.com/auth/spreadsheets"]
        )
        client = gspread.authorize(creds)
        sheet = client.open_by_url(st.secrets["sheets"]["sheet_url"])
        return sheet
    except Exception as e:
        st.error(f"❌ Error al conectar con Google Sheets:\n{e}")
        return None


# Leer una hoja específica
def read_sheet(sheet_name):
    try:
        sheet = get_connection()
        if sheet is None:
            return None

        ws = sheet.worksheet(sheet_name)
        data = ws.get_all_records()
        return data
    except Exception as e:
        st.error(f"❌ No se pudo leer la hoja '{sheet_name}':\n{e}")
        return None


# ==========================
# 2. MENÚ LATERAL
# ==========================

menu = st.sidebar.radio(
    "Selecciona una sección:",
    ["Mantenimientos", "Refacciones", "Config"]
)

# ==========================
# 3. MOSTRAR HOJAS
# ==========================

if menu == "Mantenimientos":
    st.header("🛠 Mantenimientos")
    data = read_sheet("mantenimientos")
    if data:
        st.dataframe(data, use_container_width=True)

elif menu == "Refacciones":
    st.header("🔩 Refacciones")
    data = read_sheet("refacciones")
    if data:
        st.dataframe(data, use_container_width=True)

elif menu == "Config":
    st.header("⚙️ Configuración")
    data = read_sheet("config")
    if data:
        st.dataframe(data, use_container_width=True)

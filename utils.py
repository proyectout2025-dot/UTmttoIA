import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
from datetime import datetime

# --------------------------------------------------------------------
# 🔐 CONFIGURACIÓN DE GOOGLE SHEETS
# --------------------------------------------------------------------

SCOPE = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive"
]

def _get_client():
    """Crea cliente autorizado para Google Sheets usando st.secrets."""
    credentials = Credentials.from_service_account_info(
        st.secrets["gcp_service_account"],
        scopes=SCOPE
    )
    return gspread.authorize(credentials)

# --------------------------------------------------------------------
# 📄 LECTURA Y ESCRITURA EN GOOGLE SHEETS
# --------------------------------------------------------------------

def read_sheet(spreadsheet_name: str, worksheet_name: str):
    """Lee una hoja y regresa una lista de dicts."""
    try:
        gc = _get_client()
        sh = gc.open(spreadsheet_name)
        ws = sh.worksheet(worksheet_name)
        return ws.get_all_records()
    except Exception as e:
        st.error(f"❌ Error leyendo Google Sheet: {e}")
        return None


def append_sheet(spreadsheet_name: str, worksheet_name: str, row: list):
    """Añade una fila al final de una hoja."""
    try:
        gc = _get_client()
        sh = gc.open(spreadsheet_name)
        ws = sh.worksheet(worksheet_name)
        ws.append_row(row)
        return True
    except Exception as e:
        st.error(f"❌ Error escribiendo en Google Sheet: {e}")
        return False

# --------------------------------------------------------------------
# ⏱ CHECK IN / CHECK OUT
# --------------------------------------------------------------------

CHECKIN_SHEET = "chekin_activos"   # Nombre exacto que tú usas

def add_active_checkin(spreadsheet_name, equipo, realizado_por):
    """Registra un nuevo check-in."""
    now = datetime.now().isoformat()
    row = [equipo, realizado_por, now]
    return append_sheet(spreadsheet_name, CHECKIN_SHEET, row)


def get_active_checkins(spreadsheet_name):
    """Obtiene todos los check-ins activos."""
    data = read_sheet(spreadsheet_name, CHECKIN_SHEET)
    return data if data else []


def close_checkin(spreadsheet_name, equipo):
    """Cierra el check-in de un equipo existente."""
    try:
        gc = _get_client()
        sh = gc.open(spreadsheet_name)
        ws = sh.worksheet(CHECKIN_SHEET)
        data = ws.get_all_records()

        for i, row in enumerate(data, start=2):  # fila real (1=header)
            if row["equipo"] == equipo:
                ws.update_cell(i, 4, datetime.now().isoformat())
                return True

        return False
    except Exception as e:
        st.error(f"❌ Error cerrando check-in: {e}")
        return False

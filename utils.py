import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
from datetime import datetime

# ===========================================================
#              AUTENTICACIÓN GOOGLE
# ===========================================================
def get_gs_client():
    """Autentica utilizando las credenciales almacenadas en st.secrets."""
    try:
        creds_dict = st.secrets["gcp_service_account"]
        scopes = [
            "https://www.googleapis.com/auth/spreadsheets",
            "https://www.googleapis.com/auth/drive"
        ]
        creds = Credentials.from_service_account_info(creds_dict, scopes=scopes)
        client = gspread.authorize(creds)
        return client
    except Exception as e:
        st.error(f"❌ Error autenticando Google: {e}")
        return None


SHEET_URL = st.secrets["sheets"]["sheet_url"]


# ===========================================================
#                       READ SHEET
# ===========================================================
@st.cache_data(ttl=5)
def read_sheet(worksheet_name):
    try:
        client = get_gs_client()
        sh = client.open_by_url(SHEET_URL)
        ws = sh.worksheet(worksheet_name)
        data = ws.get_all_records()
        return data
    except Exception as e:
        st.error(f"❌ Error leyendo Google Sheets ({worksheet_name}): {e}")
        return []


# ===========================================================
#                     APPEND ROW
# ===========================================================
def append_row(worksheet_name, row):
    try:
        client = get_gs_client()
        sh = client.open_by_url(SHEET_URL)
        ws = sh.worksheet(worksheet_name)
        ws.append_row(row)
        read_sheet.clear()  # Limpia cache
        return True
    except Exception as e:
        st.error(f"❌ Error guardando en Google Sheets ({worksheet_name}): {e}")
        return False


# ===========================================================
#                     CHECK-IN / CHECK-OUT
# ===========================================================
def get_active_checkins():
    data = read_sheet("checkin_activos")
    return data if data else []


def add_active_checkin(equipo, realizado_por, tipo):
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    row = [equipo, realizado_por, now, tipo]
    append_row("checkin_activos", row)


def finalize_checkin(row_data):
    """Finaliza un registro activo y lo mueve a mantenimientos."""
    try:
        inicio_dt = datetime.strptime(row_data["hora_inicio"], "%Y-%m-%d %H:%M:%S")
        fin_dt = datetime.now()

        horas = round((fin_dt - inicio_dt).total_seconds() / 3600, 2)

        row_to_save = [
            inicio_dt.strftime("%Y-%m-%d"),
            row_data["Equipo"],
            row_data["Descripcion"],
            row_data["Realizado_por"],
            "Completado",
            horas,
            row_data["hora_inicio"],
            fin_dt.strftime("%Y-%m-%d %H:%M:%S"),
            row_data.get("Tipo", "")
        ]

        append_row("mantenimientos", row_to_save)
        return True

    except Exception as e:
        st.error(f"❌ Error finalizando check-out: {e}")
        return False

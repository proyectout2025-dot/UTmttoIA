import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
from datetime import datetime

# =====================================
#   GOOGLE AUTH
# =====================================
def get_gs_client():
    try:
        creds_dict = st.secrets["gcp_service_account"]
        scopes = [
            "https://www.googleapis.com/auth/spreadsheets",
            "https://www.googleapis.com/auth/drive"
        ]
        creds = Credentials.from_service_account_info(creds_dict, scopes=scopes)
        return gspread.authorize(creds)
    except Exception as e:
        st.error(f"❌ Error autenticar Google: {e}")
        return None


SHEET_URL = st.secrets["sheets"]["sheet_url"]


# =====================================
#   READ SHEET
# =====================================
@st.cache_data(ttl=10)
def read_sheet(worksheet_name):
    """Lee una hoja completa pero con cache para evitar 429."""
    try:
        client = get_gs_client()
        sh = client.open_by_url(SHEET_URL)
        ws = sh.worksheet(worksheet_name)
        return ws.get_all_records()
    except Exception as e:
        st.error(f"❌ Error leyendo {worksheet_name}: {e}")
        return []


# =====================================
#   APPEND ROW
# =====================================
def append_row(worksheet_name, row):
    """Agrega fila y limpia cache."""
    try:
        client = get_gs_client()
        sh = client.open_by_url(SHEET_URL)
        ws = sh.worksheet(worksheet_name)
        ws.append_row(row)
        read_sheet.clear()
        return True
    except Exception as e:
        st.error(f"❌ Error escribiendo en {worksheet_name}: {e}")
        return False


# =====================================
#   CHECK-IN SYSTEM
# =====================================
def get_active_checkins():
    return read_sheet("checkin_activos")


def add_active_checkin(equipo, realizado_por):
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    row = [equipo, realizado_por, now]
    append_row("checkin_activos", row)


def finalize_checkin(rownum, descripcion="Trabajo completado"):
    """Cierra check-in → registra mantenimiento."""
    try:
        client = get_gs_client()
        sh = client.open_by_url(SHEET_URL)
        ws = sh.worksheet("checkin_activos")

        headers = ws.row_values(1)
        rowvals = ws.row_values(rownum)

        entry = {headers[i]: rowvals[i] for i in range(len(headers))}

        equipo = entry["Equipo"]
        tecnico = entry["Realizado_por"]
        hinicio = entry["hora_inicio"]

        inicio_dt = datetime.strptime(hinicio, "%Y-%m-%d %H:%M:%S")
        fin_dt = datetime.now()

        horas = round((fin_dt - inicio_dt).total_seconds() / 3600, 2)

        mantenimiento_row = [
            inicio_dt.strftime("%Y-%m-%d"),
            equipo,
            descripcion,
            tecnico,
            "Completado",
            horas,
            hinicio,
            fin_dt.strftime("%Y-%m-%d %H:%M:%S")
        ]

        append_row("mantenimientos", mantenimiento_row)

        ws.delete_rows(rownum)
        read_sheet.clear()
        return True

    except Exception as e:
        st.error(f"❌ Error finalizando check-in: {e}")
        return False

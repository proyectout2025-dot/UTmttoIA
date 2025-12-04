import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
from datetime import datetime

# =====================================
#      AUTENTICACIÓN GOOGLE
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
        st.error(f"❌ Error autenticando Google: {e}")
        return None

SHEET_URL = st.secrets["sheets"]["sheet_url"]

# =====================================
#       LECTURA CON CACHE
# =====================================
@st.cache_data(ttl=20)
def read_sheet(sheet_name):
    """Lee Google Sheet eficientemente."""
    try:
        client = get_gs_client()
        sh = client.open_by_url(SHEET_URL)
        ws = sh.worksheet(sheet_name)
        return ws.get_all_records()
    except Exception as e:
        st.error(f"❌ Error leyendo Google Sheets ({sheet_name}): {e}")
        return []

# =====================================
#       GUARDAR FILA
# =====================================
def append_row(sheet_name, row):
    try:
        client = get_gs_client()
        sh = client.open_by_url(SHEET_URL)
        ws = sh.worksheet(sheet_name)
        ws.append_row(row)
        read_sheet.clear()
        return True
    except Exception as e:
        st.error(f"❌ Error guardando en Google Sheets ({sheet_name}): {e}")
        return False

# =====================================
#   CONTROL ENCABEZADOS
# =====================================
def ensure_headers(sheet_name, expected_headers):
    """Garantiza estructura correcta de columnas."""
    try:
        client = get_gs_client()
        sh = client.open_by_url(SHEET_URL)
        ws = sh.worksheet(sheet_name)

        current = ws.row_values(1)
        if current != expected_headers:
            ws.update("A1:Z1", [expected_headers])
            read_sheet.clear()

    except Exception as e:
        st.warning(f"⚠ No se pudieron asegurar encabezados en '{sheet_name}': {e}")

# =====================================
#   CHECK-IN / CHECK-OUT
# =====================================
def get_active_checkins():
    """Regresa todos los check-ins activos."""
    return read_sheet("checkin_activos")

def start_checkin(equipo, tecnico):
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    row = [equipo, tecnico, now]
    append_row("checkin_activos", row)

def finalize_checkin(row_number, descripcion, estatus):
    try:
        client = get_gs_client()
        sh = client.open_by_url(SHEET_URL)
        ws = sh.worksheet("checkin_activos")

        headers = ws.row_values(1)
        row = ws.row_values(row_number)

        entry = {headers[i]: row[i] if i < len(row) else "" for i in range(len(headers))}

        equipo = entry.get("Equipo", "")
        tecnico = entry.get("Realizado_por", "")
        inicio_txt = entry.get("hora_inicio", "")

        try:
            inicio_dt = datetime.strptime(inicio_txt, "%Y-%m-%d %H:%M:%S")
        except:
            inicio_dt = datetime.now()

        fin_dt = datetime.now()
        horas = round((fin_dt - inicio_dt).total_seconds() / 3600, 2)

        row_to_save = [
            inicio_dt.strftime("%Y-%m-%d"),
            equipo,
            descripcion,
            tecnico,
            estatus,
            horas,
            inicio_txt,
            fin_dt.strftime("%Y-%m-%d %H:%M:%S")
        ]

        append_row("mantenimientos", row_to_save)

        ws.delete_rows(row_number)
        read_sheet.clear()

        return True
    except Exception as e:
        st.error(f"❌ Error finalizando check-out: {e}")
        return False

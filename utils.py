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


def finalize_checkin(equipo, descripcion=""):
    """
    Finaliza un check-in usando búsqueda real en Google Sheets.
    Evita index errors y no depende del índice en Python.
    """

    try:
        client = get_gs_client()
        sh = client.open_by_url(SHEET_URL)
        ws = sh.worksheet("checkin_activos")

        # Buscar fila real
        cells = ws.findall(equipo)

        if not cells:
            st.error("No se encontró un check-in activo para este equipo.")
            return False

        # Tomamos el primer match REAL del sheet
        rownum = cells[0].row

        # Leer encabezados
        headers = ws.row_values(1)
        row = ws.row_values(rownum)

        entry = {
            headers[i]: row[i] if i < len(row) else ""
            for i in range(len(headers))
        }

        # Información del check-in
        equipo = entry.get("Equipo", "")
        tecnico = entry.get("Realizado_por", "")
        hora_inicio_str = entry.get("hora_inicio", "")

        try:
            inicio_dt = datetime.strptime(hora_inicio_str, "%Y-%m-%d %H:%M:%S")
        except:
            inicio_dt = datetime.now()

        fin_dt = datetime.now()
        horas = round((fin_dt - inicio_dt).total_seconds() / 3600, 2)

        # Fila para mantenimientos
        row_to_save = [
            inicio_dt.strftime("%Y-%m-%d"),
            equipo,
            tipo if descripcion == "" else descripcion,
            tecnico,
            descripcion if descripcion != "" else "Check-out",
            horas,
            hora_inicio_str,
            fin_dt.strftime("%Y-%m-%d %H:%M:%S")
        ]

        append_row("mantenimientos", row_to_save)

        # Borrar check-in activo
        ws.delete_rows(rownum)
        read_sheet.clear()

        return True

    except Exception as e:
        st.error(f"Error finalizando check-in: {e}")
        return False

import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
from datetime import datetime

# =============================
#   GOOGLE AUTH
# =============================
def get_gs_client():
    try:
        creds_dict = st.secrets["gcp_service_account"]
        scopes = [
            "https://www.googleapis.com/auth/spreadsheets",
            "https://www.googleapis.com/auth/drive",
        ]
        creds = Credentials.from_service_account_info(creds_dict, scopes=scopes)
        client = gspread.authorize(creds)
        return client
    except Exception as e:
        st.error(f"❌ Error autenticando Google: {e}")
        return None

SHEET_URL = st.secrets["sheets"]["sheet_url"]

# =============================
#   READ SHEET (CACHE)
# =============================
@st.cache_data(ttl=60)  # como lo tenías antes
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


# =============================
#   APPEND ROW
# =============================
def append_row(worksheet_name, row):
    try:
        client = get_gs_client()
        sh = client.open_by_url(SHEET_URL)
        ws = sh.worksheet(worksheet_name)
        ws.append_row(row)
        read_sheet.clear()  # limpia cache
        return True
    except Exception as e:
        st.error(f"❌ Error guardando en Google Sheets ({worksheet_name}): {e}")
        return False


# =============================
#   CHECK-IN / CHECK-OUT
# =============================
def get_active_checkins():
    """Regresa lista de check-ins activos."""
    data = read_sheet("checkin_activos")
    return data or []


def add_active_checkin(equipo, tecnico, tipo):
    """Crea un check-in activo."""
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    row = [equipo, tecnico, now, tipo]
    append_row("checkin_activos", row)


def finalize_active_checkin(row_number, descripcion=""):
    """Finaliza un check-in leyendo SOLO UNA fila → evita 429."""
    try:
        client = get_gs_client()
        sh = client.open_by_url(SHEET_URL)
        ws = sh.worksheet("checkin_activos")

        headers = ws.row_values(1)
        row_vals = ws.row_values(row_number)

        entry = {headers[i]: row_vals[i] if i < len(row_vals) else "" for i in range(len(headers))}

        equipo = entry.get("Equipo", "")
        tecnico = entry.get("Realizado_por", "")
        hora_inicio = entry.get("hora_inicio", "")
        tipo = entry.get("Tipo", "")

        try:
            inicio_dt = datetime.strptime(hora_inicio, "%Y-%m-%d %H:%M:%S")
        except:
            inicio_dt = datetime.now()

        fin_dt = datetime.now()
        horas = round((fin_dt - inicio_dt).total_seconds() / 3600, 2)

        # Guardar en mantenimientos
        new_row = [
            inicio_dt.strftime("%Y-%m-%d"),
            equipo,
            descripcion,
            tecnico,
            "Completado",
            horas,
            hora_inicio,
            fin_dt.strftime("%Y-%m-%d %H:%M:%S"),
        ]

        append_row("mantenimientos", new_row)

        # Borrar check-in activo
        ws.delete_rows(row_number)
        read_sheet.clear()

        return True

    except Exception as e:
        st.error(f"❌ Error finalizando check-in: {e}")
        return False

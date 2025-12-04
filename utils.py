import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
from datetime import datetime


# =====================================
#   AUTENTICACIÓN GOOGLE
# =====================================
def get_gs_client():
    try:
        creds = st.secrets["gcp_service_account"]
        scopes = [
            "https://www.googleapis.com/auth/spreadsheets",
            "https://www.googleapis.com/auth/drive"
        ]
        credentials = Credentials.from_service_account_info(creds, scopes=scopes)
        client = gspread.authorize(credentials)
        return client
    except Exception as e:
        st.error(f"❌ Error autenticando Google Sheets: {e}")
        return None


SHEET_URL = st.secrets["sheets"]["sheet_url"]


# =====================================
#       LECTURA SEGURA DE SHEETS
# =====================================
@st.cache_data(ttl=10)
def read_sheet(sheet_name):
    """Lectura eficiente con cache (previene error 429)."""
    try:
        client = get_gs_client()
        sh = client.open_by_url(SHEET_URL)
        ws = sh.worksheet(sheet_name)
        return ws.get_all_records()
    except Exception as e:
        st.error(f"❌ Error leyendo Google Sheets ({sheet_name}): {e}")
        return []


# =====================================
#     AGREGAR UNA FILA
# =====================================
def append_row(sheet_name, row):
    try:
        client = get_gs_client()
        sh = client.open_by_url(SHEET_URL)
        ws = sh.worksheet(sheet_name)

        ws.append_row(row)

        read_sheet.clear()  # limpiar caché para actualizar datos
        return True
    except Exception as e:
        st.error(f"❌ Error guardando en Google Sheets ({sheet_name}): {e}")
        return False


# =====================================
#     ASEGURAR ENCABEZADOS (1 lectura)
# =====================================
def ensure_headers(sheet_name, expected_headers):
    """
    Asegura encabezados sin lecturas repetidas.
    NO usa get_all_values() → evita error 429.
    Solo lee la primera fila.
    """
    try:
        client = get_gs_client()
        sh = client.open_by_url(SHEET_URL)
        ws = sh.worksheet(sheet_name)

        headers = ws.row_values(1)

        if headers != expected_headers:
            ws.update("A1", [expected_headers])

    except Exception as e:
        st.warning(f"⚠ No se pudieron asegurar encabezados en '{sheet_name}': {e}")


# =====================================
#     CHECK-IN / CHECK-OUT
# =====================================
def get_active_checkins():
    """Regresa la lista de check-ins activos."""
    return read_sheet("checkin_activos")


def add_active_checkin(equipo, realizado_por):
    """Registra un check-in."""
    inicio = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    row = [equipo, realizado_por, inicio]
    append_row("checkin_activos", row)


def finalize_checkin(row_number, descripcion="Sin descripción", estatus="Completado"):
    """
    Finaliza check-in leyendo SOLO la fila necesaria → evita error 429.
    """
    try:
        client = get_gs_client()
        sh = client.open_by_url(SHEET_URL)
        ws = sh.worksheet("checkin_activos")

        headers = ws.row_values(1)
        row_vals = ws.row_values(row_number)

        entry = {headers[i]: row_vals[i] if i < len(row_vals) else "" for i in range(len(headers))}

        equipo = entry.get("Equipo", "")
        realizado_por = entry.get("Realizado_por", "")
        inicio = entry.get("hora_inicio", "")

        # convertir fecha
        try:
            inicio_dt = datetime.strptime(inicio, "%Y-%m-%d %H:%M:%S")
        except:
            inicio_dt = datetime.now()

        fin_dt = datetime.now()
        horas = round((fin_dt - inicio_dt).total_seconds() / 3600, 2)

        # guardar en mantenimientos
        append_row("mantenimientos", [
            inicio_dt.strftime("%Y-%m-%d"),
            equipo,
            descripcion,
            realizado_por,
            estatus,
            horas,
            inicio,
            fin_dt.strftime("%Y-%m-%d %H:%M:%S")
        ])

        # eliminar de checkin_activos
        ws.delete_rows(row_number)
        read_sheet.clear()

        return True

    except Exception as e:
        st.error(f"❌ Error finalizando check-out: {e}")
        return False

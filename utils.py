import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
from datetime import datetime

# =====================================
#   AUTENTICACIÓN GOOGLE
# =====================================
def get_gs_client():
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


# URL del Sheet
SHEET_URL = st.secrets["sheets"]["sheet_url"]


# =====================================
#       LECTURA SEGURA DE SHEETS
# =====================================
@st.cache_data(ttl=10)
def read_sheet(worksheet_name):
    """Lee de Google Sheets de forma eficiente y segura."""
    try:
        client = get_gs_client()
        sh = client.open_by_url(SHEET_URL)
        ws = sh.worksheet(worksheet_name)

        data = ws.get_all_records()  # 1 sola lectura eficiente
        return data

    except Exception as e:
        st.error(f"❌ Error leyendo Google Sheets ({worksheet_name}): {e}")
        return []


# =====================================
#     AGREGAR FILA A UN SHEET
# =====================================
def append_row(worksheet_name, row):
    """Inserta una fila al final del Sheet."""
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


# =====================================
#     ASEGURAR ENCABEZADOS
# =====================================
def ensure_headers(ws, expected_headers):
    """Garantiza que la hoja tenga encabezados correctos."""
    try:
        current = ws.row_values(1)
        if current != expected_headers:
            ws.update("A1:Z1", [expected_headers])
    except Exception as e:
        st.warning(f"Auto-fix: no se pudo asegurar encabezados de '{ws.title}': {e}")


# =====================================
#     CHECK-IN / CHECK-OUT
# =====================================
def get_active_checkins():
    """Regresa la lista de check-ins activos."""
    data = read_sheet("checkin_activos")
    if not data:
        return []
    return data


def add_active_checkin(equipo, realizado_por):
    """Agrega un check-in activo."""
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    row = [equipo, realizado_por, now]
    append_row("checkin_activos", row)


def finalize_active_checkin_by_rownum(row_number, estatus="Completado", descripcion_override=""):
    """
    Finaliza un check-in con solo 2 lecturas.
    No usa get_all_values() para evitar error 429.
    """
    try:
        client = get_gs_client()
        sh = client.open_by_url(SHEET_URL)
        ws = sh.worksheet("checkin_activos")

        # Leer encabezados
        headers = ws.row_values(1)

        # Leer SOLO la fila
        row_vals = ws.row_values(row_number)

        entry = {headers[i]: row_vals[i] if i < len(row_vals) else "" for i in range(len(headers))}

        # Datos base
        equipo = entry.get("Equipo", "")
        realizado_por = entry.get("Realizado_por", "")
        hora_inicio_str = entry.get("hora_inicio", "")

        # Convertir fecha
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
            descripcion_override,
            realizado_por,
            estatus,
            horas,
            hora_inicio_str,
            fin_dt.strftime("%Y-%m-%d %H:%M:%S"),
            ""  # Tipo
        ]

        append_row("mantenimientos", row_to_save)

        # Borrar check-in activo
        ws.delete_rows(row_number)
        read_sheet.clear()

        return True

    except Exception as e:
        st.error(f"❌ Error finalizando check-out: {e}")
        return False

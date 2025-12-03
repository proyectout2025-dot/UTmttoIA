# utils.py
import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
from datetime import datetime, timezone
import pandas as pd

# -------------------------
# Configuración
# -------------------------
SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive",
]

def _get_client():
    creds_info = st.secrets["gcp_service_account"]
    creds = Credentials.from_service_account_info(creds_info, scopes=SCOPES)
    return gspread.authorize(creds)

# -------------------------
# Leer hoja -> DataFrame
# -------------------------
def read_sheet(spreadsheet_name: str, worksheet_name: str) -> pd.DataFrame:
    """Lee worksheet y retorna DataFrame (vacío si hay problema)."""
    try:
        client = _get_client()
        sh = client.open(spreadsheet_name)
        ws = sh.worksheet(worksheet_name)
        rows = ws.get_all_records()
        return pd.DataFrame(rows)
    except Exception as e:
        st.error(f"❌ Error leyendo Google Sheets '{worksheet_name}': {e}")
        return pd.DataFrame()

# -------------------------
# Append con orden de encabezados
# -------------------------
def append_sheet(spreadsheet_name: str, worksheet_name: str, row_dict: dict) -> bool:
    """
    Añade una fila. row_dict keys deben coincidir con los encabezados de la hoja.
    Se respeta el orden de encabezados en la hoja.
    """
    try:
        client = _get_client()
        sh = client.open(spreadsheet_name)
        ws = sh.worksheet(worksheet_name)

        headers = ws.row_values(1)
        row = [row_dict.get(h, "") for h in headers]
        ws.append_row(row, value_input_option="USER_ENTERED")
        return True
    except Exception as e:
        st.error(f"❌ Error guardando en '{worksheet_name}': {e}")
        return False

# -------------------------
# Helpers para checkin_activos
# -------------------------
CHECKIN_SHEET = "checkin_activos"
MANT_SHEET = "mantenimientos"

def get_active_checkins(spreadsheet_name: str):
    """
    Devuelve lista de dicts de checkins activos con campo adicional '_row' = número de fila real.
    """
    try:
        client = _get_client()
        sh = client.open(spreadsheet_name)
        ws = sh.worksheet(CHECKIN_SHEET)
        all_values = ws.get_all_values()
        if len(all_values) < 2:
            return []
        headers = all_values[0]
        records = []
        for i, row in enumerate(all_values[1:], start=2):
            # map row into dict
            row_dict = {headers[j]: row[j] if j < len(row) else "" for j in range(len(headers))}
            row_dict["_row"] = i
            records.append(row_dict)
        return records
    except Exception as e:
        # si la hoja no existe o está vacía devolvemos lista vacía
        st.info(f"(get_active_checkins) {e}")
        return []

def add_active_checkin(spreadsheet_name: str, equipo: str, descripcion: str, realizado_por: str) -> bool:
    """
    Añade un check-in a la hoja CHECKIN_SHEET.
    Encabezados esperados en checkin_activos: Fecha, Equipo, Descripcion, Realizado_por, hora_inicio
    """
    now = datetime.now(timezone.utc).astimezone().replace(tzinfo=None)  # naive local
    hora_inicio = now.strftime("%Y-%m-%d %H:%M:%S")
    row = {
        "Fecha": now.strftime("%Y-%m-%d"),
        "Equipo": equipo,
        "Descripcion": descripcion,
        "Realizado_por": realizado_por,
        "hora_inicio": hora_inicio
    }
    return append_sheet(spreadsheet_name, CHECKIN_SHEET, row)

def delete_row_by_index(spreadsheet_name: str, worksheet_name: str, row_number: int) -> bool:
    """Elimina una fila por número (1-based)."""
    try:
        client = _get_client()
        sh = client.open(spreadsheet_name)
        ws = sh.worksheet(worksheet_name)
        ws.delete_rows(row_number)
        return True
    except Exception as e:
        st.error(f"❌ Error borrando fila {row_number} en '{worksheet_name}': {e}")
        return False

def finalize_active_checkin(spreadsheet_name: str, checkin_row_number: int, estatus: str, descripcion_override: str = "") -> bool:
    """
    Finaliza el checkin ubicado en fila checkin_row_number (de la hoja checkin_activos).
    Calcula tiempo y guarda en hoja 'mantenimientos'. Luego elimina la fila de checkin_activos.
    Retorna True si todo ok.
    """
    try:
        client = _get_client()
        sh = client.open(spreadsheet_name)
        ws_check = sh.worksheet(CHECKIN_SHEET)
        all_values = ws_check.get_all_values()
        if checkin_row_number < 2 or checkin_row_number > len(all_values):
            st.error("Fila de Check-In inválida.")
            return False

        headers_check = all_values[0]
        row_vals = all_values[checkin_row_number - 1]  # 0-based index in list
        row_dict = {headers_check[j]: row_vals[j] if j < len(row_vals) else "" for j in range(len(headers_check))}

        # parse hora_inicio
        hora_inicio_str = row_dict.get("hora_inicio", "")
        parsed = None
        for fmt in ("%Y-%m-%d %H:%M:%S", "%H:%M:%S", "%Y-%m-%dT%H:%M:%S"):
            try:
                parsed = datetime.strptime(hora_inicio_str, fmt)
                break
            except Exception:
                continue
        if parsed is None:
            # fallback: now minus 0
            parsed = datetime.now()

        hora_fin_dt = datetime.now()
        delta = hora_fin_dt - parsed
        horas = round(delta.total_seconds()/3600, 2)

        # Construir fila para 'mantenimientos' según tus encabezados exactos:
        final_row = {
            "Fecha": parsed.strftime("%Y-%m-%d"),
            "Equipo": row_dict.get("Equipo", ""),
            "Descripcion": descripcion_override if descripcion_override else row_dict.get("Descripcion", ""),
            "Realizado_por": row_dict.get("Realizado_por", ""),
            "estatus": estatus,
            "tiempo_hrs": horas,
            "hora_inicio": hora_inicio_str,
            "hora_fin": hora_fin_dt.strftime("%Y-%m-%d %H:%M:%S")
        }

        # append a mantenimientos
        ok = append_sheet(spreadsheet_name, MANT_SHEET, final_row)
        if not ok:
            return False

        # eliminar fila activa
        deleted = delete_row_by_index(spreadsheet_name, CHECKIN_SHEET, checkin_row_number)
        return deleted
    except Exception as e:
        st.error(f"❌ Error finalizando check-in: {e}")
        return False

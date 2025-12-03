# utils.py
import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseUpload
from datetime import datetime
import io

# ================================================================
#   AUTENTICACIÓN GOOGLE
# ================================================================
def _get_credentials(scopes):
    try:
        creds_dict = st.secrets["gcp_service_account"]
        return Credentials.from_service_account_info(creds_dict, scopes=scopes)
    except Exception as e:
        st.error(f"❌ Error cargando credenciales: {e}")
        return None

def get_gs_client():
    scopes = [
        "https://www.googleapis.com/auth/spreadsheets",
        "https://www.googleapis.com/auth/drive"
    ]
    creds = _get_credentials(scopes)
    if not creds:
        return None
    try:
        return gspread.authorize(creds)
    except Exception as e:
        st.error(f"❌ Error autorizando Google Sheets: {e}")
        return None

def get_drive_service():
    scopes = ["https://www.googleapis.com/auth/drive"]
    creds = _get_credentials(scopes)
    if not creds:
        return None
    try:
        return build("drive", "v3", credentials=creds)
    except Exception as e:
        st.error(f"❌ Error creando servicio de Drive: {e}")
        return None

# ================================================================
#   GOOGLE SHEETS (URL desde secrets)
# ================================================================
SHEET_URL = st.secrets["sheets"]["sheet_url"]

def read_sheet(worksheet_name):
    """Lee registros de una hoja por nombre. Retorna lista de dicts o []"""
    try:
        client = get_gs_client()
        sh = client.open_by_url(SHEET_URL)
        ws = sh.worksheet(worksheet_name)
        data = ws.get_all_records()
        return data
    except Exception as e:
        st.error(f"❌ Error leyendo Google Sheets ({worksheet_name}): {e}")
        return []

def append_row(worksheet_name, row):
    """Agrega una fila a una hoja. 'row' es lista o tupla con valores en orden de columnas."""
    try:
        client = get_gs_client()
        sh = client.open_by_url(SHEET_URL)
        ws = sh.worksheet(worksheet_name)
        ws.append_row(row, value_input_option="USER_ENTERED")
        return True
    except Exception as e:
        st.error(f"❌ Error guardando en Google Sheets ({worksheet_name}): {e}")
        return False

# --- backward compatibility wrapper (so other files using append_sheet keep working)
def append_sheet(worksheet_name, row):
    """
    Compat wrapper: mantiene la firma antigua append_sheet(worksheet_name, row)
    row puede ser lista o dict -> si dict, convertimos a list using sheet headers.
    """
    # If row is a dict, align with headers
    try:
        if isinstance(row, dict):
            client = get_gs_client()
            sh = client.open_by_url(SHEET_URL)
            ws = sh.worksheet(worksheet_name)
            headers = ws.row_values(1)
            ordered = [row.get(h, "") for h in headers]
            return append_row(worksheet_name, ordered)
        else:
            return append_row(worksheet_name, row)
    except Exception as e:
        st.error(f"❌ Error en append_sheet wrapper: {e}")
        return False

# ================================================================
#   CHECK-IN / CHECK-OUT
# ================================================================
def get_active_checkins():
    """Devuelve lista de dicts (puede ser vacía)."""
    data = read_sheet("checkin_activos")
    return data if data else []

def add_active_checkin(equipo, descripcion, realizado_por):
    """Agrega un check-in con columnas: Fecha, Equipo, Descripcion, Realizado_por, hora_inicio"""
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    row = [datetime.now().strftime("%Y-%m-%d"), equipo, descripcion, realizado_por, now]
    return append_row("checkin_activos", row)

def finalize_active_checkin_by_rownum(row_number, estatus="Completado", descripcion_override=""):
    """
    Finaliza el checkin ubicado por número de fila en la hoja checkin_activos (1-based).
    Calcula tiempo y guarda en 'mantenimientos'. Luego borra la fila activa.
    """
    try:
        client = get_gs_client()
        sh = client.open_by_url(SHEET_URL)
        ws = sh.worksheet("checkin_activos")
        all_values = ws.get_all_values()
        if row_number < 2 or row_number > len(all_values):
            st.error("Fila inválida para finalizar check-in.")
            return False

        headers = all_values[0]
        row_vals = all_values[row_number - 1]
        entry = {headers[i]: row_vals[i] if i < len(row_vals) else "" for i in range(len(headers))}

        # parse hora_inicio
        hora_inicio_str = entry.get("hora_inicio", "")
        parsed = None
        for fmt in ("%Y-%m-%d %H:%M:%S", "%H:%M:%S", "%Y-%m-%dT%H:%M:%S"):
            try:
                parsed = datetime.strptime(hora_inicio_str, fmt)
                break
            except Exception:
                continue
        if parsed is None:
            parsed = datetime.now()

        hora_fin_dt = datetime.now()
        delta = hora_fin_dt - parsed
        horas = round(delta.total_seconds()/3600, 2)

        final_row = [
            parsed.strftime("%Y-%m-%d"),
            entry.get("Equipo", ""),
            descripcion_override if descripcion_override else entry.get("Descripcion", ""),
            entry.get("Realizado_por", ""),
            estatus,
            horas,
            hora_inicio_str,
            hora_fin_dt.strftime("%Y-%m-%d %H:%M:%S")
        ]

        ok = append_row("mantenimientos", final_row)
        if not ok:
            return False

        # delete that checkin row
        ws.delete_rows(row_number)
        return True
    except Exception as e:
        st.error(f"❌ Error finalizando check-in: {e}")
        return False

# ================================================================
#   GOOGLE DRIVE – UPLOAD ARCHIVOS
# ================================================================
def upload_file_to_drive(file, folder_name="Refacciones"):
    """
    Sube archivos a Drive dentro de una carpeta.
    Si no existe la carpeta, se crea.
    Devuelve el ID del archivo subido o None.
    """
    try:
        service = get_drive_service()
        if not service:
            return None

        # find folder
        query = f"name='{folder_name}' and mimeType='application/vnd.google-apps.folder'"
        existing = service.files().list(q=query, spaces="drive", fields="files(id, name)").execute()
        items = existing.get("files", [])

        if not items:
            folder_metadata = {"name": folder_name, "mimeType": "application/vnd.google-apps.folder"}
            folder = service.files().create(body=folder_metadata, fields="id").execute()
            folder_id = folder["id"]
        else:
            folder_id = items[0]["id"]

        file.seek(0)
        media = MediaIoBaseUpload(io.BytesIO(file.read()), mimetype=file.type)
        file_metadata = {"name": file.name, "parents": [folder_id]}

        uploaded = service.files().create(body=file_metadata, media_body=media, fields="id").execute()
        return uploaded.get("id")
    except Exception as e:
        st.error(f"❌ Error subiendo archivo a Drive: {e}")
        return None

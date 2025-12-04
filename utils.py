# utils.py optimizado sin autofix automático
import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseUpload
from datetime import datetime
import io

# -----------------------------------
# CONFIG
# -----------------------------------
SHEET_URL = st.secrets["sheets"]["sheet_url"]
SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive"
]

EXPECTED_HEADERS = {
    "mantenimientos": [
        "Fecha", "Equipo", "Descripcion", "Realizado_por",
        "estatus", "tiempo_hrs", "hora_inicio", "hora_fin", "Tipo"
    ],
    "checkin_activos": [
        "Fecha", "Equipo", "Descripcion", "Realizado_por", "hora_inicio"
    ],
    "refacciones": [
        "Numero_parte", "Parte_cliente", "Descripcion", "Ubicacion",
        "Existencias", "ArchivoID"
    ],
    "config": ["Parametro", "Valor"]
}

# -----------------------------------
# GOOGLE AUTH
# -----------------------------------
def _get_credentials():
    try:
        creds_dict = st.secrets["gcp_service_account"]
        return Credentials.from_service_account_info(creds_dict, scopes=SCOPES)
    except Exception as e:
        st.error(f"❌ Error obteniendo credenciales: {e}")
        return None

def get_gs_client():
    creds = _get_credentials()
    if not creds:
        return None
    try:
        return gspread.authorize(creds)
    except Exception as e:
        st.error(f"❌ Error creando cliente de Sheets: {e}")
        return None

def get_drive_service():
    creds = _get_credentials()
    if not creds:
        return None
    try:
        return build("drive", "v3", credentials=creds)
    except Exception as e:
        st.error(f"❌ Error creando servicio Drive: {e}")
        return None


# -----------------------------------
# SHEET BASIC OPERATIONS
# -----------------------------------
def read_sheet(worksheet_name):
    """Lectura directa NORMAL, sin autofix automático."""
    try:
        client = get_gs_client()
        sh = client.open_by_url(SHEET_URL)
        ws = sh.worksheet(worksheet_name)
        return ws.get_all_records()
    except Exception as e:
        st.error(f"❌ Error leyendo {worksheet_name}: {e}")
        return []


def append_row(worksheet_name, row_list):
    """Escritura directa NORMAL."""
    try:
        client = get_gs_client()
        sh = client.open_by_url(SHEET_URL)
        ws = sh.worksheet(worksheet_name)
        ws.append_row(row_list, value_input_option="USER_ENTERED")
        return True
    except Exception as e:
        st.error(f"❌ Error guardando en {worksheet_name}: {e}")
        return False


def append_sheet(worksheet_name, row):
    """Wrapper que admite dict o list."""
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
        st.error(f"❌ Error append_sheet(): {e}")
        return False


# -----------------------------------
# CHECK-IN / CHECK-OUT
# -----------------------------------
def get_active_checkins():
    return read_sheet("checkin_activos") or []


def add_active_checkin(equipo, descripcion, realizado_por):
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    row = [
        datetime.now().strftime("%Y-%m-%d"),
        equipo,
        descripcion,
        realizado_por,
        now
    ]
    return append_row("checkin_activos", row)


def finalize_active_checkin_by_rownum(row_number, estatus="Completado", descripcion_override=""):
    try:
        client = get_gs_client()
        sh = client.open_by_url(SHEET_URL)
        ws = sh.worksheet("checkin_activos")

        all_vals = ws.get_all_values()
        headers = all_vals[0]

        row_vals = all_vals[row_number - 1]
        entry = {headers[i]: row_vals[i] if i < len(row_vals) else "" for i in range(len(headers))}

        hora_inicio_str = entry.get("hora_inicio", "")
        try:
            inicio_dt = datetime.strptime(hora_inicio_str, "%Y-%m-%d %H:%M:%S")
        except:
            inicio_dt = datetime.now()

        fin_dt = datetime.now()
        horas = round((fin_dt - inicio_dt).total_seconds() / 3600, 2)

        final = [
            inicio_dt.strftime("%Y-%m-%d"),
            entry.get("Equipo", ""),
            descripcion_override if descripcion_override else entry.get("Descripcion", ""),
            entry.get("Realizado_por", ""),
            estatus,
            horas,
            hora_inicio_str,
            fin_dt.strftime("%Y-%m-%d %H:%M:%S"),
            ""  # Tipo
        ]

        append_row("mantenimientos", final)
        ws.delete_rows(row_number)
        return True

    except Exception as e:
        st.error(f"❌ Error finalizando check-out: {e}")
        return False


# -----------------------------------
# DRIVE UPLOAD
# -----------------------------------
def upload_file_to_drive(file, folder_name="Refacciones"):
    try:
        service = get_drive_service()
        if not service:
            return None

        query = f"name='{folder_name}' and mimeType='application/vnd.google-apps.folder'"
        results = service.files().list(q=query, fields="files(id,name)").execute()
        items = results.get("files", [])

        if not items:
            folder = service.files().create(
                body={"name": folder_name, "mimeType": "application/vnd.google-apps.folder"},
                fields="id").execute()
            folder_id = folder["id"]
        else:
            folder_id = items[0]["id"]

        file.seek(0)
        media = MediaIoBaseUpload(io.BytesIO(file.read()), mimetype=file.type)
        uploaded = service.files().create(
            body={"name": file.name, "parents": [folder_id]},
            media_body=media,
            fields="id"
        ).execute()

        return uploaded.get("id")

    except Exception as e:
        st.error(f"❌ Error subiendo archivo: {e}")
        return None

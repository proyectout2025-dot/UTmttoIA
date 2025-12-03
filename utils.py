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
    """Obtiene credenciales desde st.secrets."""
    try:
        creds_dict = st.secrets["gcp_service_account"]
        return Credentials.from_service_account_info(creds_dict, scopes=scopes)
    except Exception as e:
        st.error(f"❌ Error cargando credenciales: {e}")
        return None


def get_gs_client():
    """Cliente autenticado para Google Sheets."""
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
    """Servicio autenticado de Google Drive."""
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
#   GOOGLE SHEETS
# ================================================================
SHEET_URL = st.secrets["sheets"]["sheet_url"]


def read_sheet(worksheet_name):
    """Lee registros de una hoja por nombre."""
    try:
        client = get_gs_client()
        sh = client.open_by_url(SHEET_URL)
        ws = sh.worksheet(worksheet_name)
        data = ws.get_all_records()
        return data
    except Exception as e:
        st.error(f"❌ Error leyendo Google Sheets ({worksheet_name}): {e}")
        return None


def append_row(worksheet_name, row):
    """Agrega una fila a una hoja."""
    try:
        client = get_gs_client()
        sh = client.open_by_url(SHEET_URL)
        ws = sh.worksheet(worksheet_name)
        ws.append_row(row)
        return True
    except Exception as e:
        st.error(f"❌ Error guardando en Google Sheets ({worksheet_name}): {e}")
        return False


# ================================================================
#   CHECK-IN / CHECK-OUT
# ================================================================
def get_active_checkins():
    """Obtiene check-ins activos."""
    data = read_sheet("checkin_activos")
    return data if data else []


def add_active_checkin(equipo, realizado_por):
    """Registra un check-in activo."""
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    row = [equipo, realizado_por, now]  # columnas: equipo, usuario, hora_inicio
    append_row("checkin_activos", row)


def finalize_active_checkin(equipo):
    """Finaliza un check-in y calcula horas."""
    activos = get_active_checkins()
    if not activos:
        return None

    now = datetime.now()

    for entry in activos:
        if entry["equipo"] == equipo:
            inicio = datetime.strptime(entry["hora_inicio"], "%Y-%m-%d %H:%M:%S")
            horas = round((now - inicio).total_seconds() / 3600, 2)
            fin = now.strftime("%Y-%m-%d %H:%M:%S")

            return horas, entry["realizado_por"], entry["hora_inicio"], fin

    return None


# ================================================================
#   GOOGLE DRIVE – UPLOAD ARCHIVOS
# ================================================================
def upload_file_to_drive(file, folder_name="Refacciones"):
    """
    Sube archivos a Drive dentro de una carpeta.
    Si no existe la carpeta, se crea.
    Devuelve el ID del archivo subido.
    """
    try:
        service = get_drive_service()
        if not service:
            return None

        # 1️⃣ Buscar carpeta
        query = f"name='{folder_name}' and mimeType='application/vnd.google-apps.folder'"
        existing = service.files().list(
            q=query,
            spaces="drive",
            fields="files(id, name)"
        ).execute()

        items = existing.get("files", [])

        # 2️⃣ Crear carpeta si no existe
        if not items:
            folder_metadata = {
                "name": folder_name,
                "mimeType": "application/vnd.google-apps.folder"
            }
            folder = service.files().create(
                body=folder_metadata,
                fields="id"
            ).execute()
            folder_id = folder["id"]
        else:
            folder_id = items[0]["id"]

        # 3️⃣ Subir archivo
        file_metadata = {
            "name": file.name,
            "parents": [folder_id]
        }

        media = MediaIoBaseUpload(
            io.BytesIO(file.read()),
            mimetype=file.type
        )

        uploaded = service.files().create(
            body=file_metadata,
            media_body=media,
            fields="id"
        ).execute()

        return uploaded.get("id")

    except Exception as e:
        st.error(f"❌ Error subiendo archivo a Drive: {e}")
        return None

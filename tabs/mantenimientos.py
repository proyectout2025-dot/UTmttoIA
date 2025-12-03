import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseUpload
import pandas as pd
import io
from datetime import datetime


# ==========================
#  AUTENTICACIÓN GOOGLE
# ==========================
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


def get_drive_service():
    try:
        creds_dict = st.secrets["gcp_service_account"]

        scopes = ["https://www.googleapis.com/auth/drive"]
        creds = Credentials.from_service_account_info(creds_dict, scopes=scopes)

        service = build("drive", "v3", credentials=creds)
        return service
    except Exception as e:
        st.error(f"❌ Error creando servicio de Drive: {e}")
        return None


# ==========================
#   GOOGLE SHEETS
# ==========================
SHEET_URL = st.secrets["sheets"]["sheet_url"]


def read_sheet(worksheet_name):
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
    try:
        client = get_gs_client()
        sh = client.open_by_url(SHEET_URL)
        ws = sh.worksheet(worksheet_name)
        ws.append_row(row)
        return True
    except Exception as e:
        st.error(f"❌ Error guardando en Google Sheets ({worksheet_name}): {e}")
        return False


# ==========================
#   CHECK-IN / CHECK-OUT
# ==========================
def get_active_checkins():
    data = read_sheet("checkin_activos")
    if not data:
        return []
    return data


def add_active_checkin(equipo, realizado_por):
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    row = [equipo, realizado_por, now]
    append_row("checkin_activos", row)


def finalize_active_checkin(equipo):
    activos = read_sheet("checkin_activos")
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


# ==========================
#   GOOGLE DRIVE UPLOAD
# ==========================
def upload_file_to_drive(file, folder_name="Refacciones"):
    """
    Sube un archivo a Google Drive dentro de una carpeta.
    Si la carpeta no existe, la crea.
    Devuelve el ID del archivo subido.
    """
    try:
        service = get_drive_service()

        # 1️⃣ Buscar carpeta existente
        query = f"name='{folder_name}' and mimeType='application/vnd.google-apps.folder'"
        results = (
            service.files()
            .list(q=query, spaces="drive", fields="files(id, name)")
            .execute()
        )
        items = results.get("files", [])

        # 2️⃣ Crear carpeta si no existe
        if not items:
            file_metadata = {
                "name": folder_name,
                "mimeType": "application/vnd.google-apps.folder",
            }
            folder = service.files().create(body=file_metadata, fields="id").execute()
            folder_id = folder.get("id")
        else:
            folder_id = items[0]["id"]

        # 3️⃣ Subir archivo
        file_metadata = {
            "name": file.name,
            "parents": [folder_id]
        }

        media = MediaIoBaseUpload(io.BytesIO(file.read()), mimetype=file.type)

        uploaded = (
            service.files()
            .create(body=file_metadata, media_body=media, fields="id")
            .execute()
        )

        return uploaded.get("id")

    except Exception as e:
        st.error(f"❌ Error subiendo archivo a Drive: {e}")
        return None

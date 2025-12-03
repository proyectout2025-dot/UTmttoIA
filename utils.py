import streamlit as st
import gspread
from google.oauth2.service_account import Credentials


# -----------------------------------
# Conexión a Google Sheets
# -----------------------------------
def _get_client():
    creds_info = st.secrets["gcp_service_account"]

    scopes = [
        "https://www.googleapis.com/auth/spreadsheets",
        "https://www.googleapis.com/auth/drive",
    ]

    credentials = Credentials.from_service_account_info(creds_info, scopes=scopes)
    client = gspread.authorize(credentials)
    return client


# -----------------------------------
# Leer hoja completa
# -----------------------------------
def read_sheet(spreadsheet_name, worksheet_name):
    client = _get_client()
    sh = client.open(spreadsheet_name)
    ws = sh.worksheet(worksheet_name)
    return ws.get_all_records()


# -----------------------------------
# Escribir una fila nueva
# -----------------------------------
def append_sheet(spreadsheet_name, worksheet_name, row_dict):
    client = _get_client()
    sh = client.open(spreadsheet_name)
    ws = sh.worksheet(worksheet_name)

    headers = ws.row_values(1)

    row = [row_dict.get(h, "") for h in headers]
    ws.append_row(row)

# ---------------------------------------------------------
# SUBIR ARCHIVOS A GOOGLE DRIVE Y REGRESAR URL PÚBLICA
# ---------------------------------------------------------

from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseUpload
from google.oauth2.service_account import Credentials
import io
import streamlit as st

def upload_file_to_drive(file, filename, folder_id=None):
    """
    Sube un archivo (PDF, imagen, etc.) a Google Drive y regresa un enlace público.
    No se usa en la pestaña Mantenimientos, pero se deja funcional para otras pestañas.
    """

    try:
        # 1️⃣ Credenciales desde secrets
        creds_info = st.secrets["gcp_service_account"]
        credentials = Credentials.from_service_account_info(
            creds_info,
            scopes=["https://www.googleapis.com/auth/drive"]
        )

        # 2️⃣ Servicio Drive
        drive_service = build("drive", "v3", credentials=credentials)

        # 3️⃣ Preparar archivo
        file_content = io.BytesIO(file.read())
        media = MediaIoBaseUpload(file_content, mimetype=file.type)

        metadata = {
            "name": filename,
            "mimeType": file.type,
        }

        if folder_id:
            metadata["parents"] = [folder_id]

        # 4️⃣ Subir archivo
        uploaded = drive_service.files().create(
            body=metadata,
            media_body=media,
            fields="id"
        ).execute()

        file_id = uploaded.get("id")

        # 5️⃣ Hacerlo público
        drive_service.permissions().create(
            fileId=file_id,
            body={"role": "reader", "type": "anyone"},
        ).execute()

        # 6️⃣ Regresar URL pública
        return f"https://drive.google.com/file/d/{file_id}/view?usp=sharing"

    except Exception as e:
        st.error(f"❌ Error al subir archivo a Drive: {e}")
        return None

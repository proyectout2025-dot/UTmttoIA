import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
import tempfile
import os

# -------- AUTENTICACIÓN GOOGLE ----------
def get_gsheet(sheet_name: str):
    creds = Credentials.from_service_account_info(
        st.secrets["gcp_service_account"],
        scopes=[
            "https://www.googleapis.com/auth/spreadsheets",
            "https://www.googleapis.com/auth/drive"
        ],
    )
    client = gspread.authorize(creds)

    sheet_url = st.secrets["sheets"]["sheet_url"]
    spreadsheet = client.open_by_url(sheet_url)
    return spreadsheet.worksheet(sheet_name)

# -------- LEER HOJA ----------
def read_sheet(sheet_name: str):
    ws = get_gsheet(sheet_name)
    return ws.get_all_records()

# -------- AGREGAR UNA FILA --------
def append_sheet(sheet_name: str, row: list):
    ws = get_gsheet(sheet_name)
    ws.append_row(row)

# -------- SUBIR ARCHIVO A DRIVE --------
def upload_file_to_drive(uploaded_file):
    creds = Credentials.from_service_account_info(
        st.secrets["gcp_service_account"],
        scopes=["https://www.googleapis.com/auth/drive"],
    )
    service = build("drive", "v3", credentials=creds)

    # Guardar temporalmente
    with tempfile.NamedTemporaryFile(delete=False) as tmp:
        tmp.write(uploaded_file.getvalue())
        temp_path = tmp.name

    file_metadata = {"name": uploaded_file.name}
    media = MediaFileUpload(temp_path, mimetype="application/pdf")

    file = service.files().create(
        body=file_metadata,
        media_body=media,
        fields="id"
    ).execute()

    os.remove(temp_path)

    return f"https://drive.google.com/file/d/{file['id']}/view"

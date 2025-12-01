import gspread
from google.oauth2.service_account import Credentials
import pandas as pd
from openai import OpenAI
import streamlit as st
import base64
import PyPDF2
import io

# -------------------------
# GOOGLE AUTH
# -------------------------
def get_gsheet(sheet_name):
    secrets = st.secrets["google"]
    scope = [
        "https://www.googleapis.com/auth/spreadsheets",
        "https://www.googleapis.com/auth/drive"
    ]

    credentials = Credentials.from_service_account_info(secrets, scopes=scope)
    client = gspread.authorize(credentials)
    sheet = client.open_by_url(st.secrets["sheets"]["sheet_url"])
    return sheet.worksheet(sheet_name)


# -------------------------
# LECTURA DE SHEETS
# -------------------------
def read_sheet(sheet_name):
    ws = get_gsheet(sheet_name)
    data = ws.get_all_records()
    return pd.DataFrame(data)


# -------------------------
# ESCRITURA A SHEETS
# -------------------------
def append_sheet(sheet_name, row_dict):
    ws = get_gsheet(sheet_name)
    ws.append_row(list(row_dict.values()))


# -------------------------
# SUBIR ARCHIVOS A DRIVE
# -------------------------
def upload_file_to_drive(file, filename):
    import googleapiclient.discovery
    from googleapiclient.http import MediaIoBaseUpload

    secrets = st.secrets["google"]
    credentials = Credentials.from_service_account_info(
        secrets,
        scopes=["https://www.googleapis.com/auth/drive"]
    )

    service = googleapiclient.discovery.build("drive", "v3", credentials=credentials)

    file_metadata = {
        "name": filename,
        "parents": [st.secrets["drive"]["folder_id"]]
    }

    media = MediaIoBaseUpload(file, mimetype="application/pdf", resumable=True)

    uploaded = service.files().create(
        body=file_metadata,
        media_body=media,
        fields="id, webViewLink, webContentLink"
    ).execute()

    return uploaded

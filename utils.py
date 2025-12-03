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

import streamlit as st
import gspread
from google.oauth2.service_account import Credentials

# -----------------------------------------------------
# OBTENER HOJA DE GOOGLE SHEETS
# -----------------------------------------------------
def get_gsheet(sheet_name):
    creds_dict = st.secrets["google_service_account"]

    creds = Credentials.from_service_account_info(
        creds_dict,
        scopes=[
            "https://www.googleapis.com/auth/spreadsheets",
            "https://www.googleapis.com/auth/drive"
        ],
    )

    client = gspread.authorize(creds)

    sheet = client.open_by_url(st.secrets["sheets"]["sheet_url"])

    return sheet.worksheet(sheet_name)

# -----------------------------------------------------
# LEER HOJA COMPLETA
# -----------------------------------------------------
def read_sheet(sheet_name):
    ws = get_gsheet(sheet_name)
    return ws.get_all_records()

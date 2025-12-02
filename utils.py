import streamlit as st
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials

# Autenticación Google Sheets
scope = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive"
]

creds = Credentials.from_service_account_info(
    st.secrets["gcp_service_account"], scopes=scope
)

gc = gspread.authorize(creds)

# Abrir documento
SPREADSHEET_ID = st.secrets["spreadsheet_id"]
sh = gc.open_by_key(SPREADSHEET_ID)


def get_sheet(sheet_name):
    ws = sh.worksheet(sheet_name)
    data = ws.get_all_records()
    return pd.DataFrame(data)


def add_mantenimiento(values: dict):
    ws = sh.worksheet("mantenimientos")
    ws.append_row(list(values.values()))

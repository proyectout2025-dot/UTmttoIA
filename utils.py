import gspread
from google.oauth2.service_account import Credentials
import streamlit as st
import pandas as pd

# ----------------------------
# AUTENTICACIÓN GOOGLE SHEETS
# ----------------------------

def get_gsheet_client():
    scopes = [
        "https://www.googleapis.com/auth/spreadsheets",
        "https://www.googleapis.com/auth/drive"
    ]

    creds = Credentials.from_service_account_info(
        st.secrets["gcp_service_account"],
        scopes=scopes
    )

    return gspread.authorize(creds)

# ----------------------------
# OBTENER HOJA DE CÁLCULO
# ----------------------------

def get_gsheet(sheet_name):
    client = get_gsheet_client()
    spreadsheet_url = st.secrets["sheets"]["sheet_url"]

    sheet = client.open_by_url(spreadsheet_url)
    worksheet = sheet.worksheet(sheet_name)
    return worksheet

# ----------------------------
# LEER DATOS DE GOOGLE SHEETS
# ----------------------------

def read_sheet(sheet_name):
    ws = get_gsheet(sheet_name)
    data = ws.get_all_records()
    return pd.DataFrame(data)

# ----------------------------
# AGREGAR FILA A GOOGLE SHEETS
# ----------------------------

def append_sheet(sheet_name, row_values):
    ws = get_gsheet(sheet_name)
    ws.append_row(row_values)

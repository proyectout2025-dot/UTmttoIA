import streamlit as st
import gspread
import pandas as pd
from oauth2client.service_account import ServiceAccountCredentials

# ---------------------------------------------------
# AUTENTICACIÓN GOOGLE SERVICE ACCOUNT
# ---------------------------------------------------
def get_gsheet(sheet_name):
    try:
        scope = [
            "https://www.googleapis.com/auth/spreadsheets",
            "https://www.googleapis.com/auth/drive"
        ]

        creds = ServiceAccountCredentials.from_json_keyfile_dict(
            st.secrets["gcp_service_account"], scope
        )

        client = gspread.authorize(creds)

        sheet_url = st.secrets["sheets"]["sheet_url"]
        ss = client.open_by_url(sheet_url)

        return ss.worksheet(sheet_name)

    except Exception as e:
        st.error(f"❌ Error al conectar con Google Sheets: {e}")
        return None

# ---------------------------------------------------
# LEER DATOS
# ---------------------------------------------------
def read_sheet(sheet_name):
    ws = get_gsheet(sheet_name)
    if ws is None:
        return None

    try:
        data = ws.get_all_records()
        return pd.DataFrame(data)
    except:
        return None

# ---------------------------------------------------
# INSERTAR FILAS
# ---------------------------------------------------
def append_sheet(sheet_name, row):
    ws = get_gsheet(sheet_name)
    if ws is None:
        return None

    try:
        ws.append_row(row)
        return True
    except Exception as e:
        st.error(f"❌ Error al guardar en Google Sheets: {e}")
        return False

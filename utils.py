# =============================
# utils.py — FINAL Y CORRECTO
# =============================

import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
from datetime import datetime

# ----------------------------------------
# Autenticación
# ----------------------------------------
def get_gs_client():
    creds_dict = st.secrets["gcp_service_account"]
    scopes = [
        "https://www.googleapis.com/auth/spreadsheets",
        "https://www.googleapis.com/auth/drive"
    ]
    creds = Credentials.from_service_account_info(creds_dict, scopes=scopes)
    return gspread.authorize(creds)

SHEET_URL = st.secrets["sheets"]["sheet_url"]

# ----------------------------------------
# Sheets: Lectura / Escritura
# ----------------------------------------
def read_sheet(sheet_name):
    try:
        client = get_gs_client()
        sh = client.open_by_url(SHEET_URL)
        ws = sh.worksheet(sheet_name)
        return ws.get_all_records()
    except Exception as e:
        st.error(f"Error leyendo hoja {sheet_name}: {e}")
        return []

def append_row(sheet_name, row):
    try:
        client = get_gs_client()
        sh = client.open_by_url(SHEET_URL)
        ws = sh.worksheet(sheet_name)
        ws.append_row(row)
        return True
    except Exception as e:
        st.error(f"Error agregando fila en {sheet_name}: {e}")
        return False

# ----------------------------------------
# Check-in / Check-out
# ----------------------------------------
def get_active_checkins():
    return read_sheet("checkin_activos")

def add_active_checkin(equipo, tecnico):
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    return append_row("checkin_activos", [equipo, tecnico, now])

def finalize_active_checkin(equipo):
    activos = read_sheet("checkin_activos")
    now = datetime.now()

    for a in activos:
        if a["equipo"] == equipo:
            inicio = datetime.strptime(a["hora_inicio"], "%Y-%m-%d %H:%M:%S")
            horas = round((now - inicio).total_seconds() / 3600, 2)
            return horas, a["realizado_por"], a["hora_inicio"], now.strftime("%Y-%m-%d %H:%M:%S")

    return None

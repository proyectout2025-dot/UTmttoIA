import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
import pandas as pd
from datetime import datetime

# ============================
# CONFIGURACIÓN GOOGLE
# ============================

SHEET_URL = st.secrets["sheets"]["sheet_url"]

SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive"
]

EXPECTED_HEADERS = {
    "mantenimientos": [
        "Fecha", "Equipo", "Descripcion", "Realizado_por",
        "estatus", "tiempo_hrs", "hora_inicio", "hora_fin"
    ],
    "checkin_activos": [
        "Fecha", "Equipo", "Descripcion", "Realizado_por", "hora_inicio"
    ],
    "refacciones": [
        "Codigo", "Nombre", "Descripcion", "Ubicacion", "Stock"
    ]
}


# ============================
# AUTENTICACIÓN
# ============================

def get_gs_client():
    try:
        creds_dict = st.secrets["gcp_service_account"]
        creds = Credentials.from_service_account_info(creds_dict, scopes=SCOPES)
        client = gspread.authorize(creds)
        return client
    except Exception as e:
        st.error(f"❌ Error autenticando Google: {e}")
        return None


# ============================
# AUTO-FIX GLOBAL DE ENCABEZADOS
# ============================

def autofix_all_headers():
    """Repara TODAS las hojas automáticamente."""
    client = get_gs_client()
    if not client:
        return False

    try:
        sh = client.open_by_url(SHEET_URL)

        for sheet_name, expected in EXPECTED_HEADERS.items():
            try:
                ws = sh.worksheet(sheet_name)
                current = ws.row_values(1)
                current = [c.strip() for c in current]

                if current != expected:
                    ws.update("1:1", [expected])
            except:
                pass  # Si alguna hoja no existe, la ignoramos

        return True

    except Exception as e:
        st.error(f"❌ Error ejecutando Auto-Fix global: {e}")
        return False


# ============================
# GOOGLE SHEETS HELPERS
# ============================

def read_sheet(worksheet_name):
    autofix_all_headers()  # <-- AUTO-FIX SIEMPRE ANTES DE LEER

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
    autofix_all_headers()  # <-- AUTO-FIX SIEMPRE ANTES DE GUARDAR

    try:
        client = get_gs_client()
        sh = client.open_by_url(SHEET_URL)
        ws = sh.worksheet(worksheet_name)
        ws.append_row(row)
        return True
    except Exception as e:
        st.error(f"❌ Error guardando en Google Sheets ({worksheet_name}): {e}")
        return False


# ============================
# CHECK-IN / CHECK-OUT
# ============================

def get_active_checkins():
    return read_sheet("checkin_activos") or []


def add_active_checkin(equipo, descripcion, realizado_por):
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    row = [now, equipo, descripcion, realizado_por, now]
    append_row("checkin_activos", row)


def finalize_active_checkin(equipo):
    activos = read_sheet("checkin_activos")
    if not activos:
        return None

    now = datetime.now()

    for entry in activos:
        if entry.get("Equipo") == equipo:
            inicio = datetime.strptime(entry["hora_inicio"], "%Y-%m-%d %H:%M:%S")
            horas = round((now - inicio).total_seconds() / 3600, 2)
            fin = now.strftime("%Y-%m-%d %H:%M:%S")
            return horas, entry["Descripcion"], entry["Realizado_por"], entry["hora_inicio"], fin

    return None

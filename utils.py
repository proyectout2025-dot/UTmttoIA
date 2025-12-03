import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
import pandas as pd
from datetime import datetime

# -----------------------------------
#   CONFIGURACIÓN GOOGLE SHEETS
# -----------------------------------

SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive"
]

CREDS = Credentials.from_service_account_info(
    st.secrets["gcp_service_account"], scopes=SCOPES
)

CLIENT = gspread.authorize(CREDS)


# -----------------------------------
#   LECTURA DE HOJA
# -----------------------------------

def read_sheet(spreadsheet_name: str, worksheet_name: str):
    """Lee datos de una hoja exacta."""
    try:
        sh = CLIENT.open(spreadsheet_name)
        ws = sh.worksheet(worksheet_name)
        data = ws.get_all_records()
        return data
    except Exception as e:
        st.error(f"❌ Error leyendo Google Sheets: {e}")
        return []


# -----------------------------------
#   ESCRITURA
# -----------------------------------

def append_sheet(spreadsheet_name: str, worksheet_name: str, row_list: list):
    """Agrega una fila."""
    try:
        sh = CLIENT.open(spreadsheet_name)
        ws = sh.worksheet(worksheet_name)
        ws.append_row(row_list)
        return True
    except Exception as e:
        st.error(f"❌ Error al agregar registro: {e}")
        return False


# -----------------------------------
#  CHECK-IN (INICIAR)
# -----------------------------------

def add_active_checkin(spreadsheet_name: str, equipo: str, realizado_por: str):
    """Registra un checkin en hoja 'checkin_activos'."""
    hora_inicio = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    return append_sheet(
        spreadsheet_name,
        "checkin_activos",
        [equipo, realizado_por, hora_inicio]
    )


# -----------------------------------
#  OBTENER CHECKIN ACTIVOS
# -----------------------------------

def get_active_checkins(spreadsheet_name: str):
    """Regresa diccionario con checkins: equipo → fila."""
    data = read_sheet(spreadsheet_name, "checkin_activos")

    activos = {}
    for row in data:
        activos[row["equipo"]] = row
    return activos


# -----------------------------------
#  CHECK-OUT (FINALIZAR)
# -----------------------------------

def close_checkin(spreadsheet_name: str, equipo: str,
                  descripcion: str, estatus: str):
    """Finaliza el checkin, calcula horas y lo pasa a 'mantenimientos'."""

    activos = read_sheet(spreadsheet_name, "checkin_activos")
    fila = None

    for r in activos:
        if r["equipo"] == equipo:
            fila = r
            break

    if fila is None:
        st.error("❌ No se encontró checkin activo.")
        return False

    hora_inicio = datetime.strptime(fila["hora_inicio"], "%Y-%m-%d %H:%M:%S")
    hora_fin = datetime.now()
    tiempo_hrs = round((hora_fin - hora_inicio).total_seconds() / 3600, 2)

    fecha = datetime.now().strftime("%Y-%m-%d")
    realizado_por = fila["realizado_por"]

    # Guardar en mantenimientos
    append_sheet(
        spreadsheet_name,
        "mantenimientos",
        [
            fecha,
            equipo,
            descripcion,
            realizado_por,
            estatus,
            tiempo_hrs,
            fila["hora_inicio"],
            hora_fin.strftime("%Y-%m-%d %H:%M:%S")
        ]
    )

    # Borrar checkin activo
    delete_checkin_row(spreadsheet_name, equipo)

    return True


def delete_checkin_row(spreadsheet_name: str, equipo: str):
    """Elimina un checkin activo por equipo."""
    sh = CLIENT.open(spreadsheet_name)
    ws = sh.worksheet("checkin_activos")
    data = ws.get_all_values()

    for i, row in enumerate(data, start=1):
        if row and row[0] == equipo:
            ws.delete_rows(i)
            return True
    return False

import gspread
from google.oauth2.service_account import Credentials
import pandas as pd
import datetime


# CONFIG
SPREADSHEET_NAME = "base_datos_app"

SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive",
]


def get_client():
    creds = Credentials.from_service_account_file(
        "service_account.json", scopes=SCOPES
    )
    client = gspread.authorize(creds)
    return client


# =============== GENERALES ==================

def read_sheet(sheet_name: str) -> pd.DataFrame:
    try:
        client = get_client()
        sheet = client.open(SPREADSHEET_NAME).worksheet(sheet_name)
        data = sheet.get_all_records()
        df = pd.DataFrame(data)

        return df
    except Exception as e:
        print(f"❌ Error leyendo Google Sheets: {sheet_name} → {e}")
        return pd.DataFrame()


def append_sheet(sheet_name: str, row: dict):
    try:
        client = get_client()
        sheet = client.open(SPREADSHEET_NAME).worksheet(sheet_name)
        sheet.append_row(list(row.values()))
        return True
    except Exception as e:
        print(f"❌ Error al escribir en {sheet_name}: {e}")
        return False


# =============== CHECK-IN / CHECK-OUT ==================

CHECKIN_SHEET = "checkin_activos"


def add_active_checkin(equipo, descripcion, realizado_por):
    now = datetime.datetime.now()
    row = {
        "Fecha": now.strftime("%Y-%m-%d"),
        "Equipo": equipo,
        "Descripcion": descripcion,
        "Realizado_por": realizado_por,
        "hora_inicio": now.strftime("%H:%M:%S"),
    }
    append_sheet(CHECKIN_SHEET, row)


def get_active_checkins():
    df = read_sheet(CHECKIN_SHEET)
    return df if not df.empty else pd.DataFrame()


def finalize_active_checkin(checkin_row, estatus):
    now = datetime.datetime.now()
    hora_fin = now.strftime("%H:%M:%S")

    # cálculo del tiempo total
    t1 = datetime.datetime.strptime(checkin_row["hora_inicio"], "%H:%M:%S")
    t2 = datetime.datetime.strptime(hora_fin, "%H:%M:%S")
    diff = (t2 - t1).total_seconds() / 3600

    row = {
        "Fecha": checkin_row["Fecha"],
        "Equipo": checkin_row["Equipo"],
        "Descripcion": checkin_row["Descripcion"],
        "Realizado_por": checkin_row["Realizado_por"],
        "estatus": estatus,
        "tiempo_hrs": round(diff, 2),
        "hora_inicio": checkin_row["hora_inicio"],
        "hora_fin": hora_fin,
    }

    # guardar en mantenimientos
    append_sheet("mantenimientos", row)

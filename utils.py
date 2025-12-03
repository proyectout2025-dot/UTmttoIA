import gspread
from google.oauth2.service_account import Credentials
import pandas as pd
import datetime


SPREADSHEET_NAME = "base_datos_app"

SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive",
]


def get_client():
    creds = Credentials.from_service_account_file(
        "service_account.json", scopes=SCOPES
    )
    return gspread.authorize(creds)


# =====================================================
# LECTURA / ESCRITURA SEGURA
# =====================================================

def read_sheet(sheet_name):
    try:
        client = get_client()
        sheet = client.open(SPREADSHEET_NAME).worksheet(sheet_name)
        data = sheet.get_all_records()
        return pd.DataFrame(data)
    except Exception as e:
        print(f"❌ Error leyendo hoja {sheet_name}: {e}")
        return pd.DataFrame()


def append_sheet(sheet_name, row_dict):
    try:
        client = get_client()
        sheet = client.open(SPREADSHEET_NAME).worksheet(sheet_name)

        # Obtener encabezados reales
        headers = sheet.row_values(1)

        # Acomodar los valores EXACTAMENTE en el orden correcto
        row = [row_dict.get(h, "") for h in headers]

        sheet.append_row(row)
        return True

    except Exception as e:
        print(f"❌ Error guardando en hoja {sheet_name}: {e}")
        return False


# =====================================================
# CHECK-IN / CHECK-OUT
# =====================================================

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


def finalize_active_checkin(row, estatus):
    now = datetime.datetime.now()
    hora_fin = now.strftime("%H:%M:%S")

    # calcular tiempo
    t1 = datetime.datetime.strptime(row["hora_inicio"], "%H:%M:%S")
    t2 = datetime.datetime.strptime(hora_fin, "%H:%M:%S")

    diff = (t2 - t1).total_seconds() / 3600

    new_row = {
        "Fecha": row["Fecha"],
        "Equipo": row["Equipo"],
        "Descripcion": row["Descripcion"],
        "Realizado_por": row["Realizado_por"],
        "estatus": estatus,
        "tiempo_hrs": round(diff, 2),
        "hora_inicio": row["hora_inicio"],
        "hora_fin": hora_fin
    }

    append_sheet("mantenimientos", new_row)

import gspread
from google.oauth2.service_account import Credentials
import pandas as pd

# ---------------------------------------------------------
# CONFIGURACIÓN DE GOOGLE SHEETS
# ---------------------------------------------------------

# Alcances necesarios para lectura/escritura
SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]

# Archivo de credenciales del service account
SERVICE_ACCOUNT_FILE = "service_account.json"

# Nombre del archivo de Google Sheet
SPREADSHEET_NAME = "base_datos_app"


def _get_client():
    """Autentica y devuelve el cliente de gspread."""
    creds = Credentials.from_service_account_file(
        SERVICE_ACCOUNT_FILE,
        scopes=SCOPES
    )
    client = gspread.authorize(creds)
    return client


def read_sheet(worksheet_name):
    """
    Lee una hoja del Google Sheet y devuelve una lista de dicts.
    Retorna [] si la hoja está vacía o no existe.
    """
    try:
        client = _get_client()
        sheet = client.open(SPREADSHEET_NAME).worksheet(worksheet_name)
        data = sheet.get_all_records()
        return data if data else []
    except Exception as e:
        print("Error leyendo hoja:", worksheet_name, e)
        return []


def append_sheet(worksheet_name, row_dict):
    """
    Inserta una nueva fila en la hoja indicada.
    row_dict debe ser un diccionario con los nombres EXACTOS de las columnas.
    """
    try:
        client = _get_client()
        sheet = client.open(SPREADSHEET_NAME).worksheet(worksheet_name)

        # Obtener encabezados
        headers = sheet.row_values(1)

        # Crear una fila alineada
        row = [row_dict.get(col, "") for col in headers]

        sheet.append_row(row)
        return True

    except Exception as e:
        print("Error agregando fila a hoja:", worksheet_name, e)
        return False


def update_sheet_row(worksheet_name, row_number, row_dict):
    """
    Actualiza una fila existente según row_number (1-based).
    row_dict debe coincidir con los encabezados de la hoja.
    """
    try:
        client = _get_client()
        sheet = client.open(SPREADSHEET_NAME).worksheet(worksheet_name)

        headers = sheet.row_values(1)
        row = [row_dict.get(col, "") for col in headers]

        sheet.update(f"A{row_number}", [row])
        return True

    except Exception as e:
        print("Error actualizando fila:", worksheet_name, e)
        return False


def find_row_by_value(worksheet_name, column_name, value):
    """
    Busca un valor en una columna y devuelve el número de fila (1-based).
    Si no existe, devuelve None.
    """
    try:
        client = _get_client()
        sheet = client.open(SPREADSHEET_NAME).worksheet(worksheet_name)

        headers = sheet.row_values(1)
        if column_name not in headers:
            return None

        col_index = headers.index(column_name) + 1
        column_data = sheet.col_values(col_index)

        for i, cell in enumerate(column_data, start=1):
            if str(cell).strip() == str(value).strip():
                return i

        return None
    except:
        return None
        # ---------------------------------------------------------
# CHECK-IN / CHECK-OUT (tiempos de mantenimiento)
# Usa hoja: chekin_activos
# ---------------------------------------------------------

CHECKIN_SHEET = "chekin_activos"

def add_active_checkin(equipo, descripcion, realizado_por, hora_inicio):
    """
    Crea un check-in activo en la hoja chekin_activos.
    """
    record = {
        "equipo": equipo,
        "descripcion": descripcion,
        "realizado_por": realizado_por,
        "hora_inicio": hora_inicio,
    }

    return append_sheet(CHECKIN_SHEET, record)


def get_active_checkin(equipo):
    """
    Retorna la fila completa y número de fila del check-in activo para un equipo.
    Si no existe, retorna (None, None).
    """
    row_number = find_row_by_value(CHECKIN_SHEET, "equipo", equipo)

    if row_number is None:
        return None, None

    client = _get_client()
    sheet = client.open(SPREADSHEET_NAME).worksheet(CHECKIN_SHEET)

    headers = sheet.row_values(1)
    row = sheet.row_values(row_number)

    row_dict = {headers[i]: row[i] for i in range(len(headers))}

    return row_dict, row_number


def delete_row(worksheet_name, row_number):
    """
    Elimina por completo una fila.
    """
    try:
        client = _get_client()
        sheet = client.open(SPREADSHEET_NAME).worksheet(worksheet_name)
        sheet.delete_rows(row_number)
        return True
    except Exception as e:
        print("Error eliminando fila:", e)
        return False


def close_checkin(equipo, hora_fin, tiempo_hrs):
    """
    Cierra un check-in activo:
    - Recupera el registro en chekin_activos
    - Lo elimina de chekin_activos
    - Retorna la información para que la TAB lo guarde en mantenimientos
    """
    row_dict, row_number = get_active_checkin(equipo)

    if not row_dict:
        return None  # No existe check-in

    # Eliminar de la tabla de activos
    delete_row(CHECKIN_SHEET, row_number)

    # Retornar datos completos para almacenarlos en mantenimientos
    final_data = {
        "equipo": row_dict["equipo"],
        "descripcion": row_dict["descripcion"],
        "realizado_por": row_dict["realizado_por"],
        "hora_inicio": row_dict["hora_inicio"],
        "hora_fin": hora_fin,
        "tiempo_hrs": tiempo_hrs
    }

    return final_data



import gspread
from google.oauth2.service_account import Credentials

# -----------------------------------------------------------
# CONFIGURACIÓN DE GOOGLE SHEETS
# -----------------------------------------------------------
def get_client():
    scopes = [
        "https://www.googleapis.com/auth/spreadsheets",
        "https://www.googleapis.com/auth/drive"
    ]
    credentials = Credentials.from_service_account_file("service_account.json", scopes=scopes)
    return gspread.authorize(credentials)

# -----------------------------------------------------------
# LEER UNA HOJA DE CÁLCULO
# -----------------------------------------------------------
def read_sheet(sheet_name, worksheet_name):
    client = get_client()
    sheet = client.open(sheet_name)
    worksheet = sheet.worksheet(worksheet_name)
    return worksheet.get_all_records()

# -----------------------------------------------------------
# AGREGAR DATOS A UNA HOJA
# -----------------------------------------------------------
def append_sheet(sheet_name, worksheet_name, values):
    client = get_client()
    sheet = client.open(sheet_name)
    worksheet = sheet.worksheet(worksheet_name)
    worksheet.append_row(values)

# -----------------------------------------------------------
# SUBIR ARCHIVO A GOOGLE DRIVE
# -----------------------------------------------------------
def upload_file_to_drive(file, drive_folder_id):
    from googleapiclient.discovery import build
    from googleapiclient.http import MediaIoBaseUpload
    import io

    scopes = ["https://www.googleapis.com/auth/drive"]
    credentials = Credentials.from_service_account_file("service_account.json", scopes=scopes)
    service = build("drive", "v3", credentials=credentials)

    file_metadata = {
        "name": file.name,
        "parents": [drive_folder_id],
    }

    media = MediaIoBaseUpload(
        io.BytesIO(file.getvalue()),
        mimetype=file.type,
        resumable=True
    )

    uploaded_file = service.files().create(
        body=file_metadata,
        media_body=media,
        fields="id"
    ).execute()

    return uploaded_file.get("id")

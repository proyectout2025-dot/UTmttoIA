# utils.py
import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseUpload
from datetime import datetime
import io

# ---------- CONFIG ----------
SHEET_URL = st.secrets["sheets"]["sheet_url"]

SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive"
]

EXPECTED_HEADERS = {
    "mantenimientos": [
        "Fecha", "Equipo", "Descripcion", "Realizado_por",
        "estatus", "tiempo_hrs", "hora_inicio", "hora_fin", "Tipo"
    ],
    "checkin_activos": [
        "Fecha", "Equipo", "Descripcion", "Realizado_por", "hora_inicio"
    ],
    "refacciones": [
        "Numero_parte", "Parte_cliente", "Descripcion", "Ubicacion", "Existencias", "ArchivoID"
    ],
    "config": ["Parametro", "Valor"]
}

# ---------- AUTH ----------
def _get_credentials(scopes):
    try:
        creds_dict = st.secrets["gcp_service_account"]
        return Credentials.from_service_account_info(creds_dict, scopes=scopes)
    except Exception as e:
        st.error(f"❌ Error cargando credenciales: {e}")
        return None

def get_gs_client():
    creds = _get_credentials(SCOPES)
    if not creds:
        return None
    try:
        return gspread.authorize(creds)
    except Exception as e:
        st.error(f"❌ Error autorizando Google Sheets: {e}")
        return None

def get_drive_service():
    creds = _get_credentials(["https://www.googleapis.com/auth/drive"])
    if not creds:
        return None
    try:
        return build("drive", "v3", credentials=creds)
    except Exception as e:
        st.error(f"❌ Error creando servicio Drive: {e}")
        return None

# ---------- AUTO-FIX HEADERS ----------
def _ensure_sheet_headers(sh, sheet_name, expected):
    """
    Asegura que la hoja exista y tenga exactamente los encabezados esperados en la fila 1.
    No borra datos, solo reemplaza/crea fila 1.
    """
    try:
        try:
            ws = sh.worksheet(sheet_name)
        except Exception:
            # crear hoja si no existe
            sh.add_worksheet(title=sheet_name, rows=1000, cols=20)
            ws = sh.worksheet(sheet_name)

        current = ws.row_values(1)
        current_clean = [c.strip() for c in current] if current else []
        if current_clean != expected:
            # reemplazar la fila 1 por los headers esperados (safe)
            try:
                ws.delete_rows(1)
            except Exception:
                pass
            ws.insert_row(expected, index=1)
    except Exception as e:
        st.warning(f"Auto-fix: no se pudo asegurar encabezados de '{sheet_name}': {e}")

def autofix_all_headers():
    client = get_gs_client()
    if not client:
        return False
    try:
        sh = client.open_by_url(SHEET_URL)
        for name, headers in EXPECTED_HEADERS.items():
            _ensure_sheet_headers(sh, name, headers)
        return True
    except Exception as e:
        st.error(f"❌ Error en autofix_all_headers: {e}")
        return False

# ---------- SHEETS HELPERS ----------
def read_sheet(worksheet_name):
    # Auto-fix antes de leer para garantizar encabezados correctos
    autofix_all_headers()
    try:
        client = get_gs_client()
        sh = client.open_by_url(SHEET_URL)
        ws = sh.worksheet(worksheet_name)
        return ws.get_all_records()
    except Exception as e:
        st.error(f"❌ Error leyendo {worksheet_name}: {e}")
        return []

def append_row(worksheet_name, row_list):
    autofix_all_headers()
    try:
        client = get_gs_client()
        sh = client.open_by_url(SHEET_URL)
        ws = sh.worksheet(worksheet_name)
        ws.append_row(row_list, value_input_option="USER_ENTERED")
        return True
    except Exception as e:
        st.error(f"❌ Error guardando en {worksheet_name}: {e}")
        return False

def append_sheet(worksheet_name, row):
    """
    Compat wrapper: acepta dict o list.
    Si dict -> alinea con headers actuales; si list -> pasa directo.
    """
    try:
        if isinstance(row, dict):
            client = get_gs_client()
            sh = client.open_by_url(SHEET_URL)
            ws = sh.worksheet(worksheet_name)
            headers = ws.row_values(1)
            ordered = [row.get(h, "") for h in headers]
            return append_row(worksheet_name, ordered)
        else:
            return append_row(worksheet_name, row)
    except Exception as e:
        st.error(f"❌ Error append_sheet wrapper: {e}")
        return False

# ---------- CHECK-IN / CHECK-OUT ----------
def get_active_checkins():
    return read_sheet("checkin_activos") or []

def add_active_checkin(equipo, descripcion, realizado_por):
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    row = [datetime.now().strftime("%Y-%m-%d"), equipo, descripcion, realizado_por, now]
    return append_row("checkin_activos", row)

def finalize_active_checkin_by_rownum(row_number, estatus="Completado", descripcion_override=""):
    """
    Finaliza el checkin en la fila 'row_number' (1-based).
    Calcula tiempo, guarda en 'mantenimientos' y borra la fila activa.
    """
    try:
        client = get_gs_client()
        sh = client.open_by_url(SHEET_URL)
        ws = sh.worksheet("checkin_activos")
        all_vals = ws.get_all_values()
        if row_number < 2 or row_number > len(all_vals):
            st.error("Fila inválida para finalizar check-in.")
            return False

        headers = all_vals[0]
        row_vals = all_vals[row_number - 1]
        entry = {headers[i]: row_vals[i] if i < len(row_vals) else "" for i in range(len(headers))}

        hora_inicio_str = entry.get("hora_inicio", "")
        parsed = None
        for fmt in ("%Y-%m-%d %H:%M:%S", "%H:%M:%S", "%Y-%m-%dT%H:%M:%S"):
            try:
                parsed = datetime.strptime(hora_inicio_str, fmt)
                break
            except Exception:
                continue
        if parsed is None:
            parsed = datetime.now()

        hora_fin_dt = datetime.now()
        horas = round((hora_fin_dt - parsed).total_seconds() / 3600, 2)

        final_row = [
            parsed.strftime("%Y-%m-%d"),
            entry.get("Equipo", ""),
            descripcion_override if descripcion_override else entry.get("Descripcion", ""),
            entry.get("Realizado_por", ""),
            estatus,
            horas,
            hora_inicio_str,
            hora_fin_dt.strftime("%Y-%m-%d %H:%M:%S"),
            ""  # Tipo optional
        ]

        ok = append_row("mantenimientos", final_row)
        if not ok:
            return False

        # delete that checkin row
        ws.delete_rows(row_number)
        return True
    except Exception as e:
        st.error(f"❌ Error finalizando check-in: {e}")
        return False

# ---------- DRIVE UPLOAD ----------
def upload_file_to_drive(file, folder_name="Refacciones"):
    try:
        service = get_drive_service()
        if not service:
            return None

        query = f"name='{folder_name}' and mimeType='application/vnd.google-apps.folder'"
        results = service.files().list(q=query, spaces="drive", fields="files(id, name)").execute()
        items = results.get("files", [])

        if not items:
            folder = service.files().create(body={"name": folder_name, "mimeType": "application/vnd.google-apps.folder"}, fields="id").execute()
            folder_id = folder["id"]
        else:
            folder_id = items[0]["id"]

        file.seek(0)
        media = MediaIoBaseUpload(io.BytesIO(file.read()), mimetype=file.type)
        metadata = {"name": file.name, "parents": [folder_id]}
        uploaded = service.files().create(body=metadata, media_body=media, fields="id").execute()
        return uploaded.get("id")
    except Exception as e:
        st.error(f"❌ Error subiendo archivo a Drive: {e}")
        return None

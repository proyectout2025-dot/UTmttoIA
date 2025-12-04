import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
from datetime import datetime

# =====================================
#   AUTENTICACIÓN GOOGLE
# =====================================
def get_gs_client():
    try:
        creds_dict = st.secrets["gcp_service_account"]
        scopes = [
            "https://www.googleapis.com/auth/spreadsheets",
            "https://www.googleapis.com/auth/drive"
        ]
        creds = Credentials.from_service_account_info(creds_dict, scopes=scopes)
        client = gspread.authorize(creds)
        return client
    except Exception as e:
        st.error(f"❌ Error autenticando Google: {e}")
        return None


# URL del Sheet
SHEET_URL = st.secrets["sheets"]["sheet_url"]

# =====================================
#         LECTURA SEGURA
# =====================================
@st.cache_data(ttl=10)
def read_sheet(sheet):
    try:
        client = get_gs_client()
        sh = client.open_by_url(SHEET_URL)
        ws = sh.worksheet(sheet)
        return ws.get_all_records()
    except Exception as e:
        st.error(f"❌ Error leyendo Google Sheets ({sheet}): {e}")
        return []


# =====================================
#          AGREGAR FILA
# =====================================
def append_row(sheet, row):
    try:
        client = get_gs_client()
        sh = client.open_by_url(SHEET_URL)
        ws = sh.worksheet(sheet)
        ws.append_row(row)
        read_sheet.clear()
        return True
    except Exception as e:
        st.error(f"❌ Error guardando en Google Sheets ({sheet}): {e}")
        return False


# =====================================
# ENCABEZADOS ESPERADOS (YA NO FALLA)
# =====================================
EXPECTED_HEADERS = {
    "checkin_activos": ["Equipo", "Realizado_por", "hora_inicio", "Tipo"],
    "mantenimientos": [
        "Fecha", "Equipo", "Descripcion", "Realizado_por",
        "estatus", "tiempo_hrs", "hora_inicio", "hora_fin", "Tipo"
    ]
}

def ensure_headers(sheet):
    """Crea encabezados si no existen."""
    try:
        client = get_gs_client()
        sh = client.open_by_url(SHEET_URL)
        ws = sh.worksheet(sheet)

        expected = EXPECTED_HEADERS.get(sheet, [])
        if not expected:
            return

        current = ws.row_values(1)
        if current != expected:
            ws.update("A1:Z1", [expected])

    except Exception as e:
        st.warning(f"⚠ No se pudo asegurar encabezados en '{sheet}': {e}")


# =====================================
#        CHECK-IN / CHECK-OUT
# =====================================
def get_active_checkins():
    ensure_headers("checkin_activos")
    return read_sheet("checkin_activos")


def add_active_checkin(equipo, realizado_por, tipo):
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    row = [equipo, realizado_por, now, tipo]
    append_row("checkin_activos", row)


def finalize_checkin(entry):
    """
    Recibe un dict completo del check-in y lo pasa a mantenimientos.
    """
    try:
        equipo = entry["Equipo"]
        realizado = entry["Realizado_por"]
        inicio_str = entry["hora_inicio"]
        tipo = entry.get("Tipo", "")

        inicio_dt = datetime.strptime(inicio_str, "%Y-%m-%d %H:%M:%S")
        fin_dt = datetime.now()
        horas = round((fin_dt - inicio_dt).total_seconds() / 3600, 2)

        row = [
            inicio_dt.strftime("%Y-%m-%d"),  # Fecha
            equipo,
            tipo,  # Descripcion
            realizado,
            "Completado",
            horas,
            inicio_str,
            fin_dt.strftime("%Y-%m-%d %H:%M:%S"),
            tipo
        ]

        append_row("mantenimientos", row)

        # borrar fila del check-in
        delete_active_checkin(entry)

        return True

    except Exception as e:
        st.error(f"❌ Error finalizando check-out: {e}")
        return False


def delete_active_checkin(entry):
    """Elimina la fila exacta del check-in."""
    try:
        client = get_gs_client()
        sh = client.open_by_url(SHEET_URL)
        ws = sh.worksheet("checkin_activos")

        all_rows = ws.get_all_records()
        idx = all_rows.index(entry) + 2  # fila real (saltando encabezado)
        ws.delete_rows(idx)
        read_sheet.clear()
    except:
        pass

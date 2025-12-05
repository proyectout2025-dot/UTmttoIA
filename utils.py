# utils.py
import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
from datetime import datetime

# --------------------------
# Autenticación Google
# --------------------------
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

SHEET_URL = st.secrets["sheets"]["sheet_url"]

# --------------------------
# read_sheet (cacheado)
# --------------------------
@st.cache_data(ttl=60)
def read_sheet(sheet_name):
    """
    Lee el sheet indicado (cached). Devuelve lista de dicts.
    TTL=60s para mitigar quota 429.
    """
    try:
        client = get_gs_client()
        sh = client.open_by_url(SHEET_URL)
        ws = sh.worksheet(sheet_name)
        return ws.get_all_records()
    except Exception as e:
        st.error(f"❌ Error leyendo Google Sheets ({sheet_name}): {e}")
        return []

# --------------------------
# append_row
# --------------------------
def append_row(sheet_name, row):
    """
    Agrega una fila y limpia cache.
    """
    try:
        client = get_gs_client()
        sh = client.open_by_url(SHEET_URL)
        ws = sh.worksheet(sheet_name)
        ws.append_row(row)
        read_sheet.clear()
        return True
    except Exception as e:
        st.error(f"❌ Error guardando en Google Sheets ({sheet_name}): {e}")
        return False

# --------------------------
# ensure_headers (solo write)
# --------------------------
def ensure_headers(sheet_name, expected_headers):
    """
    Asegura encabezados escribiendo directamente la fila 1.
    Evita lecturas que generan 429.
    """
    try:
        client = get_gs_client()
        sh = client.open_by_url(SHEET_URL)
        try:
            ws = sh.worksheet(sheet_name)
        except Exception:
            # crear hoja si no existe
            sh.add_worksheet(title=sheet_name, rows=1000, cols=20)
            ws = sh.worksheet(sheet_name)
        # Escribimos directamente (no leer)
        ws.update("A1", [expected_headers])
        read_sheet.clear()
    except Exception as e:
        st.warning(f"⚠ No se pudieron asegurar encabezados en '{sheet_name}': {e}")

# --------------------------
# Check-in helpers
# --------------------------
def get_active_checkins():
    """Regresa lista de check-ins (cacheada por read_sheet)."""
    return read_sheet("checkin_activos") or []

def start_checkin(equipo, tecnico, tipo=""):
    """Inicia checkin: Equipo, Realizado_por, hora_inicio, Tipo"""
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    row = [equipo, tecnico, now, tipo]
    return append_row("checkin_activos", row)

def finalize_checkin_by_equipo(equipo):
    """
    Finaliza el checkin del equipo usando búsqueda directa en sheet.
    - Busca todas las celdas que contienen el nombre del equipo,
    - Selecciona la fila válida con la hora más reciente (si hay varias),
    - Calcula horas y guarda en 'mantenimientos' respetando tus encabezados.
    """
    try:
        client = get_gs_client()
        sh = client.open_by_url(SHEET_URL)
        ws = sh.worksheet("checkin_activos")

        # Encontrar todas las celdas donde aparece el equipo en la columna Equipo
        cells = ws.findall(equipo)  # retorna celdas en todo el sheet
        if not cells:
            st.error("No se encontró un check-in activo para ese equipo.")
            return False

        # Filtrar por filas válidas y leer hora_inicio de cada una
        best_row = None
        best_inicio_dt = None
        headers = ws.row_values(1)

        for cell in cells:
            rownum = cell.row
            # evitar la fila de encabezados
            if rownum == 1:
                continue
            row_vals = ws.row_values(rownum)
            # construir entry dict seguro
            entry = {headers[i]: row_vals[i] if i < len(row_vals) else "" for i in range(len(headers))}
            hora_inicio = entry.get("hora_inicio") or entry.get("Hora_inicio") or entry.get("horaInicio") or ""
            try:
                inicio_dt = datetime.strptime(hora_inicio, "%Y-%m-%d %H:%M:%S")
            except:
                inicio_dt = None
            # preferimos la fila con hora_inicio más reciente (mayor)
            if inicio_dt:
                if best_inicio_dt is None or inicio_dt > best_inicio_dt:
                    best_inicio_dt = inicio_dt
                    best_row = (rownum, entry)
            else:
                # si no hay hora válida, aún podemos marcarla como candidata si no hay otra
                if best_row is None:
                    best_row = (rownum, entry)

        if best_row is None:
            st.error("No se encontró un check-in válido para finalizar.")
            return False

        rownum_real, entry = best_row
        equipo = entry.get("Equipo", "")
        tecnico = entry.get("Realizado_por", "")
        tipo = entry.get("Tipo", "")
        hora_inicio_str = entry.get("hora_inicio", "")

        # convertir hora inicio
        try:
            inicio_dt = datetime.strptime(hora_inicio_str, "%Y-%m-%d %H:%M:%S")
        except:
            inicio_dt = datetime.now()

        fin_dt = datetime.now()
        horas = round((fin_dt - inicio_dt).total_seconds() / 3600, 2)

        # Construir descripción: si la hoja checkin_activos no tiene una descripción, usamos Tipo dentro de la Descripcion.
        descripcion_text = f"Check-out automático [Tipo:{tipo}]" if tipo else "Check-out automático"

        # Guardar fila en 'mantenimientos' con los encabezados exactos que confirmaste:
        # Fecha,Equipo,Descripcion,Realizado_por,estatus,tiempo_hrs,hora_inicio,hora_fin
        row_to_save = [
            inicio_dt.strftime("%Y-%m-%d"),
            equipo,
            descripcion_text,
            tecnico,
            "Completado",
            horas,
            hora_inicio_str,
            fin_dt.strftime("%Y-%m-%d %H:%M:%S")
        ]

        append_row("mantenimientos", row_to_save)

        # Borrar la fila de checkin_activos
        ws.delete_rows(rownum_real)
        read_sheet.clear()
        return True

    except Exception as e:
        st.error(f"❌ Error finalizando check-in: {e}")
        return False

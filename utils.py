# --- Añadir al final de utils.py ---

import time
import uuid
from datetime import datetime, timezone

# Utility helper: open spreadsheet and worksheet
def _open_worksheet(sheet_name):
    """
    Retorna un objeto Worksheet de gspread para la hoja `sheet_name`.
    Lanza excepción si no se puede abrir.
    """
    creds = Credentials.from_service_account_info(
        st.secrets["gcp_service_account"],
        scopes=[
            "https://www.googleapis.com/auth/spreadsheets",
            "https://www.googleapis.com/auth/drive",
        ],
    )
    client = gspread.authorize(creds)
    sheet_url = st.secrets["sheets"]["sheet_url"]
    ss = client.open_by_url(sheet_url)
    return ss.worksheet(sheet_name)


# ---------- CHECK-IN ACTIVOS ----------
def add_active_checkin(record: dict):
    """
    Inserta un registro en la hoja `checkin_activos`.
    record debe contener: id, equipo, descripcion, realizado_por, hora_inicio, estatus
    """
    ws = _open_worksheet("checkin_activos")
    # Convert dict to row in a fixed order
    row = [
        record.get("id"),
        record.get("equipo", ""),
        record.get("descripcion", ""),
        record.get("realizado_por", ""),
        record.get("hora_inicio", ""),
        record.get("estatus", "EN PROCESO"),
    ]
    ws.append_row(row, value_input_option="USER_ENTERED")
    return True


def get_active_checkins():
    """
    Retorna lista de dicts con los checkins activos.
    """
    try:
        ws = _open_worksheet("checkin_activos")
        rows = ws.get_all_records()
        return rows  # lista de diccionarios
    except Exception:
        return []


def remove_active_checkin(checkin_id: str):
    """
    Elimina el registro en checkin_activos cuyo id coincida con checkin_id.
    Retorna True si borró algo.
    """
    ws = _open_worksheet("checkin_activos")
    records = ws.get_all_records()
    for i, r in enumerate(records, start=2):  # get_all_records considera encabezado en fila 1
        if str(r.get("id")) == str(checkin_id):
            ws.delete_rows(i)
            return True
    return False


def finalize_active_checkin(checkin_id: str):
    """
    Recupera el registro activo por id, calcula hora_fin y duración en horas,
    elimina el activo y devuelve una tupla (final_row_dict, removed_bool).
    final_row_dict es la fila que debe guardarse en la hoja 'mantenimientos'.
    """
    ws = _open_worksheet("checkin_activos")
    records = ws.get_all_records()
    for i, r in enumerate(records, start=2):
        if str(r.get("id")) == str(checkin_id):
            # r contiene: id, equipo, descripcion, realizado_por, hora_inicio, estatus
            hora_inicio_str = r.get("hora_inicio")
            try:
                # parse hora_inicio (esperamos ISO string)
                hora_inicio = datetime.fromisoformat(hora_inicio_str)
            except Exception:
                # Fallback: tratar como timestamp en segundos
                try:
                    hora_inicio = datetime.fromtimestamp(float(hora_inicio_str), tz=timezone.utc)
                except Exception:
                    hora_inicio = datetime.now(timezone.utc)

            hora_fin = datetime.now(timezone.utc)
            delta = hora_fin - hora_inicio
            horas = delta.total_seconds() / 3600.0

            final_row = {
                "fecha": hora_inicio.date().isoformat(),
                "equipo": r.get("equipo", ""),
                "descripcion": r.get("descripcion", ""),
                "realizado_por": r.get("realizado_por", ""),
                "estatus": "Completado",
                "tiempo_hrs": round(horas, 2),
                "hora_inicio": hora_inicio.isoformat(),
                "hora_fin": hora_fin.isoformat()
            }

            # eliminar fila activa
            ws.delete_rows(i)
            return final_row, True

    return None, False

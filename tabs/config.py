# ===========================================
# /tabs/config.py — FINAL (con AutoFix)
# ===========================================

import streamlit as st
from utils import get_gs_client, SHEET_URL


def fix_sheet(sheet_name, headers):
    try:
        client = get_gs_client()
        sh = client.open_by_url(SHEET_URL)
        ws = sh.worksheet(sheet_name)
        ws.update("1:1", [headers])
        st.success(f"✔ Hoja '{sheet_name}' reparada.")
    except Exception as e:
        st.error(f"❌ Error reparando hoja '{sheet_name}': {e}")


def show_config():
    st.header("⚙️ Configuración y AutoFix")

    st.write("Usa esta sección para corregir automáticamente las hojas del documento.")

    if st.button("🔧 Reparar hoja: mantenimientos"):
        fix_sheet("mantenimientos", [
            "Fecha", "Equipo", "Descripcion", "Realizado_por",
            "estatus", "tiempo_hrs", "hora_inicio", "hora_fin"
        ])

    if st.button("🔧 Reparar hoja: refacciones"):
        fix_sheet("refacciones", [
            "Numero_parte", "Parte_cliente", "Descripcion",
            "Ubicacion", "Existencias"
        ])

    if st.button("🔧 Reparar hoja: checkin_activos"):
        fix_sheet("checkin_activos", [
            "equipo", "realizado_por", "hora_inicio"
        ])

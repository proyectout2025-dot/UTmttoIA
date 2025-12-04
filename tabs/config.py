import streamlit as st
import pandas as pd
from utils import get_gs_client, SHEET_URL

# ======================================
# ENCABEZADOS ESPERADOS POR EL SISTEMA
# ======================================

EXPECTED_HEADERS = {
    "mantenimientos": [
        "Fecha", "Equipo", "Descripcion", "Realizado_por",
        "estatus", "tiempo_hrs", "hora_inicio", "hora_fin"
    ],

    "checkin_activos": [
        "Fecha", "Equipo", "Descripcion", "Realizado_por", "hora_inicio"
    ],

    "refacciones": [
        "Codigo", "Nombre", "Descripcion", "Ubicacion", "Stock"
    ]
}


# ======================================
# FUNCIÓN AUTO-FIX HEADERS
# ======================================

def autofix_headers(sheet_name):

    st.subheader(f"🔧 Reparando encabezados: `{sheet_name}`")

    try:
        client = get_gs_client()
        sh = client.open_by_url(SHEET_URL)
        ws = sh.worksheet(sheet_name)

        existing = ws.row_values(1)
        expected = EXPECTED_HEADERS[sheet_name]

        # Normalizar actuales
        cleaned = [h.strip() for h in existing]

        # Si ya coinciden:
        if cleaned == expected:
            st.success("✔ Encabezados correctos.")
            return True

        # Si faltan columnas:
        if len(cleaned) < len(expected):
            cleaned += [""] * (len(expected) - len(cleaned))

        # Reemplazar con los correctos
        ws.update("1:1", [expected])

        st.success(f"✔ Encabezados reparados correctamente en `{sheet_name}`")
        return True

    except Exception as e:
        st.error(f"❌ Error corrigiendo encabezados: {e}")
        return False



# ======================================
# INTERFAZ DE CONFIGURACIÓN
# ======================================

def show_config():

    st.title("⚙️ Configuración del Sistema")
    st.write("Utilidad para reparar encabezados y validar conexión con Google Sheets.")

    st.subheader("📌 Hojas disponibles")
    st.table(pd.DataFrame({
        "Hoja": list(EXPECTED_HEADERS.keys()),
        "Columnas esperadas": [", ".join(EXPECTED_HEADERS[x]) for x in EXPECTED_HEADERS]
    }))

    st.write("---")
    st.subheader("🛠 Reparar encabezados automáticamente")

    # Selección
    sheet_sel = st.selectbox(
        "Selecciona la hoja que deseas reparar:",
        list(EXPECTED_HEADERS.keys())
    )

    if st.button("🔧 Aplicar Auto-Fix"):
        autofix_headers(sheet_sel)

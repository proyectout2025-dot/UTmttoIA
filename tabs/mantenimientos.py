import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
import pandas as pd
from datetime import datetime

# ======================================================
#                AUTENTICACIÓN GOOGLE
# ======================================================

def get_gs_client():
    """Autentica Google Sheets."""
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


# ======================================================
#                FUNCIONES DE GOOGLE SHEETS
# ======================================================

def read_sheet(worksheet_name):
    """Lee una hoja completa como lista de dicts."""
    try:
        client = get_gs_client()
        sh = client.open_by_url(SHEET_URL)
        ws = sh.worksheet(worksheet_name)
        return ws.get_all_records()
    except Exception as e:
        st.error(f"❌ Error leyendo Google Sheets ({worksheet_name}): {e}")
        return []


def append_row(worksheet_name, row):
    """Agrega una fila a una hoja."""
    try:
        client = get_gs_client()
        sh = client.open_by_url(SHEET_URL)
        ws = sh.worksheet(worksheet_name)
        ws.append_row(row)
        return True
    except Exception as e:
        st.error(f"❌ Error guardando en Google Sheets ({worksheet_name}): {e}")
        return False


# ==========================
#   CHECK-IN / CHECK-OUT
# ==========================

# Buscar check-in activo de un equipo
if activos:
    activo = next((a for a in activos if a["Equipo"] == equipo_sel), None)
else:
    activo = None

# Mostrar estado
if activo:
    st.warning(f"🔴 Este equipo ya tiene un CHECK-IN activo desde: {activo['hora_inicio']}")
else:
    st.success("🟢 No hay check-in activo para este equipo.")

# BOTÓN CHECK-IN
if not activo:
    if st.button("Iniciar Check-in"):
        add_active_checkin(
            equipo_sel,
            descripcion,
            realizado_por
        )
        st.toast("Check-in iniciado")
        st.rerun()

# BOTÓN CHECK-OUT
if activo:
    if st.button("Finalizar Check-out"):
        # OBTENER NÚMERO DE FILA
        idx = activos.index(activo)
        fila = idx + 2  # +2 = cuenta encabezado + index base 0

        ok = finalize_active_checkin_by_rownum(
            fila,
            estatus_sel,
            descripcion
        )

        if ok:
            st.success("✔ Check-out completado y guardado en 'mantenimientos'")
        else:
            st.error("Error finalizando check-out")

        st.rerun()

# ======================================================
#                INTERFAZ PRINCIPAL
# ======================================================

def show_mantenimientos():

    st.header("🛠 Registro de Mantenimientos")

    st.subheader("⏱ Tiempo (Check-in / Check-out)")
    equipos = ["Torno", "Fresadora", "Router CNC", "Soldadora", "Impresora 3D"]

    equipo_sel = st.selectbox("Equipo", equipos)
    realizado_por = st.text_input("Realizado por")

    activos = get_active_checkins()
    activo = next((a for a in activos if a["equipo"] == equipo_sel), None)

    col1, col2 = st.columns(2)

    if activo:
        # Ya tiene check-in
        col1.success(f"⚡ Check-in iniciado: {activo['hora_inicio']}")

        if col2.button("⛔ Finalizar (Check-out)"):
            result = finalize_active_checkin(equipo_sel)
            if result:
                horas, persona, hora_ini, hora_fin = result

                append_row("mantenimientos", [
                    datetime.now().strftime("%Y-%m-%d"),
                    equipo_sel,
                    "Mantenimiento automático por Checkout",
                    persona,
                    "completado",
                    horas,
                    hora_ini,
                    hora_fin
                ])
                st.success("✔ Tiempo registrado correctamente.")
                st.rerun()
    else:
        # No tiene check-in
        if col1.button("▶ Iniciar Check-in"):
            if not realizado_por:
                st.warning("⚠ Debes capturar quién realiza el mantenimiento.")
            else:
                add_active_checkin(equipo_sel, realizado_por)
                st.success("⏱ Check-in iniciado.")
                st.rerun()

    st.divider()

    # ======================================================
    #                REGISTRO MANUAL
    # ======================================================

    st.subheader("📝 Registro manual")

    fecha = st.date_input("Fecha")
    descripcion = st.text_area("Descripción")
    status = st.selectbox("Estatus", ["pendiente", "en proceso", "completado"])
    horas = st.number_input("Horas trabajadas", 0.0, 100.0, 0.0)
    hora_ini = st.text_input("Hora inicio (YYYY-mm-dd HH:MM:SS)")
    hora_fin = st.text_input("Hora fin   (YYYY-mm-dd HH:MM:SS)")

    if st.button("💾 Guardar manual"):
        append_row("mantenimientos", [
            str(fecha),
            equipo_sel,
            descripcion,
            realizado_por,
            status,
            horas,
            hora_ini,
            hora_fin
        ])
        st.success("✔ Mantenimiento guardado correctamente.")

    st.divider()

    # ======================================================
    #                TABLE + GRÁFICAS
    # ======================================================

    st.subheader("📊 Reportes de Mantenimientos")

    data = read_sheet("mantenimientos")
    if not data:
        st.info("No hay datos aún")
        return

    df = pd.DataFrame(data)
    st.dataframe(df)

    try:
        horas_equipo = df.groupby("Equipo")["tiempo_hrs"].sum()
        st.bar_chart(horas_equipo)
    except:
        st.warning("⚠ No se pudo generar gráfica (columnas incorrectas).")

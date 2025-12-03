import streamlit as st
import pandas as pd
from datetime import datetime, timezone
import uuid

# IMPORTS from your utils (asegúrate de tener las funciones añadidas)
from utils import read_sheet, append_sheet
from utils import add_active_checkin, get_active_checkins, finalize_active_checkin

def _now_iso():
    return datetime.now(timezone.utc).isoformat()

def show_mantenimientos():
    st.header("🛠 Registro y Check-In / Check-Out de Mantenimientos")

    # -------------------------
    # MOSTRAR CHECK-INS ACTIVOS
    # -------------------------
    st.subheader("🔵 Check-Ins activos")
    try:
        activos = get_active_checkins() or []
    except Exception as e:
        activos = []
        st.error(f"Error leyendo checkins activos: {e}")

    if activos:
        df_activos = pd.DataFrame(activos)
        st.dataframe(df_activos)
    else:
        st.info("No hay mantenimientos en curso.")

    st.markdown("---")

    # -------------------------
    # FORMULARIO DE CHECK-IN
    # -------------------------
    st.subheader("📝 Iniciar mantenimiento (Check-In)")

    # Campos de check-in
    with st.form("form_checkin"):
        equipo_ci = st.text_input("Equipo / Máquina", key="ci_equipo")
        descripcion_ci = st.text_area("Descripción breve", key="ci_descripcion")
        realizado_por_ci = st.text_input("Realizado por", key="ci_realizado_por")

        submitted_ci = st.form_submit_button("Iniciar (Check-In)")

    if submitted_ci:
        # Validaciones básicas: no permitir check-in si ya existe un registro en curso por mismo técnico y equipo
        conflict = False
        for r in activos:
            if (r.get("equipo") == equipo_ci and r.get("realizado_por") == realizado_por_ci):
                conflict = True
                break
        if conflict:
            st.warning("Ya hay un mantenimiento en curso para ese equipo/usuario. Finaliza el anterior o usa otro equipo.")
        else:
            checkin_id = str(uuid.uuid4())
            record = {
                "id": checkin_id,
                "equipo": equipo_ci,
                "descripcion": descripcion_ci,
                "realizado_por": realizado_por_ci,
                "hora_inicio": _now_iso(),
                "estatus": "EN PROCESO"
            }
            try:
                add_active_checkin(record)
                st.success("Check-In registrado ✔")
                st.experimental_rerun()
            except Exception as e:
                st.error(f"Error al registrar Check-In: {e}")

    st.markdown("---")

    # -------------------------
    # LISTADO PARA CHECK-OUT
    # -------------------------
    st.subheader("🔴 Finalizar mantenimiento (Check-Out)")

    # Mostrar select con activos para finalizar
    activos = get_active_checkins() or []
    if activos:
        # prepare choices: "id - equipo - usuario - inicio"
        choices = [
            f"{r.get('id')} | {r.get('equipo')} | {r.get('realizado_por')} | {r.get('hora_inicio')}"
            for r in activos
        ]
        sel = st.selectbox("Selecciona mantenimiento en curso para finalizar", ["-- seleccionar --"] + choices, key="select_checkout")
        if sel and sel != "-- seleccionar --":
            chosen_id = sel.split("|")[0].strip()
            if st.button("Finalizar (Check-Out)"):
                final_row, removed = finalize_active_checkin(chosen_id)
                if removed and final_row:
                    # Convert final_row dict to list in correct order for 'mantenimientos' sheet
                    row_list = [
                        final_row.get("fecha"),
                        final_row.get("equipo"),
                        final_row.get("descripcion"),
                        final_row.get("realizado_por"),
                        final_row.get("estatus"),
                        final_row.get("tiempo_hrs"),
                        final_row.get("hora_inicio"),
                        final_row.get("hora_fin"),
                    ]
                    try:
                        append_sheet("mantenimientos", row_list)
                        st.success("Check-Out realizado y guardado en historial ✔")
                        st.experimental_rerun()
                    except Exception as e:
                        st.error(f"Error al guardar el registro final en 'mantenimientos': {e}")
                else:
                    st.error("No se encontró el Check-In seleccionado o ya fue finalizado por otro usuario.")
    else:
        st.info("No hay check-ins activos para finalizar.")

    st.markdown("---")

    # -------------------------
    # HISTORIAL DE MANTENIMIENTOS
    # -------------------------
    st.subheader("📚 Historial de mantenimientos")

    try:
        df_hist = read_sheet("mantenimientos")
        if df_hist is None or len(df_hist) == 0:
            st.info("No hay registros en el historial todavía.")
        else:
            # Si viene como lista de dicts o DataFrame, acomodamos columnas
            df = pd.DataFrame(df_hist)
            # Intentar renombrar columnas si son los encabezados por orden
            # Si tu hoja ya contiene encabezados correctos no es necesario
            st.dataframe(df, use_container_width=True)

            # Botón descarga CSV
            csv = df.to_csv(index=False).encode("utf-8")
            st.download_button("Descargar reporte CSV", csv, "reporte_mantenimientos.csv", "text/csv")

    except Exception as e:
        st.error(f"Error cargando historial: {e}")

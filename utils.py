def finalize_active_checkin_by_rownum(row_number, estatus="Completado", descripcion_override=""):
    """Finaliza un check-in con solo 2 lecturas en total (no usa get_all_values)."""
    try:
        client = get_gs_client()
        sh = client.open_by_url(SHEET_URL)
        ws = sh.worksheet("checkin_activos")

        # Leer encabezados (1 lectura)
        headers = ws.row_values(1)

        # Leer solo la fila que necesitamos (1 lectura)
        row_vals = ws.row_values(row_number)

        # Convertir fila a diccionario seguro
        entry = {headers[i]: row_vals[i] if i < len(row_vals) else "" for i in range(len(headers))}

        hora_inicio_str = entry.get("hora_inicio", "")
        try:
            inicio_dt = datetime.strptime(hora_inicio_str, "%Y-%m-%d %H:%M:%S")
        except:
            inicio_dt = datetime.now()

        fin_dt = datetime.now()
        horas = round((fin_dt - inicio_dt).total_seconds() / 3600, 2)

        row_to_save = [
            inicio_dt.strftime("%Y-%m-%d"),
            entry.get("Equipo", ""),
            descripcion_override if descripcion_override else entry.get("Descripcion", ""),
            entry.get("Realizado_por", ""),
            estatus,
            horas,
            hora_inicio_str,
            fin_dt.strftime("%Y-%m-%d %H:%M:%S"),
            ""  # Tipo
        ]

        append_row("mantenimientos", row_to_save)

        # Borrar fila activa (1 escritura)
        ws.delete_rows(row_number)

        return True

    except Exception as e:
        st.error(f"❌ Error finalizando check-out: {e}")
        return False

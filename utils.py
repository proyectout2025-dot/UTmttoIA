def finalize_active_checkin_by_rownum(row_number, estatus="Completado", descripcion_override="Mantenimiento"):
    """
    Finaliza un check-in usando solo 2 lecturas del sheet.
    No usa get_all_records() para evitar error 429.
    """

    try:
        client = get_gs_client()
        sh = client.open_by_url(SHEET_URL)
        ws = sh.worksheet("checkin_activos")

        # Leer encabezados
        headers = ws.row_values(1)

        # Leer solo la fila correspondiente
        row_vals = ws.row_values(row_number)

        entry = {
            headers[i]: row_vals[i] if i < len(row_vals) else ""
            for i in range(len(headers))
        }

        equipo = entry.get("Equipo", "")
        realizado_por = entry.get("Realizado_por", "")
        hora_inicio_str = entry.get("hora_inicio", "")
        tipo = entry.get("Tipo", "General")

        # Convertir hora de inicio
        try:
            inicio_dt = datetime.strptime(hora_inicio_str, "%Y-%m-%d %H:%M:%S")
        except:
            inicio_dt = datetime.now()

        fin_dt = datetime.now()
        horas = round((fin_dt - inicio_dt).total_seconds() / 3600, 2)

        # Fila final que guardaremos en MANTENIMIENTOS
        row_to_save = [
            inicio_dt.strftime("%Y-%m-%d"),     # Fecha
            equipo,
            descripcion_override,               # Descripcion
            realizado_por,
            estatus,
            horas,
            hora_inicio_str,
            fin_dt.strftime("%Y-%m-%d %H:%M:%S"),
            tipo
        ]

        append_row("mantenimientos", row_to_save)

        # Borrar check-in activo
        ws.delete_rows(row_number)
        read_sheet.clear()  # Limpia cache

        return True

    except Exception as e:
        st.error(f"❌ Error finalizando check-out: {e}")
        return False

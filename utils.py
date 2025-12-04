def ensure_headers(sheet_name, expected_headers):
    """
    Garantiza la fila 1 con los encabezados esperados sin hacer lecturas.
    Esto evita errores 429 por exceso de lecturas.
    """
    try:
        client = get_gs_client()
        sh = client.open_by_url(SHEET_URL)
        ws = sh.worksheet(sheet_name)

        # ❗ Escritura directa sin revisar nada (NO consume read requests)
        ws.update("A1:Z1", [expected_headers])

        # Limpiar cache
        read_sheet.clear()

    except Exception as e:
        st.warning(f"⚠ No se pudieron asegurar encabezados en '{sheet_name}': {e}")

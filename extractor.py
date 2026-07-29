import os
import pandas as pd
import requests

# Leemos las credenciales desde los secretos de GitHub
AUTH_TOKEN = os.getenv('BIWENGER_TOKEN')
LEAGUE_ID = os.getenv('BIWENGER_LEAGUE')
USER_ID = os.getenv('BIWENGER_USER')

headers = {
    'authorization': AUTH_TOKEN.strip(),
    'x-league': str(LEAGUE_ID).strip(),
    'x-user': str(USER_ID).strip(),
    'Accept': 'application/json',
    'User-Agent': (
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
    ),
}

# 1. Obtener diccionario global de jugadores
url_players = (
    'https://biwenger.as.com/api/v2/competitions/la-liga/data?lang=es&score=1'
)
res_players = requests.get(url_players, headers=headers)

mapa_jugadores = {}
if res_players.status_code == 200:
    data_players = res_players.json().get('data', {}).get('players', {})
    for p_id, p_data in data_players.items():
        mapa_jugadores[int(p_id)] = {
            'nombre': p_data.get('name', 'Desconocido'),
            'precio': p_data.get('price', 0),
        }

# 2. Extraer historial incluyendo 'auction' y los tipos de operaciones
url_board = f'https://biwenger.as.com/api/v2/league/{LEAGUE_ID.strip()}/board?type=transfer,market,clauseIncrement,clause,auction&limit=100'
response = requests.get(url_board, headers=headers)

movimientos = []

if response.status_code == 200:
    items = response.json().get('data', [])
    for entry in items:
        tipo_evento = str(entry.get('type', 'transfer')).lower()
        
        content = entry.get('content', [])
        if isinstance(content, dict):
            content = [content]
        elif not isinstance(content, list):
            continue

        fecha_ts = entry.get('date')
        fecha_str = (
            pd.to_datetime(fecha_ts, unit='s').strftime('%Y-%m-%d %H:%M')
            if fecha_ts
            else ''
        )

        for item in content:
            if isinstance(item, dict):
                p_obj = item.get('player')
                p_id = (
                    p_obj.get('id')
                    if isinstance(p_obj, dict)
                    else (p_obj if isinstance(p_obj, int) else None)
                )

                info_global = mapa_jugadores.get(p_id, {}) if p_id else {}
                nombre_jugador = (
                    (p_obj.get('name') if isinstance(p_obj, dict) else None)
                    or info_global.get('nombre')
                    or 'Desconocido'
                )
                valor_mercado = (
                    (p_obj.get('price') if isinstance(p_obj, dict) else None)
                    or info_global.get('precio')
                    or item.get('price', 0)
                )

                vendedor = item.get('from', {})
                nombre_vendedor = (
                    vendedor.get('name', 'Mercado')
                    if isinstance(vendedor, dict)
                    else 'Mercado'
                )

                comprador = item.get('to', {}) or item.get('user', {})
                nombre_comprador = (
                    comprador.get('name', 'Mercado')
                    if isinstance(comprador, dict)
                    else 'Mercado'
                )

                precio_fichaje = item.get('amount', item.get('price', 0))

                # Asignación limpia de nombres de tipos en castellano
                tipo_final = 'Compra'
                if 'auction' in tipo_evento:
                    tipo_final = 'Subasta'
                elif 'market' in tipo_evento:
                    tipo_final = 'Compra'
                elif 'transfer' in tipo_evento and nombre_comprador == 'Mercado':
                    tipo_final = 'Venta'
                elif 'clause' in tipo_evento or 'clausulazo' in tipo_evento:
                    tipo_final = 'Clausulazo'
                elif nombre_vendedor != 'Mercado' and nombre_comprador != 'Mercado':
                    if 'clause' in str(item).lower():
                        tipo_final = 'Clausulazo'
                    else:
                        tipo_final = 'Traspaso Rival'

                if precio_fichaje > 0:
                    sobreprecio_euro = (
                        precio_fichaje - valor_mercado
                        if valor_mercado > 0
                        else 0
                    )
                    porcentaje_sobreprecio = (
                        (sobreprecio_euro / valor_mercado) * 100
                        if valor_mercado > 0
                        else 0
                    )

                    movimientos.append({
                        'Fecha': fecha_str,
                        'Jugador': nombre_jugador,
                        'Vendedor': nombre_vendedor,
                        'Comprador': nombre_comprador,
                        'Precio Operación': precio_fichaje,
                        'Valor Mercado': valor_mercado,
                        'Sobreprecio (€)': sobreprecio_euro,
                        'Sobreprecio (%)': round(porcentaje_sobreprecio, 1),
                        'Tipo': tipo_final,
                    })

    if movimientos:
        df = pd.DataFrame(movimientos)
        df.to_csv('historial_biwenger_completo.csv', index=False)
        print('✅ Archivo CSV actualizado correctamente.')

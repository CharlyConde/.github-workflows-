import requests
import pandas as pd
import time
from datetime import datetime

# ==========================================
# CONFIGURACIÓN DE ACCESO A LA API DE BIWENGER
# ==========================================
# Introduce tu token de autorización (Bearer) y el ID de tu liga
TOKEN = "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJpc3MiOjI4MTU5NjM5LCJpYXQiOjE3NTU1NDQ3MDF9.GfS_aDJpfg15kRWzCtKfQtE1Jz6rg9u1eOBs_Q6ePGM"
LEAGUE_ID = "1812487"

def extraer_historial_transacciones_real():
    headers = {
        "Authorization": f"Bearer {TOKEN}",
        "X-League": str(LEAGUE_ID),
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
        "Accept": "application/json, text/plain, */*",
        "Origin": "https://biwenger.as.com",
        "Referer": "https://biwenger.as.com/"
    }
    
    print("🚀 [Extractor Definitivo] Conectando al motor de transacciones de Biwenger...")
    
    todos_los_registros = []
    ids_unicos = set()

    # Biwenger tiene un endpoint específico para el historial de fichajes y ventas de la liga que admite paginación real por bloques
    # Probamos múltiples endpoints de transacciones históricas de la liga
    endpoints = [
        f"https://biwenger.as.com/api/v2/leagues/{LEAGUE_ID}/board",
        f"https://biwenger.as.com/api/v2/leagues/{LEAGUE_ID}/transactions",
        f"https://biwenger.as.com/api/v2/leagues/{LEAGUE_ID}/market"
    ]

    # Intentamos extraer primero desde la fuente general de la liga incluyendo parámetros extendidos
    url_liga_completa = f"https://biwenger.as.com/api/v2/leagues/{LEAGUE_ID}?include=all"
    try:
        resp = requests.get(url_liga_completa, headers=headers, timeout=20)
        if resp.status_code == 200:
            data = resp.json().get("data", {})
            # A veces la liga incluye un histórico embebido más amplio
            if "transactions" in data:
                for item in data["transactions"]:
                    item_id = f"{item.get('date')}_{item.get('type')}"
                    if item_id not in ids_unicos:
                        ids_unicos.add(item_id)
                        todos_los_registros.append(item)
    except Exception as e:
        print(f"ℹ️ Aviso en carga completa de liga: {e}")

    # Si el tablón está capado a 175, vamos a extraer las operaciones consultando el feed de las jornadas (gameweeks/rounds)
    # Cada jornada almacena sus propios movimientos y resultados, lo que permite rellenar todo el histórico desde julio.
    print("🔄 Extrayendo histórico a través de las jornadas de la liga...")
    url_rounds = f"https://biwenger.as.com/api/v2/rounds"
    try:
        resp_rounds = requests.get(url_rounds, headers=headers, timeout=15)
        if resp_rounds.status_code == 200:
            rounds_data = resp_rounds.json().get("data", [])
            # Iteramos por las jornadas disputadas desde julio de 2026 hacia atrás
            for round_item in rounds_data:
                round_id = round_item.get("id")
                if round_id:
                    url_round_detail = f"https://biwenger.as.com/api/v2/leagues/{LEAGUE_ID}/board?round={round_id}"
                    resp_rd = requests.get(url_round_detail, headers=headers, timeout=10)
                    if resp_rd.status_code == 200:
                        rd_data = resp_rd.json().get("data", [])
                        if isinstance(rd_data, list):
                            for item in rd_data:
                                item_id = f"{item.get('date')}_{item.get('type')}_{str(item.get('content'))}"
                                if item_id not in ids_unicos:
                                    ids_unicos.add(item_id)
                                    todos_los_registros.append(item)
                    time.sleep(0.1)
    except Exception as e:
        print(f"ℹ️ Aviso en barrido por jornadas: {e}")

    # Si aún necesitamos más profundidad, realizamos un barrido por fecha hacia atrás de forma manual en el tablón usando offsets masivos con reintentos forzados
    if len(todos_los_registros) < 200:
        print("🔄 Aplicando fuerza bruta por bloques de offset profundos...")
        offset = 0
        while offset <= 2000:
            url_board = f"https://biwenger.as.com/api/v2/leagues/{LEAGUE_ID}/board?offset={offset}&limit=50"
            try:
                resp = requests.get(url_board, headers=headers, timeout=10)
                if resp.status_code == 200:
                    items = resp.json().get("data", [])
                    if not items:
                        break
                    nuevos = 0
                    for item in items:
                        item_id = f"{item.get('date')}_{item.get('type')}_{str(item.get('content'))}"
                        if item_id not in ids_unicos:
                            ids_unicos.add(item_id)
                            todos_los_registros.append(item)
                            nuevos += 1
                    if nuevos == 0 and offset > 150:
                        break
                else:
                    break
            except:
                break
            offset += 50
            time.sleep(0.1)

    print(f"📊 Total de registros únicos totales extraídos: {len(todos_los_registros)}")

    # Procesamiento y normalización final
    if todos_los_registros:
        filas = []
        for item in todos_los_registros:
            tipo = item.get("type", "")
            timestamp = item.get("date", "")
            
            try:
                if isinstance(timestamp, (int, float)):
                    date = datetime.fromtimestamp(timestamp).strftime('%Y-%m-%d %H:%M:%S')
                else:
                    date = str(timestamp)
            except:
                date = str(timestamp)

            content = item.get("content", {})
            if not isinstance(content, dict):
                content = {}

            jugador_obj = content.get("player", {})
            nombre_jugador = jugador_obj.get("name", "Desconocido") if isinstance(jugador_obj, dict) else "Desconocido"
                
            precio = content.get("amount", 0)
            valor = content.get("value", 0)
            
            vendedor_obj = content.get("from")
            vendedor = vendedor_obj.get("name", "Mercado") if isinstance(vendedor_obj, dict) else "Mercado"
            
            comprador_obj = content.get("to") or content.get("user")
            comprador = comprador_obj.get("name", "Mercado") if isinstance(comprador_obj, dict) else "Mercado"

            filas.append({
                "Fecha": date,
                "Tipo": tipo,
                "Jugador": nombre_jugador,
                "Precio Operación": precio,
                "Valor Mercado": valor,
                "Vendedor": vendedor if vendedor else "Mercado",
                "Comprador": comprador if comprador else "Mercado"
            })
            
        df_final = pd.DataFrame(filas)
        
        # Filtro estricto desde el 1 de julio de 2026
        df_final['Fecha_dt'] = pd.to_datetime(df_final['Fecha'], errors='coerce')
        fecha_corte = pd.to_datetime('2026-07-01')
        df_final = df_final[df_final['Fecha_dt'] >= fecha_corte]
        df_final.drop(columns=['Fecha_dt'], inplace=True, errors='ignore')
        
        df_final.drop_duplicates(inplace=True)
        df_final.sort_values(by="Fecha", ascending=False, inplace=True)
        
        nombre_archivo = "historial_biwenger_completo.csv"
        df_final.to_csv(nombre_archivo, index=False, encoding="utf-8-sig")
        print(f"\n🎉 ¡EXTRACCIÓN EXITOSA! Se han guardado {len(df_final)} operaciones reales en '{nombre_archivo}'.")
    else:
        print("❌ No se pudieron extraer registros.")

if __name__ == "__main__":
    extraer_historial_transacciones_real()

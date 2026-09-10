import requests
import pandas as pd
import os
from datetime import datetime

TOKEN = "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJpc3MiOjI4MTU5NjM5LCJpYXQiOjE3NTU1NDQ3MDF9.GfS_aDJpfg15kRWzCtKfQtE1Jz6rg9u1eOBs_Q6ePGM"
LEAGUE_ID = "1812487"
NOMBRE_ARCHIVO = "historial_biwenger_completo.csv"

def rescatar_meses_pasados():
    headers = {
        "Authorization": f"Bearer {TOKEN}",
        "X-League": str(LEAGUE_ID),
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
        "Origin": "https://biwenger.as.com",
        "Referer": "https://biwenger.as.com/"
    }
    
    print("🚀 [Fase 1] Iniciando rescate de operaciones históricas de Julio y Agosto...")
    
    todos_los_registros = []
    ids_unicos = set()

    # 1. Cargamos lo que ya tengamos guardado previamente para no perder nada
    if os.path.exists(NOMBRE_ARCHIVO):
        df_previo = pd.read_csv(NOMBRE_ARCHIVO)
        for _, row in df_previo.iterrows():
            k = f"{row.get('Fecha')}_{row.get('Tipo')}_{row.get('Jugador')}_{row.get('Precio Operación')}"
            ids_unicos.add(k)
            todos_los_registros.append(row.to_dict())
        print(f"📂 Archivo existente cargado con {len(todos_los_registros)} registros previos.")

    # 2. Extracción a través de las jornadas (Rounds) para capturar julio y agosto
    print("🔄 Consultando calendario de jornadas para extraer eventos históricos específicos...")
    url_rounds = "https://biwenger.as.com/api/v2/rounds"
    try:
        resp_rounds = requests.get(url_rounds, headers=headers, timeout=15)
        if resp_rounds.status_code == 200:
            rounds_data = resp_rounds.json().get("data", [])
            for round_item in rounds_data:
                round_id = round_item.get("id")
                # Consultamos el tablón filtrado por cada jornada histórica
                if round_id:
                    url_board_round = f"https://biwenger.as.com/api/v2/leagues/{LEAGUE_ID}/board?round={round_id}"
                    resp_rd = requests.get(url_board_round, headers=headers, timeout=10)
                    if resp_rd.status_code == 200:
                        rd_items = resp_rd.json().get("data", [])
                        if isinstance(rd_items, list):
                            for item in rd_items:
                                tipo = item.get("type", "")
                                timestamp = item.get("date", "")
                                try:
                                    if isinstance(timestamp, (int, float)):
                                        date = datetime.fromtimestamp(timestamp).strftime('%Y-%m-%d %H:%M:%S')
                                    else:
                                        date = str(timestamp)
                                except:
                                    date = str(timestamp)

                                # Filtramos estrictamente que pertenezca a julio o agosto de 2026
                                if date.startswith("2026-07") or date.startswith("2026-08"):
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

                                    item_key = f"{date}_{tipo}_{nombre_jugador}_{precio}"
                                    if item_key not in ids_unicos:
                                        ids_unicos.add(item_key)
                                        todos_los_registros.append({
                                            "Fecha": date,
                                            "Tipo": tipo,
                                            "Jugador": nombre_jugador,
                                            "Precio Operación": precio,
                                            "Valor Mercado": valor,
                                            "Vendedor": vendedor if vendedor else "Mercado",
                                            "Comprador": comprador if comprador else "Mercado"
                                        })
    except Exception as e:
        print(f"⚠️ Aviso en rescate por jornadas: {e}")

    # 3. Consolidación y guardado seguro del histórico completo (Julio + Agosto + Septiembre)
    if todos_los_registros:
        df_final = pd.DataFrame(todos_los_registros)
        
        # Filtro estricto desde el 1 de julio de 2026 en adelante
        df_final['Fecha_dt'] = pd.to_datetime(df_final['Fecha'], errors='coerce')
        fecha_corte = pd.to_datetime('2026-07-01')
        df_final = df_final[df_final['Fecha_dt'] >= fecha_corte]
        df_final.drop(columns=['Fecha_dt'], inplace=True, errors='ignore')
        
        df_final.drop_duplicates(subset=["Fecha", "Tipo", "Jugador", "Precio Operación", "Comprador"], keep="first", inplace=True)
        df_final.sort_values(by="Fecha", ascending=False, inplace=True)
        
        df_final.to_csv(NOMBRE_ARCHIVO, index=False, encoding="utf-8-sig")
        print(f"\n🎉 ¡rescate HISTÓRICO COMPLETADO! Archivo consolidado con {len(df_final)} operaciones únicas.")
    else:
        print("❌ No se pudieron rescatar registros adicionales.")

if __name__ == "__main__":
    rescatar_meses_pasados()

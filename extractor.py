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

def descargar_historial_total_forzado():
    # Endpoints alternativos de la API v2 de Biwenger para forzar la lectura del historial completo
    urls_a_probar = [
        f"https://biwenger.as.com/api/v2/leagues/{LEAGUE_ID}/board",
        f"https://biwenger.as.com/api/v2/leagues/{LEAGUE_ID}/activities"
    ]
    
    headers = {
        "Authorization": f"Bearer {TOKEN}",
        "X-League": str(LEAGUE_ID),
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
        "Accept": "application/json, text/plain, */*",
        "Accept-Language": "es-ES,es;q=0.9",
        "Origin": "https://biwenger.as.com",
        "Referer": "https://biwenger.as.com/"
    }
    
    todos_los_registros = []
    
    print("🚀 Iniciando extracción profunda y bypass de límites de Biwenger...")
    
    for url_base in urls_a_probar:
        print(f"🔄 Probando endpoint: {url_base}")
        offset = 0
        limit = 50
        intentos_fallidos = 0
        
        while True:
            params = {
                "offset": offset,
                "limit": limit
            }
            
            try:
                response = requests.get(url_base, headers=headers, params=params, timeout=15)
                
                if response.status_code != 200:
                    print(f"⚠️ Endpoint respondió con código {response.status_code} en offset {offset}.")
                    break
                
                json_data = response.json()
                
                # Biwenger a veces devuelve los datos en 'data' o directamente en una lista
                data = []
                if isinstance(json_data, dict):
                    data = json_data.get("data", [])
                    if not data and "status" in json_data and json_data.get("status") != 0:
                        # Estructura alternativa
                        data = json_data.get("activity", []) or json_data.get("board", [])
                elif isinstance(json_data, list):
                    data = json_data
                
                if not data:
                    intentos_fallidos += 1
                    if intentos_fallidos >= 2:
                        print(f"✅ Fin de datos alcanzado para este endpoint (Offset: {offset}).")
                        break
                    offset += limit
                    continue
                else:
                    intentos_fallidos = 0

                # Evitar bucles infinitos si la API devuelve los mismos elementos repetidos
                nuevos = 0
                for item in data:
                    if item not in todos_los_registros:
                        todos_los_registros.append(item)
                        nuevos += 1
                
                print(f"📥 [Endpoint Activo] Rescatados {len(todos_los_registros)} registros acumulados (Offset: {offset})...")
                
                if nuevos == 0 and offset > 100:
                    print("ℹ️ La paginación comenzó a devolver elementos duplicados. Deteniendo bucle.")
                    break
                
                offset += limit
                time.sleep(0.3)
                
            except Exception as e:
                print(f"⚠️ Error de conexión: {e}")
                break
                
        if len(todos_los_registros) > 0:
            # Si un endpoint ya nos dio datos masivos, salimos del bucle de URLs
            break

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
        
        # Filtro estricto de seguridad temporal desde el 1 de julio de 2026
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
        print("❌ No se pudieron extraer registros. Asegúrate de que el TOKEN introducido pertenece a una sesión activa en el navegador.")

if __name__ == "__main__":
    descargar_historial_total_forzado()

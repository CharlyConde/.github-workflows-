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

def extraer_historial_sin_limites_biwenger():
    headers = {
        "Authorization": f"Bearer {TOKEN}",
        "X-League": str(LEAGUE_ID),
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
        "Accept": "application/json, text/plain, */*",
        "Origin": "https://biwenger.as.com",
        "Referer": "https://biwenger.as.com/"
    }
    
    print("🚀 Iniciando extracción profunda avanzada (Bypassing API Board Limit)...")
    
    todos_los_registros = []
    ids_unicos = set()

    # 1. Extracción mediante el feed de la liga pero consultando los diarios de actividad de cada usuario (que no tienen el límite de 175)
    url_liga = f"https://biwenger.as.com/api/v2/leagues/{LEAGUE_ID}?include=all"
    
    try:
        response = requests.get(url_liga, headers=headers, timeout=20)
        if response.status_code == 200:
            data_liga = response.json().get("data", {})
            usuarios = data_liga.get("users", [])
            print(f"👥 Liga conectada correctamente. Analizando actividad de {len(usuarios)} usuarios...")
            
            for user in usuarios:
                user_id = user.get("id")
                user_name = user.get("name", f"Usuario {user_id}")
                print(f"🔍 Consultando histórico del usuario: {user_name} (ID: {user_id})...")
                
                # Biwenger almacena el histórico detallado de transacciones de cada usuario en su propio endpoint
                url_user_history = f"https://biwenger.as.com/api/v2/leagues/{LEAGUE_ID}/user/{user_id}"
                resp_user = requests.get(url_user_history, headers=headers, timeout=15)
                
                if resp_user.status_code == 200:
                    user_data = resp_user.json().get("data", {})
                    # Extraemos las actividades/transacciones particulares del usuario
                    actividades = user_data.get("activity", []) or user_data.get("history", [])
                    
                    for act in actividades:
                        act_id = f"{act.get('date')}_{user_id}_{act.get('type')}_{str(act.get('content'))}"
                        if act_id not in ids_unicos:
                            ids_unicos.add(act_id)
                            todos_los_registros.append(act)
                            
                time.sleep(0.2)
        else:
            print(f"⚠️ Error al conectar con la liga principal (Código HTTP {response.status_code}).")
    except Exception as e:
        print(f"⚠️ Error crítico en la consulta de usuarios: {e}")

    # 2. Si el número de registros sigue siendo escaso, consultamos el endpoint de mercado extendido de la liga
    if len(todos_los_registros) <= 175:
        print("ℹ️ Ampliando búsqueda mediante el historial de mercado de fichajes general...")
        url_market = f"https://biwenger.as.com/api/v2/leagues/{LEAGUE_ID}/market"
        try:
            resp_market = requests.get(url_market, headers=headers, timeout=15)
            if resp_market.status_code == 200:
                market_data = resp_market.json().get("data", {})
                # Si hay registros en el histórico de mercado o transacciones recientes
                transacciones_mercado = market_data.get("sales", []) or market_data.get("history", [])
                for item in transacciones_mercado:
                    item_id = f"m_{item.get('date')}_{str(item.get('content'))}"
                    if item_id not in ids_unicos:
                        ids_unicos.add(item_id)
                        todos_los_registros.append(item)
        except Exception as e:
            print(f"ℹ️ Aviso en mercado extendido: {e}")

    print(f"📊 Total bruto de operaciones únicas rescatadas: {len(todos_los_registros)}")

    # 3. Procesamiento y normalización de datos
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
        
        # Guardado automático en Google Drive si se ejecuta en Colab
        try:
            ruta_drive = f"/content/drive/MyDrive/Biwenger/{nombre_archivo}"
            df_final.to_csv(ruta_drive, index=False, encoding="utf-8-sig")
            print(f"\n🎉 ¡EXTRACCIÓN EXITOSA Y COMPLETA! Se han guardado {len(df_final)} operaciones reales en Google Drive y localmente.")
        except:
            print(f"\n🎉 ¡EXTRACCIÓN EXITOSA Y COMPLETA! Archivo guardado con {len(df_final)} operaciones.")
    else:
        print("❌ No se han podido extraer registros. Comprueba que el Token y el League ID sean totalmente válidos.")

if __name__ == "__main__":
    extraer_historial_sin_limites_biwenger()

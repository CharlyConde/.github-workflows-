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

def extraer_historial_biwenger_por_cursor():
    url = f"https://biwenger.as.com/api/v2/leagues/{LEAGUE_ID}/board"
    
    headers = {
        "Authorization": f"Bearer {TOKEN}",
        "X-League": str(LEAGUE_ID),
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
        "Accept": "application/json, text/plain, */*",
        "Origin": "https://biwenger.as.com",
        "Referer": "https://biwenger.as.com/"
    }
    
    todos_los_registros = []
    ids_vistos = set()
    
    # Biwenger en algunos endpoints permite parametrizar con cursor o límite dinámico
    # Si el offset se bloquea en 175, vamos a atacar por bloques de fecha hacia atrás si la API lo acepta,
    # o bien forzar la paginación mediante los parámetros internos de la API.
    
    print("🚀 [Colab] Iniciando extracción profunda por cursor dinámico...")
    
    # Probamos primero el método de paginación por bloques descendentes de ID / Fecha real
    # Si la API tiene un tope estricto en el feed público, consultaremos los datos mediante los hilos de actividad de los usuarios.
    
    offset = 0
    limite_por_peticion = 50
    intentos = 0
    
    while True:
        params = {
            "offset": offset,
            "limit": limite_por_peticion
        }
        
        try:
            response = requests.get(url, headers=headers, params=params, timeout=15)
            
            if response.status_code != 200:
                print(f"⚠️ Código HTTP {response.status_code} en offset {offset}. Deteniendo.")
                break
                
            json_data = response.json()
            data = json_data.get("data", []) if isinstance(json_data, dict) else json_data
            
            if not data:
                print("✅ Fin de datos devueltos por la API.")
                break
                
            nuevos_en_esta_pagina = 0
            for item in data:
                # Generamos un identificador único para el movimiento
                item_id = f"{item.get('date')}_{item.get('type')}_{str(item.get('content'))}"
                
                if item_id not in ids_vistos:
                    ids_vistos.add(item_id)
                    todos_los_registros.append(item)
                    nuevos_en_esta_pagina += 1
            
            print(f"📥 Offset actual: {offset} | Nuevos registros en este bloque: {nuevos_en_esta_pagina} | Total acumulado: {len(todos_los_registros)}")
            
            # Si la API devuelve los mismos registros en bucle (provocando 0 nuevos) o menos de los esperados, 
            # significa que hemos chocado con el muro de Biwenger. Intentamos un salto directo por timestamp si es posible.
            if nuevos_en_esta_pagina == 0:
                intentos += 1
                if intentos >= 3:
                    print("ℹ️ Se alcanzó el límite operativo del endpoint público de Biwenger.")
                    break
            else:
                intentos = 0
                
            offset += limite_por_peticion
            time.sleep(0.3)
            
        except Exception as e:
            print(f"❌ Error de conexión: {e}")
            break

    # Si nos hemos quedado en el muro de los 175 y necesitamos todo el histórico desde julio,
    # vamos a incorporar un volcado secundario de fichajes de mercado si la API principal se corta.
    if len(todos_los_registros) <= 175:
        print("⚠️ Advertencia: El feed público está capado a 175 registros por restricciones de Biwenger.")
        print("🔄 Intentando método alternativo de extracción por transacciones de usuarios...")
        
        # Intentamos consultar el endpoint de la liga para extraer usuarios y sus movimientos individuales
        url_liga = f"https://biwenger.as.com/api/v2/leagues/{LEAGUE_ID}"
        try:
            resp_liga = requests.get(url_liga, headers=headers, timeout=15)
            if resp_liga.status_code == 200:
                liga_info = resp_liga.json().get("data", {})
                usuarios = liga_info.get("users", [])
                print(f"👥 Usuarios detectados en la liga: {len(usuarios)}. Extrayendo histórico individual...")
                
                # Biwenger almacena el histórico detallado por usuario en su actividad particular
                for user in usuarios:
                    user_id = user.get("id")
                    user_name = user.get("name")
                    url_user = f"https://biwenger.as.com/api/v2/leagues/{LEAGUE_ID}/user/{user_id}"
                    resp_user = requests.get(url_user, headers=headers, timeout=15)
                    if resp_user.status_code == 200:
                        user_data = resp_user.json().get("data", {})
                        activity = user_data.get("activity", [])
                        for act in activity:
                            act_id = f"u_{user_id}_{act.get('date')}_{act.get('type')}"
                            if act_id not in ids_vistos:
                                ids_vistos.add(act_id)
                                todos_los_registros.append(act)
                print(f"📥 Total tras barrido por usuarios: {len(todos_los_registros)} registros.")
        except Exception as e:
            print(f"ℹ️ No se pudo completar el barrido secundario: {e}")

    # Procesamiento final a DataFrame
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
        
        # Guardar en Google Drive / Local
        nombre_archivo = "historial_biwenger_completo.csv"
        df_final.to_csv(nombre_archivo, index=False, encoding="utf-8-sig")
        
        # Si estás en Colab con Drive montado, lo guardamos también allí directamente
        try:
            ruta_drive = f"/content/drive/MyDrive/Biwenger/{nombre_archivo}"
            df_final.to_csv(ruta_drive, index=False, encoding="utf-8-sig")
            print(f"\n🎉 ¡EXTRACCIÓN FINALIZADA! Total de operaciones reales guardadas: {len(df_final)}")
        except:
            print(f"\n🎉 ¡EXTRACCIÓN FINALIZADA! Archivo guardado localmente con {len(df_final)} operaciones.")
    else:
        print("❌ No se pudieron extraer registros. Revisa tus credenciales.")

if __name__ == "__main__":
    extraer_historial_biwenger_por_cursor()

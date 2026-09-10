import requests
import pandas as pd
import time
from datetime import datetime

# ==========================================
# CONFIGURACIÓN DE ACCESO A LA API DE BIWENGER
# ==========================================
TOKEN = "TU_TOKEN_DE_AUTORIZACION"
LEAGUE_ID = "TU_ID_DE_LIGA"

def descargar_historial_infinito():
    # Usamos el endpoint principal de actividades/pizarra de la liga
    url = f"https://biwenger.as.com/api/v2/leagues/{LEAGUE_ID}/board"
    
    headers = {
        "Authorization": f"Bearer {TOKEN}",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept": "application/json, text/plain, */*",
        "Referer": "https://biwenger.as.com/"
    }
    
    offset = 0
    limit = 50  # Bloque óptimo por petición para evitar timeouts de la API
    todos_los_registros = []
    
    print("🚀 Iniciando extracción exhaustiva del historial de Biwenger desde origen...")
    
    intentos_vacios = 0
    
    while True:
        params = {
            "offset": offset,
            "limit": limit
        }
        
        try:
            response = requests.get(url, headers=headers, params=params, timeout=15)
            
            if response.status_code != 200:
                print(f"⚠️ Aviso: Código HTTP {response.status_code} en offset {offset}. Reintentando...")
                time.sleep(1)
                response = requests.get(url, headers=headers, params=params, timeout=15)
                if response.status_code != 200:
                    print(f"❌ Error crítico en la API. Deteniendo en offset {offset}.")
                    break

            json_data = response.json()
            data = json_data.get("data", [])
            
            # Si no hay datos, comprobamos si es un corte temporal o el final real
            if not data:
                intentos_vacios += 1
                if intentos_vacios >= 3:
                    print("✅ Fin del historial alcanzado (múltiples páginas vacías consecutivas).")
                    break
                offset += limit
                continue
            else:
                intentos_vacios = 0  - # Reseteamos contador si encontramos datos

            todos_los_registros.extend(data)
            print(f"📥 Progreso: {len(todos_los_registros)} registros rescatados (Offset actual: {offset})...")
            
            # Incrementamos el offset de forma estricta
            offset += limit
            time.sleep(0.25)  # Pausa de cortesía para saturar la API
            
        except Exception as e:
            print(f"⚠️ Error de conexión o timeout en offset {offset}: {e}")
            time.sleep(2)
            # Reintentamos el mismo offset una vez más
            try:
                response = requests.get(url, headers=headers, params=params, timeout=15)
                data = response.json().get("data", [])
                if data:
                    todos_los_registros.extend(data)
                    offset += limit
                else:
                    break
            except:
                break

    if todos_los_registros:
        filas = []
        for item in todos_los_registros:
            tipo = item.get("type", "")
            timestamp = item.get("date", "")
            
            # Conversión de timestamp a fecha legible por Pandas
            try:
                if isinstance(timestamp, (int, float)):
                    date = datetime.fromtimestamp(timestamp).strftime('%Y-%m-%d %H:%M:%S')
                else:
                    date = str(timestamp)
            except:
                date = str(timestamp)

            content = item.get("content", {})
            
            jugador = content.get("player", {})
            if isinstance(jugador, dict):
                nombre_jugador = jugador.get("name", "Desconocido")
            else:
                nombre_jugador = "Desconocido"
                
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
        
        # Filtrar estrictamente desde el 1 de julio de 2026 en adelante por seguridad temporal
        df_final['Fecha_dt'] = pd.to_datetime(df_final['Fecha'], errors='coerce')
        fecha_corte = pd.to_datetime('2026-07-01')
        
        # Si hay registros anteriores que no deseas, los filtramos, o mantenemos todos si la temporada empezó ahí
        df_final = df_final[df_final['Fecha_dt'] >= fecha_corte]
        df_final.drop(columns=['Fecha_dt'], inplace=True, errors='ignore')
        
        # Limpieza de duplicados y orden cronológico inverso (más reciente primero)
        df_final.drop_duplicates(inplace=True)
        df_final.sort_values(by="Fecha", ascending=False, inplace=True)
        
        nombre_archivo = "historial_biwenger_completo.csv"
        df_final.to_csv(nombre_archivo, index=False, encoding="utf-8-sig")
        print(f"\n🎉 ¡ÉXITO TOTAL! Archivo '{nombre_archivo}' guardado con {len(df_final)} operaciones desde el 1 de Julio de 2026.")
    else:
        print("⚠️ No se han podido descargar registros. Comprueba que tu Token y LEAGUE_ID sean válidos y estén activos.")

if __name__ == "__main__":
    descargar_historial_infinito()

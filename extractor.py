import requests
import pandas as pd
import time
from datetime import datetime, timedelta

# ==========================================
# CONFIGURACIÓN DE ACCESO A LA API DE BIWENGER
# ==========================================
# Introduce tu token de autorización (Bearer) y el ID de tu liga
TOKEN = "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJpc3MiOjI4MTU5NjM5LCJpYXQiOjE3NTU1NDQ3MDF9.GfS_aDJpfg15kRWzCtKfQtE1Jz6rg9u1eOBs_Q6ePGM"
LEAGUE_ID = "1812487"

def descargar_historial_por_rangos_temporales():
    url = f"https://biwenger.as.com/api/v2/leagues/{LEAGUE_ID}/board"
    
    headers = {
        "Authorization": f"Bearer {TOKEN}",
        "X-League": str(LEAGUE_ID),
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
        "Accept": "application/json, text/plain, */*",
        "Origin": "https://biwenger.as.com",
        "Referer": "https://biwenger.as.com/"
    }
    
    todos_los_registros = {} # Usamos diccionario con ID o índice único para evitar duplicados
    
    # Definimos el rango de fechas: desde el 1 de julio de 2026 hasta el día de hoy
    fecha_inicio = datetime(2026, 7, 1)
    fecha_fin = datetime.now()
    
    print(f"🚀 Iniciando extracción por bloques temporales diarios desde {fecha_inicio.strftime('%Y-%m-%d')} hasta hoy...")
    
    # Hacemos un recorrido día a día o en bloques de pocos días para forzar a la API a entregar todo
    delta_dias = 3  # Bloques de 3 días para capturar todas las operaciones sin saturar
    current_end = fecha_fin
    
    while current_end >= fecha_inicio:
        current_start = max(fecha_inicio, current_end - timedelta(days=delta_dias))
        
        # Biwenger en algunos endpoints acepta parámetros de filtrado temporal o paginación profunda
        # Si la API no filtra por fecha en este endpoint, probamos offset masivo con control de ID único
        offset = 0
        limit = 50
        
        print(f"📅 Consultando bloque temporal / desplazamiento: {current_start.strftime('%Y-%m-%d')} al {current_end.strftime('%Y-%m-%d')}...")
        
        bloque_vacio = 0
        while True:
            params = {
                "offset": offset,
                "limit": limit
            }
            
            try:
                response = requests.get(url, headers=headers, params=params, timeout=15)
                if response.status_code != 200:
                    break
                    
                json_data = response.json()
                data = json_data.get("data", []) if isinstance(json_data, dict) else json_data
                
                if not data:
                    break
                
                added_in_page = 0
                for item in data:
                    # Creamos una clave única basada en fecha y contenido para evitar duplicados exactos
                    item_id = str(item.get("date", "")) + "_" + str(item.get("type", "")) + "_" + str(item.get("content", {}))
                    if item_id not in todos_los_registros:
                        todos_los_registros[item_id] = item
                        added_in_page += 1
                
                # Si los registros devuelven IDs repetidos que ya teníamos o la página viene vacía de nuevos, paramos este offset
                if added_in_page == 0:
                    bloque_vacio += 1
                    if bloque_vacio >= 2:
                        break
                else:
                    bloque_vacio = 0
                
                if len(data) < limit:
                    break
                    
                offset += limit
                time.sleep(0.2)
                
            except Exception as e:
                print(f"⚠️ Error en petición: {e}")
                break
                
        # Retrocedemos el bloque temporal
        current_end = current_start - timedelta(days=1)
        print(f"📥 Total de registros únicos acumulados hasta ahora: {len(todos_los_registros)}")
        time.sleep(0.3)

    lista_final_bruta = list(todos_los_registros.values())
    
    if lista_final_bruta:
        filas = []
        for item in lista_final_bruta:
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
        
        # Filtro estricto de seguridad desde el 1 de julio de 2026
        df_final['Fecha_dt'] = pd.to_datetime(df_final['Fecha'], errors='coerce')
        fecha_corte = pd.to_datetime('2026-07-01')
        df_final = df_final[df_final['Fecha_dt'] >= fecha_corte]
        df_final.drop(columns=['Fecha_dt'], inplace=True, errors='ignore')
        
        df_final.drop_duplicates(inplace=True)
        df_final.sort_values(by="Fecha", ascending=False, inplace=True)
        
        nombre_archivo = "historial_biwenger_completo.csv"
        df_final.to_csv(nombre_archivo, index=False, encoding="utf-8-sig")
        print(f"\n🎉 ¡EXTRACCIÓN TOTAL COMPLETADA! Se han guardado {len(df_final)} operaciones reales en '{nombre_archivo}'.")
    else:
        print("❌ No se pudieron extraer registros. Verifica que tu TOKEN y LEAGUE_ID sean correctos.")

if __name__ == "__main__":
    descargar_historial_por_rangos_temporales()

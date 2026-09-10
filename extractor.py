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

def extraccion_por_cursor_inverso_id():
    # URL base del tablón de Biwenger
    base_url = f"https://biwenger.as.com/api/v2/leagues/{LEAGUE_ID}/board"
    
    headers = {
        "Authorization": f"Bearer {TOKEN}",
        "X-League": str(LEAGUE_ID),
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
        "Accept": "application/json, text/plain, */*",
        "Origin": "https://biwenger.as.com",
        "Referer": "https://biwenger.as.com/"
    }
    
    print("🚀 [SISTEMA NUEVO] Iniciando extracción por cursor inverso de ID (Bypassing offsets)...")
    
    todos_los_registros = {}
    
    # En lugar de usar offset numérico (que se rompe en 175), vamos a paginar usando 
    # el parámetro de control temporal o ID de última transacción si la API lo soporta,
    # o bien atacando directamente los endpoints de mercado y clasificación histórica.
    
    # 1. Extracción masiva mediante los datos de usuario y mercado combinados
    endpoints_alternativos = [
        f"https://biwenger.as.com/api/v2/leagues/{LEAGUE_ID}/market",
        f"https://biwenger.as.com/api/v2/leagues/{LEAGUE_ID}"
    ]
    
    for endpoint in endpoints_alternativos:
        try:
            print(f"🔄 Consultando endpoint alternativo: {endpoint}")
            resp = requests.get(endpoint, headers=headers, timeout=15)
            if resp.status_code == 200:
                json_data = resp.json().get("data", {})
                # Si hay datos de mercado o historial interno
                if isinstance(json_data, dict):
                    for k, v in json_data.items():
                        if isinstance(v, list) and len(v) > 0:
                            for item in v:
                                if isinstance(item, dict) and ("date" in item or "type" in item):
                                    item_key = f"{item.get('date')}_{item.get('type')}_{str(item.get('content', ''))}"
                                    todos_los_registros[item_key] = item
        except Exception as e:
            print(f"⚠️ Aviso en endpoint alternativo: {e}")

    # 2. Forzar lectura del tablón mediante bloques con parámetro de fecha si el servidor lo acepta
    # Vamos a probar bloques de peticiones hacia atrás mes a mes desde septiembre de 2026 hasta julio de 2026
    meses_a_probar = [
        ("2026-09-01", "2026-09-10"),
        ("2026-08-01", "2026-08-31"),
        ("2026-07-01", "2026-07-31")
    ]
    
    for f_ini, f_fin in meses_a_probar:
        print(f"📅 Solicitando bloque temporal en servidor: {f_ini} al {f_fin}...")
        # Intentamos enviar parámetros de fecha por si el backend los acepta de forma oculta
        params = {
            "from": f_ini,
            "to": f_fin,
            "limit": 200
        }
        try:
            resp = requests.get(base_url, headers=headers, params=params, timeout=15)
            if resp.status_code == 200:
                data = resp.json().get("data", [])
                if isinstance(data, list):
                    for item in data:
                        item_key = f"{item.get('date')}_{item.get('type')}_{str(item.get('content', ''))}"
                        todos_los_registros[item_key] = item
                    print(f"📥 Obtenidos {len(data)} registros para el rango {f_ini} - {f_fin}")
        except Exception as e:
            print(f"⚠️ Aviso en bloque temporal: {e}")
        time.sleep(0.3)

    # 3. Si aún necesitamos rellenar, hacemos un barrido por ID descendente bruto (simulando peticiones masivas)
    print("🔄 Realizando barrido de seguridad por bloques numéricos de ID...")
    ultimo_id_conocido = 99999999
    intentos_vacios = 0
    
    while intentos_vacios < 5:
        url_cursor = f"{base_url}?max={ultimo_id_conocido}&limit=50"
        try:
            resp = requests.get(url_cursor, headers=headers, timeout=10)
            if resp.status_code != 200:
                break
            data = resp.json().get("data", [])
            if not data:
                intentos_vacios += 1
                ultimo_id_conocido -= 50000
                continue
            
            nuevos = 0
            min_id_en_lote = ultimo_id_conocido
            for item in data:
                item_key = f"{item.get('date')}_{item.get('type')}_{str(item.get('content', ''))}"
                if item_key not in todos_los_registros:
                    todos_los_registros[item_key] = item
                    nuevos += 1
                # Intentamos capturar un identificador numérico si existe
                if "id" in item:
                    try:
                        min_id_en_lote = min(min_id_en_lote, int(item["id"]))
                    except:
                        pass
            
            if nuevos == 0:
                intentos_vacios += 1
            else:
                intentos_vacios = 0
                
            ultimo_id_conocido = min_id_en_lote - 1
            time.sleep(0.2)
        except:
            break

    lista_final = list(todos_los_registros.values())
    print(f"📊 Total absoluto de operaciones únicas recolectadas: {len(lista_final)}")

    if lista_final:
        filas = []
        for item in lista_final:
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
        
        try:
            ruta_drive = f"/content/drive/MyDrive/Biwenger/{nombre_archivo}"
            df_final.to_csv(ruta_drive, index=False, encoding="utf-8-sig")
            print(f"\n🎉 ¡EXTRACCIÓN REALIZADA CON ÉXITO! Se han guardado {len(df_final)} operaciones en Google Drive.")
        except:
            print(f"\n🎉 ¡EXTRACCIÓN REALIZADA CON ÉXITO! Archivo guardado localmente con {len(df_final)} operaciones.")
    else:
        print("❌ No se pudieron extraer registros.")

if __name__ == "__main__":
    extraccion_por_cursor_inverso_id()

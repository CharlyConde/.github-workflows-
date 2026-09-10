import requests
import pandas as pd
import time

# ==========================================
# CONFIGURACIÓN DE ACCESO A LA API DE BIWENGER
# ==========================================
# Inserta aquí tu token de sesión (Bearer token) y el ID de tu liga
TOKEN = "TU_TOKEN_DE_AUTORIZACION"
LEAGUE_ID = "TU_ID_DE_LIGA"

def descargar_historial_infinito():
    # Endpoint oficial de la pizarra / actividades de la liga en Biwenger
    url = f"https://biwenger.as.com/api/v2/leagues/{LEAGUE_ID}/board"
    
    headers = {
        "Authorization": f"Bearer {TOKEN}",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        "Accept": "application/json, text/plain, */*"
    }
    
    offset = 0
    limit = 50  # Tamaño del bloque por petición
    todos_los_registros = []
    
    print("🚀 Iniciando extracción completa de la pizarra de Biwenger...")
    
    while True:
        params = {"offset": offset, "limit": limit}
        
        try:
            response = requests.get(url, headers=headers, params=params)
            
            if response.status_code != 200:
                print(f"❌ Error en la API de Biwenger. Código HTTP: {response.status_code}")
                # Si falla el board, probamos con el endpoint alternativo de actividades
                url_alt = f"https://biwenger.as.com/api/v2/leagues/{LEAGUE_ID}/activities"
                response = requests.get(url_alt, headers=headers, params=params)
                if response.status_code != 200:
                    break

            data = response.json().get("data", [])
            
            # Si la API ya no devuelve elementos, hemos llegado al origen de la liga
            if not data:
                print("✅ Se han descargado absolutamente todos los registros históricos disponibles.")
                break
                
            todos_los_registros.extend(data)
            print(f"📥 Registros acumulados hasta el momento: {len(todos_los_registros)}")
            
            # Avanzamos el offset para la siguiente página
            offset += limit
            time.sleep(0.3)  # Pequeña pausa para evitar bloqueos por rate-limit
            
        except Exception as e:
            print(f"⚠️ Ocurrió un error durante la petición: {e}")
            break

    if todos_los_registros:
        filas = []
        for item in todos_los_registros:
            tipo = item.get("type", "")
            date = item.get("date", "")
            content = item.get("content", {})
            
            # Extracción robusta de campos mapeados
            jugador = content.get("player", {}).get("name", "Desconocido")
            precio = content.get("amount", 0)
            valor = content.get("value", 0)
            
            vendedor_obj = content.get("from")
            vendedor = vendedor_obj.get("name", "Mercado") if vendedor_obj else "Mercado"
            
            comprador_obj = content.get("to") or content.get("user")
            comprador = comprador_obj.get("name", "Mercado") if comprador_obj else "Mercado"

            filas.append({
                "Fecha": date,
                "Tipo": tipo,
                "Jugador": jugador,
                "Precio Operación": precio,
                "Valor Mercado": valor,
                "Vendedor": vendedor,
                "Comprador": comprador
            })
            
        df_final = pd.DataFrame(filas)
        
        # Limpieza de duplicados y orden cronológico
        df_final.drop_duplicates(inplace=True)
        df_final.sort_values(by="Fecha", ascending=False, inplace=True)
        
        nombre_archivo = "historial_biwenger_completo.csv"
        df_final.to_csv(nombre_archivo, index=False, encoding="utf-8-sig")
        print(f"🎉 ¡Archivo '{nombre_archivo}' actualizado con éxito con {len(df_final)} registros!")
    else:
        print("⚠️ No se pudieron rescatar registros. Revisa que tu Token y tu LEAGUE_ID sean correctos.")

if __name__ == "__main__":
    descargar_historial_infinito()

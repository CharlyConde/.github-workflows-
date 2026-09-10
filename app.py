import requests
import pandas as pd

# CONFIGURACIÓN DE ACCESO A BIWENGER
# Reemplaza 'TU_TOKEN_DE_AUTORIZACION' con tu token de sesión real de Biwenger
TOKEN = "TU_TOKEN_DE_AUTORIZACION"
LEAGUE_ID = "TU_ID_DE_LIGA"  # Opcional si tu endpoint lo requiere

def obtener_historial_completo():
    url = f"https://biwenger.as.com/api/v2/leagues/{LEAGUE_ID}/board" # O el endpoint de fichajes/historial que utilices
    headers = {
        "Authorization": f"Bearer {TOKEN}",
        "User-Agent": "Mozilla/5.0"
    }
    
    offset = 0
    limit = 30
    todos_los_movimientos = []
    
    print("Iniciando la descarga de todo el histórico de Biwenger...")
    
    while True:
        params = {"offset": offset, "limit": limit}
        response = requests.get(url, headers=headers, params=params)
        
        if response.status_code != 200:
            print(f"Error al conectar con la API: {response.status_code}")
            break
            
        data = response.json().get("data", [])
        
        # Si la API ya no devuelve registros, llegamos al final de los tiempos de la liga
        if not data:
            break
            
        todos_los_movimientos.extend(data)
        print(f"Descargados {len(todos_los_movimientos)} registros acumulados...")
        
        # Incrementamos el offset para la siguiente página
        offset += limit
        
    # Procesar los datos y guardarlos en el CSV definitivo
    if todos_los_movimientos:
        df = pd.DataFrame(todos_los_movimientos)
        df.to_csv("historial_biwenger_completo.csv", index=False)
        print("¡Historial completo descargado y guardado con éxito en 'historial_biwenger_completo.csv'!")
    else:
        print("No se encontraron datos para exportar.")

if __name__ == "__main__":
    obtener_historial_completo()

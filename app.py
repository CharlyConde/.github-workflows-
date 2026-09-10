import requests
import pandas as pd
import time

# ==========================================
# CONFIGURACIÓN DE ACCESO A LA API DE BIWENGER
# ==========================================
# Introduce aquí tu token de autenticación (Bearer Token)
TOKEN = "TU_TOKEN_DE_BEARER_AQUÍ" 
LEAGUE_ID = "TU_ID_DE_LIGA_AQUÍ"  # Opcional según tu implementación previa

headers = {
    "Authorization": f"Bearer {TOKEN}",
    "Accept": "json",
    "Content-Type": "application/json"
}

def obtener_historial_completo():
    all_movements = []
    offset = 0
    limit = 50  # Tamaño del bloque por petición (ajustable según la API)
    
    print("Iniciando la descarga completa del historial de Biwenger...")
    
    while True:
        # Endpoint habitual de actividades/historial de Biwenger
        # Añadimos parámetros de paginación (offset / limit) por si la API los soporta
        url = f"https://biwenger.as.com/api/v2/leagues/{LEAGUE_ID}/activities?offset={offset}&limit={limit}"
        
        try:
            response = requests.get(url, headers=headers)
            
            if response.status_code != 200:
                print(f"Error en la petición. Código HTTP: {response.status_code}")
                # Intentamos endpoint alternativo general si el de liga da error específico
                url_alt = f"https://biwenger.as.com/api/v2/league/board?offset={offset}&limit={limit}"
                response = requests.get(url_alt, headers=headers)
                if response.status_code != 200:
                    break

            data = response.json()
            
            # Extraer la lista de movimientos (suele venir en 'data' o directamente en la respuesta)
            movements = data.get('data', []) if isinstance(data, dict) else data
            
            if not movements:
                # Si no devuelve más elementos, terminamos el bucle
                break
                
            all_movements.extend(movements)
            print(f"Descargados {len(all_movements)} registros acumulados...")
            
            # Si el número de elementos devueltos es menor que el límite, hemos llegado al final
            if len(movements) < limit:
                break
                
            offset += limit
            # Pausa breve para evitar bloqueos por rate-limiting
            time.sleep(0.5)
            
        except Exception as e:
            print(f"Ocurrió un error durante la descarga: {e}")
            break

    return all_movements

# ==========================================
# PROCESAMIENTO Y LIMPIEZA DE DATOS
# ==========================================
def procesar_datos(movimientos):
    filas_procesadas = []
    
    for mov in movimientos:
        # Extracción segura de los campos del JSON de Biwenger
        fecha = mov.get('date', '')
        tipo = mov.get('type', '')
        
        # Procesamiento según la estructura interna de Biwenger
        # (Compatible con traspasos, mercado, cláusulas, etc.)
        content = mov.get('content', {})
        
        jugador = content.get('player', {}).get('name', 'Desconocido')
        vendedor = content.get('from', {}).get('name', 'Mercado') if content.get('from') else 'Mercado'
        comprador = content.get('to', {}).get('name', 'Mercado') if content.get('to') else 'Mercado'
        precio = content.get('amount', 0)
        valor_mercado = content.get('value', 0)
        
        sobreprecio_eur = precio - valor_mercado
        sobreprecio_pct = (sobreprecio_eur / valor_mercado * 100) if valor_mercado > 0 else 0

        filas_procesadas.append({
            'Fecha': fecha,
            'Jugador': jugador,
            'Vendedor': vendedor,
            'Comprador': comprador,
            'Precio Operación': precio,
            'Valor Mercado': valor_mercado,
            'Sobreprecio (€)': sobreprecio_eur,
            'Sobreprecio (%)': round(sobreprecio_pct, 1),
            'Tipo': tipo
        })
        
    df = pd.DataFrame(filas_procesadas)
    
    # Eliminar posibles duplicados basados en fecha, jugador y precio
    if not df.empty:
        df.drop_duplicates(subset=['Fecha', 'Jugador', 'Precio Operación'], keep='first', inplace=True)
        # Ordenar cronológicamente del más reciente al más antiguo
        df.sort_values(by='Fecha', ascending=False, inplace=True)
        
    return df

# ==========================================
# EJECUCIÓN PRINCIPAL
# ==========================================
if __name__ == "__main__":
    raw_data = obtener_historial_completo()
    df_historial = procesar_datos(raw_data)
    
    # Guardar a CSV manteniendo todo lo anterior y asegurando el histórico completo
    nombre_archivo = "historial_biwenger_completo.csv"
    df_historial.to_csv(nombre_archivo, index=False, encoding='utf-8-sig')
    print(f"¡Proceso completado! Se han guardado {len(df_historial)} registros en '{nombre_archivo}'.")

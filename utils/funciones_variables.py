import math
import polars as pl
from models.base_models import BaseRecommendationRequest

filtro_estados = ['AZ', 'CA', 'DE', 'FL', 'ID', 'IL', 'IN', 'LA', 'MO', 'NV', 'PA', 'TN']

lista_categorias = [
    'JAPONESA - ASIATICA',
    'BARES - CERVECERIAS - TAPAS',
    'RESTAURANTES GENERALES',
    'MEDITERRANEA',
    'PIZZERIAS',
    'GRILL - ASADOS - CARNES',
    'MEXICANA',
    'COMIDA RAPIDA',
    'CAFETERIAS - COMIDAS LIGERAS',
    'COCINA INTERNACIONAL',
    'DIETA - VEGANA - ENSALADAS'
]

lista_caracteristicas = [
    'ACEPTA TARJETA DE CREDITO',
    'SERVICIO DE DELIVERY',
    'SERVICIO PARA LLEVAR',
    'ACCESIBILIDAD SILLAS DE RUEDA',
    'ESTACIONAMIENTO BICICLETAS',
    'APROPIADO PARA NIÑOS',
    'ACEPTA MASCOTAS'
]

orden_estados = {
    'AZ': 0,
    'CA': 1,
    'DE': 2,
    'FL': 3,
    'ID': 4,
    'IL': 5,
    'IN': 6,
    'LA': 7,
    'MO': 8,
    'NV': 9,
    'PA': 10,
    'TN': 11
}


def distancia_haversine(lat1, lon1, lat2, lon2):
    """
    Calcula la distancia entre dos localidades dadas sus latitudes y longitudes.

    Parámetros:
    lat1 (float): Latitud de la primera localidad (en grados).
    lon1 (float): Longitud de la primera localidad (en grados).
    lat2 (float): Latitud de la segunda localidad (en grados).
    lon2 (float): Longitud de la segunda localidad (en grados).

    Retorna:
    float: Distancia entre las dos localidades en kilómetros.
    """
    # Radio de la Tierra en kilómetros
    radio_tierra = 6371

    # Convertir grados a radianes
    lat1_rad = math.radians(lat1)
    lon1_rad = math.radians(lon1)
    lat2_rad = math.radians(lat2)
    lon2_rad = math.radians(lon2)

    # Diferencias entre latitudes y longitudes
    delta_lat = lat2_rad - lat1_rad
    delta_lon = lon2_rad - lon1_rad

    # Fórmula de Haversine
    a = math.sin(delta_lat / 2) ** 2 + math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(delta_lon / 2) ** 2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))

    distancia = radio_tierra * c

    return distancia


def valida_requets_app(request_app: BaseRecommendationRequest, df_business: pl.DataFrame, df_user_ids: pl.DataFrame) -> bool:

    # Validando buena entrada de estado
    if request_app.estado.strip().upper() not in filtro_estados:
        return True, 'estado'
    # Validando buena entrada de caracteristicas
    if len(request_app.caracteristicas) > 0:
        for caracteristica in request_app.caracteristicas:
            if caracteristica.strip().upper() not in lista_caracteristicas:
                return True, 'caracteristicas'
    # Validando buena entrada de Categorias
    if len(request_app.categorias) > 0:
        for categoria in request_app.categorias:
            if categoria.strip().upper() not in lista_categorias:
                return True, 'categorias'
    # Validando buena entrada de ciudad
    mask = df_business['Estado'] == request_app.estado
    ciudades = df_business.filter(mask)['Ciudad'].unique().to_list()
    if request_app.ciudad not in ciudades:
        return True, 'ciudad'
    # Validando buena entrada de km
    if request_app.km not in [25, 37, 50]:
        return True, 'km'
    # Validando buena entrada de usuario
    if request_app.usuario not in df_user_ids['user_id'].to_list():
        return True, 'usuario'

    return False, ""

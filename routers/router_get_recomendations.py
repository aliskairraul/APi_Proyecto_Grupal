from fastapi import APIRouter, status, HTTPException
import pandas as pd
import numpy as np
import joblib
from models.base_models import BaseRecommendationRequest, BaseRecomendations

# Cargando el Modelo de Recomendación
model = joblib.load('data/model.pkl')

# Cargando las matrices de Características
user_features = joblib.load('data/user_features.pkl')
item_features = joblib.load('data/item_features.pkl')

# Cargando los DataFrames necesarios para el Filtrado
df_user_ids = pd.read_parquet('data/df_user_ids.parquet')
df_business = pd.read_parquet('data/df_business.parquet')

router = APIRouter(
    prefix="/get_recomendations",
    tags=["get_recomendations"],
    responses={400: {"message": "BAD REQUEST"}},
)


@router.get("/", status_code=status.HTTP_200_OK)
async def get_recomendations(request_app: BaseRecommendationRequest) -> BaseRecomendations:
    """
    get_recomendations: recibe una peticion GET con payload con la estructura de BaseRecommendationRequest
                        y devuelve las n recomendaciones solicitadas con la estructura BaseRecomendations

    Args:
        request_app (BaseRecommendationRequest): Datos de la Peticion:
                                                    id del usuario al que se le realizara las recomendaciones
                                                    Estado donde quiere las recomendaciones
                                                    Categoría de la cual quiere las recomendaciones
                                                    Número de recomendaciones
    Raises:
        HTTPException: En caso de una mala solicitud da una respuesta con codigo 400 y mensaje `BAD REQUEST`

    Returns:
        BaseRecomendations: Lista de Diccionarios con esta estructura, que contiene las recomendaciones
                            devuelve por cada recomendacion
                            id del negocio
                            Direccion del mismo
                            Ciudad en que se encuentra
                            Coordenada Latitud
                            Coordenada Longitud
    """

    try:
        if request_app.state.strip().upper() not in df_business['state'].unique().tolist():
            raise HTTPException(status_code=400, detail="BAD REQUEST")
        if request_app.category.strip().lower() != 'normal':
            raise HTTPException(status_code=400, detail="BAD REQUEST")

        # Obteniendo el ID Entero del usuario
        mask = df_user_ids['user_id'] == request_app.user_id_str.strip()
        user_id = int(df_user_ids[mask]['user_id_int'].values[0])

        # Creando la lista de Negocios Segun el estado
        mask = df_business['state'] == request_app.state.strip().upper()
        business_id_list = df_business[mask]['business_id_int'].tolist()

        # Aplicando procedimiento estandard de LightFm para obtener Recomendaciones
        scores = model.predict(user_id, business_id_list, item_features=item_features, user_features=user_features)
        top_items = np.argsort(-scores)[:request_app.top_n]
        recomendations = [business_id_list[i] for i in top_items]

        # Obteniendo las Caracteristicas de cada Recomendación
        recomendations_list = []
        for recomendation in recomendations:
            recomendation_dict = {}
            mask = df_business['business_id_int'] == recomendation
            recomendation_dict['business_id'] = df_business[mask]['business_id'].values[0]
            recomendation_dict['name'] = df_business[mask]['name'].values[0]
            recomendation_dict['address'] = df_business[mask]['address'].values[0]
            recomendation_dict['city'] = df_business[mask]['city'].values[0]
            recomendation_dict['latitude'] = df_business[mask]['latitude'].values[0]
            recomendation_dict['longitude'] = df_business[mask]['longitude'].values[0]
            recomendations_list.append(recomendation_dict)
    except IndexError:
        raise HTTPException(status_code=400, detail="BAD REQUEST")

    return BaseRecomendations(recomendations=recomendations_list)

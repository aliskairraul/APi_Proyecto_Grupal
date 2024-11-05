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

    try:
        # Obteniendo el ID Entero del usuario
        mask = df_user_ids['user_id'] == request_app.user_id_str
        user_id = int(df_user_ids[mask]['user_id_int'].values[0])

        # Creando la lista de Negocios Segun el estado
        mask = df_business['state'] == request_app.state
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

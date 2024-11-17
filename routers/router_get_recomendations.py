from fastapi import APIRouter, status, HTTPException
import polars as pl
import numpy as np
import joblib
import pickle
from models.base_models import BaseRecommendationRequest, BaseRecomendations
from utils.funciones_variables import orden_estados, distancia_haversine, valida_requets_app
# DATA, MODELO y MATRICES DE CARACTERISTICAS
df_user_ids = pl.read_parquet('data/df_user_ids.parquet')
new_row = pl.DataFrame({"user_id_int": [0], "user_id": ["USUARIO NUEVO"]})
df_user_ids = df_user_ids.vstack(new_row)

df_business = pl.read_parquet('data/df_business.parquet')
columns_business = df_business.columns

categorias_yelp = pl.read_parquet('data/categorias_yelp.parquet')

data_coordenadas = joblib.load('data/ciudades_dash.joblib')

# ***********************************  MODELO SOLO FUNCIONA EN LINUX
with open('data/model.pkl', 'rb') as f:
    model = pickle.load(f)

with open('data/user_features.pkl', 'rb') as f:
    user_features = pickle.load(f)

with open('data/item_features.pkl', 'rb') as f:
    item_features = pickle.load(f)
# ******************************************************************************

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
        bad, message = valida_requets_app(request_app=request_app, df_business=df_business, df_user_ids=df_user_ids)
        if bad:
            raise HTTPException(status_code=400, detail=message)

        # OBTENIENDO SOLO LOS NEGOCIOS DE LAS CATEGORIAS SELECCIONADAS
        if len(request_app.categorias) > 0:
            mask = categorias_yelp['category_general'].is_in(request_app.categorias)
            lista_negocios = categorias_yelp.filter(mask)['business_id'].unique().to_list()
            mask = df_business['business_id'].is_in(lista_negocios)
            df_business_seleccionados = df_business.filter(mask)

        # FILTRANDO SEGUN LAS CARACTERISTICAS ESCOGIDAS
        if len(request_app.caracteristicas) > 0 and len(request_app.categorias) > 0:
            for caracteristica in request_app.caracteristicas:
                mask = df_business_seleccionados[caracteristica] == 1
                df_business_seleccionados = df_business_seleccionados.filter(mask)
        elif len(request_app.caracteristicas) > 0 and len(request_app.categorias) == 0:
            for caracteristica in request_app.caracteristicas:
                mask = df_business[caracteristica] == 1
                df_business_seleccionados = df_business.filter(mask)

        if len(request_app.caracteristicas) == 0 and len(request_app.categorias) == 0:
            df_business_seleccionados = df_business[columns_business]

        # FILTRANDO POR EL ESTADO Y TOMANDO EN CUENTA CUANDO HAY VECINOS
        if request_app.estado == 'MO':
            lista_estados = ['MO', 'TN', 'IL']
        elif request_app.estado == 'TN':
            lista_estados = ['TN', 'MO']
        elif request_app.estado == 'IL':
            lista_estados = ['IL', 'MO', 'IN']
        elif request_app.estado == 'IN':
            lista_estados = ['IN', 'IL']
        elif request_app.estado in ['PA', 'DE']:
            lista_estados = ['PA', 'DE']
        else:
            lista_estados = [request_app.estado]

        mask = df_business_seleccionados['Estado'].is_in(lista_estados)
        df_business_seleccionados = df_business_seleccionados.filter(mask)

        # CALCULANDO LAS COORDENADAS PROMEDIO DE LA CIUDAD
        data = data_coordenadas[orden_estados[request_app.estado]]
        df_coordenadas = pl.DataFrame(data)
        mask = df_coordenadas['City'] == request_app.ciudad
        latitud_1 = df_coordenadas.filter(mask)['Latitude'][0]
        longitud_1 = df_coordenadas.filter(mask)['Longitude'][0]

        # CALCULANDO DISTANCIAS
        df_business_seleccionados = df_business_seleccionados.with_columns(
            pl.struct(["Latitud", "Longitud"])
            .map_elements(lambda row: round(distancia_haversine(latitud_1, longitud_1, row["Latitud"], row["Longitud"]), 2), return_dtype=pl.Float64)
            .alias("Distancia")
        )

        # FILTRANDO POR DISTANCIA
        mask = df_business_seleccionados['Distancia'] <= request_app.km
        df_business_seleccionados = df_business_seleccionados.filter(mask)

        # APLICANDO PROCEDIMIENTO STANDAR DE LIGHTFM PARA OBTENER RECOMENDACIONES
    #  ***************** SOLO CORRE EN LINUX *************************
        business_id_list = df_business_seleccionados['business_id_int'].to_list()
        mask = df_user_ids['user_id'] == request_app.usuario
        user_id = df_user_ids.filter(mask)['user_id_int'][0]
        top_n = 5
        scores = model.predict(user_id, business_id_list, item_features=item_features,
                               user_features=user_features, num_threads=4)
        top_items = np.argsort(-scores)[:top_n]
        recomendations = [business_id_list[i] for i in top_items]

        # OBTENIENDO LAS RECOMENDACIONES
        mask = df_business_seleccionados['business_id_int'].is_in(recomendations)
        df_business_seleccionados = df_business_seleccionados.filter(mask)

    except IndexError:
        raise HTTPException(status_code=400, detail="BAD REQUEST")

    columns = ['Negocio', 'Direción', 'Ciudad', 'Estado', 'Lunes', 'Martes', 'Miercoles', 'Jueves',
               'Viernes', 'Sabado', 'Domingo', 'Distancia', 'Latitud', 'Longitud']
    response_columns = ['negocio', 'direccion', 'ciudad', 'estado', 'lunes', 'martes', 'miercoles', 'jueves',
                        'viernes', 'sabado', 'domingo', 'distancia', 'latitud', 'longitud']
    response = df_business_seleccionados[columns]
    response.columns = response_columns

    return BaseRecomendations(recomendations=response.to_dicts())

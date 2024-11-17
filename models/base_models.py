from pydantic import BaseModel


class BaseRecommendation(BaseModel):
    negocio: str
    direccion: str
    ciudad: str
    estado: str
    lunes: str
    martes: str
    miercoles: str
    jueves: str
    viernes: str
    sabado: str
    domingo: str
    distancia: float
    latitud: float
    longitud: float


class BaseRecomendations(BaseModel):
    recomendations: list[BaseRecommendation]


class BaseRecommendationRequest(BaseModel):
    km: int
    estado: str
    ciudad: str
    usuario: str
    caracteristicas: list
    categorias: list

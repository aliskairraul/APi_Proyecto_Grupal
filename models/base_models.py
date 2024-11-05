from pydantic import BaseModel


class BaseRecommendation(BaseModel):
    business_id: str
    name: str
    city: str
    address: str
    latitude: float
    longitude: float


class BaseRecomendations(BaseModel):
    recomendations: list[BaseRecommendation]


class BaseRecommendationRequest(BaseModel):
    state: str
    user_id_str: str
    category: str | None
    top_n: int = 5

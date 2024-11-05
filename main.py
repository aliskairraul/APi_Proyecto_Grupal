from fastapi import FastAPI

from routers import router_get_recomendations


app = FastAPI()

# ROUTERS:
app.include_router(router_get_recomendations.router)


@app.get("/")
async def read_root():
    return {
        "Message": "DataPulse Analytics",
        "Documentation": "/docs",
    }

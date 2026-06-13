from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.documents import router as documents_router
from app.api.history import router as history_router
from app.api.simulate import router as simulate_router
from app.config import settings
from app.database import init_sqlite


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_sqlite()
    yield


app = FastAPI(
    title="Backend Simulador DAD",
    description="Motor de validación de cumplimiento basado en la ecuación DAD",
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


app.include_router(documents_router)
app.include_router(history_router)
app.include_router(simulate_router)


@app.get("/")
def home():
    return {"status": "Backend del Simulador DAD Activo y Corriendo"}

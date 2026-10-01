from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from seed import seed_database
import catalog_service
import sales_service

app = FastAPI(title="API Restaurante / Panadería - Redes e Infraestructura")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
def startup_event():
    seed_database()

app.include_router(catalog_service.router)
app.include_router(sales_service.router)

@app.get("/")
def root():
    return {"status": "Back-end Activo y Funcionando"}
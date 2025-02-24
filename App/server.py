from fastapi import FastAPI
from contextlib import asynccontextmanager
from Integrations.index import Source
from API.routes.sources_router import SourcesRoutesRegister

@asynccontextmanager
async def lifespan(app: FastAPI):
    print("Starting up")
    yield
    print("Disconnected")

app = FastAPI(lifespan=lifespan)
src = Source()

sources_implementation = SourcesRoutesRegister(src=src)

app.include_router(sources_implementation.sourcesRouter, prefix="/source", tags=["SOURCE"])

@app.get("/")
async def root():
    return {"message": "API is running"}
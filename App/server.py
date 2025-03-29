from fastapi import FastAPI
from contextlib import asynccontextmanager
from Integrations.index import Source
from API.routes.sources_router import SourcesRoutesRegister
from Database.redis.redis_concrete import RedisConcrete
from Database.prisma.prisma_concrete import PrismaConcrete
import os

def intanciateRedis():

    host = os.getenv("REDIS_HOST")
    port = os.getenv("REDIS_PORT")
    db = os.getenv("REDIS_DB")
    password = os.getenv("REDIS_PASSWORD")

    return RedisConcrete(host, port, db, password)

async def instanciatePrisma():
    instance = PrismaConcrete()
    print("Connecting prisma...")
    await instance.connect()
    return instance

@asynccontextmanager
async def lifespan(app: FastAPI):
    print("Starting up")
    
    print("Connecting redis...")
    internalDb = intanciateRedis()
    print(f"Connected to redis {internalDb}")

    #==============================================
    internalPrisma = await instanciatePrisma()
    print(f"Connected to prisma {internalPrisma.prisma.is_connected()}")

    try:
        cachedCollections = await internalPrisma.prisma.cachedcollections.find_many()
        print(dict(cachedCollections[0]))
    except Exception as e:
        print(e)

    #==============================================

    yield
    await internalPrisma.disconnect()
    print("Disconnected")

app = FastAPI(lifespan=lifespan)
src = Source()

sources_implementation = SourcesRoutesRegister(src=src)

app.include_router(sources_implementation.sourcesRouter, prefix="/source", tags=["SOURCE"])

@app.get("/")
async def root():
    return {"message": "API is running"}
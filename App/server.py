from fastapi import FastAPI
from contextlib import asynccontextmanager
from Integrations.index import Source
from API.routes.engine_router import EngineRoutesRegister
from API.routes.cache_router import CacheRoutesRegister
from API.routes.sources_router import SourcesRoutesRegister
from Database.redis.redis_concrete import RedisConcrete
from Database.prisma.prisma_concrete import PrismaConcrete
from dotenv import load_dotenv, find_dotenv
import os

# Carrega as variáveis de ambiente do arquivo .env
load_dotenv(find_dotenv())

def intanciateRedis():
    # Obtém as variáveis de ambiente com valores padrão
    host = os.getenv("REDIS_HOST", "localhost")
    port = int(os.getenv("REDIS_PORT", 6379))  # Converte para inteiro
    db = int(os.getenv("REDIS_DB", 0))  # Converte para inteiro
    password = os.getenv("REDIS_PASSWORD", None)

    print(f"Connecting to Redis at {host}:{port} (DB: {db})")
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
    print(f"Connected to redis {internalDb.redis_client.ping()}")

    #==============================================
    internalPrisma = await instanciatePrisma()
    print(f"Connected to prisma {internalPrisma.prisma.is_connected()}")

    app.state.prisma = internalPrisma
    app.state.redis = internalDb
    
    try:
        cachedCollections = await internalPrisma.prisma.cachedcollections.find_many()
        
        parsed_collections = [dict(c) for c in cachedCollections]

        internalDb.load_collections(parsed_collections)

        # Initialize cache router
        cache_api = CacheRoutesRegister(redis_client=app.state.redis, prisma_client=internalPrisma)
        app.include_router(cache_api.cacheRouter, prefix="/cache", tags=["CACHE"])


        # Initialize engine router
        src = Source()
        #Initialize sources router
        sources_api = SourcesRoutesRegister(src=src)
        app.include_router(sources_api.sourcesRouter, prefix="/source", tags=["SOURCES"])
 
        engine_api = EngineRoutesRegister(src=src, redis_client=app.state.redis)
        app.include_router(engine_api.engineRouter, prefix="/engine", tags=["ENGINE"])

    except Exception as e:
        print(f"Error during initialization: {str(e)}")

    #==============================================

    yield
    await internalPrisma.disconnect()
    print("Disconnected")

app = FastAPI(lifespan=lifespan)

@app.get("/")
async def root():
    return {"message": "API is running"}
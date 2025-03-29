from .redis_implementation import RedisImplementation
import json
from datetime import datetime
class RedisConcrete(RedisImplementation):
    _instance = None 

    def __new__(cls, host, port, db, password=None):
        if cls._instance is None:
            cls._instance = super(RedisConcrete, cls).__new__(cls) 
        return cls._instance

    def __init__(self, host, port, db, password=None):
        if not hasattr(self, "_initialized"):
            super().__init__(host, port, db, password)
            self._initialized = True


    def update_collection_metadata(self, collection_name, increment=1):
        metadata_key = f"collection_metadata:{collection_name}"
        if not self.redis_client.exists(metadata_key):
            self.redis_client.hset(metadata_key, mapping={
                "created_at": json.dumps(str(datetime.now())),
                "updated_at": json.dumps(str(datetime.now())),
                "record_count": 0
            })
        else:
            self.redis_client.hincrby(metadata_key, "record_count", increment)
            self.redis_client.hset(metadata_key, "updated_at", json.dumps(str(datetime.now())))

    def get_collection_metadata(self, collection_name):
        metadata_key = f"collection_metadata:{collection_name}"
        metadata = self.redis_client.hgetall(metadata_key)
        return {k: json.loads(v) if self._is_json(v) else v for k, v in metadata.items()} if metadata else None

    def create_collection(self, collection_name):
        super().create_collection(collection_name)  # Mantém o comportamento da classe base
        self.update_collection_metadata(collection_name, 0)  # Atualiza metadados para coleção criada

    def add_to_collection(self, collection_name, record):
        record_id = super().add_to_collection(collection_name, record)  # Chama o método da classe base
        self.update_collection_metadata(collection_name, increment=1)  # Atualiza metadados
        return record_id

    def delete_from_collection(self, collection_name, record_id):
        super().delete_from_collection(collection_name, record_id)  # Chama o método da classe base
        self.update_collection_metadata(collection_name, increment=-1)  # Atualiza metadados
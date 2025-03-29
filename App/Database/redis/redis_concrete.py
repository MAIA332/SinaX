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

    def load_collections(self, collections):
        for collection in collections:
            if not self.redis_client.exists(collection["name"]):
                self.create_collection(collection["name"])
                self.initialize_collection_metadata(collection["name"], collection.get("fields", []))

    def initialize_collection_metadata(self, collection_name, fields):

        metadata_key = f"collection_metadata:{collection_name}"
        if not self.redis_client.exists(metadata_key):
            self.redis_client.hset(metadata_key, mapping={
                "created_at": json.dumps(str(datetime.now())),
                "updated_at": json.dumps(str(datetime.now())),
                "record_count": 0,
                "fields": json.dumps(fields),  # Armazena os campos dessa collection
                "size_in_bytes": 0
            })

    def update_collection_metadata(self, collection_name, increment=1, record_size=0):

        metadata_key = f"collection_metadata:{collection_name}"
        if not self.redis_client.exists(metadata_key):
            self.initialize_collection_metadata(collection_name, [])

        # Incrementa o contador de registros e o tamanho da collection
        self.redis_client.hincrby(metadata_key, "record_count", increment)
        self.redis_client.hincrby(metadata_key, "size_in_bytes", record_size)
        self.redis_client.hset(metadata_key, "updated_at", json.dumps(str(datetime.now())))

    def get_collection_metadata(self, collection_name):

        metadata_key = f"collection_metadata:{collection_name}"
        metadata = self.redis_client.hgetall(metadata_key)
        return {k: json.loads(v) if self._is_json(v) else v for k, v in metadata.items()} if metadata else None

    def create_collection(self, collection_name, size_in_bytes=0):

        super().create_collection(collection_name)  # Mantém o comportamento da classe base
        self.update_collection_metadata(collection_name, increment=0, record_size=size_in_bytes)  # Atualiza metadados ao criar

    def add_to_collection(self, collection_name, record):

        record_id = super().add_to_collection(collection_name, record)  # Chama o método da classe base
        record_size = sum(len(v.encode('utf-8')) for v in record.values())  # Calcula o tamanho do registro
        self.update_collection_metadata(collection_name, increment=1, record_size=record_size)  # Atualiza metadados
        return record_id

    def delete_from_collection(self, collection_name, record_id):
 
        super().delete_from_collection(collection_name, record_id)  # Chama o método da classe base
        self.update_collection_metadata(collection_name, increment=-1)  # Atualiza metadados (decrementa o contador)

    def _is_json(self, value):
 
        try:
            json.loads(value)
            return True
        except (ValueError, TypeError):
            return False

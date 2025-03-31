import redis
import json
import uuid

class RedisImplementation:
    def __init__(self,host,port,db,password):
        self.redis_client = redis.Redis(host=host, port=port, db=db,password=password,decode_responses=True)

    def get(self, key):
        return self.redis_client.get(key)

    def set(self, key, value):
        self.redis_client.set(key, value)

    def delete(self, key):
        self.redis_client.delete(key)

    def hset(self, key, value):
        self.redis_client.hset(key, mapping=value)

    def hgetall(self, key):
        return self.redis_client.hgetall(key)
    
    def create_collection(self, collection_name):
        if not self.redis_client.exists(collection_name):
            self.redis_client.lpush(collection_name, "")  # Adiciona um placeholder inicial
            self.redis_client.ltrim(collection_name, 1, -1)  # Remove o placeholder

    def add_to_collection(self, collection_name, record):

        record_id = str(uuid.uuid4())
        record["id"] = record_id
        key = f"{collection_name}:{record_id}"
        
        record_serialized = {k: json.dumps(v) if isinstance(v, (list, dict)) else v for k, v in record.items()}
        
        self.redis_client.hset(key, mapping=record_serialized)  
        return record_id
    
    def get_record(self, collection_name,record_id):

        key = f"{collection_name}:{record_id}"

        print(key)

        key_type = self.redis_client.type(key)

        record = self.redis_client.hgetall(key)
        if record:
            record_deserialized = {k: json.loads(v) if self._is_json(v) else v for k, v in record.items()}
            return record_deserialized
    
        return None


    def get_collection(self, collection_name):

        keys = self.redis_client.keys(f"{collection_name}:*") 
        records = []

        for key in keys:
            record = self.redis_client.hgetall(key)
            
            record_deserialized = {k: json.loads(v) if self._is_json(v) else v for k, v in record.items()}
            
            records.append(record_deserialized)
        return records
    
    def get_all_collections(self):
        keys = self.redis_client.keys("*:*")  # Pega todas as chaves que seguem o padrão "collection_name:*"
        collections = {}

        for key in keys:
            collection_name, record_id = key.split(":", 1)  # Divide o nome da coleção e o ID do registro
            record = self.redis_client.hgetall(key)
            
            record_deserialized = {k: json.loads(v) if self._is_json(v) else v for k, v in record.items()}
            
            if collection_name not in collections:
                collections[collection_name] = []
            
            collections[collection_name].append(record_deserialized)

        return collections

    def delete_collection(self, collection_name,record_id):
        key = f"{collection_name}:{record_id}"
        self.redis_client.delete(key)

    def clear_collection_data(self,collection_name):

        try:
            cursor = 0
            pattern = f"{collection_name}:*"
            
            while True:
                cursor, keys = self.redis_client.scan(cursor, match=pattern, count=1000)
                
                if keys:
                    self.redis_client.delete(*keys)
                
                if cursor == 0:
                    break

            return {"success":True,"message":f"All data in collection '{collection_name}' has been cleared."}
        except Exception as e:
            return {"success":False,"message":f"Failed to clear data in collection '{collection_name}': {e}"}
        
    def _is_json(self, value):
        try:
            json.loads(value)
            return True
        except (ValueError, TypeError):
            return False
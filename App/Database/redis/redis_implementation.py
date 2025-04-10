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
        """Add or update a record in the collection"""
        # If record has an ID, try to update existing record
        if "id" in record:
            record_id = record["id"]
            existing_record = self.get_record(collection_name, record_id)
            if existing_record:
                # Merge existing record with new data
                merged_record = {**existing_record, **record}
                # Ensure lists are properly merged
                for key, value in record.items():
                    if isinstance(value, list) and key in existing_record:
                        # If both are lists, concatenate them
                        if isinstance(existing_record[key], list):
                            merged_record[key] = existing_record[key] + value
                        else:
                            merged_record[key] = value
                
                # Update existing record
                key = f"{collection_name}:{record_id}"
                record_serialized = {k: json.dumps(v) if isinstance(v, (list, dict)) else v for k, v in merged_record.items()}
                self.redis_client.hset(key, mapping=record_serialized)
                return record_id

        # If no ID or record doesn't exist, create new record
        record_id = str(uuid.uuid4())
        record["id"] = record_id
        key = f"{collection_name}:{record_id}"
        
        # Add new record
        record_serialized = {k: json.dumps(v) if isinstance(v, (list, dict)) else v for k, v in record.items()}
        self.redis_client.hset(key, mapping=record_serialized)
        
        return record_id
    
    def get_record(self, collection_name, record_id):
        """Get a specific record from the collection"""
        key = f"{collection_name}:{record_id}"
        record = self.redis_client.hgetall(key)
        
        if not record:
            return None
            
        # Convert values back to their original types
        record_deserialized = {}
        for k, v in record.items():
            try:
                # Try to parse JSON first
                record_deserialized[k] = json.loads(v)
            except (json.JSONDecodeError, TypeError):
                # If not JSON, keep as string
                record_deserialized[k] = v
                
        return record_deserialized

    def get_collection(self, collection_name):
        """Get all records from a collection"""
        keys = self.redis_client.keys(f"{collection_name}:*")
        records = []

        for key in keys:
            record = self.redis_client.hgetall(key)
            if not record:
                continue
                
            # Convert values back to their original types
            record_deserialized = {}
            for k, v in record.items():
                try:
                    # Try to parse JSON first
                    record_deserialized[k] = json.loads(v)
                except (json.JSONDecodeError, TypeError):
                    # If not JSON, keep as string
                    record_deserialized[k] = v.decode('utf-8') if isinstance(v, bytes) else v
                    
            records.append(record_deserialized)
            
        return records
    
    def get_all_collections(self):
        print("get_all_collections")
        keys = self.redis_client.keys("*:*")  # Pega todas as chaves que seguem o padrão "collection_name:*"
        collections = {}

        for key in keys:
            print(key)
            collection_name, record_id = key.split(":", 1)  # Divide o nome da coleção e o ID do registro
            record = self.redis_client.hgetall(key)
            print(collection_name,record_id,record)
            record_deserialized = {k: json.loads(v) if self._is_json(v) else v for k, v in record.items()}
            
            if record_id not in collections:
                collections[record_id] = []
            
            collections[record_id].append(record_deserialized)

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
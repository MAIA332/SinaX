from .redis_implementation import RedisImplementation
import json
from datetime import datetime
from API.models.sources_models import QACache
import uuid

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
            # Initialize QA cache collection if it doesn't exist
            self.create_collection("qa_cache")

    def load_collections(self, collections):
        for collection in collections:
            print("updating collection")
            name = collection.get("name",f"no-name-{str(datetime.now())}")
            print(name)
            fields = collection.get("fields", [])
            print(fields)
            self.create_collection(name)
            self.update_collection_metadata(name, fields,collection.get("record_count", 0),collection.get("sizeInBytes", 0))

    def initialize_collection_metadata(self, collection_name, fields,record_count=0, size_in_bytes=0):
        metadata_key = f"collection_metadata:{collection_name}"
        self.redis_client.hset(metadata_key, mapping={
            "created_at": json.dumps(str(datetime.now())),
            "updated_at": json.dumps(str(datetime.now())),
            "record_count": record_count,
            "fields": json.dumps(fields),
            "size_in_bytes": size_in_bytes
        })

    def update_collection_metadata(self, collection_name, fields=[],record_count=0, size_in_bytes=0,increment=1):
        metadata_key = f"collection_metadata:{collection_name}"
        if not self.redis_client.exists(metadata_key):
            self.initialize_collection_metadata(collection_name, [])

        self.redis_client.hincrby(metadata_key, "record_count", record_count)
        self.redis_client.hincrby(metadata_key, "size_in_bytes", size_in_bytes)
        self.redis_client.hset(metadata_key, "updated_at", json.dumps(str(datetime.now())))

    def get_collection_metadata(self, collection_name):
        metadata_key = f"collection_metadata:{collection_name}"
        metadata = self.redis_client.hgetall(metadata_key)
        return {k: json.loads(v) if self._is_json(v) else v for k, v in metadata.items()} if metadata else None

    def create_collection(self, collection_name, size_in_bytes=0):
        super().create_collection(collection_name)
        self.update_collection_metadata(collection_name, increment=0, size_in_bytes=size_in_bytes)

    def _calculate_record_size(self, record):
        """Calcula o tamanho do registro em bytes"""
        total_size = 0
        for value in record.values():
            if isinstance(value, (list, dict)):
                total_size += len(json.dumps(value).encode('utf-8'))
            else:
                total_size += len(str(value).encode('utf-8'))
        return total_size

    def add_to_collection(self, collection_name, record):
        """Add or update a record in the collection"""
        # If record has an ID, try to update existing record
        if "id" in record:
            record_id = record["id"]
            existing_record = self.get_record(collection_name, record_id)
            if existing_record:
                # Update existing record
                self.redis_client.hset(
                    f"{collection_name}:{record_id}",
                    mapping={k: json.dumps(v) if isinstance(v, (dict, list)) else str(v) 
                            for k, v in record.items()}
                )
                # Update metadata
                record_size = self._calculate_record_size(record)
                self.update_collection_metadata(collection_name, increment=0, size_in_bytes=record_size)
                return record_id

        # If no ID or record doesn't exist, create new record
        record_id = str(uuid.uuid4())
        record["id"] = record_id
        
        # Add new record
        self.redis_client.hset(
            f"{collection_name}:{record_id}",
            mapping={k: json.dumps(v) if isinstance(v, (dict, list)) else str(v) 
                    for k, v in record.items()}
        )
        
        # Update metadata
        record_size = self._calculate_record_size(record)
        self.update_collection_metadata(collection_name, increment=1, size_in_bytes=record_size)
        
        return record_id

    def delete_from_collection(self, collection_name, record_id):
        super().delete_from_collection(collection_name, record_id)
        self.update_collection_metadata(collection_name, increment=-1)

    async def cache_qa(self, qa: QACache):
        """Cache a question-answer pair"""
        qa_dict = qa.dict()
        return self.add_to_collection("qa_cache", qa_dict)

    async def get_similar_qa(self, question: str):
        """Get similar question-answer pairs from cache"""
        cached_qa = self.get_collection("qa_cache")
        if not cached_qa:
            return None
            
        # Find the most similar question
        best_match = None
        best_score = 0.0
        
        for qa in cached_qa:
            cached_question = qa.get("question")
            if not cached_question:
                continue
                
            # Calculate similarity score
            similarity_score = self._calculate_similarity(question, cached_question)
            
            # Update best match if this one is better
            if similarity_score > best_score:
                best_score = similarity_score
                best_match = qa
                
        # If we found a good match (similarity > 0.8)
        if best_match and best_score > 0.8:
            return {
                "cached": True,
                "content": {
                    "answer": best_match.get("answer"),
                    "llm_provider": best_match.get("llm_provider"),
                    "similarity_score": best_score
                }
            }
                
        return None

    def _calculate_similarity(self, str1: str, str2: str) -> float:
        """Calculate similarity between two strings using Jaccard similarity"""
        # Convert to sets of words
        set1 = set(str1.lower().split())
        set2 = set(str2.lower().split())
        
        # Calculate Jaccard similarity
        intersection = len(set1.intersection(set2))
        union = len(set1.union(set2))
        
        return intersection / union if union > 0 else 0.0

    def _is_json(self, value):
 
        try:
            json.loads(value)
            return True
        except (ValueError, TypeError):
            return False

    def get_record(self, collection_name, record_id):
        """Get a specific record from the collection"""
        record_data = self.redis_client.hgetall(f"{collection_name}:{record_id}")
        if not record_data:
            return None
            
        # Convert values back to their original types
        record = {}
        for key, value in record_data.items():
            try:
                # Try to parse JSON first
                record[key] = json.loads(value)
            except (json.JSONDecodeError, TypeError):
                # If not JSON, keep as string
                record[key] = value.decode('utf-8') if isinstance(value, bytes) else value
                
        return record

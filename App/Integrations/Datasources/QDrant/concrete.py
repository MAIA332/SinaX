from dotenv import load_dotenv,find_dotenv
import os
import uuid
from qdrant_client import QdrantClient
from qdrant_client.models import Filter, FieldCondition, MatchValue
from qdrant_client.models import PointStruct
from qdrant_client.models import Distance, VectorParams
from sentence_transformers import SentenceTransformer
from langchain_community.embeddings import SentenceTransformerEmbeddings
from langchain_community.vectorstores import Qdrant
class QDrantConcrete:
    def __init__(self):
        self.base_url = os.getenv("QDRANT_HOST")
        self.client = QdrantClient(self.base_url)
        self.main_collection_name = "sinaX"
        self.vectordim = 768 
        self.Distance = Distance 
        self.base_model = "all-MiniLM-L6-v2"  
        self.selected_model = None 

    def define_embbedings_model(self, model=None):
        self.model = SentenceTransformer(model)
        self.selected_model = model

    def create_collection(self, collection_name, size=768, distance=Distance.COSINE):
        print(f"Criando a coleção '{collection_name}'...")
        self.client.create_collection(
            collection_name=collection_name,
            vectors_config=VectorParams(size=size, distance=distance),
        )
          
    def insert_vectors(self, collection_name, vectors, ids=None, payloads=None):
        points = []
        for i in range(len(vectors)):
            point = {
                'id': ids[i] if ids else str(uuid.uuid4()),  # Gera UUIDs se não for passado
                'vector': vectors[i],
            }
            if payloads:
                point['payload'] = payloads[i]  # Adiciona payload, se fornecido
            points.append(point)
        
        self.client.upsert(
            collection_name=collection_name,
            points=points
        )

    def generate_embeddings(self, texts):
        embeddings = self.model.encode(texts)
        return embeddings

    def search_vectors(self, collection_name, query_text, limit=5):
        query_vector = self.generate_embeddings([query_text])[0]
        result = self.client.search(
            collection_name=collection_name,
            query_vector=query_vector,
            limit=limit
        )
        return result

    def get_qdrant_vectorstore(self, collection_name):
        embeddings = SentenceTransformerEmbeddings(model=self.model)
        vectorstore = Qdrant(client=self.client, collection_name=collection_name, embeddings=embeddings)
        return vectorstore

    def delete_collection(self, collection_name):
        self.client.delete_collection(collection_name=collection_name)

    def describe_collection(self, collection_name):
        collection_info = self.client.get_collection(collection_name)
        return collection_info

    def get_vector(self, collection_name, vector_id):
        vector_data = self.client.retrieve(
            collection_name=collection_name,
            ids=[vector_id]
        )
        return vector_data

    def update_vectors(self, collection_name, vector_ids, new_vectors, payloads=None):
        points = []
        for i in range(len(new_vectors)):
            point = {
                'id': vector_ids[i],
                'vector': new_vectors[i],
            }
            if payloads:
                point['payload'] = payloads[i]
            points.append(point)
        
        self.client.upsert(
            collection_name=collection_name,
            points=points
        )

    def upsert_vectors(self, collection_name, vectors, ids=None, payloads=None):
        if ids is None:
            ids = [str(uuid.uuid4()) for _ in range(len(vectors))]
        
        self.insert_vectors(collection_name, vectors, ids, payloads)

    def process_document(self, document_text):
        paragraphs = document_text.split("\n")
        return paragraphs

    def store_document_in_qdrant(self, collection_name, document_text):
        document_id = str(uuid.uuid4())
        parts = self.process_document(document_text)
        embeddings = self.generate_embeddings(parts)
        ids = [str(uuid.uuid4()) for _ in range(len(parts))]
        payloads = [{"content": part} for part in parts]
        
        self.upsert_vectors(collection_name, embeddings, ids, payloads)
        return document_id

    def delete_document_from_qdrant(self, collection_name, document_id):
        self.client.delete(
            collection_name=collection_name,
            points_selector={'ids': [document_id]}
        )
        print(f"Documento {document_id} e seus embeddings foram deletados.")
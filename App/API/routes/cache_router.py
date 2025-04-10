from fastapi import APIRouter
from API.models.sources_models import QACache
from Integrations.LLM.similarity import QuestionSimilarity
from datetime import datetime
from fastapi import HTTPException

class CacheRouterImplementation:
    def __init__(self, redis_client=None, prisma_client=None):
        self.cacheRouter = APIRouter()
        self.redis_client = redis_client
        self.prisma_client = prisma_client
        self.similarity_checker = QuestionSimilarity()

class CacheRoutesRegister(CacheRouterImplementation):
    def __init__(self, redis_client=None, prisma_client=None):
        """
        Constructor for CacheRoutesRegister class.

        Parameters
        ----------
        redis_client : RedisImplementation
            An instance of RedisImplementation class.

        Returns
        -------
        None
        """

        super().__init__(redis_client=redis_client, prisma_client=prisma_client)
        
        @self.cacheRouter.get("/")
        async def get_all_collections():
            collections = await self.prisma_client.get_cachedcollections()
            return {"message": "success", "content": collections}
        
        @self.cacheRouter.get("/sync")
        async def sync_collections():
            cachedCollections = await self.prisma_client.get_cachedcollections()
            parsed_collections = [dict(c) for c in cachedCollections]
            result = self.redis_client.load_collections(parsed_collections)
            return {"message": "success", "content": result}

        @self.cacheRouter.post("/qa")
        async def cache_qa(qa: QACache):
            # Add timestamp
            qa_dict = qa.dict()
            qa_dict['created_at'] = str(datetime.now())
            qa_dict['updated_at'] = str(datetime.now())
            
            # Store in Redis
            record_id = self.redis_client.add_to_collection("qa_cache", qa_dict)
            return {"message": "success", "content": {"id": record_id}}

        @self.cacheRouter.get("/qa/{question}")
        async def get_similar_qa(question: str):
            # Get all cached QAs
            cached_qa = self.redis_client.get_collection("qa_cache")
            
            # Find similar question
            similar_qa = self.similarity_checker.find_similar_question(question, cached_qa)
            
            if similar_qa:
                return {"message": "success", "content": similar_qa, "cached": True}
            return {"message": "success", "content": None, "cached": False}

        @self.cacheRouter.delete("/clear")
        async def clear_cache():
            """Clear all cached data"""
            try:
                # Clear QA cache
                qa_cache_result = self.redis_client.clear_collection_data("qa_cache")
                
                # Clear workspaces
                workspaces_result = self.redis_client.clear_collection_data("workspaces")
                
                # Clear collection metadata
                metadata_keys = self.redis_client.redis_client.keys("collection_metadata:*")
                if metadata_keys:
                    self.redis_client.redis_client.delete(*metadata_keys)
                
                return {
                    "message": "success",
                    "content": {
                        "qa_cache_cleared": qa_cache_result.get("success", False),
                        "workspaces_cleared": workspaces_result.get("success", False),
                        "metadata_cleared": len(metadata_keys) > 0,
                        "cleared": True
                    }
                }
            except Exception as e:
                raise HTTPException(
                    status_code=500,
                    detail=f"Failed to clear cache: {str(e)}"
                )

        @self.cacheRouter.get("/view")
        async def view_cache():
            """View all cached data"""
            try:
                # Get all collections
                collections = self.redis_client.get_all_collections()
                
                # Get QA cache
                qa_cache = self.redis_client.get_collection("qa_cache")
                
                # Get workspaces
                workspaces = self.redis_client.get_collection("workspaces")
                
                # Get collection metadata
                metadata = {}
                metadata_keys = self.redis_client.redis_client.keys("collection_metadata:*")
                for key in metadata_keys:
                    # Key is already a string, no need to decode
                    collection_name = key.split(":")[1]
                    metadata[collection_name] = self.redis_client.get_collection_metadata(collection_name)
                
                return {
                    "message": "success",
                    "content": {
                        "qa_cache": qa_cache,
                        "workspaces": workspaces,
                        "collections": collections,
                        "metadata": metadata
                    }
                }
            except Exception as e:
                raise HTTPException(
                    status_code=500,
                    detail=f"Failed to view cache: {str(e)}"
                )
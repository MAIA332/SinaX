from fastapi import APIRouter
from API.models.sources_models import SourcesExecute, QACache
from datetime import datetime

class SourcesRouterImplementation:
    def __init__(self, src=None):
        self.sourcesRouter = APIRouter()
        self.src = src

class SourcesRoutesRegister(SourcesRouterImplementation):
    def __init__(self, src=None):
        super().__init__(src=src)
        
        @self.sourcesRouter.get("/")
        async def root():
            return {"message": "success", "content": f"{self.src.sources[0]}"}
        
        @self.sourcesRouter.post("/execute")
        async def execute(execute: SourcesExecute):
            # Check if this is a question-answering request
            if execute.method_name == "quest_something":
                question = execute.args[0] if execute.args else None
                workspace_id = execute.args[1] if len(execute.args) > 1 else None
                
                if question and workspace_id:
                    # Get LLM instance
                    llm_instance = self.src.LLMLoadBalance.get_instance_for_method()
                    
                    # Check cache first
                    cached_response = await self.src.redis_client.get_similar_qa(question)
                    if cached_response and cached_response.get("cached"):
                        return {"message": "success", "content": cached_response["content"]["answer"], "cached": True}
                    
                    # If not in cache, process with LLM
                    result = self.src.execute_method_on_instance(execute.plugin_name, execute.method_name, *execute.args)
                    
                    # Cache the result
                    qa_cache = QACache(
                        question=question,
                        answer=result,
                        llm_provider=llm_instance["name"]
                    )
                    await self.src.redis_client.cache_qa(qa_cache)
                    
                    return {"message": "success", "content": result, "cached": False}
            
            # For non-QA requests, process normally
            result = self.src.execute_method_on_instance(execute.plugin_name, execute.method_name, *execute.args)
            return {"message": "success", "content": result}
        
        @self.sourcesRouter.get("/hooks")
        async def execute():
            return {"message": "success", "content": "result"}
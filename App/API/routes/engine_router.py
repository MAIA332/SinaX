from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from datetime import datetime
import uuid
import json

class CompletionRequest(BaseModel):
    question: str
    workspace_id: Optional[str] = None

class CompletionResponse(BaseModel):
    answer: str
    workspace_id: str
    llm_provider: str
    cached: bool
    similarity_score: Optional[float] = None

class Workspace(BaseModel):
    id: str
    history: List[Dict[str, str]]
    created_at: str
    updated_at: str

class EngineRouterImplementation:
    def __init__(self, src=None, redis_client=None):
        self.engineRouter = APIRouter()
        self.src = src
        self.redis_client = redis_client

class EngineRoutesRegister(EngineRouterImplementation):
    def __init__(self, src=None, redis_client=None):
        super().__init__(src=src, redis_client=redis_client)
        
        @self.engineRouter.post("/completion")
        async def completion(request: CompletionRequest):
            # Get or create workspace
            workspace_id = request.workspace_id
            if not workspace_id:
                workspace_id = str(uuid.uuid4())
                # Initialize workspace in Redis
                workspace = {
                    "id": workspace_id,
                    "history": [],
                    "created_at": str(datetime.now()),
                    "updated_at": str(datetime.now())
                }
                self.redis_client.add_to_collection("workspaces", workspace)

            # Check if question is contextual
            contextual_keywords = [
                "acabei de perguntar",
                "perguntei",
                "disse",
                "falei",
                "mencionei",
                "anteriormente",
                "antes",
                "última pergunta",
                "última mensagem",
                "histórico",
                "contexto",
                "conversa anterior",
                "diálogo anterior",
                "discussão anterior",
                "comentário anterior",
                "resposta anterior",
                "explicação anterior",
                "informação anterior",
                "dado anterior",
                "fato anterior",
                "referência anterior",
                "citado anteriormente",
                "mencionado antes",
                "falado antes",
                "dito antes",
                "comentado antes",
                "explicado antes",
                "respondido antes",
                "informado antes",
                "citado antes"
            ]
            
            is_contextual = any(keyword in request.question.lower() for keyword in contextual_keywords)
            
            # Only check cache for non-contextual questions
            if not is_contextual:
                cached_response = await self.redis_client.get_similar_qa(request.question)
                if cached_response and isinstance(cached_response, dict) and cached_response.get("cached"):
                    return CompletionResponse(
                        answer=cached_response["content"]["answer"],
                        workspace_id=workspace_id,
                        llm_provider=cached_response["content"]["llm_provider"],
                        cached=True,
                        similarity_score=cached_response["content"]["similarity_score"]
                    )

            # Get LLM instance using load balancer
            llm_instance = self.src.LLMLoadBalance.get_instance_for_method()
            
            # Process question with LLM
            result = self.src.execute_method_on_instance(
                llm_instance["name"],
                "quest_something",
                request.question,
                workspace_id
            )

            # Only cache non-contextual questions
            if not is_contextual:
                # Cache the result
                qa_cache = {
                    "question": request.question,
                    "answer": result,
                    "llm_provider": llm_instance["name"],
                    "created_at": str(datetime.now()),
                    "updated_at": str(datetime.now())
                }
                self.redis_client.add_to_collection("qa_cache", qa_cache)

            # Update workspace history
            workspace = self.redis_client.get_record("workspaces", workspace_id)
            if workspace:
                # Ensure history is a list
                if not isinstance(workspace.get("history", []), list):
                    workspace["history"] = []
                
                # Create new history entry
                new_history = [
                    {
                        "role": "user",
                        "content": request.question,
                        "timestamp": str(datetime.now())
                    },
                    {
                        "role": "assistant",
                        "content": result,
                        "timestamp": str(datetime.now())
                    }
                ]
                
                # Update workspace with new history
                workspace["history"] = workspace["history"] + new_history
                workspace["updated_at"] = str(datetime.now())
                
                # Update workspace in Redis
                self.redis_client.add_to_collection("workspaces", workspace)
            else:
                # Create new workspace with history
                workspace = {
                    "id": workspace_id,
                    "history": [
                        {
                            "role": "user",
                            "content": request.question,
                            "timestamp": str(datetime.now())
                        },
                        {
                            "role": "assistant",
                            "content": result,
                            "timestamp": str(datetime.now())
                        }
                    ],
                    "created_at": str(datetime.now()),
                    "updated_at": str(datetime.now())
                }
                self.redis_client.add_to_collection("workspaces", workspace)

            return CompletionResponse(
                answer=result,
                workspace_id=workspace_id,
                llm_provider=llm_instance["name"],
                cached=False
            )

        @self.engineRouter.get("/workspaces")
        async def get_workspaces():
            workspaces = self.redis_client.get_collection("workspaces")
            return {
                "message": "success",
                "content": workspaces
            }

        @self.engineRouter.post("/workspaces")
        async def create_workspace(name: Optional[str] = None):
            workspace_id = str(uuid.uuid4())
            workspace = {
                "id": workspace_id,
                "name": name or f"Workspace {workspace_id[:8]}",
                "history": [],
                "created_at": str(datetime.now()),
                "updated_at": str(datetime.now())
            }
            self.redis_client.add_to_collection("workspaces", workspace)
            return {
                "message": "success",
                "content": workspace
            }

        @self.engineRouter.get("/workspaces/{workspace_id}")
        async def get_workspace(workspace_id: str):
            workspace = self.redis_client.get_record("workspaces", workspace_id)
            if not workspace:
                raise HTTPException(status_code=404, detail="Workspace not found")
            return {
                "message": "success",
                "content": workspace
            }

        @self.engineRouter.delete("/workspaces/{workspace_id}")
        async def delete_workspace(workspace_id: str):
            workspace = self.redis_client.get_record("workspaces", workspace_id)
            if not workspace:
                raise HTTPException(status_code=404, detail="Workspace not found")
            
            self.redis_client.delete_collection("workspaces", workspace_id)
            return {
                "message": "success",
                "content": {
                    "id": workspace_id,
                    "deleted": True
                }
            }

        @self.engineRouter.delete("/workspaces")
        async def delete_all_workspaces():
            """Delete all workspaces"""
            try:
                # Get all workspaces
                workspaces = self.redis_client.get_collection("workspaces")
                
                # Delete each workspace
                for workspace in workspaces:
                    self.redis_client.delete_collection("workspaces", workspace["id"])
                
                return {
                    "message": "success",
                    "content": {
                        "deleted_count": len(workspaces),
                        "deleted": True
                    }
                }
            except Exception as e:
                raise HTTPException(
                    status_code=500,
                    detail=f"Failed to delete workspaces: {str(e)}"
                ) 
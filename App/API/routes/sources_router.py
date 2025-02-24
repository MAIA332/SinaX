from fastapi import APIRouter
from API.models.sources_models import SourcesExecute

class SourcesRouterImplementation:
    def __init__(self, src=None):
        self.sourcesRouter = APIRouter()
        self.src = src

class SourcesRoutesRegister(SourcesRouterImplementation):
    def __init__(self, src=None):
        super().__init__(src=src)
        
        @self.sourcesRouter.get("/")
        async def root():
            return {"message": "success", "content": f"{self.src.sources[0]}"
            }
        
        @self.sourcesRouter.post("/execute")
        async def execute(execute:SourcesExecute):

            result = self.src.execute_method_on_instance(execute.plugin_name,execute.method_name,*execute.args)

            return {"message": "success", "content": result}
        
        @self.sourcesRouter.get("/hooks")
        async def execute():

            #result = self.src.execute_method_on_instance(execute.plugin_name,execute.method_name,*execute.args)

            return {"message": "success", "content": "result"}
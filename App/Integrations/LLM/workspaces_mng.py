import uuid

class WorkspacesMng:
    def __init__(self, instance_data):
        self.instance_data = instance_data

    def createWorkspace(self,name="None"):
        id = uuid.uuid4()
        self.instance_data["workspace"].append(
            {
                "id":id,
                "messages":[],
                "config":{
                    "system_paradigma":[],
                    "name":name,
                    "history_limit":5
                }
            }
        )

        return id
    
    def getWorkspace(self,id):

        if isinstance(id, str):
            id = uuid.UUID(id)
            
        workspace = [i for i in self.instance_data["workspace"] if i["id"] == id]
        
        if len(workspace)>=1:
            return workspace[0]
        else:
            return None
        
    def update_workspace_history(self,payload,workspaceId):
        workspace = self.getWorkspace(workspaceId)
        
        if not workspace:
            return {"message":"workspace not found"}
        
        if len(workspace["messages"])<= workspace["config"]["history_limit"]:
            workspace["messages"].append(payload)

        for i in range(len(self.instance_data["workspace"])):
            if self.instance_data["workspace"][i]["id"] == workspaceId:
                self.instance_data["workspace"][i] = workspace
                break

        return workspace
    
    def update_workspace_paradigma(self,payload,workspaceId):
        workspace = self.getWorkspace(workspaceId)
        
        if not workspace:
            return {"message":"workspace not found"}
        
        workspace["config"]["system_paradigma"].append({"role":"system","content":payload})

        for i in range(len(self.instance_data["workspace"])):
            if self.instance_data["workspace"][i]["id"] == workspaceId:
                self.instance_data["workspace"][i] = workspace
                break

        return workspace
    
    def update_workspace_hoistory_limit(self,limit,workspaceId):
        workspace = self.getWorkspace(workspaceId)
        
        if not workspace:
            return {"message":"workspace not found"}
        
        workspace["config"]["history_limit"] = limit

        for i in range(len(self.instance_data["workspace"])):
            if self.instance_data["workspace"][i]["id"] == workspaceId:
                self.instance_data["workspace"][i] = workspace
                break

        return workspace

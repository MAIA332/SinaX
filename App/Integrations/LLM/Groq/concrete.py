from dotenv import load_dotenv,find_dotenv
import os
import uuid
from groq import Groq
from Integrations.LLM.workspaces_mng import WorkspacesMng

class PyGroq(WorkspacesMng):
    def __init__(self,temperature=1,max_tokens=8192,top_p=1,stream=False,stop=None,seed=10,model="llama-3.3-70b-versatile") -> None:

        load_dotenv(find_dotenv())  
        self.KEY =  os.environ.get("GROQ_API_KEY")

        self.client = Groq(
            api_key=self.KEY,
        )

        self.instance_data = {
            "id":uuid.uuid4(),
            "workspace":[
               
            ],

            "hiper_params":{
                "temperature":temperature,
                "max_tokens":max_tokens,
                "top_p":top_p,
                "stream":stream,
                "stop":stop,
                "seed":seed,
                "model":model
            }
        }
        super().__init__(self.instance_data)

    
    def quest_something(self,input,workspaceId):

        if isinstance(workspaceId, str):
            workspaceId = uuid.UUID(workspaceId)

        messages = [j for i in self.instance_data["workspace"] if i["id"] == workspaceId for j in i["config"]["system_paradigma"]]
        
        updated_workspace = self.update_workspace_history({"role":"user","content":input},workspaceId)

        for i in updated_workspace["messages"]:
            messages.append(i)

        chat_completion = self.client.chat.completions.create(
            messages=messages,
            temperature=self.instance_data["hiper_params"]["temperature"],
            max_tokens=self.instance_data["hiper_params"]["max_tokens"],
            top_p=self.instance_data["hiper_params"]["top_p"],
            stream=self.instance_data["hiper_params"]["stream"],
            stop=self.instance_data["hiper_params"]["stop"],
            seed=self.instance_data["hiper_params"]["seed"],
            model=self.instance_data["hiper_params"]["model"],
        )

        response = chat_completion.choices[0].message.content

        updated_workspace = self.update_workspace_history({"role":"assistant","content":response},workspaceId)

        return response
    
        
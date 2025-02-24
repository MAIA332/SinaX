import os,json

class LLM:
    def __init__(self,services):
        self.services = services
        self.LLMs = self.determine_LLMs()
        self.LLMs_isntances = self.instance_LLMs()

    def instance_LLMs(self):
        instances = []
        for i in self.LLMs:
            plugin_name = i["plugin_name"]
            
            lib = __import__(f"Integrations.LLM.{plugin_name}.implementation", fromlist=[""])
            class_name = i["entry_point"]

            plugin_class = getattr(lib, class_name)
        
            object_instance = plugin_class()

            instances.append({
                "name":plugin_name,
                "instance":object_instance
            })

        return instances
        
    def determine_LLMs(self):
        LLMs = [self.services[i] for i in self.services if self.services[i]["habilited"] == True]
        return LLMs